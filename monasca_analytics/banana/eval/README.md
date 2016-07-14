## Interpreter / Evaluator

This folder contains everything related to the evaluation
of banana files.

This pass makes some assumptions: it is valid to create
all the components and connecting them won't throw any errors.

Some components might need to be created in order to
check if they are valid. For instance, when a DNS lookup is
involved. In such cases, an error will be thrown during
the interpretation. However, the general intention is to move 
the checks out of the evaluation as much as possible. We want to
avoid at all cost an half-working pipeline as it could have
side-effects on external data sources by corrupting them or
feeding them with incorrect data.

The execution environment (e.g Spark) might also reject the
pipeline during an evaluation for some reason. However, this is
less likely to happen as the `deadpathck` pass removes
components and paths that would lead to errors.

This is the last step of the pipeline:
```
       +---------------------+
       |                     |
 --->  |   AST & TypeTable   | ---- interpret --->     Done
       |                     |
       +---------------------+
```

### Current status

* [x] Evaluate expressions
* [x] Create components
* [x] Connect components
* [x] Restart the pipeline

### Tests

All tests are located in `test/banana/eval`. We only try
to evaluate valid files, so for this pass there's only a
`should_pass` directory.

#### Available instruction

* `# LHS_EQ <string-version-of-the-value>`: This instruction
  compares the evaluation of the left hand side of the previous
  expression with the provided string. If they are not equal,
  the test will fail.