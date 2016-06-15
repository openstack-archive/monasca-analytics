# MoNanas/GettingStarted

This section serves as a user guide and helps you to get started with MoNanas.
For developer guide, see: [MoNanas/DevGuide](dev_guide.md).

> Note: `$XXX_HOME` indicates the root directory where the corresponding
project resides. For example, `$KAFKA_HOME` refers to where Kafka's source
files have been extracted to.

## Pre-requisites

* Python (>= v.2.7.6)
* Apache Spark (>= v.1.6.1)
* Apache Kafka (>= v.0.8.2.1) - this comes with Apache Zookeeper.
* Vagrant (for development environment or testing MoNanas only).

> Note: Newer versions of these software/tools should be compatible, but are
not tested so nothing is guaranteed.

## Installation

* Clone MoNanas repo: https://github.com/openstack/monasca-analytics

### Everything on Host

The easiest way to install everything on a physical host is through our
provided script, `fetch-deps.sh` located in `$MONANAS_HOME`.

### Everything on VM

MoNanas comes with a Vagrantfile for quick deployment. For more information,
see: [MoNanas/DevGuide](dev_guide.md).

## Usage

* Start Apache ZooKeeper<sup>1</sup>
```bash
$KAFKA_HOME/bin/zookeeper-server-start.sh \
    $KAFKA_HOME/config/zookeeper.properties
```
* Start Apache Kafka<sup>1</sup>
```bash
$KAFKA_HOME/bin/kafka-server-start.sh \
    $KAFKA_HOME/config/server.properties
```
* Start MoNanas with your configuration
```bash
python $MONANAS_HOME/run.py -p $SPARK_HOME -c <config_file> \
    -l <log_config_file>
```
e.g.
```bash
python $HOME/monanas/run.py -p $HOME/spark -c $HOME/monanas/config/config.json \
    $HOME/monanas/config/logging.json
```

> Note:
1. Only when `KafkaSource` or `KafkaSink` is used in your processes.

## Configurations
MoNanas consumes two configuration files, one for orchestrating data execution
and the other for logging. A Domain Specific Language (DSL) has been implemented in order to manipulate configurations.
Please, see [MoNanas/Configuration](configuration.md) for more details on MoNanas configuration;
and [MoNanas/Dsl](dsl.md) for more details on MoNanas DSL.

## Examples

To run examples and see how MoNanas works step-by-step, see: [MoNanas/Examples](examples.md)
