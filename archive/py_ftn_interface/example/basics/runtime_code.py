from math import prod
import cffi
from data_desc import Data_py_t
import inspect
import numpy as np
from typing import Optional

TYPEMAP = {
    "float": np.float32,
    "double": np.float64,
    "int": np.int32,
}


def fortran_to_numpy(
    FFI: cffi.FFI,
    fptr: "cffi.FFI.CData",
    dimensions: list[int],
) -> np.ndarray:
    """
    Input: Fortran data pointed to by fptr and of shape dim = (i, j, k)
    Output: C-ordered double precision NumPy data of shape (i, j, k)
    """
    ftype = FFI.getctype(FFI.typeof(fptr).item)
    if ftype not in TYPEMAP:
        raise ValueError(
            f"Fortran Python memory converter: cannot convert type {ftype}"
        )
    return np.frombuffer(
        FFI.buffer(fptr, prod(dimensions) * FFI.sizeof(ftype)),
        TYPEMAP[ftype],
    )


def check_function(data: Data_py_t, value: int, f_array: "cffi.FFI.CData"):
    # Check the magic number
    if data.i_am_123456789 != 123456789:
        raise ValueError("Magic number failure")

    # Print the structure
    print(f"Data comes as {data} of type {type(data)}")
    members = inspect.getmembers(Data_py_t)
    keys = list(
        list(filter(lambda x: x[0] == "__dataclass_fields__", members))[0][1].values()
    )
    for k in keys:
        print(f"{k.name} of value {getattr(data, k.name)}")

    # Print the int parameter
    print(f"Int parameter: {value}")

    # Modify the array
    #  Map to `numpy` buffer
    FFI = cffi.FFI()
    py_array = fortran_to_numpy(FFI, f_array, [2, 3, 4])
    py_array[:] = 3
