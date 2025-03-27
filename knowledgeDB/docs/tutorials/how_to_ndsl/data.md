# NDSL Data Types and Storage System

## Types

NDSL uses unique data types (`Float`/`Int`/`Bool`) which correspond to commonly used NumPy data
types (`float`/`int`/`bool`). These NDSL data types are able to dynamically determine the precision
of the environment and assign the correct data type at execution
(e.g. `Float` will become `np.float32` vs `np.float64`).

TEMPORARY, UPDATE WITH DEVELOPMENT: To control the behavior of this, the set the environment variable `GT4PY_LITERAL_PRECISION` to
either 32 or 64 (default is 64).

## Fields

Unlike traditional Python, NDSL data types also implicitly carry information about the shape
of the object. `Float`/`Int`/`Bool` all denote scalar (dimensionless) objects.

All objects with one or more dimensions are considered "fields". NDSL assumes a cartesian
I/J/K coordinate system field, where I and J are horizontal dimensions and K is the vertical
dimension, but allows these to be defined dynamically (more on this in the next section).

The name of NDSL fields depends on the data type and the dimensions present. Some examples:

- `FloatFieldI`: one dimensional (I) field of type Float
- `BoolFieldIK`: two dimensional (I, K) field of type Bool
- `FloatFieldJK`: two dimensional (J, K) field of type Float
- `Bool`: scalar variable of type Bool
- `IntField`: three dimensional (I, J, K) field of type Int

Note that there is no `*_FieldIJK`; this is simply `*_Field`. 

## Data Storage

NDSL stores all data in a "quantity" object. Quantities allocate memory and assign field type
based which axis are present. Quantities must have at least one axis (else you have a
scalar variable, which have no special storage methods).

Below is an example of how to initalize an NDSL quantity with three dimensions:

``` py linenums="1"
from ndsl.boilerplate import get_factories_single_tile
from ndsl.constants import X_DIM, Y_DIM, Z_DIM

domain = (3, 2, 1)
nhalo = 0
stencil_factory, quantity_factory = get_factories_single_tile(
    domain[0], domain[1], domain[2], nhalo,
)

quantity_example = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a", dtype=Float)
```

For now, lets just worry about line 10. Here, we use the `quantity_factory` object (more about this
later) to initalize a quantity. The first argument, `[X_DIM, Y_DIM, Z_DIM]`, tells the system
where to put each dimension within the quantity. Generally, the size of each dimension will be
determined automatically, but here we have supplied `domain = (3, 2, 1)`, so the resulting quantity
will have three dimensions, with the size the X/Y/Z dimension corresponding to position 0/1/2 in
domain, respectively. Note that changing the order of the first argument only changes the order of
each dimension within the quantity, and that one dimension can be used twice (e.g.
`[Y_DIM, X_DIM, X_DIM]`, will correspond to a 2x3x3 quantity); however, unless you have a very good
reason to do so, it is generally best to leave the dimensions as [X, Y, Z] and only remove any
that are unneeded.

The second argument, `"n/a"`, specifies the units of the data stored. This is only for
metadata and ease of use, and has no impact on calculations. The final argument `dtype` controls
the type of data stored in the quantity, and can be `Float`/`Int`/`Bool`.

Finally, we can print the quantity we have just created to check our work. Based on the code above,

``` py linenums="11"
print(quantity_example)
```

will return:

```
Quantity(
    data=
[[[0. 0.]
  [0. 0.]
  [0. 0.]]

 [[0. 0.]
  [0. 0.]
  [0. 0.]]

 [[0. 0.]
  [0. 0.]
  [0. 0.]]

 [[0. 0.]
  [0. 0.]
  [0. 0.]]],
    dims=('x', 'y', 'z'),
    units=n/a,
    origin=(0, 0, 0),
    extent=(3, 2, 1)
)
```

Here you can see information about the dimensions present, size (extent), units,
and origin (a concept we will discuss later).

But wait, if our extent is (3, 2, 1), why is `data` size (4, 3, 2)?

**Center vs Interface Computations**

This extra index along each dimension are for interface computations. In weather and climate
modeling, there are often situations where it is necessary to perfome calculations on the interface
between grid points, rather than at the center of grid points. NDSL always
creates quantities with one extra grid point on each dimension; however, this extra point is
ignored by the system unless you explitly state that it should be considered by replacing
(for example) `Z_DIM` with `Z_INTETFACE_DIM`.

**Halo**

NDSL quantities can be contructed with a halo on the X and Y dimensions. This is useful
when working with components such as the FV3 core, which uses a halo to facilitate data exchange
between faces of the cube. In the example above, the halo is set to zero (`nhalo=0`), but this can
be set to any value smaller than the smallest X/Y dimension.

**Accessing Data**

There are two main methods for accessing data stored within a quantity:

- `quantity.view[:]`: returns the numerical contents of the quantity as a numpy array. This print
always include the extra point from the interface dimension, regardless of whether that point is
being considered for computations. Note that, since this is a NumPy array, it can be acccessed
using normal Python accessing rules.

- `quantity.data[:]`: similar to `quantity.view[:]`, but `.data` also returns the halo, if one
is present.

**Stencil/Quantity Factories**

NDSL comes with a number of predesigned factory functions (e.g. `get_factories_single_tile`).
These are designed to provide users with easy entry points to features while developing new code.

When working in a larger system the tasks of determining the domain and constructing factories
(lines 4-8 from the example above) are done automatically, and as such this code will not be needed.

Therefore, we recommend you don't worry about how `get_factories_single_tile` works for now. As we
move through more advanced guides we will introduce additional details and complexities that will
peel back the shades on some of the magic, but even as that occurs it is important to remember that
this is a tool used strictly for development/testing new code, and should not be relied upon for any
automated processes.

The `QuantityFactory` and `StencilFactory` will be present in all your code, but once again you
need not worry about how they function for now. For now, just remember that a `QuantityFactory`
produces quantities and a `StencilFactory` produces stencils (something we will talk about in the
next guide).

# Looking Backwards to Move Forward

In this guide, we have discussed the unique NDSL data types and storage objects, focusing on how
to create, access, and print their contents.

Next, we will discuss how to write acceleratable code with NDSL.