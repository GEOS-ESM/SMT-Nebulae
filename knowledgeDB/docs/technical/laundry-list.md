# 👕 Laundry list

This document is a loose list of topics, bringing together planned and known issues from multiple repositories into what we hope is a better overview.

## ⏱️ Performance related topics

### Planned optimizations 🚀

There are a bunch of optimizations that we have planned with the [schedule tree bridge](./backend/schedule-tree.md) and a bunch of optimization that we need to build back with the new bridge:

- Different loops per target hardware: like [previously](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/backend/dace_backend.py#L75-L120), but less confusing
- Tiling: like [previously](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/backend/dace_backend.py#L123-L132), but hardware dependent. More details in [this file](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/gtc/dace/expansion_specification.py#L237-L240).
- CPU: temps are allocated & de-allocated on the fly
- Axis-split merge
- Over-computation merge
- Local caching
- Inline thread-local transients: like [previously](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/gtc/dace/transformations.py#L36).
- Optimize OpenMP pragmas: Check which of the [previous optimizations](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/backend/dace_backend.py#L162-L182) still make sense.
- We ran a [special version](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/gtc/dace/transformations.py#L15-L33) of `TrivialMapElimination` with more condition to when it applies.
- Special cases for stencils without effect? They were treated separately in [the previous bridge](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/backend/dace_backend.py#L148-L152).
- In the previous bridge, we'd [merge a horizontal region with the loop bounds](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/gtc/dace/expansion/daceir_builder.py#L1042-L1053) in case the horizontal region was the only thing inside that loop.
- In the previous bridge, we'd [split horizontal execution regions](https://github.com/GridTools/gt4py/blob/a2687f9126d1d27e7caaebf629f9e41035766bb5/src/gt4py/cartesian/gtc/dace/expansion/expansion.py#L149). This was also used for [orchestration in NDSL](https://github.com/NOAA-GFDL/NDSL/blob/2986b450386b5006d847f246ff6e8b23abdc9190/ndsl/dsl/dace/sdfg_opt_passes.py). To be re-evaluated.
- When orchestrating a lot of the fields that are held by the classes (the `self.tmp_field`) are transient to the local object (could be multiple stencils!) but those are flagged as global memory anyway. Re-scoping them to proper transients could lead to better memory & scalarization. At the `stree` level we don't scope the arrays to any space, we just flag them and the STREE-to-SDFG bridge deals with localizing them. Could we just write a pass scoping the containers post parsing and let the bridge do it?
- For stencils only we are missing a `simplify` (and potentially a `validate`?) right before [going to code generation](https://github.com/romanc/gt4py/blob/06cd753135d1a6caaabe0aca37cf735fb1d96c52/src/gt4py/cartesian/backend/dace_backend.py#L407)

### Allocation lifetime of temporaries 🗑️

IN the OIR -> Schedule Tree bridge, we allocate temporary fields with `AllocationLifetime.Persistent`. This has been done before (in the initial GT4Py-DaCe bridge). This isn't a good default and we tried to change it. Ideally we'd like to keep the scope of temporary fields as small as possible. `AllocationLifetime.Global` seems like a good default (since `AllocationLifetime.Scope`is too small for temporaries that are populated in one `with computation(..)` block and re-used subsequent ones).

We tried allocating temporary field with `AllocationLifetime.Global` and hit two issues

1. Dead dataflow elimination (DDE) crashed hard when we access (non-scalarized) temporaries with data dimension inside Tasklets ([DaCe issue](https://github.com/spcl/dace/issues/2086)). We put a temporary workaround in place, such that DDE doesn't try to remove such calls.
2. With the above fix in place, Florian ran into (massive) memory leaks with tracers when running the dycore. Basically, the generated SDFG validates, but code generation writes `new` without corresponding `delete[]`. It looks like the workaround from above, generates "Zombie 3D fields" (e.g. `br` which is allocated, never read and never deleted) in `FvTp2d` under certain conditions. As per Florian, not easy to repro and no smaller repro found thus far.

### Dynamics runtime 🐌

Chris reported a runtime of 25 sec per timestep for dynamics (`NX=2` and `NY=12`) with `gt:cpu_kfirst` where the Fortran baseline is only 5 sec / timestep. This is with the new amount of tracers, but still, we shouldn't be so far off.

### Load time of `.so` files ⌛

Running (`FV3_DACEMODE=Run`) the pre-compiled, orchestrated translate test for `D_SW` shows that the majority of time (5 sec) is spent in loading the `.so` file, compared to the actual run time (27 ms).

```none
2025-07-08 17:44:40|INFO|rank 0|ndsl.logging:[DaCeOrchestration.Run] Rank 0 reading/writing cache .gt_cache_FV3_A
[DaCe Config] Rank 0 loading SDFG [...]/PyFV3/.gt_cache_FV3_A/dacecache/pyFV3_stencils_d_sw_DGridShallowWaterLagrangianDynamics___call__
2025-07-08 17:44:40|DEBUG|rank 0|ndsl.logging:[DaCeOrchestration.Run] Load precompiled .sdfg (.so)...
2025-07-08 17:44:45|DEBUG|rank 0|ndsl.logging:[DaCeOrchestration.Run] Load precompiled .sdfg (.so)...4.979876279830933s.
2025-07-08 17:44:45|DEBUG|rank 0|ndsl.logging:[DaCeOrchestration.Run] Run...
2025-07-08 17:44:45|DEBUG|rank 0|ndsl.logging:[DaCeOrchestration.Run] Run...0.026755094528198242s.
```

#### Repro

Run the orchestrated translate test for `D_SW` from the PyFV3 repository. Build once with `FV3_DACEMODE=Build` and then run with `FV3_DACEMODE=Run`.

### Hardware detection 🛠️

We might want to centralize hardware detection. We currently

- detect HW for CPU/GPU through the presence of cupy,
- check for [GH200 nodes explicitly](https://github.com/NOAA-GFDL/NDSL/pull/183) to build a valid DaCe config in NDSL,
- and plan to use HW-dependent tiling (in NDSL/gt4py).

## </\> Frontend

- 🐞: Unable to do operation in absolute indexer in stencils.
    - This WORKS: `field.at(K=k22 - k_index)` with `k22` and `k_index` as `IntField32`
    - This FAILS: `field.at(K=kbcon - 1)` with `kbcon` as `IntField32`
- Missing integer divide operator (`//`) in GT4Py ([issue](https://github.com/NOAA-GFDL/NDSL/issues/179))
- Support for `pass` inside stencils

## 🚧 Code maintenance

### Grid layout 🌐

- Issues with 3x3 layouts (because of the tile "in the middle", the one that has no edge/corner) - is this still a problem?

### Layout transparency: missing tests 🌐

We are missing layout transparency tests.

Issue: <https://github.com/NOAA-GFDL/NDSL/issues/131>

### OIR mask statements 😷

There are two issues with OIR mask statements in GT4Py.

### `else` branches are not preserved 🔀

OIR translates

```py
if condition:
    pass
else:
    pass
```

into

```py
if condition:
    pass
if not condition:
    pass
```

while this is great for e.g. the numpy backend, it makes DaCe graphs overly complicated and generates ugly (and maybe slow?) C++ code.

The current plan is to work around this by not applying the above transformation if we are lowering to the DaCe backend. This way, we don't have to add support for `else`-branches in all other backends.

### Condition evaluation split from condition 🔀

OIR will translate

```py
if condition:
    pass
```

into

```py
condition_eval = condition
if condition_eval:
    pass
```

in case `condition` contains a `FieldAccess`. While this is great for e.g. the numpy backend, it makes DaCe graphs overly complicated and generates ugly (and maybe slow?) C++ code. This optimization should be a backend choice (e.g. be applied after OIR).

The current plan is to work around this by not applying the above transformation if we are lowering to the DaCe backend. This way, we don't have to touch all other backends.

### Schedule tree / horizontal regions: oob memlet warnings ⚠️

DaCe (most times?) emits warnings about potential out of bound memory access when horizontal regions are used. We think this is okay (e.g. we think there are no out-of-bounds memory accesses) and tracked it down to how we setup the data, define the iteration variable and how we set the Memlets.

Ideally, we'd like to refactor data setup, iteration scopes and memlet definition such that the warning disappears. Since validation is okay and this warning has been there before, we don't take immediate action.

Issues:

- <https://github.com/GridTools/gt4py/issues/727> (mentions "add issue (and fix) for negative origins in DaCe-orchestrated context")

### Python version and numpy support 🐍

NDSL python version support is currently hard-coded to 3.11. Moving on to 3.12 reportedly breaks things. To be investigated.

Bottom line, this will come in the future as 3.12 is the last to support numpy < 2.0. DaCe and GT4Py (next) moved to support numpy 2.0. Python version 3.12 (see discussion above) is the last python version to support 1.26.4.

### Stabilize schedule tree and move to DaCe 2.0 🌳

DaCe stopped feature development on the v1 branch (only critical fixes can go in) and is working actively on shaping the next major version. According to Tal, DaCe 2.0 will be much nicer and fix everything ;)

We built the schedule tree on top of the v1 branch [see here why](./backend/ADRs/stree_dace-version.md) and are thus currently in limbo between versions. We'll need to update once DaCe 2.0 gets stable or - at least - takes shape.

### Storing compressed SDFGs 🗜️

DaCe has the option to store SDFGs in compressed format. Since SDFGs are stored as (human readable) plain-text json, this can reduce file sizes drastically. To be evaluated if this has a negative impact on save & load times. The hypothesis is no, but it's always better to check and there are probably a bunch of hard-coded `.sdfg` extension that need to be adapted.

### Interval context: drop explicit `PARALLEL` 🟰

Currently, users need to specify whether their stencil can run in parallel or not. From data dependency analysis, we should be able to derive if it is safe to run a stencil in parallel or not. The would allow us to remove the `PARALLEL` option and auto-magically enable parallelism when possible.

Issue: <https://github.com/GridTools/gt4py/issues/1009>

### Auto-detect compile-time constant conditions 🪄

Currently, users can mark compile-time constant conditions with the `__INLINED` keyword. Since we are a DSL and since the idea is that users shouldn't need to care, we'd like to detect auto-magically when a condition is compile-time constant. We can then automatically remove compile-time constant conditions that evaluate to `False`.

Issue:<https://github.com/GridTools/gt4py/issues/1011>

### Stencil call arguments shouldn't be pruned 🧹

We might find arguments to be unused or we might make them unused by removing compile-time constant branches of conditions. Even in these scenarios, we shouldn't attempt to remove call arguments because this is hard to trace through all backends and shouldn't have any noticeable performance impact. A general compiler should be able to prune unused function arguments.

Issues:

- <https://github.com/GridTools/gt4py/issues/710>
- <https://github.com/GridTools/gt4py/issues/1010>
- <https://github.com/GridTools/gt4py/issues/2083>
- <https://github.com/NOAA-GFDL/NDSL/issues/70>

### NDSL constants system 📋

There are a bunch of issue floating around (in NDSL) about constants and that they should be refactored into a new/better system.

Issues:

- <https://github.com/NOAA-GFDL/NDSL/issues/6>
- <https://github.com/NOAA-GFDL/NDSL/issues/32>
- <https://github.com/NOAA-GFDL/NDSL/issues/64>

## 🏗️ Build system

### Multi-compiler native support ⚒️

- `clang` compilation fails on `dace:cpu` because of `-fopenmp` default flag
- `icc`/`ifx` support (never tried)

### Reflect orchestration in backend name 🎼

Currently, orchestration (or not) defined as a combination of backend name `dace:{cpu, gpu}` and the environment variable `FV3_DACEMODE`.

Issue: <https://github.com/NOAA-GFDL/NDSL/issues/46>

### Move dace cache into gt4py cache folder ♻️

Issue: <https://github.com/GridTools/gt4py/issues/1035>

### Leverage cmake in GT4Py toolchain 🛠️

In GT4py, we'd like to move away from setuptools and leverage cmake. This will unlock goodies like parallel compilation and more modern build backends (e.g. we might give ninja a try), which will hopefully speed up code generation.

Issue: <https://github.com/GridTools/gt4py/issues/83>

### Dace bridge caching ♻️

The OIR -> schedule tree -> SDFG bridge has support for caching the generated (unspecific) SDFG. It's used as "online" caching where the first SDFG is always generated (and then written to disk for re-use). We could expand this to "offline" caching where we'd fist check if an SDFG exists on disk and use this one if it does.

### Dependabot for GHA dependencies 🤖

Dependabot can be used to keep dependencies up to date. We could start by letting the bot check versions of GitHub Actions. In the `pace` repo, there's even a [dormant `dependabot.yml` config](https://github.com/NOAA-GFDL/pace/blob/develop/.github/dependabot.yml) for updating the submodules.

### ✅ Python packaging questions (NDSL, PyFV3, PySHiELD, pace) 🗄️

We are considering to move to `pyproject.toml`. Some questions about developer installs remain.

Issues:

- <https://github.com/NOAA-GFDL/NDSL/issues/138>
- <https://github.com/NOAA-GFDL/PyFV3/issues/52>
- <https://github.com/NOAA-GFDL/pace/issues/118>
- <https://github.com/NOAA-GFDL/PySHiELD/issues/32>

## 📁 Work organization

### Issue duplication / fragmentation 📄

For [milestone 1](../project2426/milestone1.md), we were using a GitHub project in the `GEOS-ESM` organization. This forced us to have a fork of NDSL under that organization, which lead to issue fragmentation / duplication on that fork. We should find the time to clean [these issues](https://github.com/GEOS-ESM/NDSL/issues).
