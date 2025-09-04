#!/bin/bash

export DSLSW_VERSION="2025.09.00"
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
export DSLSW_BASELIBS_VER=7.27.0
export DSLSW_SERIALBOX_REMOTE_NAME="FlorianDeconinck"
export DSLSW_SERIALBOX_REMOTE_URL="https://github.com/FlorianDeconinck/serialbox.git"
export DSLSW_SERIALBOX_BRANCH_NAME="feature/data_ijkbuff"
export DSLSW_SERIALBOX_SHA="feature/data_ijkbuff"
export DSLSW_GNU_VER=12.2.0
export DSLSW_NDSL_VER=2024.XX.XX
export DSLSW_BOOST_VER=1.76.0
export DSLSW_BOOST_VER_STR=1_76_0 

# Base directory & versioning
export DSLSW_BASE=$PWD/build
mkdir -p $DSLSW_BASE
export DSLSW_INSTALL_DIR=${DSLSW_custom_install_path:-$PWD/install}
mkdir -p $DSLSW_INSTALL_DIR
