## Grammar

This folder is all about the definition of the `banana` grammar.
The grammar purpose is to convert the input, text, into an
abstract syntax tree (AST).

This is the first step of the pipeline:
```
      +--------+                  +---------+
      |        |                  |         |
      |  Text  | --- grammar ---> |   AST   | --->
      |        |                  |         |
      +--------+                  +---------+
```

The module `ast.py` contains all the possible `ASTNode` which
itself is defined in `base_ast.py`.

### Current status

* [x] Parsing connections such as `a -> b`, `a -> [b, c]`,
      `[a, b] -> [c, d]`
* [x] Parsing numbers
* [x] Parsing string literals
* [ ] Parsing booleans
* [x] Parsing assignments where the left hand side can be a property
      or an identifier.
* [x] Parsing assignments where the right hand side is a number, a
      string literal, a property or an identifier.
* [x] Parsing components arguments using a constructor-like syntax.
* [ ] Parsing ingestors generators (for JSON dialect)
* [ ] Parsing imports such as `from ldp.monasca import *`
* [ ] Parsing disconnections such as `a !-> b` *(requires imports)*

### Tests

All test regarding the grammar (i.e. the syntax and the way
the AST is built) is defined in `test/banana/grammar`.

This folder looks like this:

```
test/banana/grammar
├── should_fail
│   ├── ...
│   └── file.banana
├── should_pass
│   ├── ...
│   └── file.banana
└── test_config.py
```

The `test_config` generates one test for each file in the
`should_pass` and `should_fail` directories.

Test can assert various things using instructions below.

#### Available instruction

* `# RAISE <exception-name>`: Check that `exception-name` is raised.
* `# STMT_EQ <ast-of-statements>` Check the AST of statements.
* `# AST_EQ <full-ast>` Check the full AST.
* `# CONN_EQ <ast-of-connections>` Check the AST of connections.