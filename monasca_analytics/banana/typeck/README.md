## Type-checker

This folder is all about the type checking of `banana` files.
The type checker purpose is to verify that components exist,
the type of local variable matches the requirements of components
parameters and assignments between them are correct. It also
checks that connections between components are valid.

The biggest difference between the old `validation` of the JSON
format is that we have more information available. We can warn
users when they make mistakes and point at the exact locations
using `Span`. Also, the type table generated is used by other passes
to perform other static analyses.

This is the second step of the pipeline:
```
       +-------+                  +---------------------+
       |       |                  |                     |
 --->  |  AST  | ---- typeck ---> |   AST & TypeTable   | --->
       |       |                  |                     |
       +-------+                  +---------------------+
```

The module `type_util.py` contains all the possible types that are
known by the type checker. The `TypeTable` built lives in the
`type_table.py` module.

### Current status

* [x] Type check numbers
* [x] Type check string literals
* [x] Type check variable assignments
* [x] Type check component assignments
* [x] Type check component parameters
* [x] Type check connections
* [x] Resolve variable names
* [ ] Resolve imports
* [ ] Type check disconnections

### Tests

All tests for the type checker (i.e. making sure that
inferred types are correct and that errors are raised in
appropriate situation) lives in `test/banana/typeck`.

This folder looks like this:

```
test/banana/typeck
├── should_fail
│   ├── ...
│   └── file.banana
├── should_pass
│   ├── ...
│   └── file.banana
└── test_typeck_config.py
```

The `test_typeck_config`, generates one test for each file 
in the `should_pass` and `should_fail` directories.

For each generated test, we basically run the following passes:

* `grammar`: convert the input text into an AST.
* `typeck`: run the type checker.

Tests can assert various things in `banana` comments:

 - In the `should_fail` directory, a test is expected to use
   the `RAISE` instruction to specify a type of exceptions
   that should be raised by the test.
 - In the `should_pass` directory, a test is expected to not
   raised any exception **and** to specify the state of the
   `TypeTable` when the type checker has type checked everything
   in the file. This is done with the `TYPE_TABLE_EQ` instruction.


#### Available instruction

* `# RAISE <exception-name>`: Check that `exception-name` is raised.
* `# TYPE_TABLE_EQ <string-version-of-the-type-table>`
* `# NEW_TEST`: This instruction splits the file into two tests. However, 
  the expected exception or type table should still be the same. It 
  allows us to verify what should be semantically equivalent in the 
  grammar.