#!/bin/sh

export OMP_NUM_THREADS=1

VTUNE=/home/fgdeconi/intel/oneapi/vtune/latest/bin64/vtune

BENCH=MicrophysicsDriver
export NDSL_LITERAL_PRECISION=32

$VTUNE -collect hotspots -r ./.vtune_results/$BENCH python benchmarker_$BENCH.py 

# hpc-performance

# $VTUNE -collect hotspots python benchmarker_DSW.py 

# hotspots

#-knob sampling-interval=1