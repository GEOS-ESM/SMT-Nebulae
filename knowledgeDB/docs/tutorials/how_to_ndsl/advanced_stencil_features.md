# Advanced Stencil Properties and Techniques

NDSL has a number of features which are designed to streamline development.

To help illustrate them, let's create a simple stencil where we convert temperature from Celcius
to Kelvin:

??? Example

    ``` py linenums="1"
    from gt4py.cartesian.gtscript import PARALLEL, computation, interval
    from ndsl import StencilFactory
    from ndsl.boilerplate import get_factories_single_tile
    from ndsl.constants import X_DIM, Y_DIM, Z_DIM
    from ndsl.dsl.typing import FloatField
    import random


    def celcius_to_kelvin(temperature_Celcius: FloatField, temperature_Kelvin: FloatField):
        with computation(PARALLEL):
            with interval(...):
                temperature_Kelvin = temperature_Celcius + 273.15


    class Convert:
        def __init__(self, stencil_factory: StencilFactory):

            self.constructed_copy_stencil = stencil_factory.from_dims_halo(
                func=celcius_to_kelvin,
                compute_dims=[X_DIM, Y_DIM, Z_DIM],
            )

        def __call__(self, in_quantity: FloatField, out_quantity: FloatField):
            self.constructed_copy_stencil(in_quantity, out_quantity)


    if __name__ == "__main__":

        domain = (5, 5, 3)
        nhalo = 0
        stencil_factory, quantity_factory = get_factories_single_tile(
            domain[0],
            domain[1],
            domain[2],
            nhalo,
        )

        convert = Convert(stencil_factory)

        temperature_Celcius = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
        for i in range(temperature_Celcius.view[:].shape[0]):
            for j in range(temperature_Celcius.view[:].shape[1]):
                for k in range(temperature_Celcius.view[:].shape[2]):
                    temperature_Celcius.view[i, j, k] = 20 + round(
                        random.uniform(-10, 10), 2
                    )

        temperature_Kelvin = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
        temperature_Kelvin.view[:] = -999

        convert(temperature_Celcius, temperature_Kelvin)
    ```

## Externals

NDSL has the ability build a stencil with immutable constants (called "externals") that can be
referenced only within that instance of the stencil. In this example, we can pass 273.15 to the
stencil as an external called `C_TO_K` and reference that throughout the stencil.

This ability is particularly useful as code gets more complicated, where constants may need to be
modified outside of the stencil (for instance, a tuning parameter which can vary from 0 to 1) and
where a constant is referenced numerous times throughout a stencil.

To build the stencil with an external, we just need to add a single argument to the build command:

``` py linenums="18"
        self.constructed_copy_stencil = stencil_factory.from_dims_halo(
            func=celcius_to_kelvin,
            compute_dims=[X_DIM, Y_DIM, Z_DIM],
            externals={
                "C_TO_K": 273.15,
            },
        )
```

And then to load in the external within the stencil:

``` py linenums="9"
def celcius_to_kelvin(temperature_Celcius: FloatField, temperature_Kelvin: FloatField):
    from __externals__ import C_TO_K

    with computation(PARALLEL):
        with interval(...):
            temperature_Kelvin = temperature_Celcius + C_TO_K
```

Note that these externals are not automatically passed down to any functions called with the
stencil. They must be passed in as an input.

Externals may be of type `float`, `int`, or `bool`, but must be scalar values.

NDSL has a a number of externals which are related to the compute domain of a stencil and are
always available (we will discuss compute domain more in a later section). These are:
- `i_start`
- `i_end`
- `j_start`
- `j_end`
- `k_start`
- `k_end`

## Restricting the Compute Domain

The compute domain is the subset of the model domain over which the stencil is being computed. By
default, the compute domain is the entire model domain, but NDSL has tools to introduce
restrictions. Thus far, we have used `from_dims_halo`, which always
includes the entire domain. There is another method - `from_origin_domain`, which allows more
flexibility (in fact, `from_dims_halo` calls this method with fixed arguments). Modifying our
example above:

``` py linenums="15"
class Convert:
    def __init__(self, stencil_factory: StencilFactory, domain):

        self.constructed_copy_stencil = stencil_factory.from_origin_domain(
            func=celcius_to_kelvin,
            origin=(0, 0, 0),
            domain=domain,
            externals={
                "C_TO_K": 273.15,
            },
        )
```

and now we need to pass in an additional argument to the class:


``` py linenums="38"
    convert = Convert(stencil_factory, domain)
```

The key arguments with `from_dims_halo` are `origin` (which specifies the starting point for
all computations) and `domain` (which specifies the end point). Any restrictions on `interval`
will count from these points. For example, if origin is set to `(0, 0, 1)`, and the stencil has
a computation using `with interval(1, None)`, the calculations will begin at the second K level.
A similar behavior occurs with `domain` and `interval` end points.

Note that restricting `domain` is the only way to restrict computation across the X/Y plane.
Additionally, a single stencil template can be used multiple times with different supporting
arguments to create multiple executable stencils.

Of course, using `from_dims_halo` requires information about the `domain` to be available, and a
previous guide stated that `domain` would not (and should not) be explicitly defined when
integrating code into a larger system. At that stage, informaiton about the domain will be
automatically generated and stored in a variable called `grid` - but we will talk more about that
when we get there.

## Four Dimensional Fields and Data Dimensions

It is possible to create a four dimensional field in NDSL. This is constructed as a standard
three dimensional field plus a fourth "data dimension". This fourth dimension cannot be
parallelized, and therefore cannot be iterated over like the primary three dimensions.

METHOD FOR CERATING FOUR DIMENSIONAL FIELDS WILL GO HERE ONCE IT IS FINALIZED
(if we are sticking with the current method let me know and I will put that here, but I think
we should have it more streamlined at some point)

These fields have a unique accessing method: `field.A[0, 0, 0][0]`. The first three indexes are
the standard relative indexing method, while the fourth is an *absolute* index cooresponding to the
desired location along the additional axis that you want to reference.

Using a similar method as above, it is also possible to create data dimensions with one or two
of the primary three dimensions. Note that there must always be one primary dimension present.

## Typecasting

NDSL uses the traditional Python functions `int()` and `float()` to cast numbers to integers or
floating point precision, respectively. When using these casts, the precision is automatically
set to line up with the specified global precision. It is possible; however, to overwrite this and
cast explicitly to a 32 or 64 bit version with `i32()`/`i64()`/`f32()`/`f64()`

It is also possible to initate a temporary field with a specific type. The correct nomenclature is:
`field: type = 0` where `type` can be any of `i32`/`i64`/`f32`/`f64`

## Current Index Information

NDSL stores informaiton about the current K level in a variable called `THIS_K` as type `Int`.
This must be imported from `gt4py.cartesian.gtscript` prior to being used.

## Absolute K Indexing

NDSL does have a method for absolute indexing within a stencil, but it should be used with caution.
This can only be used at read (similar to offsets), and should only be used when absolutly
necessary (i.e. do not rely on this when relative offsetting is sufficient).

The proper nomenclature is `field.at(K=level)` where level is a `Int` type number, variable, or
expression which cooresponds to a level present in the accessed field.

NOTE: add information about four dimensional fields once we have updated that

## Looking Backwards to Move Forward

This guide introduced some more advanced features and exceptions to some of NDSL's rules. If used
as designed these features will have no impact on performance, but it is possible to misuse these
features in ways that will degrade performance. For that reason, it is recommended that these
features are used sparingly, to that they do not become a crutch that enables poor coding habits
and reduces the potentcy of the software as a whole.

Next, we will present a number of patterns commonly seen in weather and climate modeling,
and provide examples of how they are implemented in NDSL.