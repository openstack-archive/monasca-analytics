# Command line interface to generate a JSON configuration

A simple command line tool has been implemented in order to manage
configurations in an easier way. It is not expected to be maintained in the
long term. It is introduced to experiment with the creation of `banana`, the
configuration language of Monanas.

This section explains what operations are currently available and how to use
them.

> NOTE: Please refer to [Monasca/Configuration](configuration.md) for the
>       structure of the JSON configuration.

> NOTE: This tool is DEPRECATED, use [BANANA](banana.md) configuration language
>       instead.

## Usage

* Start the Monanas cli
```bash
python $MONANAS_HOME/config_dsl.py
```
After running this command, a simple empty configuration will be created. You
can then modify it by running the commands listed below:

## Available commands

You can run the following operations from the CLI in order to create, remove, connect,
disconnect and modify components from the configuration.

### Create component

Create a component and assign it to a variable:

```python
>> A = IPTablesSource
```

This command adds a new source of type `IPTablesSource` to the configuration,
assigning it with a default configuration. It links the source component to
variable A and returns a unique ID. You can either use the variable or the ID
to refer to the instance of the `IPTablesSource` created.

### Remove component

Remove a component using an ID or a variable name:

```python
>> rm A
```

This command removes the component referenced by `A` from the configuration.
The parameter can either be a variable or an ID associated to a component
in the configuration. The component will only be removed if it is not connected
to any other component.

### Connect components

Connect two components in the configuration:

```python
>> A -> B
```

This command connects the component referenced by `A` with the component
referenced by `B`. Both `A` and `B` can be variables or IDs, and the connection
is directional from `A` to `B`. The connection is valid and considered only if
the associated components exist and allowed for connection. For example,
connecting a source with an ingestor is allowed, but connecting a source with
a voter is not.

### Disconnect components

Disconnect two components in the configuration:

```python
>> A !-> B
```

This command disconnects the component `A` from component `B`. Both `A` and `B`
can be variables or IDs and the connection is directional from `A` to `B`. If
the connection doesn't exist, nothing will happen.

### Modify component

Modify values of the configuration of a component:

```python
>> A.params.subparam1.subparam2 = value
```

This command modifies the value of the configuration parameter at the end of
the path defined by a dot notation. The configuration is validated before being
modified; hence, if the modification results in an invalid configuration, it
will not be executed. `A` can either be a variable or an ID.

## Config presentation operations

The following operations can be run using the tool in order to view the
current configuration, sub-configurations, and available components that can be
instantiated.

### Print

Print the full configuration:

```python
>> print
```

This command displays the full configuration in JSON format on the screen.

Print component type sub-configuration:

```python
>> print connections
```

If a parameter is passed to the print command that corresponds to a component
type, or in general, a first level key of the configuration, only the relevant
sub-configuration that is selected will be displayed on the screen.

Print a particular component sub-configuration:

```python
>> print A
```

If a parameter is passed to the print command that corresponds to a variable
or an ID associated to a particular component, only its configuration will be
displayed on the screen.

### List

Print all available components:

```python
>> list
```

This command displays all available components that can be add to the
configuration, organized by type.

Print all available components of a particular type:

```python
>> list smls
```

If a type is passed as a parameter to the list command, only the available
components of that type will be listed.

## Config storage operations

The following operations can be run from the tool in order to load and save
configurations from/to files.

### Load

Load a configuration from a file:

```python
>> load filename
```

This command loads the configuration stored in the file 'filename', overriding
the configuration currently being manipulated in memory.

### Save

Save a configuration to a file:

```python
>> save filename
```

This command saves the configuration being currently handled to the file
'filename', overriding the file if it existed previously.

Save a configuration to the last file:

```python
>> save
```

If no parameter is provided, the save operation saves the current
configuration being handled to the last file loaded from or saved to.
