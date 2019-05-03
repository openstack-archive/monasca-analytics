Team and repository tags
========================

[![Team and repository tags](https://governance.openstack.org/tc/badges/monasca-analytics.svg)](https://governance.openstack.org/tc/reference/tags/index.html)

<!-- Change things from this point on -->

# MoNanas - Monasca Analytics Framework

![MoNanas Logo](doc/images/monanas-logo.png)

## Overview

Monasca Analytics (MoNanas) is a statistical/machine-learning
([SML](doc/design.md#sml)) [flow](doc/design.md#flow) composition
engine. Users can compose a sequence of algorithms to be executed by just
providing a description as an input to MoNanas. The data flow is automatically
handled by the framework.

Easy [flow](doc/design.md#flow) composition and reusability means that
we can speed up the extraction of actionable infrastructure insight.

### Advantages
:thumbsup: Decouple algorithm design from execution.

:thumbsup: Reusable specification of the desired [flow](doc/design.md#flow).

:thumbsup: Language independent [flow](doc/design.md#flow) definition.

:thumbsup: Data source and format independent.

:thumbsup: Easy to add new [SML](doc/design.md#sml) algorithms and # combine them with pre-existing ones in the [flow](doc/design.md#flow).

:thumbsup: Transparently exploit data parallelism.

### Documentation
* [MoNanas/GettingStarted](doc/getting_started.md): A starting point for users
and developers of MoNanas.

### Repositories
Core: https://github.com/openstack/monasca-analytics.git

## Example Use Cases

### Integrate with Monasca
See: [MoNanas/IntegrateMonasca](doc/monasca.md) for more details integration with Monasca

### Relevant to OpenStack
See: [MoNanas/UseCases](doc/use_cases.md) for more details use cases that are relevant to OpenStack.

## MoNanas Design
See: [MoNanas/Design](doc/design.md) for details on MoNanas's architecture,
its functional requirements and core concepts.

## Technologies
MoNanas uses a number of third-party technologies:
* Apache Spark (https://spark.apache.org/): Apache Spark is a fast and general
engine for large-scale data processing.
* Apache Kafka (https://kafka.apache.org/): Used by Monasca and MoNanas's Kafka
`source` and `sink`.
* Apache ZooKeeper (https://zookeeper.apache.org/): Used by Kafka.

## Feature Release Schedule
- [x] Basic SML flow.
- [x] New algorithm "add-on" ability.
- [x] Example datasets and SML flows.
- [ ] Support end-to-end learning + data processing flows (currently, the latter part does not get updated due to Spark's immutability.)
- [ ] Refactor codes to be consistent with terms used in the documentation.
- [ ] Add a source, ingestor and transformer for Monasca.
- [ ] Model connections as objects rather than references and have driver specifics in one place.
- [ ] Expanded orchestration abilities/expressiveness.
- [ ] Container-enabled testing/deployment for non-production environments.
- [ ] Add Vitrage Sink.
- [ ] Add a ready-to-use virtual machine image (get rid of the fetch-deps.sh).

## Contributing
There are multiple ways to contribute to the project. All are equally important
to us!
* You can have a look at the
[Monasca launchpad](https://launchpad.net/monasca) for problems that
needs to be solved (bugs/issues), and blueprints.
* You can also help us to add
[new learning algorithms](doc/dev_guide.md#add_new_algorithms).
* Finally, we are very interested in having more data sources to experiment
with. The source can either be from an existing data provider or randomly
generated. The more, the better! :) If you are interested to work on that
aspect, [you are welcome as well](doc/dev_guide.md#add_new_sources).

For more information on setting up your development environment, see
[MoNanas/DevGuide](doc/dev_guide.md).

For more information about Monanas, please visit the wiki page:
[Monanas wiki](https://wiki.openstack.org/wiki/Monasca/Analytics).

And for more information about Monasca, please visit the wiki page:
[Monasca wiki](https://wiki.openstack.org/wiki/Monasca).

## License
Copyright (c) 2016 Hewlett Packard Enterprise Development Company, L.P.
Licensed under the Apache License, Version 2.0 (the "License"); you may not
used this file except in compliance with the License. You may obtain a copy of
the License at:
```
http://www.apache.org/licenses/LICENSE-2.0
```
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
