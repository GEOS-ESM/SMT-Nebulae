# GT4Py / DaCe bridge

"The bridge" commonly refers to the DaCe backends of GT4Py. The backends translate GT4Py stencils into SDFGs, which allows DaCe to do its magic on them. Since stencil-level optimization isn't enough for application performance, NDSL supercharges the DaCe backends by transforming all code to SDFGs. We call this orchestration.

## Building the bridge - a two step process

Roughly, the dace backends are built in two steps:

1. For each stencil, we build a "coarse-grained SDFG" with a library node for every `VerticalLoop`
2. We then "expand" each library node, replacing it with a nested SDFG

### Building the coarse-grained SDFG

Building the coarse-grained SDFG happens in the `OirSDFGBuilder`[^1] and is cached as `unexpanded_sdfg` in the `SDFGManager`[^2] after "pre-expand transformations" (e.g. setting loop expansion order and tile sizes) are applied.

??? note "Refactor opportunity: Transient read after write"
    `OirSDFGBuilder` follows a simple algorithm that connects an incoming Memlet for every read access and an outgoing Memlet for every write access to the library node. For transient memory that is only read after written (within that library node), this results in an unused incoming Memlet. DaCe will warn about such situation while building the SDFG, reporting a Memlet that reads undefined memory.

### Expanding the library nodes

Expanding a library node results in what the `SDFGManager` knows as the `expanded_sdfg`. There's no caching at this level. All library nodes are - one by one - transformed by the `expansion()` call on `StencilComputationExpansion`[^3]. This forms one big SDFG on which "post expansion transformations" (eliminating trivial maps, controlling OpenMP parallelization) are applied.

Library node expansion is again a two step process:

1. Build DaCe-IR from OIR
2. Build a nested SDFG from the DaCe-IR
    1. Codegen for code in Tasklets.

#### Building DaCe-IR from OIR

The DaCe-IR is built in `DaCeIRBuilder`[^4]. DaCe-IR is a hybrid IR somewhere between keeping semantic information (e.g. `dcir.HorizontalRestriction`) used for potential optimizations and - on the other hand - trying to be close to the SDFG (e.g. `dcir.Memlet` and `dcir.Tasklet`). This dual-use make the IR a bit cumbersome to work with at times. A task[^5] was logged to evaluate splitting the IR.

??? note "First version and bridge refactors"
    The original bridge was written in a way that pushed all code of a `oir.HorizontalRegion` into one big `Tasklet`, hiding all control flow happening inside horizontal regions. Control flow was exposed with [this PR](https://github.com/GridTools/gt4py/pull/1894). In many places, you might see remnants of that past and sub-optimal design decisions that we'll need to address in the future.

A rundown of what we do while building the IR

1. The IR starts a the `oir.VerticalLoop` level, where the "unexpanded SDFG" left off.
2. "Expansions" are the current system to change loop order depending on HW (currently: hard-coded lists for CPU- and GPU-devices)
3. While visiting `oir.HorizontalRegion`s, we recursively create `oir.CodeBlock`s, to group statements that belong together. Initially, the body the `oir.HorizontalRegion` is put in a `CodeBlock`. As we then process the `oir` statements in that `CodeBlock` and we recursively add nested `oir.CodeBlocks` to group the bodies of `oir.MaskStmt`s and `oir.While` loops. This allows us to keep track of `targets`, the set of variables written in the current `Tasklet`. `targets` are used when visiting `FieldAccess` or `ScalarAccess` to name the variables. For each Tasklet map incoming Memlets to `gtIN__{name}` and outgoing Memlets to `gtOUT__{name}`. We thus need to know if read from or write to a variable/field. Furthermore, when reading after writing to the same variable within a Tasklet, we need to read from the "out"-version of the variable that was previously written.
4. While loops and if statements inside horizontal regions are translated to `dcir.While` and `dcir.MaskStmt` which will generate control flow in tasklet code. A [task](https://github.com/GridTools/gt4py/issues/1900) was logged to change this in the future. For now we keep it as-is because this would need changes to the `HorizontalMaskRemover`, which operates on the DaCe-IR mid-flight while building (see `remove_horizontal_region()` inside `_process_map_item()` in the `DaCeIRBuilder`).
5. Each `oir.CodeBlock` is then translated into one of three objects
    1. `dcir.ComputeState` wraps assignment statements in a `dcir.Tasklet`
    2. `dcir.Condition` contains a `dcir.Tasklet` to evaluate the condition and a `true_state` of type `ComputeState | Condition | WhileLoop`. Technically, the DaCe-IR also allows a `false_state`. However, somewhere in "higher IRs" the decision was made to transform all `else` branches to separate `if` statements with a negated condition.
    3. `dcir.WhileLoop` contains a `dcir.Tasklet` to evaluate the condition and a `body` of type `ComputeState | Condition | WhileLoop`
6. When a `dcir.Tasklet`s is built, we construct `dcir.Memlets` for field access inside that Tasklet from the oir. Memlets for scalar access are only added when building the SDFG from the DaCe-IR (see below).
7. After a tasklet is built, `_fix_memlet_array_access()` runs a pass for Memlets with partial index subset, variable offset reads, or K-write offsets. This pass writes explicit indices into `explicit_indices`, which are then used during Tasklet codegen (see below). We should revisit this and clean up our approach to indexing (see note below).

??? note "Refactor opportunity: `if` / `else` statements"
    We should track down where `else` branches of `if` statements get "lost" and propagate them all the way down to DaCe-IR and when we build the SDFGs. While DaCe has a pass that detects subsequent `if` statements with negated conditions, it doesn't always apply. As a result, our generated code is over complicated. We don't expect this to impact performance to the point that it matters now, but it might in the future and - more importantly - it makes debugging and reasoning about generated code more complicated than it has to be.

??? note "Refactor opportunity: Indexing"
    `_fix_memlet_array_access()` was introduced as a [temporary fix](https://github.com/GridTools/gt4py/pull/1410) after DaCe stopped support for partial index subset. We should re-visit indexing as a whole and find a cleaner solution that doesn't create partial index subsets in the first place and supports new features like variable offset reads and K-offset writes.

![CodeBlocks: general idea](./images/code-blocks.drawio)

??? note "Refactor opportunity: `CodeBlock`s"
    `CodeBlock`s were added at the OIR-level such that the DaCe-IR visitor could recursively create and visit them at the same time. `oir.CodeBlock`s are not used in any other backend for now. This is fundamentally not the way to how build things nicely and a temporary duct tape solution. We should propagate `gtir.BlockStmt` throughout the `oir`-level and re-use that instead in the DaCe-IR. `if` / `else` statements should be kept together at the `oir`-level. `oir.MaskStmt` sounds like we were catering too much for the `numpy` backend in the past.

#### Building SDFG from DaCe-IR

The main work is done in `StencilComputationSDFGBuilder`[^6]. Tasklet code is generated in a separate visitor, `TaskletCodegen`[^7].

`StencilComputationSDFGBuilder` is your standard node visitor translating the DaCe-related concepts of DaCe-IR to actual SDFGs. Whenever this process is not straight forward, it's because we didn't prepare things well enough in previous steps. One notable pain point is how we access scalar variables. In the image above, note how `statements{0,1,8}` are in the same (blue) `CodeBlock`. In the SDFG representation, the picture looks more like this

![CodeBlock example SDFG](./images/sdfg.drawio)

Notice how `statements{0,1}` are in one Tasklet and `statement8` is in another Tasket. If any local temporaries are written as part of statements 0 or 1, they could be read in `statement8`. We thus don't have any local scalars anymore and expose all writes (to scalars) for possible future reads. A standard DaCe cleanup pass will get rid of any unused write access node. This only needs special care for local scalar accesses because array memory is managed at the (nested) SDFG level. In the first version of the bridge, scalars could be represented as local scalars of the one big Tasklet. This leave a refactor opportunity to adapt the DaCe-IR.

??? note "Refactor opportunity: Memlets for scalar accesses"
    In the first version of the bridges, scalar could be treated as local scalars of the one big Tasklet that existed. There was thus no need for scalar access to be represented in Memlets. When re-designing the DaCe-IR and/or when looking at Indexing, we should take a moment to asses what we could do better in terms of how we handle scalars. We should aim for knowing if a scalar is going to be read in a subsequent Tasklet when we build the SDFG.

??? note "Refactor opportunity: Memlets and `node_ctx`"
    The `StencilComputationSDFGBuilder` holds a "node context" to keep track of Memlets and where to connect them to/from. When re-designing the DaCe-IR, we should aim for getting that information into the last IR before building SDFGs such that we can just focus on building the SDFG at this point.

#### Code generation for Tasklets

Tasklet code is generated in `TaskletCodegen`, which is called from `StencilComputationSDFGBuilder` when visiting Tasklets. It translates DaCe-IR statements back into python code and - more importantly - handles Memlets going into and out of the Tasklet.

??? note "Refactor opportunity: Indexing (part two)"
    The indexing hacks done when building the DaCe-IR show here again because we now need to handle special cases, e.g for explicit vs. non-explicit indexing.

??? note "Refactor opportunity: Horizontal regions in Tasklets"
    Even after exposing control flow with [this PR](https://github.com/GridTools/gt4py/pull/1894), some Tasklets still contain code flow. This comes from two sources: ternary operators (we don't care too much about that for now) and horizontal regions. In the future, we should aim for getting all horizontal regions out of Tasklet code.

## Orchestration

NDSL supercharges DaCe-backends by not only "daceifying" GT4Py stencils but also the code in between. This results in one big SDFG that can be analyzed with the powers of DaCe.

## Future work

Future work includes leveraging DaCe's schedule tree to adapt the loop order and merge loops along the same axis (possibly with over-computation).

We'd also like to look into HW-dependant scheduling and JIT tiling.


[^1]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/oir_to_dace.py>
[^2]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/backend/dace_backend.py>
[^3]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/expansion/expansion.py>
[^4]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/expansion/daceir_builder.py>
[^5]: <https://github.com/GridTools/gt4py/issues/1898>
[^6]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/expansion/sdfg_builder.py>
[^7]: <https://github.com/GridTools/gt4py/blob/main/src/gt4py/cartesian/gtc/dace/expansion/tasklet_codegen.py>
