# General coding guidelines

This page documents very general coding guidelines as emerged from team discussions.

!!! Note

    In case you are contributing to downstream repositories such as [GT4Py](./repositories/gt4py.md) or [DaCe](./repositories/dace.md), be sure to comply with their coding guidelines.

## string concatenation

Prefer `f-strings` over any other method of concatenation strings.

???+ Example "String concatenation with f-strings"

    ```python
    my_world = "world"
    greeting = "Hello"
    concatenated_string = "f{greeting} {my_world}"
    ```

Rationale: Florian likes this way and nobody else had a strong opinion.

## pytest:  `raises` vs. `xfail` vs. `skip`

In short:

- use `pytest.raises` to check that we raise an exception if the user makes a mistake, e.g. to check that for a program with syntax error we raise an exception.
- use `xfail` to indicate that a test fails, but should be supported, e.g. because we are missing a feature (or missing a feature for a certain backend).
- use `skip` to indicate that under a certain condition the test doesn't make sense.

That means: `skip` and `pytest.raises` are used in bugfree cases, `xfail`s are the ones that should be fixed. Further reading in the [pytest docs](https://docs.pytest.org/en/7.1.x/how-to/skipping.html).

Rationale: Established standard in the ecosystem and actively promoted by the `pytest` documentation.
