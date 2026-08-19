# Nebulae (WIP)

## Dev setup

```bash
cd workspace/
git clone git@github.com:spcl/dace.git --recurse-submodules
git clone git@github.com:GridTools/gt4py.git
git clone git@github.com:NOAA-GFDL/NDSL.git
# TODO (current, manual)
# go checkout FlorianDeconinck:devops/uv_pyproject
git clone git@github.com:NOAA-GFDL/pyFV3.git
cd ../
uv sync
source .venv/bin/activate
```

## To sort

- `dsl_patterns` should end up in the manual of NDSL
- `hardware_tests` should be completed and end up in some pipeline for GEOS and HPC