# Schedule tree - NDSL integration

In the context of [schedule trees](./stree.md), facing uncertainty of future usage, we decided to integrate schedule trees at the NDSL-level to facilitate writing GEOS-specific optimizations. We considered adding schedule trees at the GT4Py-level (as part of the [DaCe backend](../dace-bridge.md)) and accept that we have to revisit the question of where to integrate in the future.

## Context

Given first schedule tree passes from [earlier experiments](https://github.com/GEOS-ESM/NDSL/issues/6) and a rudimentary back transformation from schedule trees to SDFG, questions popped up at which level to integrate schedule tress in the pipeline. Should this be an NDSL feature? Should it be an option in [the dace bridge](../dace-bridge.md) of GT4Py? How will pushing the k-loop outwards relate to the GT4Py feature of setting an "expansion order"?

## Decision

We chose to integrate at the NDSL level to simplify writing GEOS-specific schedule tree passes and avoid having to write a pass registry in the DaCe backend of GT4Py.

## Consequences

- No schedule tree optimizations for non-orchestrated code.
- No decision on how schedule tree optimizations will fit in the bigger picture (in DaCe as well as in GT4Py)
- Reduced start-up overhead and a lot of flexibility for [Milestone 2](../../../project2426/milestone2.md).
- Given the results of [Milestone 2](../../../project2426/milestone2.md), we'll be able to re-evaluate the questions above. Positive results lead the way to productize this experimental feature.

## Alternatives considered

### Integration into GT4Py

Most likely, the feature will move down into the DaCe backend of GT4Py in the future.

- Good: Allows schedule tree passes for orchestrated and non-orchestrated code.
- Good: Brings the power of schedule tree optimizations to the whole GT4Py community.
- Currently bad because it means building a system to register custom passes and opt in/out of default stree optimizations (assuming there'll be some).
- Currently bad because it raises questions about overlapping features, e.g. expansion specification and tiling.

## References

- [Why we chose schedule tree in the first place](./stree.md)
