# GT4Py / DaCe bridge

"The bridge" commonly refers to the part lowering GT4Py's OIR into DaCe SDFGs.

## Expose code flow to DaCe

The current first version of the bridge keeps much of the stencil code hidden from DaCe's analytic capabilities. For every vertical loop, one Tasklet is generated, containing all the code inside that loop. We are in the process of exposing control flow (`if` statements and `while` loops) to DaCe, see issue: <https://github.com/GEOS-ESM/NDSL/issues/53>.

![General idea](./images/code-blocks.drawio.svg)