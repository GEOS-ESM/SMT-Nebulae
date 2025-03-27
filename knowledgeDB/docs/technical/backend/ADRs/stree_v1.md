# Schedule tree - first version

In the context of [schedule trees](./stree.md), facing time pressure and spill-over from Milestone 1, we decided to write the back transformation from schedule trees to SDFGs against the `v1/maintenance` branch of DaCe to minify up-front cost and deliver CPU performance as part of Milestone 2. We considered updating to the mainline version of DaCe and accept follow-up cost to rewrite part of the transformation once DaCe v2 releases.

## Context

[Milestone 1](../../../project2426/milestone1.md) didn't exactly turn out as we hoped and we were left we a bunch of tasks spilling over into [Milestone 2](../../../project2426/milestone2.md). At the end of this milestone, we'd like to have comparable performance numbers on CPU runs.

We blame much of the slowness of the current CPU version on macro-level optimizations that were hard-coded into the FORTRAN codebase, e.g. pushing the k-loop all the way out to the border of `D_SW`. To solve these performance challenges, we rely on the [schedule tree representation](./stree.md) to do that work automatically as part of a transformation in DaCe-land. This requires building the transformation back from schedule tress to SDFGs. DaCe is moving fast with breaking changes on `main` compared to the released `v1.x` versions. We thus had to answer the question if we should update to mainline DaCe first or build a first version against `v1.x`.

## Decision

We chose to build a first version of the schedule tree to SDFG back-transformation against the `v1.x` version of DaCe.

## Consequences

- We'll be able to code against a familiar API (same as the [gt4py/dace bridge](../dace-bridge.md)) and thus hope to get results faster.
- We won't be able to merge into `v1.x`.

## Alternatives Considered

### Update to DaCe mainline first

- Good because mainline DaCe is accepting new features while `v1.x` is closed for new feature development.
- Bad because it incurs an up-front cost (we'd need to update the [gt4py/dace bridge](../dace-bridge.md)) and we are trying to minimize up-front cost to get results fast.
- Bad because we aren't trained to use the new control flow graphs (CFG).
- Bad because we heard that DaCe mainline isn't stable at the moment.

## References

- [Why we chose schedule tree in the first place](./stree.md)
