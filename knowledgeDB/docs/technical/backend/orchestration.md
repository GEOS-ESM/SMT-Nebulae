# Orchestration: One Code To Rule Them in The DaCeness Bind Them

"Orchestration" refers to the concept of parsing stencil code & pythonc code together into a single `dace.program`. This system allows for full-context optimization and is the basis of the most performant version of the NDSL delivered code.

## Orchestrating code: a partial guide to a sea of potholes

### The parser wants _simple_ things

The python parser of DaCe hates dynamicity. No allocations must be done in the runtime code. We supersede a lot of the python actions or guide them to be resolved but there's still a (ongoing) list of failure that could be triggered.

Original [documentation](https://spcldace.readthedocs.io/en/latest/frontend/daceprograms.html) provides some introduction with very simple examples.

### The List of Issues

#### Conditional code on input

You shall not use `boolean` variable to switch between code

```python

class Input_Conditional_Function_Call:
    def __init__(self, stencil_factory: StencilFactory):
        orchestrate(obj=self, config=stencil_factory.config.dace_config)
        self._stencil_A = stcil_fctry.from_dims_halo(
            func=stencil_A,
            compute_dims=[X_DIM, Y_DIM, Z_DIM],
        )
        self._stencil_B = stcil_fctry.from_dims_halo(
            func=stencil_B,
            compute_dims=[X_DIM, Y_DIM, Z_DIM],
        )
        self._tmp_field = np.zeros(domain)

    def _internal_computation_no_scalar(self, in_field, out_field):
        out_field[:] = in_field[:] + 2

    def _internal_computation_scalar(self, in_field, out_field, scalar_field):
        out_field[:] = in_field[:] + scalar_field[:]

    def __call__(
        self,
        in_field: FloatField,
        out_field: FloatField,
        cond_flag: bool = False,
    ):
        if cond_flag:
            self._internal_computation_no_scalar(in_field, out_field)
        else:
            self._internal_computation_scalar(in_field, out_field, self._tmp_field)

class Faulty_Code_No_Stencils:
    def __init__(self, stencil_factory: StencilFactory):
        orchestrate(obj=self, config=stencil_factory.config.dace_config)
        self._subclass_build_A = Input_Conditional_Function_Call(stencil_factory)
        self._subclass_build_B = Input_Conditional_Function_Call(stencil_factory)

    def __call__(self, in_field: FloatField, out_field: FloatField):
        self._subclass_build_A(in_field, out_field)
        self._subclass_build_B(in_field, out_field, cond_flag=True)

if __name__ == "__main__":
    domain = (3, 3, 4)

    stcil_fctry, ijk_qty_fctry = get_factories_single_tile_orchestrated(
        domain[0], domain[1], domain[2], 0, on_cpu=True
    )

    arr_I = ijk_qty_fctry._numpy.arange(
        domain[0] * domain[1] * domain[2], dtype=np.float64
    ).reshape(domain)
    arr_O = ijk_qty_fctry._numpy.zeros(domain)

    code = Faulty_Code_No_Stencils(stcil_fctry)
    code(arr_I, arr_O)
```

This also fails when you mix in `stencils`.
Issue: <https://github.com/NOAA-GFDL/NDSL/issues/146>
