# General coding guidelines

This page documents very general coding guidelines as emerged from team discussions.

!!! NOTE

    In case you are contributing to downstream repositories such as [GT4Py](./repositories/gt4py.md) or [DaCe](./repositories/dace.md), be sure to comply with their coding guidelines.

## pytest: `xfail` vs. `raises`

In `pytest`, there are two was to expect test failure. You can either decorate the entire test function with the `@pytest.mark.fail` decorator or use the `pytest.raises` context manager within the test function to specify sections that you are expecting to fail. In general, we prefer `pytest.raises` as long as you can narrowly specify which part is expected to fail.
