#!/usr/bin/python
# -*- coding: utf-8 -*-

import inject
import re
import os

from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER, CONFIG
from cloudshell.configuration.cloudshell_snmp_binding_keys import SNMP_HANDLER
from cloudshell.networking.operations.interfaces.autoload_operations_interface import AutoloadOperationsInterface
from cloudshell.shell.core.context_utils import get_attribute_by_name

from cloudshell.networking.brocade.autoload.brocade_snmp_autoload import BrocadeSnmpAutoload
from cloudshell.networking.autoload.networking_autoload_resource_attributes import NetworkingStandardRootAttributes
from cloudshell.networking.autoload.networking_autoload_resource_structure import Port, PortChannel, PowerPort, \
    Chassis, Module
from cloudshell.shell.core.config_utils import override_attributes_from_config
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.snmp.quali_snmp import QualiMibTable



class FastIronSnmpAutoload(AutoloadOperationsInterface):
    pass