#!/bin/bash

# Source the share basics
source ./basics.sh

export FC=mpifort
export CC=mpicc
export CXX=mpic++

cd $DSLSW_BASE

rm -rf ./baselibs-$DSLSW_BASELIBS_VER
git clone --recurse-submodules -b v$DSLSW_BASELIBS_VER https://github.com/GEOS-ESM/ESMA-Baselibs.git ./baselibs-$DSLSW_BASELIBS_VER
cd ./baselibs-$DSLSW_BASELIBS_VER
# sed -i 's/download: gsl.download szlib.download cdo.download hdfeos.download hdfeos5.download SDPToolkit.download/download: gsl.download szlib.download cdo.download/g' GNUmakefile
# make download
# echo "=>Baselibs >> Removing HDF4 from the ESSENTIALS"
# sed -i 's/ESSENTIAL_DIRS = jpeg zlib szlib hdf4 hdf5/ESSENTIAL_DIRS = jpeg zlib szlib hdf5/g' GNUmakefile
# sed -i 's/\/zlib \/szlib \/jpeg \/hdf5 \/hdf \/netcdf,\\/\/ \/zlib \/szlib \/jpeg \/hdf5 \/netcdf,\\/g' GNUmakefile

echo " === Baselibs === "

# export LDFLAGS="$LDFLAGS -Wl,-ld_classic"

cd $DSLSW_BASE/baselibs-$DSLSW_BASELIBS_VER
make -j ESMF_COMM=openmpi \
    ESMF_COMPILER=gfortran \
    BUILD=ESSENTIALS \
    ALLOW_ARGUMENT_MISMATCH=-fallow-argument-mismatch \
    prefix=$DSLSW_INSTALL_DIR/baselibs-$DSLSW_BASELIBS_VER/install/Darwin \
    install
