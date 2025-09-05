#!bin/bash

# Source the share basics
source ./basics.sh

echo " === Make environment with NDSL === "

# Git clone `ndsl`, with the minimuum amount of history
cd $DSLSW_INSTALL_DIR
git clone --recurse-submodules https://github.com/NOAA-GFDL/NDSL.git NDSL

pip install -e $DSLSW_INSTALL_DIR/NDSL
pip install -e $DSLSW_INSTALL_DIR/NDSL/external/dace
pip install -e $DSLSW_INSTALL_DIR/NDSL/external/gt4py
