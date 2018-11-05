#!/usr/bin/env python

# Copyright (c) 2016 Hewlett Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
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
"""

import json
import logging
import logging.config as log_conf
import os
import subprocess
import sys

import argparse
import textwrap

import setup_property


class RunnerError(Exception):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)


def main(arguments):
    spark_submit = "{0}/bin/spark-submit".format(arguments.spark_path)
    monanas_path = os.environ.get('MONANAS_HOME', "")
    kafka_jar = None

    try:
        for filename in os.listdir("{0}/external/kafka-assembly/target".
                                   format(arguments.spark_path)):
            if filename.startswith("spark-streaming-kafka-assembly") and\
               not any(s in filename for s in ["source", "test"]):
                kafka_jar = filename
                break

        if not kafka_jar:
            raise OSError("Spark's external library required does not exist.")
    except OSError as e:
        raise RunnerError(e.__str__())

    spark_kafka_jar = "{0}/external/kafka-assembly/target/{1}".\
                      format(arguments.spark_path, kafka_jar)
    command = [
        spark_submit, "--master", "local[2]",
        "--jars", spark_kafka_jar, monanas_path + "/monasca_analytics/monanas.py",
        arguments.config, arguments.log_config
    ]

    if arguments.sources is not None:
        command += arguments.sources

    try:
        logger.info("Executing `{}`...".format(" ".join(command)))
        subprocess.Popen(command).communicate()
    except OSError as e:
        raise RunnerError(e.__str__())


def setup_logging(filename):
    """Setup logging based on a json string."""
    with open(filename, "rt") as f:
        config = json.load(f)

    log_conf.dictConfig(config)

def setup_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__.strip()),
        add_help=False)

    parser.add_argument('-c', '--config',
                        help='Config file.', required=True)
    # "-d" currently unused
    parser.add_argument('-d', '--debug',
                        help='Show debug messages.', action='store_true')
    parser.add_argument('-h', '--help',
                        help='Show this screen.', action='help')
    parser.add_argument('-l', '--log_config',
                        help='Log config file\'s path.', required=True)
    parser.add_argument('-p', '--spark_path',
                        help='Spark\'s path.', required=True)
    parser.add_argument('-s', '--sources',
                        help='A list of data sources.', nargs='*')
    parser.add_argument('-v', '--version',
                        help='Show version.', action='version',
                        version=setup_property.VERSION)

    return parser

if __name__ == "__main__":
    arguments = setup_parser().parse_args()

    try:
        setup_logging(arguments.log_config)
    except IOError:
        raise RunnerError("File not found: {0}.".
                          format(arguments.log_config))
    except ValueError:
        raise RunnerError("{0} is not a valid logging config file.".
                          format(arguments.log_config))

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
