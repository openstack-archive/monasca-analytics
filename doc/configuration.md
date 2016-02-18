# Configurations
MoNanas consumes two configuration files, one for orchestrating data execution
and the other for logging.

## Orchestrating Configuration
> Note: Please refer to [Monasca/Design](design.md) to understand the concept
of each component before creating or modifying a configuration.

With the current implementation, a JSON file is used to configure how MoNanas
orchestrates the data execution pipeline. This comes in different parts as
follows.

### ID (`id`)

A unique identifier for the configuration.

### Spark (`spark_config`)

* `appName`: A string describing the Spark's application name.
* `streaming`: Attributes for data streaming.
  * `batch_interval`: DStream's batch interval.

### Server (`server`)

* `port`: Port number to listen.
* `debug`: Debug mode.

### Sources (`sources`)

`sources` is a JSON object (equivalent to python dictionary in this case) where
the keys represent unique identifiers of sources. Each source has the following
attributes:
* `module`: The name of the python module used for connecting to the source.
* `params`: A JSON object representing the source's parameters (e.g. data model
used).

### Ingestors (`ingestors`)

`ingestors` is a JSON object (equivalent to python dictionary in this case)
where the keys represent unique identifiers of ingestors. Each ingestor has
the following attributes:
* `module`: The name of the python module implementing the ingestor.
* `params`: A JSON object representing the ingestor's parameters (e.g.
parameters for data conversion).

### Aggregators (`aggregators`)

`aggregators` is a JSON object (equivalent to python dictionary in this case)
where the keys represent unique identifiers of aggregators. Each aggregator
has the following attributes:
* `module`: The name of the python module implementing the aggregator.
* `params`: A JSON object representing the aggregator's parameters (e.g. how
data streams are aggregated).

> Note: Currently, only one aggregator is supported - the python module is
`default_aggregator`.

### SML Functions (`sml`)

`sml` is a JSON object (equivalent to python dictionary in this case)
where the keys represent unique identifiers of SML functions. Each SML function
has the following attributes:
* `module`: The name of the python module implementing the SML function.
* `params`: A JSON object representing the SML function's parameters (e.g.
number of samples, confidence interval).

### Voters (`voters`)

`voters` is a JSON object (equivalent to python dictionary in this case) where
the keys represent unique identifiers of voters. Each voter has the following
attributes:
* `module`: The name of the python module implementing the voter.
* `params`: A JSON object representing the voter's parameters (e.g. weights,
topology).

### Live Data Processors (`ldp`)

`ldp` is a JSON object (equivalent to python dictionary in this case) where
the keys represent unique identifiers of live data processors. Each live data
processor has  the following attributes:
* `module`: The name of the python module implementing the live data processor.
* `params`: A JSON object representing the live data processor's parameters
(e.g. mode).

### Sinks (`sinks`)

`sinks` is a JSON object (equivalent to python dictionary in this case) where
the keys represent unique identifiers of sinks. Each sink has the following
attributes:
* `module`: The name of the python module used for connecting to the sink.
* `params`: A JSON object representing the sink's parameters (e.g. server's
details, data format).

### Connections

`connections` is a JSON object (equivalent to python dictionary in this case)
where each key represents a unique identifier of the component acting as the
originating end of the data flow where its associated value is an list of
unique identifiers of components acting as terminating ends of the data flow.
The information described by `connections` can be used to represent the flow
of data execution end-to-end.

## Logging Configuration

### MoNanas

MoNanas comes with a default logging configuration. To change the logging
properties including format, level, etc., simply override
`$MONANAS_HOME/config/logging.json`.

### Spark

By default, Spark's logging is at an INFO level. To avoid unnecessary console
output, change `log4j.rootCategory=INFO, console` to `log4j.rootCategory=ERROR,
console` in `$SPARK_HOME/conf/log4j.properties` or as preferred.

> Note: Not required for a Vagrant generated VM.

### Other Software/Tools

For logging configuration of other software/tools, please refer to their
user guide.

