# Schedule tree

In the context of the gt4py/dace backend, facing under performing map- & state fusion, we decided to introduce schedule trees to achieve hardware dependent macro-level optimizations (e.g. loop merging and loop re-ordering). We considered writing custom fusion passes based on SDFG and accept the additional (maintenance & codegen) overhead of converting from SDFG to schedule trees and back (for codegen from SDFG).

## Context

While there are map & state fusion passes for SDFGs, they under-perform our expectations. Schedule Trees were thus drafted as an alternative representation to allow such high-level optimizations. Specifically, for NDSL, we are interested in two high-level optimizations

1. Flip the iteration order from I-J-K to K-I-J, pushing the K-loop as far out as possible to gain cache locality on CPU. Note that this transformation should be optional to allow optimal iteration order based on the target hardware (CPU or GPU).
2. Map merge on SDFGs currently fails for the most basic examples. Especially on GPUs, we'd like to merge as many maps as possible to cut down on the (currently excessive) amount of kernel launches.
3. If possible, look at force-merging K-loops/maps inserting if statements (as guards) as needed (over.computation) to further cut down on kernel launches on the GPU.

NDSL issue: <https://github.com/GEOS-ESM/NDSL/issues/6>

## Decision

We chose to write macro-level optimizations (e.g. loop re-reordering, (forced) map merges) in the schedule tree representation.

## Consequences

With the schedule tree representation, writing potent map fusion and loop re-ordering passes will be easier than in the SDFG representation.

We will need to write and maintain the back transformation from schedule tree to SDFG.

## Alternatives considered

### Improve the existing map fusion pass

Philip Müller has done this work (for gt4py-next) and an improved version is merged in the unreleased mainline version of DaCe.

We think we'll need a custom map fusion pass that let's us defined in which cases over-computation is desirable. A general map fusion pass will never allow this.

### Write custom map fusion based on SDFG syntax

Possible, but a lot more cumbersome than writing the same transformation based on the schedule tree syntax.

### Codegen from schedule tree

While it is theoretically possible to generate code directly from Schedule Trees, we would loose the possibility to run (existing) optimization passes after loop transformations and map fusion, which could unlock things like vectorization. In addition, current AI research is based on the SDFG representation.
