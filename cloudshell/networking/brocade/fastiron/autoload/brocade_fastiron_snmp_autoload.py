#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from cloudshell.networking.brocade.autoload.brocade_snmp_autoload import BrocadeSnmpAutoload
from cloudshell.networking.autoload.networking_autoload_resource_attributes import NetworkingStandardRootAttributes
from cloudshell.networking.autoload.networking_autoload_resource_structure import Port, PortChannel, PowerPort, \
    Chassis, Module
from cloudshell.shell.core.config_utils import override_attributes_from_config
from cloudshell.shell.core.context_utils import get_attribute_by_name
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.snmp.quali_snmp import QualiMibTable


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
        self._config = config
        self._snmp = snmp_handler
        self._logger = logger
        self.snmp_community = snmp_community
        if not self.snmp_community:
            self.snmp_community = get_attribute_by_name("SNMP Read Community") or "quali"
        self._cli_service = cli_service

        """Override attributes from global config"""
        overridden_config = override_attributes_from_config(FastIronSnmpAutoload, config=self.config)
        self._supported_os = overridden_config.SUPPORTED_OS

    def _is_valid_device_os(self):
        """ Validate device OS using snmp
            :return: True or False
        """

        system_description = self.snmp.get_property('SNMPv2-MIB', 'sysDescr', '0')
        self.logger.debug('Detected system description: \'{0}\''.format(system_description))
        result = re.search(r"({0})".format("|".join(self._supported_os)),
                           system_description,
                           flags=re.DOTALL | re.IGNORECASE)

        if result:
            return True
        else:
            error_message = 'Incompatible driver! Please use this driver for \'{0}\' operation system(s)'. \
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
            raise Exception('Unsupported device OS')



        # TODO: AUTOLOAD LOGIC SHOULD BE HERE
