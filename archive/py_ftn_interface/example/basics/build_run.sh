#!/bin/bash

python bridge.py
gfortran bridge.f90 main.f90 -o test ./bridge.so
PYTHONPATH=. ./test