# Milestone 2

Milestone 2 was started on March 2025 and will run until the end of August 2025.

Results can be found in the [results section](results/M2_Sept25/summary.md).

## Branches setup

Not all features that we use in the results for milestone 2 are/were merged to mainline at the time. We have/had the following setup:

### NDSL

Follows branch [`nasa/milestone2`](https://github.com/NOAA-GFDL/NDSL/tree/nasa/milestone2) (see [PR #189](https://github.com/NOAA-GFDL/NDSL/pull/189)). This branch includes

- a hard-coded DaCe version with the new schedule tree bridge and
- a hardcoded GT4Py version with the following experimental features (in the `dace:*` backends only)
    - Hybrid indexing, i.e. absolute indexes in K via `field.at(K=absolute_index)`
    - Access to the iteration variable through `K`, working title `THIS_K`
    - Access to the `round()` function in stencils

??? note "`int` / `float` literal precision, working title "mixed precision work""

    The "mixed precision work" made it into mainline GT4Py with [this PR](https://github.com/GridTools/gt4py/pull/2187). There was only one major change compared to previous versions: the names of type annotations and casts changed in the following way

    - `i32` -> `int32`
    - `i64` -> `int64`
    - `f32` -> `float32`
    - `f64` -> `float64`

    If you get issues/errors about `i32`, `i64`, `f32`, `f64` not being defined, update your code with the above mapping.

## TaskBoard

As of March 2nd:

![Taskboard](taskboard.drawio)
