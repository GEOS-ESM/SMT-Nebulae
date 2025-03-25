# Stencil and Function Basics

NDSL derives much of its power from the ability to accelerate and dynamically compile code for
the situation at hand. To do this, NDSL has two constructs which are used to denote and contain
acceleratable code: "stencils" and "functions". Conceptually, the two are similar, but their uses
are quite different.
</br></br>

# Stencils

Stencils are the primary method of creating parralelizable code with NDSL, and indeed in NDSL
everything must begin with a stencil.

Within a 3-dimensional domain, NDSL evaluates computations in two parts. If we assume an (X, Y, Z)
coordinate system as a reference, NDSL separates computations in the horizontal (X, Y) plane from the
vertical (Z) column. In the horizontal plane, computations are implicitly executed in parallel,
which means that there is no assumed calculation order within the plane. In the vertical column,
comptuations are performed by an iteration policy that is declared within the stencil.

To demonstrate how to implement a NDSL stencil, let's step through an example that copies the
values of one array into another array.

## Basic Stencil Example

First, we import several packages:

``` py linenums="1"
from ndsl import StencilFactory
from ndsl.boilerplate import get_factories_single_tile
from ndsl.constants import X_DIM, Y_DIM, Z_DIM, Z_INTERFACE_DIM
from ndsl.dsl.typing import Float, FloatField
import gt4py.cartesian.gtscript as gtscript
from gt4py.cartesian.gtscript import PARALLEL, computation, interval
```

Next, we define our stencil template:

``` py linenums="7"
def copy_stencil(in_field: FloatField, out_field: FloatField):
    with computation(PARALLEL):
        with interval(...):
            out_field = in_field
```

This stencil template has a number of important features and keywords. Let's start with the inputs:
`in_field` and `out_field`. These are both declared to be type `FloatField` (more information
available [here](./data.md)). This notation is used in traidtional Python, and may be familiar to
you as optional "type hinting". For stencils (and functions) these type hints are required, and the
code will not execute if the supplied type does not match the expected/declared.

Looking into the stencil code, we can see perhaps the most important keywords in NDSL. 

The statement `with computation(PARALLEL)` states that *all three* dimensions can be executed in
parallel. The statement `with interval()` controls the vertical columns over which the stencil is
executed. We will discuss both of these in more detail later.

While not entirely accurate, it is reasonable to consider `with computation()` as a conceptual
replacement for traditional Python loops over X and Y, and `with interval()` as a replacement for
a loop over Z.

Now we set up our class:

``` py linenums="11"
class create_quantity:
    def __init__(self, stencil_factory: StencilFactory):

        self.constructed_copy_stencil = stencil_factory.from_dims_halo(
            func=copy_stencil,
            compute_dims=[X_DIM, Y_DIM, Z_DIM],
        )

    def __call__(self, in_quantity: FloatField, out_quantity: FloatField):
        self.constructed_copy_stencil(in_quantity, out_quantity)
```

Here is where we actually build our stencil (lines 13-16). Behind the scenes the system is
compiling code based on a number of considerations, most important of which is the target
architecture: CPU or GPU. We will discuss more build options in a future sections, but you will
always have to specify `func` (to determine what stencil is being built), and `compute_dims`
(unless you have a very good reason, should likely remain `[X_DIM, Y_DIM, Z_DIM]).

Stencils modify fields in place, may not contain a return statement, and therefore must have all
inputs *and* outputs passed into it at call.

Finally we can run the program:

``` py linenums="21"
if __name__ == "__main__":

    domain = (5, 5, 3)
    nhalo = 0
    stencil_factory, quantity_factory = get_factories_single_tile(
        domain[0],
        domain[1],
        domain[2],
        nhalo,
    )

    class_instance = create_quantity(stencil_factory)

    in_quantity = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
    for i in range(in_quantity.view[:].shape[0]):
        for j in range(in_quantity.view[:].shape[1]):
            for k in range(in_quantity.view[:].shape[2]):
                in_quantity.view[i, j, k] = i * 100 + j * 10 + k

    out_quantity = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
    out_quantity.view[:] = -999

    class_instance(in_quantity, out_quantity)
```

## Offsets

Within a stencil, points are referenced relative to each other. For example, the statement
`field[0, 0, 1]` displays that you want an offset of positive one along the K axis (Z dimension
in our example). Additionally, all offsets must occur at read. NDSL does not allow writing with
an offset.

With this knowledge, we can now create a stencil that copies data from the level above:

``` py linenums="1"
def copy_with_offset(in_field: FloatField, out_field: FloatField):
    with computation(PARALLEL):
        with interval(0, -1):
            out_field = in_field[0, 0, 1]
```

Note that we have to restrict the interval to prevent the computaiton from occuring on the top
level of `out_field`, as looking "up" from the top level would look into the extra point included
for interface calculations. Since this computation is not being performed on the interface (both
quantities are created using `Z_DIM`, not `Z_INTERFACE_DIM`), that row of data will be zero, and
accessing here will have unintented consequences in subsequent calculations.

## Intervals and Iteration Policies

The statement `with interval()` controls the subset of the K axis over which the stencil is
executed, and is controlled using traditional Python indexing (e.g. `interval(0, 10)`,
`interval(1, -1)`). The argument `None` can be used to say "go to end of the domain" (e.g.
`interval(10, None)`). The argument `...` signals compute at all levels - equivalent to `0, None`.

As previously mentioned, NDSL has three possible iterations policies: `PARALLEL`, `FORWARD`, and
`BAKWARD`. Choosing `PARALLEL` states that all three dimensions can be executed in parallel
(recall that NDSL always executes the I and J dimensions - in our example `X_DIM` and `Y_DIM` -
in parallel).

The `FORWARD` and `BACKWARD` options require that all calculations for a perticular K level are
computed before moving on to the next K level, and are therefore slower than `PARALLEL`. `FORWARD`
executes from the first argument in the `with interval()` statement to the second (e.g.
`with computaiton(FORWARD), interval(0, 10)` begins at 0 and ends at 9), while `BACKWARD` does the
opposite (begins at 9, ends at 0).

`FORWARD` and `BACKWARD` are useful for more complex situations where data is being read with an
offset and written in the same stencil:

``` py linenums="1"
def NEED_NAME(in_field: FloatField, out_field: FloatField):
    with computation(FORWARD):
        with interval(0, -1):
            out_field = in_field[0, 0, 1]
            in_field = in_field * 2
```

In this example, `in_field` is being read in but also modified. It is therefore necessary to use
`FORWARD` to ensure that there is not a situation where in_field is doubled at a level `n`
before it is read at level `n - 1`.

## Flow Control

A number of traditional Python flow control keywords can be used within NDSL stencils. These are:

- `if`
- `elif`
- `else`
- `while`
- `for`
</br></br>

**Conditionals**

NDSL allows conditionals to be used inside of a stencil in the same way they would be used
in traditional Python.

**Loops**

Loops are legal with NDSL stencils, but must have definite limits (e.g. no `while True`)

NEED TO UNDERSTAND THE NEW FOR LOOP FEATURE THEN WRITE SOMETHING ABOUT IT
</br></br>

# Functions

Functions appear visually similar to stencils, but are differ greatly in their use. Functions are
fundamanetally **point computations** - they execute at each point in the domain (if they are
called form the stencil at that point) entirely independent of executions elsewhere in the domain.

Functions have a number of important quirks. Functions:
- cannot contain the keywords `computaiton` or `interval` (they rely on the stencil for this info)
- cannot be called outside of a stencil
- cannot possess any offsets (read or write)
- must be defined with scalar inputs/outputs
- are not tied to a single stencil, and may be reused across any number of stencils
- do not need to be constructed with a stencil factory (they are built with the stencil)

Below is an example of a NDSL function, called from within a stencil:

``` py linenums="1"
@gtscript.function
def copy_plus_five(in_scalar: Float, out_scalar: Float):
    out_scalar = in_scalar + 5
    return out_scalar


def copy_stencil(in_field: FloatField, out_field: FloatField):
    with computation(PARALLEL):
        with interval(...):
            out_field = copy_plus_five(in_field, out_field)
```

Note that you can pass fields to the function, even though the function is defined with scalar
inputs. This is a quality of life feature of NDSL. Behind the scenes, the system takes these
fields and extracts the scalar value which cooresponds to the current index, and only this value
is passed onwards to the function.
</br></br>

# Stencils vs Functions

Every computaiton block must have an outermost layer of a stencil. The stencil signals that
parallel computation is possible, and defines the iteration policy and interval. From this point
the following logic applies:

- It is not possible to call one stencil from within another, as that would create a situation where
you have two layers of parallelization. If you want to reuse code in two stencils, it should be put
into a function. For similar reasons, it is not possible to call a stencil from within a function.

- Since functions are point computations and operate independently of iteration polity and interval,
it is possible to call one function from other within functions.
</br></br>

# Basic Stencil & Function Tips and Tricks

Multiple stencils can be used sequantially with no impact on performanc - NDSL will combine
these stencils during compilation.

Similarly, a single stencil can have any number of `with computation()` and `with interval()`
statments. They do not need to appear in pairs, but often do (in which case they can be
concisely stated as `with computation(), interval()`). Remember that all numerical calculations must
be inside of these two statements (either directly in a stencil, or indirectly via a function call).

When writing code in NDSL, it is generally best to prioritze readability and make your
code as *approachable* as possible. NDSL will find ways to optimize it and make it as *fast*
as possible.
</br></br>

# Looking Backwards to Move Forward

This guide introduced the basic principles of stencils and functions. We have discussed how and
when to use each, and highlighted features that make their use more flexible, and
discussed limitations which act as guardrails against unfavorable outcomes.

With this knowledge, it is possible to use NDSL and obtain much of the designed performance;
however, development may at times seem tedious and implementing more complicated patterns may
be challenging. Future sections will introduce more complex ideas and discuss quality of life
features which aim to alleviates these issues.
