#!/bin/sh

export OMP_NUM_THREADS=1

VTUNE=/home/fgdeconi/intel/oneapi/vtune/latest/bin64/vtune

BENCH=UW_State
export NDSL_LOGLEVEL=DEBUG
export OMP_NUM_THREADS=1
export NDSL_LITERAL_PRECISION=32
export GT4PY_COMPILE_OPT_LEVEL=3

# $VTUNE -collect hotspots -r ./.vtune_results/$BENCH python benchmarker_$BENCH.py 

$VTUNE -collect hpc-performance -r ./.vtune_results/HPC__$BENCH python benchmarker_$BENCH.py 

# $VTUNE -collect memory-access -r ./.vtune_results/MemAccess__HALO2_$BENCH python benchmarker_$BENCH.py
