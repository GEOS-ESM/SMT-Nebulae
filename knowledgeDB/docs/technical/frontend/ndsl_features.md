# NDSL features

List of features that NDSL brings on top of GT4Py:

1. [Stencil- and Quantity-Factories](https://github.com/NOAA-GFDL/NDSL/blob/develop/examples/NDSL/02_NDSL_basics.ipynb)
2. [Orchestration](https://github.com/NOAA-GFDL/NDSL/blob/develop/examples/NDSL/03_orchestration_basics.ipynb)

## Tips and tricks

The not so obvious stuff.

??? note "Experimental features"

    See [Experimental "Physics" features](./experimental_features.md) for a list of experimental features, which might or might not make it to mainline in the future.

!!! example "Stencil factory with different K profile"

    To generate a new sterncil factory from an existing one but with a different K profile (start and size), run

    ```python
        new_factory = existing_factory.restrict_vertical(k_start=1)
    ```
