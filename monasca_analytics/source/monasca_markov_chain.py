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

import logging
import random
import schema


import monasca_analytics.source.markov_chain.base as base
import monasca_analytics.source.markov_chain.events as ev
import monasca_analytics.source.markov_chain.prob_checks as pck
import monasca_analytics.source.markov_chain.state_check as dck
import monasca_analytics.source.markov_chain.transition as tr
import monasca_analytics.util.timestamp as tp

logger = logging.getLogger(__name__)


class MonascaMarkovChainSource(base.MarkovChainSource):

    @staticmethod
    def validate_config(_config):
        return schema.Schema({
            "module": schema.And(basestring,
                                 lambda i: not any(c.isspace() for c in i)),
            "params": {
                "server_sleep_in_seconds": schema.And(float,
                                                      lambda v: 0 < v < 1)
            },
        }).validate(_config)

    @staticmethod
    def get_default_config():
        return {
            "module": MonascaMarkovChainSource.__name__,
            "params": {
                "server_sleep_in_seconds": 0.01
            }
        }

    def get_feature_list(self):
        return ["vm1", "vm2", "host1", "host2"]

    def _create_system(self):
        mc = tr.MarkovChain([])
        vm_triggers = [
            ev.Trigger(
                event_builder=MonascaFakeMetricBuilder("vm.mem.used_mb"),
                node_check=dck.TrueCheck(),
                prob_check=pck.NoProbCheck()
            ),
            ev.Trigger(
                event_builder=MonascaFakeMetricBuilder("cpu.idle_perc"),
                node_check=dck.TrueCheck(),
                prob_check=pck.NoProbCheck()
            ),
            ev.Trigger(
                event_builder=MonascaFakeMetricBuilder(
                    "cpu.total_logical_cores"),
                node_check=dck.TrueCheck(),
                prob_check=pck.NoProbCheck()
            )
        ]
        host_trigger = ev.Trigger(
            event_builder=MonascaFakeMetricBuilder("mem.total_mb"),
            node_check=dck.TrueCheck(),
            prob_check=pck.NoProbCheck()
        )

        return [
            # vm.mem.used_mb
            base.StateNode(3, mc, vm_triggers[0], _id="vm1"),
            base.StateNode(1, mc, vm_triggers[0], _id="vm2"),
            # cpu.idle_perc
            base.StateNode(0.75, mc, vm_triggers[1], _id="vm1"),
            base.StateNode(0.75, mc, vm_triggers[1], _id="vm2"),
            # cpu.total_logical_cores
            base.StateNode(3, mc, vm_triggers[2], _id="vm1"),
            base.StateNode(2, mc, vm_triggers[2], _id="vm2"),
            # mem.total_mb
            base.StateNode(5, mc, host_trigger, _id="host1"),
            base.StateNode(6, mc, host_trigger, _id="host2"),
        ]


class MonascaFakeMetricBuilder(object):

    def __init__(self, metric_name):
        """
        :type metric_name: str
        :param metric_name: The name of the metric
        """
        self.metric_name = metric_name

    def __call__(self, node, fake_date, request):
        """
        :type node: monasca_analytics.source.markov_chain.base.StateNode
        :param node: The node associated with the event.
        :type fake_date: datetime.datetime
        :param fake_date: A date that you can use to generate a ctime.
        :type request:
            monasca_analytics.source.markov_chain.base.RequestBuilder
        """
        half_hour = 60 * 60 / 2
        request.send({
            "metric": {
                "name": self.metric_name,
                "dimensions": {
                    "service": "monitoring",
                    "hostname": node.id()
                },
                "timestamp": tp.timestamp(fake_date) +
                random.randint(- half_hour, half_hour),
                "value": node.state
            },
            "meta": {
                "tenantId": 0,
                "region": "earth"
            },
            "creation_time": 0
        })
