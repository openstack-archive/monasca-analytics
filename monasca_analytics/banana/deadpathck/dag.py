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

import monasca_analytics.banana.typeck.type_util as type_util


class DagNode(object):

    def __init__(self, typec):
        """
        Create a DAGNode.

        :param typec: The type of the node.
        """
        self.parents = []
        self.children = []
        self.typec = typec
        self._visited = False
        self._seen_sink = False

    def visit(self):
        """
        Visit this nodes and all of its connections.
        """
        if not self._visited:
            self._visited = True
            if isinstance(self.typec, type_util.Sink):
                self.visit_parents()
                return
            for child in self.children:
                child.visit()

    def visit_parents(self):
        """
        Visit the parent to tell them that we've seen a Sink.
        """
        if not self._seen_sink:
            self._seen_sink = True
            for parent in self.parents:
                parent.visit_parents()

    def is_alive(self):
        return self._visited and self._seen_sink
