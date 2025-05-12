# Current state of schedule tree feature

This is a quick overview of the current state of the schedule tree feature.

## Working branch

Work is being done in the branch [`romanc/stree-to-sdfg`](https://github.com/romanc/dace/tree/romanc/stree-to-sdfg) on [Roman's fork](https://github.com/romanc/dace). The branch branches off from `v1/maintenance` and includes Tal's work from the branch [`stree-to-sdfg`](https://github.com/spcl/dace/tree/stree-to-sdfg). For a quick overview of the changes, look at

<https://github.com/spcl/dace/compare/v1/maintenance...romanc:romanc/stree-to-sdfg>

## Schedule tree to SDFG

In big terms, schedule tree to SDFG conversion has the following steps:

1. Setup a new SDFG and initialize it's descriptor repository from the schedule tree.
2. Insert artificial state boundary nodes in the schedule tree:
    - Insert state boundary nodes before control flow nodes and state labels.
    - Insert memory dependency state boundaries (e.g. potential data races)
    - Insert a state boundary after inter-state assignment nodes[^1].
    - Insert state boundary before maps containing a nested SDFG[^2].
3. Visitor on the schedule tree, translating every node into the new SDFG, see class `StreeToSDFG`.
4. Memlet propagation through the newly crated SDFG.
5. Run `simplify()` on the newly created SDFG (optional).

## Hacks and shortcuts

- `StreeToSDFG` has many visitors raising a `NonImplementedError`. I've implemented these visitors on an as-needed basis.
- I've added additional state boundaries around nested SDFGs (needed for state changes, e.g. `IfScope`, inside `MapNodes`) to force correct execution order.
- I've added additional state boundaries after inter-state assigns to ensure the symbols are defined before they are accessed. As far as I understand, that shouldn't be necessary. However, I've had SDFGs (todo: which ones?) with unused assigns at the end of the main visitor.
- I've written tests for some things as a way of developing the main visitor. For simple schedule trees, I've already added checks on the resulting SDFG, but pretty fast I ended up validating by "looking at the resulting SDFG".

## Current issues

- [x] Running a roundtrip for `tmp_UpdateDzD.sdfgz` (smaller) and `tmp_D_SW.sdfgz` (bigger), I end up with a duplicate `dt`, which is found in the symbols as well as in the arrays (as scalar). Since we copy both when building the descriptor repository (in step 1), assuming the SDFG was de-duplicated, the resulting SDFG  fails validation after the roundtrip.
- [ ] Running a roundtrip for `tmp_D_SW.sdfgz`, node validation fails for `__g_self__column_namelist__d_con__'
- [ ] Missing implementation of `NView` for `tmp_Fillz.sdfgz` (small) and `tmp_Ray_Fast.sdfgz` (bigger).
- [ ] Performance issue with `_insert_memory_dependency_state_boundaries()`. Known sources are:
    1. `MemletDict` checks for subset coverage and `subset.covers(other_subset)` is slow. While a cache is in place, this remains the number one issue according to `py-spy`.
    2. `node.input_memlets()` is number two on the list of `py-spy`.

For working on the performance issue, the following script can be handy:

```py
import sys
import time

from dace import SDFG
import dace.sdfg.analysis.schedule_tree.sdfg_to_tree as s2t
import dace.sdfg.analysis.schedule_tree.tree_to_sdfg as t2s

if __name__ == '__main__':
    s = time.time()
    sdfg = SDFG.from_file(sys.argv[1])
    print(f"Loaded SDFG in {(time.time() - s):.3f} seconds.")
    s = time.time()
    stree = s2t.as_schedule_tree(sdfg, in_place=True)
    print(f"Created schedule tree in {(time.time() - s):.3f} seconds.")

    # after WAW, before label, etc.
    s = time.time()
    stree = t2s.insert_state_boundaries_to_tree(stree)
    print(f"Inserted state boundaries in {(time.time() - s):.3f} seconds.")
```

in combination with SDFGs from [this GitHub issue](https://github.com/GEOS-ESM/NDSL/issues/6#issuecomment-2743978233).

## State of translate tests

|              | Roundtrip SDFG validating | Translate test passing |
| ------------ | ------------------------- | ---------------------- |
| XPPM         | yes                       | yes                    |
| DelnFluxNoSG | yes                       | yes                    |
| DelnFlux     | yes                       | yes                    |
| FvTp2d       | yes                       | yes                    |
| FxAdv        | yes                       | yes                    |
| Fillz        | no (NView)                |  -                     |
| Ray_Fast     | no (NView)                |  -                     |
| D_SW         | no (invalid SDFG node)    |  -                     |
| UpdateDzD    | yes                       | yes                    |

SDFGs for roundtrip validation can be downloaded from [this GitHub issue](https://github.com/GEOS-ESM/NDSL/issues/6#issuecomment-2743978233).

[^1]: as far as I understand `_insert_memory_dependency_state_boundaries`, this shouldn't be necessary. Might be related to extra state boundaries for nested SDFGs.
[^2]: Nested SDFGs are added when multiple states are needed inside a map.
