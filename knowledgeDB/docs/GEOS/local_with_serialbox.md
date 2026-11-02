# GEOS: Local build with serialbox

This guide about running GEOS with serialbox on your machine. If you "just" want to run GEOS locally (i.e. without serialbox), have a look at [HowTo: GEOS local build and usage](./local_build_usage.md). In any case, we will heavily lean on that HowTo anyway.

Note in case you already have a [GEOS local install](./local_build_usage.md). It is recommended to have a separate GEOS installation for serialization with serialbox. This is mainly because it gets very cluttered with the extra `.SER` serialization files and locally modified `.F90` files (see below). People thus tend to have a separate GEOS (build in debug, i.e. no optimizations) and with the extra serialization statements.

## Prepare your environment

This guide uses [spack](https://spack.io) to create an environment in which we will compile and run both serialbox and GEOS.

- build a spack environment as [outlined here](./local_build_usage.md#prepare-your-environment)
- use [the "serialbox spack.yaml"](./geos_local/spack_serialbox.yaml)
- or just add `boost` to your "normal geos" spack environment

## Compile serialbox

With the above `spack` environment, you should have everything to compile serialbox.

- activate the spack environment: `spack env activate -p geos-serialbox`
- pull serialbox from Florian's fork, branch [feature/dataijkbuff](https://github.com/FlorianDeconinck/serialbox/tree/feature/data_ijkbuff)
- build serialbox [see docs](https://gridtools.github.io/serialbox/Building.html)
    - turn on Fortran: `-DSERIALBOX_ENABLE_FORTRAN=ON`
    - turn off examples: `-DSERIALBOX_EXAMPLES=OFF`

```bash
cd serialbox
mkdir build install
cd build
cmake -DCMAKE_INSTALL_PREFIX=../install -DSERIALBOX_ENABLE_FORTRAN=ON -DSERIALBOX_EXAMPLES=OFF ..
make install -j 10
```

-> serialbox (the .so) is now in `install/lib`

## Compile GEOS with serialbox

With the `spack` environment and serialbox, you now have everything to compile GEOS with serialbox.

- Compile GEOS as [outlined here](./local_build_usage.md#compile-geos)
- after `mepo clone`, switch to development branches used for serialization (e.g. with `*.SER` files under version control)
- then, run `pp_ser` to generate annotated `*.F90` files from `*.SER` files
    - as explained in [the validation guide](./validation_basics.md#generate-data-using-serialbox)
    - `python /PATH_TO_SERIALBOX/src/serialbox-python/pp_ser/pp_ser.py ./microphysics.F90.ser >| ./microphysics.F90`
- and take [this cmake_serialbox.sh](./geos_local/cmake_serialbox.sh)
    - compared to the ["standard cmake"](./geos_local/cmake.sh), we add `-DBUILD_SERIALBOX_SER=ON` and set `SERIALBOX_ROOT`
    - make sure to configure `/path/to/your/serialbox/install` to where you installed serialbox
    - use a debug build (i.e. no optimizations) for stable results
- run `make.sh` as [normal](./local_build_usage.md#compile-geos): `./make.sh debug .`

## Create & run an experiment

- Setup an experiment as outlined in [GEOS HowTo](./local_build_usage.md#setup-an-experiment)
- Make sure to only [run one timestep](./local_build_usage.md#running-one-timestep-instead-of-one-day)
- Run your experiment as outlined in [GEOS HowTo](./local_build_usage.md#running-your-geos-experiment)
- Check / Copy out the serialized output
    - Assuming `!$ser init directory='./serialized_data/' prefix='Generator' mpi_rank=mpi_rank unique_id=.true.`
    - you should see `scratch/serialized_data/` inside the experiment
    - these are the raw serialbox binary dumps (pretty much not useable in this form)
- Convert the raw serialbox data to netCDF format with `ndsl-serialbox_to_netcdf` (part of NDSL)
    - build NDSL with the `serialbox` extra
    - call `ndsl-serialbox_to_netcdf [flags] path/to/experiment/scratch/serialized_data [output_dir]`
    - assuming a c24 run with `NX=1` and `NY=6`, pass the following flags `--npx 25 --npy 25 --layout 1 1 --grid-type 0`
    - the output directory `[output_dir]` doesn't need to exist yet
