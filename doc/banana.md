# Banana: a configuration language for Monanas

Welcome to Banana, a configuration language for Monanas. The language is the
key of "recipes" allowing users to reuse it to tailor solutions for their
use-cases. In other words, Banana allows us to write a recipe(s) that will be
ingested by Monanas.

The language is fully typed. It uses type inference to avoid having to add any
typing annotation. It is still in its early stages, so more features will be
added to solve common problems.

> Note: a valid `banana` recipe (or file) might still contain errors that
>       can only be discovered at run-time. The type system, will remove
>       most of them though.

To get you started, we provide an example below, which would allow us to
understand most parts of the language.

> TODO: Once we have a specified interface, we should use it instead as it will
> provide syntax highlighting, in-editor error indication as well as other
> features such as autocompletion.

## Part 1: Creating components

Here is how we create a component:

```python
# Create an IPTablesSource with sleep parameter set to 0.01
src = IPTablesSource(sleep=0.01)
```

We could also create a component without any parameter. In that case, each
parameter is initialized with a default value.

In order to get something interesting we first create the following components:

```python
src = IPTablesSource(sleep=0.01)
ing1 = IptablesIngestor()
svm = SvmOneClass()
voter = PickIndexVoter(0)
ldp1 = IptablesLDP()
stdout = StdoutSink()
sqlite = IptablesSQLiteSink()
```

## Part 2: Connecting components

Connections can be placed anywhere in the file. They will always be processed
after everything else.

We have created five components so far, but note that, some components can only
connected to certain types of components). For instance, a source can only
be connected to an ingestor or a live data processor. However, you can't
connect it to a statistical or machine learning algorithms as those need to get
curated data only. Try to add the following line:

```py
src -> alg
```

You should see an error, saying that this is not possible:

```
Error: Can't connect src to alg, src can only be connected to Ingestor.
```

What we want is to have those connections:

```
+---------+       +---------+        +---------+       +---------+     +---------+       +------------+
|   src   +-----> |   ing1  +------> |   alg   +-----> |   vot   +---> |   ldp   +-----> |   stdout   |
+----+----+       +---------+        +---------+       +---------+     +----+----+       +------------+
     |                                                                      ^
     |                                                                      |
     +----------------------------------------------------------------------+
```

Here is how we can achieve that:

```
src -> [ing1 -> alg -> vot -> ldp, ldp]
ldp -> stdout
```

We could also write it like this:

```
src -> ing1 -> alg -> vot -> ldp
src -> ldp -> stdout
```

Or like this:

```
src -> ing1
src -> ldp
ing1 -> alg
alg -> vot
vot -> ldp
ldp -> stdout
```

The main difference is readability and this is subjective. Use the version that
you think is more readable.

Banana will treat all of them as being semantically identical.

## Part 3: Sharing settings between components

From what we described above, it is possible that we could end up with many
similar parameters across components. It would be great if we could share them.
In Banana we can declare a variable not only for components, but also for
`string`, `number` and json-like `object`.

For instance, this is valid in banana:

```python
sleep = 0.01
# ...
```

You can also make use of arithmetic operators to perform any computation you
might require with previously declared variables or anything else.

Some global variables, defined by the execution environment are also available.
For instance, you could define `sleep` like this:

```python
sleep = 0.01 / $spark.BATCH_INTERVAL
# ...
```

> TODO: the above feature has not yet been implemented.

Finally, Banana supports string interpolation to mix many types together:

```python
port = 9645
host = "localhost:" + port
```
