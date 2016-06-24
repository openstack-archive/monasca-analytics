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


import monasca_analytics.source.markov_chain.base as bmkv


class MockRequestBuilder(bmkv.RequestBuilder):

    def __init__(self, events):
        super(MockRequestBuilder, self).__init__(request=None)
        self.events = events

    def send(self, data):
        self.events.append(data)

    def finalize(self):
        pass
