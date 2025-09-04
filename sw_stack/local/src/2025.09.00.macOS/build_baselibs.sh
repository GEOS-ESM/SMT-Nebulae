#!/bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

git clone --recurse-submodules -b v$DSLSW_BASELIBS_VER https://github.com/GEOS-ESM/ESMA-Baselibs.git ./baselibs-$DSLSW_BASELIBS_VER
cd ./baselibs-$DSLSW_BASELIBS_VER
make download
echo "=>Baselibs >> Removing HDF4 from the ESSENTIALS"
sed -i '' 's/ESSENTIAL_DIRS = jpeg zlib szlib hdf4 hdf5/ESSENTIAL_DIRS = jpeg zlib szlib hdf5/g' GNUmakefile
sed -i '' 's/\/zlib \/szlib \/jpeg \/hdf5 \/hdf \/netcdf,\\/\/ \/zlib \/szlib \/jpeg \/hdf5 \/netcdf,\\/g' GNUmakefile

echo " === Baselibs === "

# install cmake needed for baselibs
cd $DSLSW_BASE
wget https://cmake.org/files/v3.12/cmake-3.12.0.tar.gz
tar -xzf cmake-3.12.0.tar.gz
rm cmake-3.12.0.tar.gz

cd cmake-3.12.0
./bootstrap --prefix=$DSLSW_INSTALL_DIR/cmake-3.12
make -j install

cd $DSLSW_BASE/baselibs-$DSLSW_BASELIBS_VER
PATH="$DSLSW_INSTALL_DIR/cmake-3.12/bin:$PATH" \
make ESMF_COMM=openmpi \
    ESMF_COMPILER=gfortranclang \
    BUILD=ESSENTIALS \
    ALLOW_ARGUMENT_MISMATCH=-fallow-argument-mismatch \
    prefix=$DSLSW_INSTALL_DIR/baselibs-$DSLSW_BASELIBS_VER/install/Darwin \
    install

# Verify installation
cd $DSLSW_BASE/baselibs-$DSLSW_BASELIBS_VER
make ESMF_COMM=openmpi \
    BUILD=ESSENTIALS \
    ALLOW_ARGUMENT_MISMATCH=-fallow-argument-mismatch \
    prefix=$DSLSW_INSTALL_DIR/baselibs-$DSLSW_BASELIBS_VER/install/Darwin \
    verify
