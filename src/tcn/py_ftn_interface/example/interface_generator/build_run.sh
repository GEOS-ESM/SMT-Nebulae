#!/bin/bash

python basic_interface.py
gfortran basic_interface_f.f90 basic_interface_c.c main.f90 -o test ./libbasic_interface.so
PYTHONPATH=. ./test