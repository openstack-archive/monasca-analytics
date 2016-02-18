#!/usr/bin/env python

import json
from logging import config as log_conf
import os

from main.dsl import interpreter

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
