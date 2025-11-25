# Python <-> Fortan interface generator

## Install

This is part of the larger sandbox repository nicknamed `tcn` and the tool can be reached via installing this package.

```bash
# Source your venv or get into your conda environment
# From the top of the repository run:
pip install .
```

## Basic example of how the Fortran <--> C <--> Python works

In the `example` directory, you can run a test that showcase the legit case of memory transfer

```bash
cd ./example/basics
./build_and_run
```

This should outputs

```text
 Allocated field fortran side before python call:           2
Data comes as <cdata 'data_t *' 0x4040e0> of type <class '_cffi_backend._CDataBase'>
x of value 42.41999816894531
y of value 24
b of value True
i_am_123456789 of value 123456789
Int parameter: 4202824
 Allocated field fortran side AFTER python call:           3
```

## Interface generator

WARNING: the generator work on the hypothesis that the fortran<>python interface and the reference fortran share the argument signature.

Yaml schema:

```yaml
type: py_ftn_interface # mandatory
name: NAME_OF_INTERFACE
functions:
    FUNCTION_NAME_A:
        inputs:
            SCALAR_PARAMETER_NAME_A : int
            SCALAR_PARAMETER_NAME_B : float
        inouts:
            ARRAY_PARAMETER_NAME_A : array_int
            ARRAY_PARAMETER_NAME_B : array_float
```

An example lives is available

```bash
cd ./example/basics
tcn-fpy example_simple.yaml # This will generate the interface files
./build_and_run
```

This should outputs

```text
My code for basic_add_scalar_to_3D_quantity goes here.
My code for basic_add_2D_quantity_to_3D_quantity goes here.
```
