#!/usr/bin/env python

"""
Copyright (c) 2016 Hewlett Packard Enterprise.

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
