#!/bin/bash

# save source dir for later
RUN_DIR=$PWD

BUILD_TYPE_ARG="$1"

case "$BUILD_TYPE_ARG" in
    debug)
        CMAKE_BUILD_TYPE=Debug
        SUFFIX=debug
        ;;
    release)
        CMAKE_BUILD_TYPE=Release
        SUFFIX=release
        ;;
    *)
        echo "Usage: $0 debug|release [path_to_geosdir]"
        exit 1
        ;;
esac

# Use the second argument if provided, otherwise default to "../model"
GEOSDIR_PATH="${2:-../model}"
GEOSDIR=$(cd "$GEOSDIR_PATH" && pwd)
RUNDIR=$PWD

rm -rf $GEOSDIR/build-$SUFFIX
rm -rf $GEOSDIR/install-$SUFFIX
mkdir -p $GEOSDIR/build-$SUFFIX
cd $GEOSDIR/build-$SUFFIX

cmake $GEOSDIR \
    -DCMAKE_INSTALL_PREFIX="$GEOSDIR/install-$SUFFIX" \
    -DPython3_EXECUTABLE=$(which python3) \
    -DCMAKE_BUILD_TYPE=$CMAKE_BUILD_TYPE \
    -DCMAKE_C_COMPILER=mpicc \
    -DCMAKE_CXX_COMPILER=mpic++ \
    -DCMAKE_Fortran_COMPILER=mpif90 \
    -DUSE_F2PY=OFF \
    -DBUILD_PYTHONBRIDGE=ON \
    -DBUILD_PYFV3_INTERFACE=ON \
    -DBUILD_WITH_PFLOGGER=NO \
    2>&1 | tee $RUN_DIR/compile_geos.out
    