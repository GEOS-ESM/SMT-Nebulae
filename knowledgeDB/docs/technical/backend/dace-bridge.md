# GT4Py / DaCe bridge

"The bridge" commonly refers to the part lowering GT4Py's OIR into DaCe SDFGs.

## Building the bridge - a two step process

1. Build coarse-grained SDFG with library nodes for every `VerticalLoop`
2. Expand each library node with a nested SDFG

### Building the coarse-grained SDFG

Building the coarse-grained SDFG happens in the `OirSDFGBuilder`[^1] and is cached as `unexpanded_sdfg` in the `SDFGManager`[^2] after "pre-expand transformations" (e.g. setting loop expansion order and tile sizes) are applied.

### Expanding the library nodes

Expanding a library node will result in what the `SDFGManager` knows as the `expanded_sdfg`. There's no caching at this level. All library nodes are - one by one - transformed by the `expansion()` call on `StencilComputationExpansion`[^3]. This forms one big SDFG on which "post expansion transformations" (eliminating trivial maps, controlling OpenMP parallelization) are applied.

Library node expansion is again a two step process:

1. Build DaCe IR from OIR
2. Build a nested SDFG from the DaCe-IR

#### Building DaCe-IR from OIR

The DaCe-IR is built in `DaCeIRBuilder`[^4]. DaCe-IR is a hybrid IR somewhere between keeping semantic information (e.g. `dcir.HorizontalRestriction`) used for potential optimizations while trying to be close to the SDFG (e.g. `dcir.Memlet` and `dcir.Tasklet`). This dual-use make the IR a bit cumbersome to work with at times. A task[^5] was logged to evaluate splitting the IR.

??? NOTE "First version and bridge refactors"
    The original bridge was written in a way that pushed all code of a `oir.HorizontalRegion` into one big `Tasklet`, hiding all control flow happening inside horizontal regions. Control flow was exposed with [this PR](https://github.com/GridTools/gt4py/pull/1894). In many places, you might see remnants of that past and sub-optimal design decisions that we'll need to address in the future.

A rundown of what we do while building the IR

1. The IR starts a the `oir.VerticalLoop` level, where the "unexpanded SDFG" left off.
2. "Expansions" are the current system to change loop order depending on HW (currently: hard-coded lists for CPU- and GPU-devices)
3. While visiting `oir.HorizontalRegion`s, we recursively create `oir.CodeBlock`s, to group statements together that belong together. Initially, the body the `oir.HorizontalRegion` is put in a `CodeBlock`. As we process the `oir` statements in that `CodeBlock` we add nested `oir.CodeBlocks` to group the bodies of `oir.MaskStmt`s and `oir.While` loops. This allows us to keep track of `targets`, the set of variables written in the current `Tasklet`. That will be important for read-after write situation.
4. While loops and if statements inside horizontal regions are translated to `dcir.While` and `dcir.MaskStmt` which will generate control flow in tasklet code. A [task](https://github.com/GridTools/gt4py/issues/1900) was logged to change this in the future. For now we keep it as-is because this would need changes to the `HorizontalMaskRemover`, which operates on the DaCe-IR mid-flight while building (see `remove_horizontal_region()` inside `_process_map_item()` in the `DaCeIRBuilder`).
5. Each `oir.CodeBlock` is then translated into one of three objects
    1. a `dcir.ComputeState` which wraps assignment statements in a `dcir.Tasklet`
    2. a `dcir.Condition` contains a `dcir.Tasklet` to evaluate the condition and a `true_state` of type `ComputeState | Condition | WhileLoop`. Technically, the DaCe-IR also allows a `false_state`. However, somewhere in "higher" IRs the decision was made to transform all `else` branches to separate `if` statements with a negated condition.
    3. a `dcir.WhileLoop` contains a `dcir.Tasklet` to evaluate the condition and a `body` of type `ComputeState | Condition | WhileLoop`
6. When `dcir.Tasklet`s are built, we build `dcir.Memlets` for field access inside that Tasklet from the oir. Memlets for scalar access is only added when building the SDFG from the DaCe-IR (see below)

!!! warning "to be expanded"
    The block on Tasklets and Memlets need further clarification.

![CodeBlocks: general idea](./images/code-blocks.drawio)

#### Building SDFG from DaCe-IR

!!! warning "to be expanded"

The main work is done in `StencilComputationSDFGBuilder`[^6]. Tasklet code is generated in a separate visitor, `TaskletCodegen`[^7].

## Orchestration

!!! warning "to be expanded"

NDSL supercharges DaCe-backends by not only "daceifying" gt4py stencils but also the code in between.

## Future work

Future work includes leveraging DaCe's schedule tree to adapt the loop order and merge loops along the same axis (possibly with over-computation).

We'd also like to look into HW-dependant scheduling and JIT tiling.

## Expose code flow to DaCe

The current first version of the bridge keeps much of the stencil code hidden from DaCe's analytic capabilities. For every vertical loop, one Tasklet is generated, containing all the code inside that loop. We are in the process of exposing control flow (`if` statements and `while` loops) to DaCe, see issue: <https://github.com/GEOS-ESM/NDSL/issues/53>.

[^1]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/oir_to_dace.py>
[^2]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/backend/dace_backend.py>
[^3]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/expansion/expansion.py>
[^4]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/expansion/daceir_builder.py>
[^5]: <https://github.com/GridTools/gt4py/issues/1898>
[^6]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/expansion/sdfg_builder.py>
[^7]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/expansion/tasklet_codegen.py>
