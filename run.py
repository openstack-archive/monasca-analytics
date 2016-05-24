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

"""Monanas Runner.

This script checks for appropriate arguments and starts Monanas to use
data coming from one or more given sources. The source(s) can be configured
using the optional argument --sources. However, a default source using random
data generator is provided in the config folder.

Usage:
    run.py -p <spark_path> -c <config> -l <log_config> [-s <sources>...
        [<sources>]] [-dvh]
    run.py -v | --version
    run.py -h | --help

Options:
    -c --config          Config file.
    -d --debug           Show debug messages.
    -h --help            Show this screen.
    -l --log_config      Log config file's path.
    -p --spark_path      Spark's path.
    -s --sources         A list of data sources.
    -v --version         Show version.

"""

import json
import logging
import logging.config as log_conf
import os
import subprocess
import sys

import docopt

import setup_property


class RunnerError(Exception):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)


def main(arguments):
    spark_submit = "{0}/bin/spark-submit".format(arguments["<spark_path>"])
    kafka_jar = None

    try:
        for filename in os.listdir("{0}/external/kafka-assembly/target".
                                   format(arguments["<spark_path>"])):
            if filename.startswith("spark-streaming-kafka-assembly") and\
               not any(s in filename for s in ["source", "test"]):
                kafka_jar = filename
                break

        if not kafka_jar:
            raise OSError("Spark's external library required does not exist.")
    except OSError as e:
        raise RunnerError(e.__str__())

    spark_kafka_jar = "{0}/external/kafka-assembly/target/{1}".\
                      format(arguments["<spark_path>"], kafka_jar)
    command = [
        spark_submit, "--master", "local[2]",
        "--jars", spark_kafka_jar, "main/monanas.py",
        arguments["<config>"], arguments["<log_config>"]
    ]
    command += arguments["<sources>"]

    try:
        subprocess.Popen(command).communicate()
    except OSError as e:
        raise RunnerError(e.__str__())


def setup_logging(filename):
    """Setup logging based on a json string."""
    with open(filename, "rt") as f:
        config = json.load(f)

    log_conf.dictConfig(config)

if __name__ == "__main__":
    arguments = docopt.docopt(__doc__, version=setup_property.VERSION)

    try:
        setup_logging(arguments["<log_config>"])
    except IOError:
        raise RunnerError("File not found: {0}.".
                          format(arguments["<log_config>"]))
    except ValueError:
        raise RunnerError("{0} is not a valid logging config file.".
                          format(arguments["<log_config>"]))

    logger = logging.getLogger(__name__)

    try:
        main(arguments)
    except KeyboardInterrupt:
        logger.info("Monanas run script stopped.")
    except RunnerError as e:
        logger.error(e.__str__())
    except Exception as e:
        logger.error("Unexpected error: {0}. {1}.".
                     format(sys.exc_info()[0], e))
