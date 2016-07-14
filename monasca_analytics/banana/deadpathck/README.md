## Dead path checker

Dead path checking is about removing paths in the pipeline that
lead to nothing. For instance, if there's no source or no sink
in a path. This pass is the only one that modifies the AST.

This is the third step of the pipeline:
```
       +---------------------+                        +---------------------+
       |                     |                        |                     |
 --->  |   AST & TypeTable   | ---- deadpathck --->   |  AST' & TypeTable'  | --->
       |                     |                        |                     |
       +---------------------+                        +---------------------+
```

### Current status:

* [x] Remove branches that are dead from the list of connections.
* [x] Remove the components from the collected list of components.
* [ ] Remove statements that are dead code:
  - [ ] Do not instantiate components.
  - [ ] Do not compute expressions for unused variables.
