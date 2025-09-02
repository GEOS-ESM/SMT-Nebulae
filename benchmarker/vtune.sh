#!/bin/sh

export OMP_NUM_THREADS=1

VTUNE=/home/fgdeconi/intel/oneapi/vtune/latest/bin64/vtune

$VTUNE -collect hpc-performance -r DSW__gt_cpu_kfirst python benchmarker_DSW.py 

# $VTUNE -collect hotspots python benchmarker_DSW.py 

# hotspots

#-knob sampling-interval=1