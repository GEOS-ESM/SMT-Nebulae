#!/bin/bash

source ./basics.sh

echo " === Installing DSLSW Software Stack v${DSLSW_VERSION} === "


MINICONDA_INSTALL_DIR = $HOME/miniconda3
ENV_NAME = DSLSW_v${DSLSW_VERSION}

# Install miniconda3
if [ ! -x "$MINICONDA_INSTALL_DIR/bin/conda" ]; then
    mkdir -p $MINICONDA_INSTALL_DIR
    curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh -o $MINICONDA_INSTALL_DIR/miniconda.sh
    bash $MINICONDA_INSTALL_DIR/miniconda.sh -b -u -p $MINICONDA_INSTALL_DIR
    rm $MINICONDA_INSTALL_DIR/miniconda.sh
fi

if ! conda env list | grep -qE "^${ENV_NAME}[[:space:]]"; then
    conda create -n "$ENV_NAME"
fi

conda activate $ENV_NAME
conda install conda-forge::python=3.11.9 gfortran_osx-arm64==14.2.0 openmpi==4.1.6 openmpi-mpicxx==4.1.6 cmake==3.30.2

# Build Serialbox
./build_serialbox.sh

# Build Baselibs
./build_baselibs.sh

# Build NDSL environment
./build_ndsl.sh