#!/bin/sh

if [ -f "./.local.env" ]; then
    echo "Sourcing local environment in './.local.env'"
    source ./.local.env
fi

export NDSL_LOGLEVEL=DEBUG
export OMP_NUM_THREADS=1
export NDSL_LITERAL_PRECISION=64

python benchmarker_DSW.py
