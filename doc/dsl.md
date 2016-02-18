# Domain Specific Language (DSL) for configuration handling

A simple DSL language, accessible from a command line tool, has been implemented
in order to manage configurations in an easier way. This section explains what
operations are available, and how to use them.

> Note: Please refer to [Monasca/Configuration](configuration.md) to understand the structure of the configuration.

## Usage

* Start Mananas DSL tool
```bash
python $MONANAS_HOME/config_dsl.py
```
After running this command, a simple empty orchestration configuration will be created,
which you can then modify running operations according to your needs.

## Config manipulation operations
You can run the following operations from the DSL command line in order to create, remove, connect, disconnect and modify components in the configuration.

###Create component
* Create a component and assign it to a variable
```bash
>> A = IPTablesSource
```
This command adds a new source of type IPTablesSource to the configuration, assigning it
its default configuration. It links the source component to variable A, and returns a unique ID.
You can either use the variable or the ID in order to reference the instance of IPTablesSource
you just created.

### Remove component
* Remove a component using its ID or variable name
```bash
>> rm A
```
This command removes the component referenced by A from the configuration.
The parameter can either be a variable or an ID associated to a component
in the configuration.
The component will only be removed if it is not connected to any other component.

### Connect components
* Connect two components in the configuration
```bash
>> A -> B
```
This command connects the component referenced by A with the component referenced
by B. Both A and B can be variables or IDs, and the connection is directional from A to B.
The connection will only be performed if the components exist and their connection is allowed.
For example, connecting a source with an ingestor is allowed, but connecting a source with a voter is not.

### Disconnect components
* Disconnect two components in the configuration
```bash
>> A !-> B
```
This command disconnects the component A from component B. Both A and B can be variables or IDs, and the connection is directional from A to B.
If the connection didn't exist, nothing will happen.

### Modify component
* Modify values of the configuration of a component
```bash
>> A.params.subparam1.subparam2 = value
```
This command modifies the value of the configuration parameter at the end of the path defined by the dot notation.
The configuration is validated before being modified, hence if the modification results in an invalid configuration,
it will not be performed.
A can either be a variable or an ID.

## Config presentation operations
You can run the following operations from the DSL command line in order to view the current configuration, sub-configurations, and available components that you can instantiate.

### Print

* Print the full configuration
```bash
>> print
```
This command displays the full configuration in json format to your screen.

* Print component type sub-configuration
```bash
>> print connections
```
If you pass a parameter to the print command that corresponds to a component type, or, in general, a first level key of the configuration, only the relevant sub-configuration that you selected will be displayed to your screen.

* Print a particular component sub-configuration
```bash
>> print A
```
If you pass a parameter to the print command that corresponds to a variable or an ID associated to a particular component, only its configuration will be displayed to your screen.

### List

* Print all available components
```bash
>> list
```
This command displays all available components that you can add to your configuration, organized by type.

* Print all available components of a particular type
```bash
>> list smls
```
If you pass the type as a parameter to the list command, only the available components of that type will be listed.

## Config storage operations
You can run the following operations from the DSL command line in order to load and save configurations from/to files.

### Load

* Load a configuration from a file
```bash
>> load filename
```
This command loads the configuration stored in the file 'filename', overriding the existing configuration you were handling before.

### Save

* Save a configuration to a file
```bash
>> save filename
```
This command saves the configuration being currently handled to the file 'filename', overriding the file if it existed before.

* Save a configuration to the last file
```bash
>> save
```
If no parameter is provided, the save operation saves the current configuration being handled to the last file you loaded from or saved to.
