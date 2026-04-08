from dataclasses import dataclass


@dataclass
class Data_py_t:
    x: float
    y: int
    b: bool
    # Magic number: see Fortran
    i_am_123456789: int
