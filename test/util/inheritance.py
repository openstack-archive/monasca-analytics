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


class Baseclass(object):
    pass


class Extended_1_1(Baseclass):
    pass


class Extended_1_2(Baseclass):
    pass


class Extended_1_3(Baseclass):
    pass


class Extended_2_1(Extended_1_1):
    pass


class Extended_3_1(Extended_2_1):
    pass
