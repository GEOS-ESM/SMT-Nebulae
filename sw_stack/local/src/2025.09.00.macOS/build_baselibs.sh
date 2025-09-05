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
cd $DSLSW_BASE/baselibs-$DSLSW_BASELIBS_VER/esmf/src/Infrastructure/IO/PIO/ParallelIO
sed -i '' 's|set(CMAKE_C_ARCHIVE_FINISH "<CMAKE_RANLIB> -c <TARGET>")|set(CMAKE_C_ARCHIVE_FINISH "<CMAKE_RANLIB> <TARGET>")|' CMakeLists.txt

echo " === Baselibs === "

cd $DSLSW_BASE/baselibs-$DSLSW_BASELIBS_VER
PATH="$DSLSW_INSTALL_DIR/cmake-$DSLSW_CMAKE_MAJOR_VER.$DSLSW_CMAKE_MINOR_VER/bin:$PATH" \
make VERBOSE=1 -j ESMF_COMM=openmpi \
    ESMF_COMPILER=gfortranclang \
    BUILD=ESSENTIALS \
    ALLOW_ARGUMENT_MISMATCH=-fallow-argument-mismatch \
    prefix=$DSLSW_INSTALL_DIR/baselibs-$DSLSW_BASELIBS_VER/install/Darwin \
    install 2>&1 | tee run.out

# Verify installation
cd $DSLSW_BASE/baselibs-$DSLSW_BASELIBS_VER
make ESMF_COMM=openmpi \
    BUILD=ESSENTIALS \
    ALLOW_ARGUMENT_MISMATCH=-fallow-argument-mismatch \
    prefix=$DSLSW_INSTALL_DIR/baselibs-$DSLSW_BASELIBS_VER/install/Darwin \
    verify
