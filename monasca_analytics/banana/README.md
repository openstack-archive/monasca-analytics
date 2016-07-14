## Banana configuration language

This module contains everything related to Banana. In each
sub-module (sub-folder) you will find a `README.md` file
that describes:
 
 * Purpose of the module.
 * The current status of the implementation.
 * How testing is done.

The compiler is split in passes. Each pass performs some
transformations and / or generates more data. Only the last
step has side-effects on the Monanas instance.

Each sub-module roughly maps to one pass run by the compiler.

### Passes

The Banana compiler runs the following passes:

 * `parse`, parse the input and build an [AST](./grammar/README.md).
 * `typeck`, type check the input.
 * `deadpathck`, remove dead path in the connections.
 * `eval`, evaluate the AST generated.

Each pass makes some assumptions about the state of
the data, and in particular that the previous passes
have run successfully. While this is made obvious by
the arguments required to run some passes, it is less
so for others.

Generally, things to remember:

 * Changing the ordering of passes is more likely to
   break things.
 * New passes are free to modify the AST / TypeTable.
 * New passes should not break invariants.

For more information on passes, have a look in their
specific `README.md` file.