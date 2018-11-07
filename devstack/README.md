# Monasca Analytics DevStack Plugin

The Monasca Analytics DevStack plugin currently only works on Ubuntu 16.04 (Xenial).
More Linux Distributions will be supported in the future.

Running the Monasca Analytics DevStack plugin requires a machine with 8GB of RAM.

Directions for installing and running Devstack can be found here:

    http://docs.openstack.org/developer/devstack/

To run Monasca Analytics in DevStack, do the following three steps.

1. Clone the DevStack repo.

    git clone https://git.openstack.org/openstack-dev/devstack

2. Add the following to the DevStack local.conf file in the root of the devstack directory. You may
   need to create the local.conf if it does not already exist.

    \# BEGIN DEVSTACK LOCAL.CONF CONTENTS

    [[local|localrc]]
    MYSQL_PASSWORD=secretmysql
    DATABASE_PASSWORD=secretdatabase
    RABBIT_PASSWORD=secretrabbit
    ADMIN_PASSWORD=secretadmin
    SERVICE_PASSWORD=secretservice
    SERVICE_TOKEN=111222333444

    LOGFILE=$DEST/logs/stack.sh.log
    LOGDIR=$DEST/logs
    LOG_COLOR=False

    \# This line will enable all of Monasca Analytics.
    enable_plugin monasca-analytics git://git.openstack.org/openstack/monasca-analytics

    \# END DEVSTACK LOCAL.CONF CONTENTS

3.   Run './stack.sh' from the root of the devstack directory.

If you want to run Monasca Analytics with the bare mininum of OpenStack components
you can add the following two lines to the local.conf file.

    disable_all_services
    enable_service rabbit mysql key

```
# (C) Copyright 2016  FUJITSU LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```
