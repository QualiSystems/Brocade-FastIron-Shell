#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from cloudshell.networking.brocade.brocade_connectivity_operations import BrocadeConnectivityOperations
from cloudshell.networking.networking_utils import validateVlanNumber, validateVlanRange


class BrocadeFastIronConnectivityOperations(BrocadeConnectivityOperations):
    def __init__(self, context=None, api=None, cli_service=None, logger=None):
        BrocadeConnectivityOperations.__init__(self)
        self._context = context
        self._api = api
        self._cli_service = cli_service
        self._logger = logger

    def add_vlan(self, vlan_range, port, port_mode, qnq=False, ctag=''):
        """ Configure specified vlan range in specified switchport mode on provided port

        :param vlan_range: range of VLANs to be added
        :param port: interface Resource Full Address
        :param port_mode: type of adding VLAN ('trunk' or 'access')
        :param qnq: QNQ parameter for switchport mode dot1nq
        :param ctag: CTag details
        :return: success message or Exception
        """

        self.logger.info('VLANs Configuration Started')
        self.validate_vlan_methods_incoming_parameters(vlan_range, port, port_mode)
        if_name = self.get_port_name(port)

        for vlan in vlan_range.split(","):
            if port_mode == "trunk":
                tag_type = "tagged"
            elif port_mode == "access":
                tag_type = "untagged"
            else:
                raise Exception(self.__class__.__name__,
                                "Unsupported port mode '{}'. Should be 'trunk' or 'access'".format(port_mode))

            if "-" in vlan:
                if len(vlan.split("-")) == 2 and validateVlanRange(vlan):
                    start, end = map(int, vlan.split("-"))
                    if start > end:
                        start, end = end, start
                    self.cli_service.send_config_command("vlan {start} to {end}".format(start=start, end=end))
                    res = self.cli_service.send_config_command(command="{tag_type} {if_name}".format(tag_type=tag_type,
                                                                                                     if_name=if_name),
                                                               expected_str=r"vlan\s*{0}|VLAN\s*{0}".format(end))
                    if re.search(r"error", res, re.IGNORECASE|re.DOTALL):
                        raise Exception(self.__class__.__name__, "Error during vlan creation. See logs for details")
                else:
                    raise Exception(self.__class__.__name__, "Wrong VLAN range declaration'{}'.".format(vlan))
            else:
                if validateVlanNumber(vlan):
                    self.cli_service.send_config_command("vlan {}".format(vlan))
                    res = self.cli_service.send_config_command(command="{tag_type} {if_name}".format(tag_type=tag_type,
                                                                                                     if_name=if_name),
                                                               expected_str=r"vlan\s*{0}|VLAN\s*{0}".format(vlan))
                    if re.search(r"error", res, re.IGNORECASE|re.DOTALL):
                        raise Exception(self.__class__.__name__, "Error during vlan creation. See logs for details")
                else:
                    raise Exception(self.__class__.__name__, "Wrong VLAN number '{}'.".format(vlan))

            self.cli_service.send_config_command("")

            if qnq and self._does_interface_support_qnq(if_name):
                self.cli_service.send_config_command("interface {if_name}".format(if_name=if_name))
                self.cli_service.send_config_command("tag-profile enable")

        self.cli_service.send_config_command("end")

        return "Vlan Configuration Completed"

    def remove_vlan(self, vlan_range, port, port_mode):
        """ Remove vlan from port

        :param vlan_range: range of VLANs to be deleted
        :param port: interface Resource Full Address
        :param port_mode: type of adding vlan ('trunk' or 'access')
        :return: success message or Exception
        """
        self.logger.info('VLANs Configuration Started')
        self.validate_vlan_methods_incoming_parameters(vlan_range, port, port_mode)
        if_name = self.get_port_name(port)

        if port_mode == "trunk":
            tag_type = "tagged"
        elif port_mode == "access":
            tag_type = "untagged"
        else:
            raise Exception(self.__class__.__name__,
                            "Unsupported port mode '{}'. Should be 'trunk' or 'access'".format(port_mode))

        for vlan in vlan_range.split(","):
            if "-" in vlan:
                if len(vlan.split("-")) == 2 and validateVlanRange(vlan):
                    start, end = map(int, vlan.split("-"))
                    if start > end:
                        start, end = end, start
                    self.cli_service.send_config_command("vlan {start} to {end}".format(start=start, end=end))
                    res = self.cli_service.send_config_command(command="no {tag_type} {if_name}".format(tag_type=tag_type,
                                                                                                        if_name=if_name),
                                                               expected_str=r"vlan\s*{0}|VLAN\s*{0}".format(end))
                    if re.search(r"error", res, re.IGNORECASE|re.DOTALL):
                        raise Exception(self.__class__.__name__, "Error during vlan removing. See logs for details")
                else:
                    raise Exception(self.__class__.__name__, "Wrong VLAN range declaration'{}'.".format(vlan))
            else:
                if validateVlanNumber(vlan):
                    self.cli_service.send_config_command("vlan {}".format(vlan))
                    res = self.cli_service.send_config_command(command="no {tag_type} {if_name}".format(tag_type=tag_type,
                                                                                                        if_name=if_name),
                                                               expected_str=r"vlan\s*{0}|VLAN\s*{0}".format(vlan))
                    if re.search(r"error", res, re.IGNORECASE | re.DOTALL):
                        raise Exception(self.__class__.__name__, "Error during vlan removing. See logs for details")
                else:
                    raise Exception(self.__class__.__name__, "Wrong VLAN number '{}'.".format(vlan))

            self.cli_service.send_config_command("")

        self.cli_service.send_config_command("end")

        return "Remove Vlan Completed"
