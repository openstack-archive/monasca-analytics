#!/usr/bin/env python

"""Common util functions."""

import importlib
import inspect
import json
import logging
from logging import config as log_conf
import os
import pkgutil

from main.config import const
from main.exception import monanas as err
from main import ingestor
from main import ldp
from main import sink
from main import sml
from main import source
from main import voter

logger = logging.getLogger(__name__)


available_classes = None


def parse_json_file(filename):
    """Parses json and return a dict.

    :param filename: str -- Filename to be parsed to a dictionary.
    :returns: dict -- Parsed data.
    :raises: IOError --If the file does not exist.
    :raises: ValueError -- If the file is an invalid json file.
    """
    try:
        with open(filename, "rt") as f:
            return json.load(f)
    except (IOError, ValueError) as e:
        logger.error("Exception parsing json file : " + str(e))
        raise e


def setup_logging(filename):
    """Setup logging based on a json string.

    :param filename: str -- Log configuration file.
    :raises: IOError -- If the file does not exist.
    :raises: ValueError -- If the file is an invalid json file.
    """
    try:
        config = parse_json_file(filename)
        log_conf.dictConfig(config)
        logpy4j = logging.getLogger("py4j")
        logpy4j.setLevel(logging.ERROR)
        logkafka = logging.getLogger("kafka")
        logkafka.setLevel(logging.ERROR)
    except (IOError, ValueError) as e:
        raise e


def get_available_inherited_classes(pkg, base_class):
    """Gets all inherited classes in modules for a given package

    This does not include subpackages.

    :param pkg: str -- a package name.
    :param base_class: Class -- a base class.
    :returns: list -- a list of inherited classes.
    """
    available_classes = []
    pkg_path = os.path.dirname(pkg.__file__)

    for _, mod_name, _ in pkgutil.iter_modules([pkg_path]):
        if not mod_name.startswith("_"):
            try:
                module = importlib.import_module("{0}.{1}".format(pkg.__name__,
                                                                  mod_name))

                for clazz in inspect.getmembers(module, inspect.isclass):
                    if clazz is not base_class:
                        if issubclass(clazz[1], base_class) and\
                           not inspect.isabstract(clazz[1]) and\
                           clazz[1] != base_class:
                            available_classes.append(clazz[1])
            except Exception as e:
                logger.warn(e.__str__())

    return set(available_classes)


def get_available_classes(class_type=None):
    """Creates a dictionary containing pipeline available classes of each type

    :param class_type: str -- if provided, only this type of classes
    will be returned
    :returns: dict -- all subclasses keyed by type
    """
    _classes = {}

    if not class_type or class_type == const.SOURCES:
        from main.source.base import BaseSource
        _classes[const.SOURCES] = get_available_inherited_classes(source,
                                                                  BaseSource)
    if not class_type or class_type == const.INGESTORS:
        from main.ingestor.base import BaseIngestor
        _classes[const.INGESTORS] = \
            get_available_inherited_classes(ingestor, BaseIngestor)

    if not class_type or class_type == const.SMLS:
        from main.sml.base import BaseSML
        _classes[const.SMLS] = get_available_inherited_classes(sml, BaseSML)

    if not class_type or class_type == const.VOTERS:
        from main.voter.base import BaseVoter
        _classes[const.VOTERS] = get_available_inherited_classes(voter,
                                                                 BaseVoter)
    if not class_type or class_type == const.SINKS:
        from main.sink.base import BaseSink
        _classes[const.SINKS] = get_available_inherited_classes(sink, BaseSink)

    if not class_type or class_type == const.LDPS:
        from main.ldp.base import BaseLDP
        _classes[const.LDPS] = \
            get_available_inherited_classes(ldp, BaseLDP)

    return _classes


def get_component_type(class_name):
    for cls_type in const.components_types:
        names = get_available_class_names(cls_type)
        if class_name in names:
            return cls_type


def get_class_by_name(class_name, class_type=None):
    """Gets the class by class name.

    :param class_name: str -- a class name to look for
    :param class_type: str -- the type of the class to look for
    (e.g. data_sources, ingestors, etc.).
    :returns: class -- the source class requested.
    :raises: MonanasNoSuchSourceError -- If no source class found.
    :raises: MonanasDuplicateSourceError -- If the system has multiple sources
    of the same class name.
    """
    classes = get_available_classes(class_type)
    if class_type:
        clazz = filter(lambda t_class: t_class.__name__ == class_name,
                       classes[class_type])
    else:
        for c_type in classes.keys():
            clazz = filter(lambda t_class: t_class.__name__ == class_name,
                           classes[c_type])
            if clazz:
                break
    if not clazz:
        raise err.MonanasNoSuchClassError(class_name)
    elif len(clazz) > 1:
        raise err.MonanasDuplicateClassError(class_name)
    else:
        return clazz[0]


def get_available_class_names(class_type):
    """Gets available class names of type class_type.

    :param class_type: str -- type of classes to look for
    :returns: list -- a list of available source class names.
    """
    classes = get_available_classes(class_type)
    return [Clazz.__name__ for Clazz in classes[class_type]]


def get_source_class_by_name(class_name):
    """Gets the source class by class name.

    :param class_name: str -- name of the source class requested.
    :raises: MonanasNoSuchIngestorError -- if no source class found.
    :raises: MonanasDuplicateIngestorError -- if the system has multiple
    source of the same class name.
    """
    return get_class_by_name(class_name, const.SOURCES)


def get_available_source_class_names():
    """Gets available source class names.

    :returns: list -- a list of available source class names.
    """
    return get_available_class_names(const.SOURCES)


def get_ingestor_class_by_name(class_name):
    """Gets the ingestor class by class name.

    :param class_name: str --name of the ingestor class requested.
    :raises: MonanasNoSuchIngestorError -- if no ingestor class found.
    :raises: MonanasDuplicateIngestorError -- if the system has multiple
    ingestors of the same class name.
    """
    return get_class_by_name(class_name, const.INGESTORS)


def get_available_ingestor_class_names():
    """Gets available ingestor class names.

    :returns: list: a list of available ingestor class names.
    """
    return get_available_class_names(const.INGESTORS)


def get_sml_class_by_name(class_name):
    """Gets the sml class by class name.

    :param class_name: str -- name of the sml class requested.
    :raises: MonanasNoSuchIngestorError -- if no sml class found.
    :raises: MonanasDuplicateIngestorError -- if the system has multiple
    sml algorithms of the same class name.
    """
    return get_class_by_name(class_name, const.SMLS)


def get_available_sml_class_names():
    """Gets available sml class names.

    :returns: list - a list of available sml class names.
    """
    return get_available_class_names(const.SMLS)


def get_voter_class_by_name(class_name):
    """Gets the voter class by class name.

    :param class_name: str -- name of the voter class requested.
    :raises: MonanasNoSuchIngestorError -- If no voter class found.
    :raises: MonanasDuplicateIngestorError: If the system has multiple
    voter of the same class name.
    """
    return get_class_by_name(class_name, const.VOTERS)


def get_available_voter_class_names():
    """Gets available voter class names.

    :returns: list -- a list of available voter class names.
    """
    return get_available_class_names(const.VOTERS)


def get_available_ldp_class_names():
    """Gets available ldp class names.

    :returns: list -- a list of available ldp class names.
    """
    return get_available_class_names(const.LDPS)
