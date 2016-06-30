

# MoNanas/DevGuide

## Development Environment

MoNanas's repository comes with a Vagrantfile for a quick deployment on the
client system. To use vagrant, simple do the following.

* Install [vagrant](https://www.vagrantup.com/) on your local machine.
* Clone the project from https://github.hpe.com/labs/monanas/.
* From `$MONANAS_HOME`, run `vagrant up && vagrant ssh`. This will set up a VM
using VMWare or VirtualBox and ssh onto it. Once you have logged into the
instance, following the guideline provided in
[MoNanas/GettingStarted](getting_started.md).

At the root of the project there is a `Makefile` which provides common tasks:

* `make test`: Run the test suite.
* `make style`: Check for pep8 compliance on the entire code base.
* `make testspec <python.path.to.TestCase>` A handy way to test only a
  `TestCase` subclass.
* `make all`: Run both `test` and `style`.
* `make start`: Start Monanas and send the `start_streaming` action via the
   REST interface.

## Adding Custom Components

As illustrated in [Monasca/Design](design.md), MoNanas's architecture was
designed to be pluggable. Therefore, integrating a new component or a new
statistical/machine learning algorithm is very simple. The following shows a
step-by-step guide on how to add a new data source and a new learning
algorithm. A custom implementation of other components can be added in similar
fashion.

### <a name="add_new_sources"></a>Add New Data Sources

When creating a new data source, everything you need is located in `main/source` package, and new sources should be contained in that package in order to keep the convention. All you need to do is extend the class `BaseSource` in `main/source/base.py` module.

#### Default configuration and Validation
The first step in the Data Source life-cycle is its creation and configuration validation. Also, a default configuration is needed by DSL in order to add a component to the configuration, and it can be very convenient for users to have a default configuration. Please, implement the following methods:

* `validate_config`
It should validate the schema of the configuration passed as parameter, checking that expected parameters are there, and values have the expected type and/or values. Please, check other classes validate_config implementations in order to have examples on how to use the Schema library. Please, make this method static by annotating it with the @staticmethod decorator.

* `get_default_config`
It should return a dictionary containing the default schema of this component. This method will be called by DSL when creating a component of this type. Please, make this method static by annotating it with the @staticmethod decorator.

#### Main logic functions
The aim of a source class is to provide data which will then be consumed by ingestors. When MoNanas is ordered to start streaming data, the source classes will be asked to create a stream of data, and other components in the pipeline may be interested in the features of the data provided by the source class.

* `create_dstream`
It should create a spark dstream using the Spark Streaming Context passed as parameter. Please, refer to spark documentation if you want more details about dstream object, and feel free to view implementations of this function by other source classes.

* `get_feature_list`
It should return a list of strings in order representing the features provided by the dstream.

#### Termination functions
When MoNanas is ordered to stop streaming data, it will call terminate_source in all the sources that are streaming.

* `terminate_source`
It should do any necessary cleanup of the source when it is terminated. For example, if the source was running a TCP server generating traffic, at this point it may want to stop it.


### <a name="add_new_algorithms"></a>Add New Learning Algorithms
When adding a new algorithm, everything you need is located in:
`main/sml` package, and new algorithms should be contained in that package in order to keep the convention. All you need to do is extend the class `BaseSML` in `main/sml/base.py` module.

#### Default configuration and Validation
Please, refer to the 'Add New Data Sources'  section.

#### Main logic functions
The aim of a SML class is to train a machine learning algorithm, or do statistics to learn something, using a batch of data provided by the aggregator. When data is available, it will be manipulated by the logic implemented in the learn_structure function; the data flow will be stopped by MoNanas when all the SMLs have consumed at least the number of samples provided by the number_of_samples_required function.

* `learn_structure`
This is the function that implements the logic of the algorithm. The data is provided as a parameter, and it should return the structure learned from the data (e.g. causality matrix, or trained classifier object).

* `number_of_samples_required`
this function should return the number of samples that the algorithm requires in order to provide reliable results.

## Coding Standards
Python: All Python code conforms to the OpenStack standards at:
http://docs.openstack.org/developer/hacking/

* Developers must add unit tests for all logical components before merging to
master.
* Pull Requests are welcome and encouraged to ensure good code quality. Label
the PR as `ready for review` when all the features are completed.

