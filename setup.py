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

"""
Monanas setup script.
"""

import setuptools

import setup_property

setuptools.setup(
    name="monanas",
    version=setup_property.VERSION,
    description="Monanas - Monasca Analytics, ",
    author="Actionable Insights, Manageability Group, "
           "Security and Manageability Lab, Hewlett Packard Enterprise",
    author_email="suksant.sae-lor@hpe.com, david.perez5@hpe.com, "
                 "luis.vaquero@hpe.com, joan.varvenne@hpe.com",
    install_requires=[
        "docopt",
        "findspark",
        "libpgm",
        "numpy",
        "schema",
        "scipy",
        "tornado",
        "sklearn",
        "kafka-python",
        "pyparsing"
    ]
)
