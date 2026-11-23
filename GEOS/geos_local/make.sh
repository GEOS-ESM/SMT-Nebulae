#!/bin/bash

BUILD_TYPE_ARG="$1"
if [ -z "$BUILD_TYPE_ARG" ]; then
    echo "Usage: $0 debug|release [path_to_geosdir]"
    exit 1
fi

# Use the second argument if provided, otherwise default to "../model"
GEOSDIR="${2:-../model}"
cd $GEOSDIR/build-$BUILD_TYPE_ARG

RUNDIR=$PWD
echo $RUNDIR
make -j 11 install
