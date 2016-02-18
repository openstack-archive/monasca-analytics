#!/usr/bin/env python

import json
import logging

import schema

import main.ldp.base as bt


logger = logging.getLogger(__name__)


class CloudCausalityLDP(bt.BaseLDP):
    """A causality live data processor"""

    @staticmethod
    def validate_config(_config):
        return schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
        }).validate(_config)

    @staticmethod
    def get_default_config():
        return {"module": CloudCausalityLDP.__name__}

    def map_dstream(self, dstream):
        """Executes _aggregate for each RDD in the dstream

        :param dstream: pyspark.streaming.DStream
        """
        data = self._data
        return dstream.flatMap(lambda r: self._aggregate(r, data))

    def _aggregate(self, rdd_entry, data):
        rdd_entry = json.loads(rdd_entry)
        new_entries = []
        events = rdd_entry["events"]
        features = data["features"]
        matrix = data["matrix"]

        for event in events:
            event["ctime"] = rdd_entry["ctime"]

        if features is None or matrix is None:
            return events

        for event in events:
            causes = []

            try:
                cause = features.index(event["id"])
                for other_event in events:
                    if other_event["id"] != event["id"]:
                        try:
                            caused = features.index(other_event["id"])

                            if matrix[caused][cause]:
                                causes.append(other_event["id"])
                        except ValueError:
                            pass
            except ValueError:
                pass

            event["__monanas__"] = dict(causes=causes)
            new_entries.append(event)

        return new_entries
