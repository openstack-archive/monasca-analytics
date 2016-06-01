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

import logging

import pyspark
from pyspark import streaming

import monasca_analytics.config.config as config
import monasca_analytics.ingestor.base as bi
import monasca_analytics.spark.aggregator as agg
import monasca_analytics.sml.base as bml
import monasca_analytics.voter.base as mvoter
import monasca_analytics.sink.base as msink
import monasca_analytics.ldp.base as mldp

logger = logging.getLogger(__name__)


class DriverExecutor(object):
    """Driver part of the job submitted to spark.

    This is where we control what is submitted to workers,
    what is driver specific and how the pipeline is constructed.
    We also execute the pipeline from here.
    """

    def __init__(self, _config):
        self._links = config.instantiate_components(_config)
        self._sources = config.collect_sources(self._links)
        self._orchestrator = agg.Aggregator(self)

        def restart_spark():
            self._ssc = streaming.StreamingContext(self._sc, _config[
                "spark_config"]["streaming"]["batch_interval"])

        self._restart_spark = restart_spark
        self._sc = pyspark.SparkContext(
            appName=_config["spark_config"]["appName"])
        self._ssc = streaming.StreamingContext(self._sc, _config[
            "spark_config"]["streaming"]["batch_interval"])
        logger.debug("Propagating feature list...")
        self._propagate_feature_list()

    def start_pipeline(self):
        """Start the pipeline"""

        # Start by connecting the source
        self._prepare_phase(self._connect_dependents_phase1)

        # Preparation step for the orchestrator:
        #   Accumulate everything from the sources
        self._orchestrator.prepare_final_accumulate_stream_step()

        # Then prepare the orchestrator
        self._prepare_orchestrator()

        logger.info("Start the streaming context")
        self._ssc.start()

    def stop_pipeline(self):
        self._terminate_sources()
        self._ssc.awaitTermination()
        self._ssc = None
        self._sc = None

    def move_to_phase2(self):
        if self._ssc is not None:
            logger.debug("Phase 2: Stop SparkStreamingContext.")
            self._ssc.stop(False, False)
            logger.debug("Phase 2: Stop sources")
            self._terminate_sources()
            logger.debug("Phase 2: Restart streaming...")
            self._restart_spark()
            logger.debug("Phase 2: Create new connections")
            self._prepare_phase(self._connect_dependents_phase2)
            self._ssc.start()

    def _terminate_sources(self):
        """Terminates the sources."""
        for source in self._sources:
            source.terminate_source()

    def _prepare_orchestrator(self):
        """
        This is a part of phase 1. The orchestrator collects
        input from all ingestors and then orchestrate the sml
        pipeline to solve it and provide to LDPs the learned
        data structure.
        """
        smls = filter(lambda c: isinstance(c, bml.BaseSML),
                      self._links.keys())
        sml_with_no_dependents = filter(
            lambda c: set(self._links[c]).isdisjoint(smls),
            smls)
        for sml in sml_with_no_dependents:
            logger.debug("Append {} to orchestrator".format(sml))
            self._orchestrator.append_sml(sml)
            self._connect_sml_dependents(sml)

    def _prepare_phase(self, connect_dependent):
        """Prepare given phase by starting sources.

        :type connect_dependent: (pyspark.streaming.DStream,
            monasca_analytics.source.base.BaseSource) -> None
        :param connect_dependent: Callback that is going to selectively connect
                                  the appropriate dependencies of each sources.
        """
        for src in self._sources:
            logger.debug("Prepare source {}".format(src))
            dstream = src.create_dstream(self._ssc)
            connect_dependent(dstream, src)

    def _connect_sml_dependents(self, from_component):
        """Connect an sml component with all its dependencies.

        During phase 1 this code is running exclusively by the driver
        at the moment.

        :type from_component: bml.BaseSML | mvoter.BaseVoter
        :param from_component: Where we came from.
        """
        for connected_node in self._links[from_component]:

            # SML can, for now, only be connected to voter.
            if isinstance(connected_node, mvoter.BaseVoter) and \
               isinstance(from_component, bml.BaseSML):
                logger.debug("Set {} to {}"
                             .format(connected_node, from_component))
                from_component.set_voter(connected_node)

            # Voter can only be connected to LDPs
            if isinstance(from_component, mvoter.BaseVoter) and \
               isinstance(connected_node, mldp.BaseLDP):
                logger.debug("Append {} to {}"
                             .format(connected_node, from_component))
                from_component.append_ldp(connected_node)
                # We don't connect LDP to anything
                continue

            # Only SML can be connected to a sink
            if isinstance(connected_node, msink.BaseSink):
                logger.debug("Sink {} into {}"
                             .format(from_component, connected_node))
                connected_node.sink_ml(from_component)
                # Sink can't be connected to anything
                continue

            self._connect_sml_dependents(connected_node)

    def _connect_dependents_phase2(self, dstream, from_component):
        """Connect a component to its dependencies.

        During phase 2, only live data processors are considered.
        All ingestors are shutdown.

        :type dstream: pyspark.streaming.DStream | None
        :param dstream: Dstream that will be modified by dependent.
                        It can be None, only if from_component is aggregator,
                        sml or voter.
        :type from_component: monasca_analytics.component.base.BaseComponent
        :param from_component: Where we came from.
        """
        for connected_node in self._links[from_component]:
            # Live data processors are also doing a map, they add
            # the causality bit to each element in the stream.
            if isinstance(connected_node, mldp.BaseLDP):
                new_dstream = connected_node.map_dstream(dstream)
                self._connect_dependents_phase2(new_dstream, connected_node)

            # Sink are at the end of the branch!
            if isinstance(connected_node, msink.BaseSink):
                connected_node.sink_dstream(dstream)

    def _connect_dependents_phase1(self, dstream, from_component):
        """Connect a component to its dependencies for phase 1.

        All live data processors are ignored during that phase.

        :type dstream: pyspark.streaming.DStream | None
        :param dstream: Dstream that will be modified by dependent.
                        It can be None, only if from_component is aggregator,
                        sml or voter.
        :type from_component: monasca_analytics.component.base.BaseComponent --
        :param from_component: Where we came from.
        """
        for connected_node in self._links[from_component]:

            # Ingestors "map" the dstream. They are mainly doing worker
            # specific transformation. Like parsing and vectorizing the
            # data.
            if isinstance(connected_node, bi.BaseIngestor):
                logger.debug("Stream from {} to {}"
                             .format(from_component, connected_node))
                new_dstream = connected_node.map_dstream(dstream)

                # We then connect directly this stream to the orchestrator
                self._orchestrator.accumulate_dstream_samples(new_dstream)
                # And we look for sink if any
                self._connect_dependents_phase1(new_dstream, connected_node)

            # Sink are at the end of the branch!
            if isinstance(connected_node, msink.BaseSink):
                logger.debug("Sink {} into {}"
                             .format(from_component, connected_node))
                connected_node.sink_dstream(dstream)

    def _propagate_feature_list(self):
        """Set the appropriate features list on each live data processor."""
        for source in self._sources:
            features = source.get_feature_list()
            for connected_node in self._links[source]:
                propagated = False
                if isinstance(connected_node, bi.BaseIngestor):
                    connected_node.set_feature_list(features)
                    propagated = True
                if isinstance(connected_node, mldp.BaseLDP):
                    connected_node.set_feature_list(features)
                    propagated = True
                if propagated:
                    logger.info("Feature list {} propagated from {} to {}"
                                .format(features, source, connected_node))
