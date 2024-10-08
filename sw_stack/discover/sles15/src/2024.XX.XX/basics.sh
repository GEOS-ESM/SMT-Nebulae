#!/bin/bash

export DSLSW_VERSION="2024.XX.XX"
echo "DSL Software Stack v${DSLSW_VERSION}"

# Version
export DSLSW_GDRCOPY_VER=2.3
export DSLSW_OMPI_MAJOR_VER=4.1
export DSLSW_OMPI_VER=${DSLSW_OMPI_MAJOR_VER}.6
export DSLSW_UCX_VER=1.15.0
export DSLSW_CUDA_VER=12.2
export DSLSW_OSUMICRO_VER=7.3
export DSLSW_LAPACK_VER=3.11.0
export DSLSW_PY_VER=3.11.7
export DSLSW_BASELIBS_VER=7.17.1
export DSLSW_SERIALBOX_VER=2.6.2-unreleased
export DSLSW_SERIALBOX_SHA=88ac4e4dfc824953d068fe63c8e7b3dd9560a914
export DSLSW_GNU_VER=12.2.0
export DSLSW_NDSL_VER=2024.XX.XX
export DSLSW_BOOST_VER=1.76.0
export DSLSW_BOOST_VER_STR=1_76_0 

# Base directory & versioning
export DSLSW_BASE=$PWD/build
mkdir -p $DSLSW_BASE
export DSLSW_INSTALL_DIR=$PWD/install
mkdir -p $DSLSW_INSTALL_DIR

# Modules
module use -a /discover/nobackup/projects/geosongpu/sw_sles15/live/modulefiles/
module load SMTStack/${DSLSW_VERSION}
CUDA_DIR=/usr/local/other/nvidia/hpc_sdk/Linux_x86_64/23.9/cuda/

# Enforce proper compilers
export FC=gfortran
export CC=gcc
export CXX=g++
