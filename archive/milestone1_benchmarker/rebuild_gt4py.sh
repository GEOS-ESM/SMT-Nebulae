#!/bin/sh

g++ \
    -Wsign-compare \
    -fwrapv \
    -Wall \
    -fPIC \
    -I/home/fgdeconi/work/venv/ndsl_work/lib/python3.11/site-packages/pybind11/include \
    -I/home/fgdeconi/work/venv/ndsl_work/lib/python3.11/site-packages/pybind11/include \
    -I/home/fgdeconi/work/venv/ndsl_work/include \
    -I/home/fgdeconi/.pyenv/versions/3.11.9/include/python3.11 \
    -c \
    .gt_cache_000000/py311_1013/dacecpu/pyMoist/UW/compute_uwshcu/compute_uwshcu_invert_before/m_compute_uwshcu_invert_before__dacecpu_50a5b2a4ea_pyext_BUILD/bindings.cpp \
    -o \
    .gt_cache_000000/py311_1013/dacecpu/pyMoist/UW/compute_uwshcu/compute_uwshcu_invert_before/m_compute_uwshcu_invert_before__dacecpu_50a5b2a4ea_pyext_BUILD/.gt_cache_000000/py311_1013/dacecpu/pyMoist/UW/compute_uwshcu/compute_uwshcu_invert_before/m_compute_uwshcu_invert_before__dacecpu_50a5b2a4ea_pyext_BUILD/bindings.o \
    -std=c++17 \
    -ftemplate-depth=1024 \
    -fvisibility=hidden \
    -fPIC \
    -fsigned-char \
    -isystem/home/fgdeconi/work/venv/ndsl_work/lib/python3.11/site-packages/gridtools_cpp/data/include \
    -O3 \
    -DNDEBUG \
    -isystem/home/fgdeconi/work/git/ndsl/external/dace/dace/runtime/include \
    -fopenmp \
    -g

g++ \
    -Wsign-compare \
    -fwrapv \
    -Wall \
    -pthread \
    -shared \
    .gt_cache_000000/py311_1013/dacecpu/pyMoist/UW/compute_uwshcu/compute_uwshcu_invert_before/m_compute_uwshcu_invert_before__dacecpu_50a5b2a4ea_pyext_BUILD/.gt_cache_000000/py311_1013/dacecpu/pyMoist/UW/compute_uwshcu/compute_uwshcu_invert_before/m_compute_uwshcu_invert_before__dacecpu_50a5b2a4ea_pyext_BUILD/bindings.o \
    -L/home/fgdeconi/.pyenv/versions/3.11.9/lib \
    -o \
    .gt_cache_000000/py311_1013/dacecpu/pyMoist/UW/compute_uwshcu/compute_uwshcu_invert_before/m_compute_uwshcu_invert_before__dacecpu_50a5b2a4ea_pyext_BUILD/_GT_/pyMoist/UW/compute_uwshcu/compute_uwshcu_invert_before/m_compute_uwshcu_invert_before__dacecpu_50a5b2a4ea_pyext.cpython-311-x86_64-linux-gnu.so \
    -O3 \
    -DNDEBUG \
    -fopenmp 
