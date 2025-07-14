# Stencil and Function Basics

NDSL derives its power from the ability to accelerate and dynamically compile code. To do this,
NDSL creates an interface to two GT4Py constructs which are used to denote and contain acceleratable code: "stencils" and "functions". Conceptually, the two are similar, but their uses are different.

## Stencils

Stencils are the primary method of creating parralelizable code with NDSL, and indeed in NDSL
everything must begin with a stencil.

Within a 3-dimensional domain, NDSL evaluates computations in two parts. If we assume an (X, Y, Z)
coordinate system as a reference, NDSL separates computations in the horizontal (X, Y) plane from the
vertical (Z) column.

In the horizontal plane, computations are **always** executed in parallel, which means that there is
no assumed calculation order within the plane. This concept is the foundation of of NDSL's
performance capabilities, and cannot be altered.

In the vertical column, computations are performed by an iteration policy that is declared
within the stencil. This is done to enable the implementation of more scientific patterns using
NDSL. We will discuss this in more detail shortly.

**Basic Stencil Example**

To demonstrate how to implement a NDSL stencil, let's step through an example that copies the
values of one field into another field. First, we import several packages:

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

Note that there is no return statement here. Stencils modify fields in place **may not** contain
a return statement, and therefore must have all inputs *and* outputs passed into it at call.

This stencil template has a number of important features and keywords. Let's start with the inputs:
`in_field` and `out_field`. These are both declared to be type `FloatField`. This notation is used
in traditional Python, and may be familiar to you as optional "type hinting". For stencils
(and functions) these type hints are required, and the code will not execute if the supplied type
does not match the declared type.

Looking into the stencil code, we can see the two most important keywords in NDSL.

The statement `with computation(PARALLEL)` signals that *all three* dimensions can be executed in
parallel. The statement `with interval(...)` signals that the computation should apply to all
vertical levels over which the stencil is executed. More specifically, `with computation(PARALLEL)` specifies the iteration direction in K, and `with interval(...)` describes the extent of the K-axis 
to apply this computation to. A stencil may have multiple compute blocks and each compute block may 
have multiple intervals, but intervals within a compute block must be in-order and cannot overlap.

Now we set up our class:

``` py linenums="11"
class CopyData:
    def __init__(self, stencil_factory: StencilFactory):

        self.constructed_copy_stencil = stencil_factory.from_dims_halo(
            func=copy_stencil,
            compute_dims=[X_DIM, Y_DIM, Z_DIM],
        )

    def __call__(self, in_quantity: FloatField, out_quantity: FloatField):
        self.constructed_copy_stencil(in_quantity, out_quantity)
```

Here is where we actually build our stencil (lines 14-17). Behind the scenes the system is
compiling code based on a number of considerations, most important of which is the target
architecture: CPU or GPU. You will always have to specify `func` (to determine what stencil is being built), and `compute_dims`(we will discuss restricting the `compute_dims` in a later guide), 
unless you are using stencil_factory.from_origin_domain() to compile a stencil, which will be 
discussed in a later section.


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

    copy_data = CopyData(stencil_factory)

    in_quantity = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
    for i in range(in_quantity.view[:].shape[0]):
        for j in range(in_quantity.view[:].shape[1]):
            for k in range(in_quantity.view[:].shape[2]):
                in_quantity.view[i, j, k] = i * 100 + j * 10 + k

    out_quantity = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
    out_quantity.view[:] = -999

    copy_data(in_quantity, out_quantity)
```

**Temporary Fields**

NDSL has the ability to generate temporary quantities within a stencil. All temporary quantities
(defined as variables which are used within the stencil but not passed to the stencil at call) are
initialized as a field of dimensions equal to the full stencil domain. These fields can be used
just as any other field can be used.

**Offsets**

Within a stencil, points are referenced relative to each other. For example, the statement
`field[0, 0, 1]` implies that you want an offset of positive one along the K axis (Z dimension
in our example). Offsets can only occur at read; NDSL does not allow writing with an offset.
Additionally, it is not possible to write to a field when you read from it with an offset in the
same statement (e.g. `field = field[0, 0, 1]` is illegal).

With this knowledge, we can now create a stencil that copies data from the level above:

``` py linenums="1"
def copy_with_offset(in_field: FloatField, out_field: FloatField):
    with computation(PARALLEL):
        with interval(0, -1):
            out_field = in_field[0, 0, 1]
```

Note that the interval is restricted to prevent the computation from occurring on the top
level of `out_field`, as looking "up" from the top level would look into the extra point included
for interface calculations. Since this computation is not being performed on the interface (both
quantities are created using `Z_DIM`, not `Z_INTERFACE_DIM`), that row of data will be zero, and
accessing it here will have unintended consequences in subsequent calculations.

**Intervals and Iteration Policies**

The statement `with interval()` controls the subset of the K axis over which the stencil is
executed, and is controlled using traditional Python indexing (e.g. `interval(0, 10)`,
`interval(1, -1)`). The argument `None` can be used to say "go to end of the domain" (e.g.
`interval(10, None)`). The argument `...` signals compute at all levels, equivalent to `0, None`.

NDSL has three possible iteration policies: `PARALLEL`, `FORWARD`, and `BACKWARD`.
Choosing `PARALLEL` states that the vertical dimension will be executed in parallel. In this state,
each point in the domain is computed independently in the fastest possible order. This means that
fields are being written in random order, and therefore any operations which depend on data at
other points in a field which is being written (e.g. `out = in_field[0, 0, 1]`) cannot use
`PARALLEL`.

The `FORWARD` and `BACKWARD` options can be considered non-parallel options for the K axis. These
options require that all calculations for a particular K level are computed before moving on to the
next K level. This is **often significantly slower than `PARALLEL`**, but ensures that each kernel
has the information between execution of each index along the K axis. `FORWARD` executes from the
first argument in the `with interval()` statement to the second (e.g.
`with computation(FORWARD), interval(0, 10)` begins at 0 and ends at 9), while `BACKWARD` does the
opposite (begins at 9, ends at 0).

`FORWARD` and `BACKWARD` are useful for more complex situations where data is being read with an
offset and written in the same stencil:

``` py linenums="1"
def offset_read_with_write(in_field: FloatField, out_field: FloatField):
    with computation(FORWARD):
        with interval(0, -1):
            out_field = in_field[0, 0, 1]
            in_field = in_field * 2
```

In this example, `in_field` is being read in but also modified. It is therefore necessary to use
`FORWARD` to ensure that there is not a situation where `in_field` is doubled at a level `n`
before it is read at level `n - 1`.

Using offsets often requires a careful consideration of iteration policy.

**Flow Control**

A number of traditional Python flow control keywords can be used within NDSL stencils. These are:

- `if`
- `elif`
- `else`
- `while`
- `for`

**Conditionals**

NDSL allows conditionals to be used inside of a stencil in the same way they would be used
in traditional Python.

**Loops**

Loops are legal with NDSL stencils, but must have definite limits (e.g. no `while True`)

NEED TO UNDERSTAND THE NEW FOR LOOP FEATURE THEN WRITE SOMETHING ABOUT IT

## Functions

Functions in NDSL are used similar to traditional Python functions. They can be used to make code
visually more appealing, and are inlined at execution. Technically, NDSL functions are GT4Py 
constructs, that NDSL provides an interface for. They are "pure" functions - meaning they 
cannot modify arguments in-place and just return values.

Functions follow all the same rules as stencils, a but have a number of important quirks. Functions:

- cannot contain the keywords `computation` or `interval` (they rely on the host stencil for this info)
- cannot be called outside of a stencil
- must have a single return statement, but can return multiple values
- are not tied to a single stencil, and may be reused across any number of stencils
- do not need to be constructed with a stencil factory (they are built with the stencil)

Below is an example of a NDSL function, called from within a stencil:

``` py linenums="1"
@gtscript.function
def copy_plus_five(in_field: FloatField, out_field: FloatField):
    out_field = in_field + 5
    return out_field


def copy_stencil(in_field: FloatField, out_field: FloatField):
    with computation(PARALLEL):
        with interval(...):
            out_field = copy_plus_five(in_field, out_field)
```

**Builtin Functions**

NDSL has a number of builtin functions:

- `abs`: absolute value
- `min`: minimum
- `max`: maximum
- `mod`: modulo
- `sin`: sine
- `cos`: cosine
- `tan`: tangent
- `sinh`: hyperbolic sine
- `cosh`: hyperbolic cosine
- `tanh`: hyperbolic tangent
- `asin`: arc sine
- `acos`: arc cosine
- `atan`: arc tangent
- `asinh`: inverse hyperbolic sine
- `acosh`: inverse hyperbolic cosine
- `atanh`: inverse hyperbolic tangent
- `sqrt`: square root
- `exp`: inverse hyperbolic sine
- `log`: natural log
- `log10`: base 10 log
- `gamma`: gamma function
- `cbrt`: cubic root
- `isfinite`: determine if number is finite
- `isinf`: determine if number is infinite
- `isnan`: determine if number is nan
- `floor`: round down to nearest integer
- `ceil`: round up to nearest integer
- `trunc`: truncate
- `round`: round to nearest integer
- `erf`: error function
- `erfc`: complementary error function

NOTE. EVENTUALLY ADD LINKS TO FULL DOCSTRING DOCUMENTATION FOR EACH FUNCTION ONCE THEY EXIST

## Stencils vs Functions

Every computation block must have an outermost layer of a stencil. The stencil signals that
parallel computation is possible, and defines the iteration policy and interval. From this point
the following logic applies:

- It is not possible to call one stencil from within another, as that would create a situation where
there are two layers of parallelization. If you want to reuse code across multiple stencils, it
should be put into a function.

- For similar reasons, it is not possible to call a stencil from within a function.

- As long as you are originating from a stencil, it is possible to call one function from
within another function.

## Basic Stencil & Function Tips and Tricks

When using a DaCe backend, multiple stencils can be used sequentially with no impact on 
performance - NDSL will combine these stencils during compilation.

Similarly, a single stencil can have any number of `with computation()` and `with interval()`
statements. They do not need to appear in pairs, but often do (in which case they can be
concisely stated as `with computation(), interval()`). Remember that all numerical calculations must
be inside of these two statements (either directly in a stencil, or indirectly via a function call).

When writing code in NDSL, it is generally best to prioritize readability and make your
code as *approachable* as possible. NDSL will find ways to optimize it and make it as *fast*
as possible.

## Looking Backwards to Move Forward

This guide introduced the basic principles of stencils and functions. We have discussed how and
when to use each, and highlighted features that make their use more flexible, and
discussed limitations which act as guardrails against unfavorable outcomes.

With this knowledge, it is possible to use NDSL and obtain much of the designed performance;
however, development may at times seem tedious and implementing more complicated patterns may
be challenging. Future sections will introduce more complex ideas and discuss quality of life
features which aim to alleviates these issues.
