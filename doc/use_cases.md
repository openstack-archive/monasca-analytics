# Example Use Cases

Below are few use cases that are relevant to OpenStack. However, MoNanas
enables you to add your own [data ingestors](doc/dev_guide.md#ingestors).

| Example                       | Alert Fatigue Management | Anomaly Detection |
|:------------------------------|:-------------------------|:------------------|
| **Dataset**                   | Synthetic, but representative, set of Monasca alerts that are processed in a stream manner. This alert set represents alerts that are seen in a data center consisting of several racks, enclosures and nodes. | `iptables` rules together with the number of times they are fired in a time period. |
| **Parsing**                   | Monasca alert parser. | Simple parser extracting period and number of fire events per rule. |
| **SML algorithm flow**        | `filter(bad_formatted) -> filter(duplicates) -> aggregate() >> aggregator` aggregation can utilize conditional independence causality, score-based causality, linear algebra causality. | `detect_anomaly() >> aggregator` anomaly detection could be based on SVM, trend, etc. |
| **Output**                    | Directed acyclic alert graph with potential root causes at the top. | Rule set with an anomalous number of firing times in a time period. |
| **:information_source: Note** | Even though this could be consumed directly by devops, the usage of  [Vitrage MoNanas Sink](doc/getting_started.md#vitrage_sink) is recommended. The output of this module can speed up creation of a [Vitrage](https://wiki.openstack.org/wiki/Vitrage) entity graph to do further analysis on it. | None. |

`->` indicates a sequential operation in the flow.

`//` indicates beginning of group of operations running in parallel.

`-` indicates operations running in parallel.

`>>` indicates end of group of operations running in parallel.
