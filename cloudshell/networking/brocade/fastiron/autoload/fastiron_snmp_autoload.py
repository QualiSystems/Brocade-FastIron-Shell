#!/usr/bin/python
# -*- coding: utf-8 -*-

import inject
import os
import re

from cloudshell.configuration.cloudshell_snmp_binding_keys import SNMP_HANDLER
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER

from cloudshell.networking.autoload.networking_attributes import RootAttributes, ChassisAttributes, PowerPortAttributes, \
    ModuleAttributes, SubModuleAttributes, PortAttributes, PortChannelAttributes
from cloudshell.networking.autoload.networking_model import RootElement, Chassis, Module, SubModule, Port, PowerPort, \
    PortChannel
from cloudshell.networking.brocade.utils import sort_elements_by_attributes
from cloudshell.networking.operations.interfaces.autoload_operations_interface import AutoloadOperationsInterface
from cloudshell.shell.core.config_utils import override_attributes_from_config


class FastIronSnmpAutoload(AutoloadOperationsInterface):
    pass