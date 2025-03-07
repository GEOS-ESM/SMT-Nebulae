# Translate test

⚠️ This is a copy-paste of the older `pyFV3` documentation. It is out-of-date but concepts remain the same ⚠️

## Writing tests

Generation of regression data occurs in the fv3gfs-fortran repo (<https://github.com/VulcanClimateModeling/fv3gfs-fortran>) with serialization statements and a build procedure defined in `tests/serialized_test_data_generation`. The version of data this repo currently tests against is defined in `FORTRAN_SERIALIZED_DATA_VERSION` in this repo's `docker/Makefile.image_names`. Fields serialized are defined in Fortran code with serialization comment statements such as:

```fortran
    !$ser savepoint C_SW-In
    !$ser data delpcd=delpc delpd=delp ptcd=ptc
```

where the name being assigned is the name the fv3core uses to identify the variable in the test code. When this name is not equal to the name of the variable, this was usually done to avoid conflicts with other parts of the code where the same name is used to reference a differently sized field.

The majority of the logic for translating from data serialized from Fortran to something that can be used by Python, and the comparison of the results, is encompassed by the main Translate class in the tests/savepoint/translate/translate.py file. Any units not involving a halo update can be run using this framework, while those that need to be run in parallel can look to the ParallelTranslate class as the parent class in tests/savepoint/translate/parallel_translate.py. These parent classes provide generally useful operations for translating serialized data between Fortran and Python specifications, and for applying regression tests.

A new unit test can be defined as a new child class of one of these, with a naming convention of `Translate<Savepoint Name>` where `Savepoint Name` is the name used in the serialization statements in the Fortran code, without the `-In` and `-Out` part of the name. A translate class can usually be minimally specify the input and output fields. Then, in cases where the parent compute function is insufficient to handle the complexity of either the data translation or the compute function, the appropriate methods can be overridden.

For Translate objects

- The init function establishes the assumed translation setup for the class, which can be dynamically overridden as needed.
- the parent compute function does:
  - Makes gt4py storages of the max shape (grid.npx+1, grid.npy+1, grid.npz+1) aligning the data based on the start indices specified. (gt4py requires data fields have the same shape, so in this model we have buffer points so all calculations can be done easily without worrying about shape matching).
  - runs the compute function (defined in self.compute_func) on the input data storages
  - slices the computed Python fields to be compared to fortran regression data
- The unit test then uses a modified relative error metric to determine whether the unit passes
- The init method for a Translate class:
  - The input (self.in_vars["data_vars"]) and output(self.out_vars) variables are specified in dictionaries, where the keys are the name of the variable used in the model and the values are dictionaries specifying metadata for translation of serialized data to gt4py storages. The metadata that can be specified to override defaults are:
  - Indices to line up data arrays into gt4py storages (which all get created as the max possible size needed by all operations, for simplicity): "istart", "iend", "jstart", "jend", "kstart", "kend". These should be set using the 'grid' object available to the Translate object, using equivalent index names as in the declaration of variables in the Fortran code, e.g. real:: cx(bd%is:bd%ie+1,bd%jsd:bd%jed ) means we should assign. Example:

```python
      self.in_vars["data_vars"]["cx"] = {"istart": self.is\_, "iend": self.ie + 1,
                                         "jstart": self.jsd, "jend": self.jed,}
```

- There is only a limited set of Fortran shapes declared, so abstractions defined in the grid can also be used,
    e.g.: `self.out_vars["cx"] = self.grid.x3d_compute_domain_y_dict()`. Note that the variables, e.g. `grid.is\_` and `grid.ie` specify the 'compute' domain in the x direction of the current tile, equivalent to `bd%is` and `bd%ie` in the Fortran model EXCEPT that the Python variables are local to the current MPI rank (a subset of the tile face), while the Fortran values are global to the tile face. This is because these indices are used to slice into fields, which in Python is 0-based, and in Fortran is based on however the variables are declared. But, for the purposes of aligning data for computations and comparisons, we can match them in this framework. Shapes need to be defined in a dictionary per variable including `"istart"`, `"iend"`, `"jstart"`, `"jend"`, `"kstart"`, `"kend"` that represent the shape of that variable as defined in the Fortran code. The default shape assumed if a variable is specified with an empty dictionary is `isd:ied, jsd:jed, 0:npz - 1` inclusive, and variables that aren't that shape in the Fortran code need to have the 'start' indices specified for the in_vars dictionary , and 'start' and 'end' for the out_vars.
  - `"serialname"` can be used to specify a name used in the Fortran code declaration if we'd like the model to use a different name
  - `"kaxis"`: which dimension is the vertical direction. For most variables this is '2' and does not need to be specified. For Fortran variables that assign the vertical dimension to a different axis, this can be set to ensure we end up with 3d storages that have the vertical dimension where it is expected by GT4py.
  - `"dummy_axes"`: If set this will set of the storage to have singleton dimensions in the axes defined. This is to enable testing stencils where the full 3d data has not been collected and we want to run stencil tests on the data for a particular slice.
  - `"names_4d"`: If a 4d variable is being serialized, this can be set to specify the names of each 3d field. By default this is the list of tracers.
  - input variables that are scalars should be added to `self.in_vars["parameters"]`
  - `self.compute_func` is the name of the model function that should be run by the compute method in the translate class
  - `self.max_error` overrides the parent classes relative error threshold. This should only be changed when the reasons for non-bit reproducibility are understood.
  - `self.max_shape` sets the size of the gt4py storage created for testing
  - `self.ignore_near_zero_errors[<varname>] = True`: This is an option to let some fields pass with higher relative error if the absolute error is very small
  - `self.skip_test`: This is an option to jump over the test case, to be used in the override file for temporary deactivation of tests.

For `ParallelTranslate` objects:

- Inputs and outputs are defined at the class level, and these include metadata such as the "name" (e.g. understandable name for the symbol), dimensions, units and n_halo(numb er of halo lines)
- Both `compute_sequential` and `compute_parallel` methods may be defined, where a mock communicator is used in the `compute_sequential` case
- The parent assumes a state object for tracking fields and methods exist for translating from inputs to a state object and extracting the output variables from the state. It is assumed that Quantity objects are needed in the model method in order to do halo updates.
- `ParallelTranslate2Py` is a slight variation of this used for many of the parallel units that do not yet utilize a state object and relies on the specification of the same index metadata of the Translate classes
- `ParallelTranslateBaseSlicing` makes use of the state but relies on the Translate object of self._base, a Translate class object, to align the data before making quantities, computing and comparing.

## Debugging Tests

Pytest can be configured to give you a pdb session when a test fails. To route this properly through docker, you can run:

```bash
TEST_ARGS="-v -s --pdb" RUN_FLAGS="--rm -it" make tests
```
