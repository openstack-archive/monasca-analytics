#!/usr/bin/env python

# Copyright (c) 2016 Hewlett Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not used this file except in compliance with the License. You may obtain
# a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
from logging import config as log_conf
import os

from monasca_analytics.dsl import interpreter

DEFAULT_LOGGING_CONFIG_FILE = "config/logging.json"


def setup_logging():
    current_dir = os.path.dirname(__file__)
    logging_config_file = os.path.join(current_dir,
                                       DEFAULT_LOGGING_CONFIG_FILE)
    with open(logging_config_file, "rt") as f:
        config = json.load(f)
    log_conf.dictConfig(config)


def main():
    setup_logging()
    print "Welcome to Monanas config command line"
    print "Type help for help about commands"
    inter = interpreter.DSLInterpreter()
    cmd = ""
    while("exit" != cmd.lower()):
        cmd = raw_input(">> ")
        if cmd != "":
            try:
                print inter.execute_string(cmd)
            except Exception as e:
                print "Failed : " + str(e)

if __name__ == "__main__":
    main()
