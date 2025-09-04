#!/bin/sh
perf mem record -f \
    python benchmarker_FVTP2D.py

    # -e task-clock          \
    # -e context-switches    \
    # -e cpu-migrations      \
    # -e page-faults         \
    # -e cycles              \
    # -e instructions        \
    # -e branches            \
    # -e branch-misses       \
    # -e slots               \
    # -e topdown-retiring    \
    # -e topdown-bad-spec    \
    # -e topdown-fe-bound    \
    # -e topdown-be-bound    \
    # -e fp_arith_inst_retired.scalar_single \
    # -e fp_arith_inst_retired.scalar_double \
    # -e fp_arith_inst_retired.128b_packed_double \
    # -e fp_arith_inst_retired.128b_packed_single \
    # -e fp_arith_inst_retired.256b_packed_double \
    # -e fp_arith_inst_retired.256b_packed_single \
    # -e fp_arith_inst_retired.512b_packed_double \
    # -e fp_arith_inst_retired.512b_packed_single \

