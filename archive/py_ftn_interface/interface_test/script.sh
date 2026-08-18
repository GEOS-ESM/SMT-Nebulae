#!/bin/bash

export PYTHONPATH=/home/ckung/Documents/Code/GEOS_Fortran_Python_Interface/SMT-FP-Interface-Code/src/tcn/py_ftn_interface/interface_test:/home/ckung/Documents/Code/GEOS_Fortran_Python_Interface/SMT-FP-Interface-Code/src:${PYTHONPATH}
export PACE_FLOAT_PRECISION=32
export GT4PY_LITERAL_PRECISION=32

rm *.o *.mod TEST
gfortran -c geos_pyfv3_interface_f.f90
mpicc -c geos_pyfv3_interface_c.c
gfortran -c test_file.f90
mpif90 -o TEST geos_pyfv3_interface_c.o geos_pyfv3_interface_f.o test_file.o -I./ -L./ -lgeos_pyfv3_interface
./TEST
