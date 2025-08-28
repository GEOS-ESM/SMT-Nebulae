#!/bin/sh

VTUNE=/home/fgdeconi/intel/oneapi/vtune/latest/bin64/vtune

$VTUNE -collect hpc-performance python benchmarker_FVTP2D.py 

# hotspots

#-knob sampling-interval=1