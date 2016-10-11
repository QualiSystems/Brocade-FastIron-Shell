#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re

from cloudshell.networking.brocade.autoload.brocade_snmp_autoload import BrocadeSnmpAutoload
from cloudshell.networking.autoload.networking_autoload_resource_attributes import NetworkingStandardRootAttributes
from cloudshell.networking.autoload.networking_autoload_resource_structure import Chassis, Module, PowerPort, Port, \
    PortChannel
from cloudshell.shell.core.config_utils import override_attributes_from_config
from cloudshell.shell.core.driver_context import AutoLoadDetails


class FastIronSnmpAutoload(BrocadeSnmpAutoload):
    SUPPORTED_OS = ["Brocade.+ICX.+IronWare"]

    def __init__(self, snmp_handler=None, logger=None, config=None, cli_service=None, snmp_community=None):
        """ Basic init with injected snmp handler and logger

        :param snmp_handler:
        :param logger:
        :param config:
        :return:
        """

        BrocadeSnmpAutoload.__init__(self,  snmp_handler, logger, config, cli_service, snmp_community)

        self.port_exclude_pattern = r'serial|stack|engine|management|mgmt'
        self.relative_path = {}
        self.resources = list()
        self.attributes = list()

        """Override attributes from global config"""
        overridden_config = override_attributes_from_config(FastIronSnmpAutoload, config=self.config)
        self._supported_os = overridden_config.SUPPORTED_OS

    def _is_valid_device_os(self):
        """ Validate device OS using snmp
            :return: True or False
        """

        system_description = self.snmp.get_property("SNMPv2-MIB", "sysDescr", 0)
        self.logger.debug("Detected system description: '{0}'".format(system_description))
        result = re.search(r"({0})".format("|".join(self._supported_os)),
                           system_description,
                           flags=re.DOTALL | re.IGNORECASE)

        if result:
            return True
        else:
            error_message = "Incompatible driver! Please use this driver for '{0}' operation system(s)". \
                format(str(tuple(self._supported_os)))
            self.logger.error(error_message)
            return False

    def _get_autoload_details(self):
        """
        Read device structure and attributes:
        chassis, modules, submodules, ports, port-channels and power supplies

        :return: AutoLoadDetails object or Exception
        """

        if not self._is_valid_device_os():
            raise Exception("Unsupported device OS")

        self.logger.info("*" * 70)
        self.logger.info("Start SNMP discovery process .....")

        self.load_additional_mibs()
        self.snmp.update_mib_sources(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mibs")))

        self.snmp.load_mib(["FOUNDRY-SN-AGENT-MIB", "FOUNDRY-SN-SWITCH-GROUP-MIB", "FOUNDRY-SN-STACKING-MIB",
                            "FOUNDRY-SN-IP-MIB"])

        self.lldp_local_table = self.snmp.get_table('LLDP-MIB', 'lldpLocPortDesc')
        self.lldp_remote_table = self.snmp.get_table('LLDP-MIB', 'lldpRemTable')
        self.ip_v4_table = self.snmp.get_table('IP-MIB', 'ipAddrTable')
        self.ip_v6_table = self.snmp.get_table('IPV6-MIB', 'ipv6AddrEntry')

        self._get_device_details()
        self._get_chassis_info()
        self._get_power_ports_info()
        self._get_modules_info()
        self._get_ports_info()

        result = AutoLoadDetails(resources=self.resources, attributes=self.attributes)
        self.logger.info("*" * 50)
        self.logger.info("SNMP discovery Completed.")
        self.logger.info("The following platform structure detected:\nModel, Name, Relative Path, Unique Id")

        for resource in self.resources:
            self.logger.info("{0},\t\t{1},\t\t{2},\t\t{3}".format(resource.model, resource.name,
                                                                  resource.relative_address, resource.unique_identifier))
        self.logger.info("-" * 30)
        for attribute in self.attributes:
            self.logger.info("{0},\t\t{1},\t\t{2}".format(attribute.relative_address, attribute.attribute_name,
                                                          attribute.attribute_value))
        self.logger.info("*" * 50)

        return result

    def _get_device_details(self):
        """ Get root element attributes """

        self.logger.info("Load Device Attributes:")
        result = {"system_name": self.snmp.get_property("SNMPv2-MIB", "sysName", 0),
                  "vendor": "Brocade",
                  "model": self._get_device_model(),
                  "location": self.snmp.get_property("SNMPv2-MIB", "sysLocation", 0),
                  "contact": self.snmp.get_property("SNMPv2-MIB", "sysContact", 0),
                  "version": ""}

        match_version = re.search(r"Version\s+(?P<software_version>\S+)\S*\s+",
                                  self.snmp.get_property("SNMPv2-MIB", "sysDescr", 0))
        if match_version:
            result["version"] = match_version.groupdict()["software_version"].replace(",", "")

        root = NetworkingStandardRootAttributes(**result)
        self.attributes.extend(root.get_autoload_resource_attributes())
        self.logger.info("Load Device Attributes completed.")

    def _get_device_model(self):
        """Get device model form snmp SNMPv2 mib

        :return: device model
        :rtype: str
        """

        result = ""
        match_name = re.search(r"::(?P<model>\S+$)", self.snmp.get_property("SNMPv2-MIB", "sysObjectID", 0))
        if match_name:
            result = match_name.groupdict()["model"].capitalize()
        return result

    def _add_resource(self, resource):
        """Add object data to resources and attributes lists

        :param resource: object which contains all required data for certain resource
        """

        self.resources.append(resource.get_autoload_resource_details())
        self.attributes.extend(resource.get_autoload_resource_attributes())

    def _get_chassis_info(self):
        """ Get chassis elements attributes """

        self.logger.info("Start loading Chassis")

        for chassis in self.snmp.get_table("FOUNDRY-SN-AGENT-MIB", "snChasUnitTable").values():
            chassis_id = chassis.get("snChasUnitIndex")
            self.relative_path.update({chassis_id: chassis_id})

            chassis_details_map = {
                "chassis_model": self.snmp.get_property("FOUNDRY-SN-STACKING-MIB",
                                                        "snStackingConfigUnitType",
                                                        int(chassis_id)),
                "serial_number": chassis.get("snChasUnitSerNum", "Unknown")
            }
            chassis_object = Chassis(relative_path=chassis_id, **chassis_details_map)
            self._add_resource(chassis_object)
            self.logger.info("Added Chassis '{}'".format(chassis_details_map["chassis_model"]))

        self.logger.info("Finished loading Chassis")

    def _get_power_ports_info(self):
        """ Get power port elements attributes """

        self.logger.info("Start loading Power Ports")
        for power_port in self.snmp.get_table("FOUNDRY-SN-AGENT-MIB", "snChasPwrSupply2Table").values():
            power_port_id = power_port.get("snChasPwrSupply2Index")

            relative_path = '{0}/PP{0}-{1}'.format(power_port.get("snChasPwrSupply2Unit"), power_port_id)
            port_name = "PP{}".format(power_port_id)

            power_port_full_info = self.snmp.get_property("FOUNDRY-SN-AGENT-MIB",
                                                          "snChasPwrSupplyDescription",
                                                          int(power_port_id))
            # power_port_full_info_2 = self.snmp.var_binds[0]._ObjectType__args[1]._value
            if power_port_full_info.startswith("0x"):
                power_port_full_info = power_port_full_info[2:].decode("hex")

            matched = re.match(r"(?P<descr>.+)"
                               r"Model Number:(?P<port_model>.+)"
                               r"Serial Number:(?P<serial_number>.+)"
                               r"Firmware Ver:(?P<version>.+)", power_port_full_info, re.DOTALL)

            if matched:
                port_details = {"port_model": matched.groupdict()["port_model"].strip(),
                                "description": matched.groupdict()["descr"].strip(),
                                "version": matched.groupdict()["version"].strip(),
                                "serial_number": matched.groupdict()["serial_number"].strip()}
            else:
                matched = re.match(r"(?P<descr>.+)"
                                   r"Model Number:(?P<port_model>.+)"
                                   r"Serial Number:(?P<serial_number>.+)"
                                   r"Firmware Ver:(?P<version>.+)", power_port_full_info.decode("hex"), re.DOTALL)
                if matched:
                    port_details = {"port_model": matched.groupdict()["port_model"].strip(),
                                    "description": matched.groupdict()["descr"].strip(),
                                    "version": matched.groupdict()["version"].strip(),
                                    "serial_number": matched.groupdict()["serial_number"].strip()}
                else:
                    port_details = {"port_model": "",
                                    "description": "",
                                    "version": "",
                                    "serial_number": ""}

            power_port_object = PowerPort(name=port_name, relative_path=relative_path, **port_details)
            self._add_resource(power_port_object)
            self.logger.info("Added Power Port '{}'".format(port_name))

        self.logger.info("Finished loading Power Ports")

    def _get_modules_info(self):
        """ Get module elements attributes """

        self.logger.info("Start loading Modules")
        for module in self.snmp.get_table("FOUNDRY-SN-AGENT-MIB", "snAgentBrd2Table").values():
            module_id = module.get("snAgentBrd2Slot")

            relative_path = "{0}/{1}".format(module.get("snAgentBrd2Unit"), module_id)

            module_serial_number = self.snmp.get_property("FOUNDRY-SN-AGENT-MIB",
                                                          "snAgentBrdSerialNumber",
                                                          int(module_id))
            if module_serial_number.startswith("0x"):
                module_serial_number = module_serial_number[2:].decode("hex")
            elif "no such object" in module_serial_number.lower():
                module_serial_number = ""

            module_details_map = {'module_model': module.get("snAgentBrd2MainBrdDescription"),
                                  'version': "",  # TODO
                                  'serial_number': module_serial_number
                                  }
            module_name = 'Module {0}'.format(module_id)
            model = 'Generic Module'
            module_object = Module(name=module_name, model=model, relative_path=relative_path, **module_details_map)
            self._add_resource(module_object)
            self.logger.info("Added Module '{}'".format(module_name))

        self.logger.info("Finished loading Modules")

    def _get_ports_info(self):
        """ Get port elements attributes """

        self.logger.info("Start loading Ports")
        port_index_mapping = {int(value["snSwPortIfIndex"]): key
                              for key, value in
                              self.snmp.get_table("FOUNDRY-SN-SWITCH-GROUP-MIB", "snSwPortIfIndex").iteritems()}

        for port_id, port_name in self.snmp.get_table("IF-MIB", "ifName").iteritems():
            if not re.search(self.port_exclude_pattern, port_name.get("ifName", ""), re.IGNORECASE):
                interface_name = self.snmp.get_property("IF-MIB", "ifName", int(port_id)).replace("/", "-")

                relative_path = self.snmp.get_property("FOUNDRY-SN-SWITCH-GROUP-MIB",
                                                       "snSwPortDescr",
                                                       port_index_mapping[port_id])

                attribute_map = {"l2_protocol_type": self.snmp.get_property("IF-MIB", "ifType", int(port_id)).replace("/", "").replace("'", ""),
                                 "mac": self.snmp.get_property("IF-MIB", "ifPhysAddress", int(port_id)),
                                 "mtu": self.snmp.get_property("IF-MIB", "ifMtu", int(port_id)),
                                 "bandwidth": self.snmp.get_property("IF-MIB", "ifSpeed", int(port_id)),
                                 "description": self.snmp.get_property("IF-MIB", "ifAlias", int(port_id)),
                                 "adjacent": self._get_adjacent(port_id),
                                 "duplex": self._get_duplex(port_index_mapping.get(port_id, -1)),
                                 "auto_negotiation": self._get_auto_negotiation(port_id),
                                 }

                attribute_map.update(self._get_ip_interface_details(int(port_id)))
                port_object = Port(name=interface_name, relative_path=relative_path, **attribute_map)
                self._add_resource(port_object)
                self.logger.info("Added Interface '{}'".format(interface_name))

        self.logger.info("Finished loading Ports")

    def _get_adjacent(self, port_id):
        """Get connected device interface and device name to the specified port id, using cdp or lldp protocols

        :param port_id: port index in ifTable
        :return: device's name and port connected to port id
        """

        result = ''
        if self.lldp_remote_table:
            for key, value in self.lldp_local_table.iteritems():
                interface_name = self.snmp.get_property("IF-MIB", "ifName", int(port_id))
                if interface_name == '':
                    break
                if 'lldpLocPortDesc' in value and interface_name in value['lldpLocPortDesc']:
                    if 'lldpRemSysName' in self.lldp_remote_table and 'lldpRemPortDesc' in self.lldp_remote_table:
                        result = '{0} through {1}'.format(self.lldp_remote_table[key]['lldpRemSysName'],
                                                          self.lldp_remote_table[key]['lldpRemPortDesc'])
        return result

    def _get_duplex(self, port_num):
        """ Determine interface duplex

        :param port_num: port index in snSwPortInfoTable
        :return: Full or Half
        """

        if "halfDuplex" in self.snmp.get_property("FOUNDRY-SN-SWITCH-GROUP-MIB", "snSwPortInfoChnMode", port_num):
            return "Half"
        return "Full"

    def _get_auto_negotiation(self, port_id):
        """ Determine interface auto negotiation

        :param port_id: port index in ifTable
        :return: "True" or "False"
        """

        try:
            auto_negotiation = self.snmp.get(('MAU-MIB', 'ifMauAutoNegAdminStatus', port_id, 1)).values()[0]
            if "enabled" in auto_negotiation.lower():
                return "True"
        except Exception as e:
            self.logger.error('Failed to load auto negotiation property for interface {0}'.format(e.message))
        return "False"

    def _get_ip_interface_details(self, port_index):
        """Get IP address details for provided port

        :param port_index: port index in ifTable
        :return interface_details: detected info for provided interface dict{'IPv4 Address': '', 'IPv6 Address': ''}
        """

        interface_details = {'ipv4_address': '', 'ipv6_address': ''}
        if self.ip_v4_table and len(self.ip_v4_table) > 1:
            for key, value in self.ip_v4_table.iteritems():
                if 'ipAdEntIfIndex' in value and int(value['ipAdEntIfIndex']) == port_index:
                    interface_details['ipv4_address'] = key
                break
        if self.ip_v6_table and len(self.ip_v6_table) > 1:
            for key, value in self.ip_v6_table.iteritems():
                if 'ipAdEntIfIndex' in value and int(value['ipAdEntIfIndex']) == port_index:
                    interface_details['ipv6_address'] = key
                break
        return interface_details
