#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import time

from cloudshell.networking.brocade.brocade_firmware_operations import BrocadeFirmwareOperations
from cloudshell.shell.core.config_utils import override_attributes_from_config


class BrocadeFastIronFirmwareOperations(BrocadeFirmwareOperations):
    SAVE_RESPONSE_TIMEOUT = 3
    SAVE_RESPONSE_RETRIES = 10

    def __init__(self, context=None, api=None, cli_service=None, logger=None):
        BrocadeFirmwareOperations.__init__(self, context, api, cli_service, logger)
        overridden_config = override_attributes_from_config(BrocadeFastIronFirmwareOperations)
        self._save_response_timeout = overridden_config.SAVE_RESPONSE_TIMEOUT
        self._save_response_retries = overridden_config.SAVE_RESPONSE_RETRIES

    def _buffer_readup(self, output):
        """ Read buffer to end of command execution if prompt returned immediately """
        retries = 1
        while not re.search(r"[Dd]one|[Ee]rror|[Ff]ailed", output, re.DOTALL):
            if retries > self._save_response_retries:
                raise Exception(self.__class__.__name__, "Save configuration failed with error: TFTP session timeout")

            time.sleep(self._save_response_timeout)
            output += self.cli_service.send_command(command="", expected_str=self._default_prompt)
            retries += 1

        output += self.cli_service.send_command(command="", expected_str=self._default_prompt)

        return output
