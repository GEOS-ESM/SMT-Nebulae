# HowTo: GEOS local build and usage

This guide is for you if you are crazy enough to try and run GEOS locally on your machine. It starts with setting up the `spack` environment and ends with explaining how to run with NDSL integrated.

## Prepare your environment

This guide uses [`spack`](https://spack.io/) to create an environment in which we will compile and run GEOS. We will assume a a fresh install of GEOS.

- make sure you have [`rust`](https://rust-lang.org/) installed on your system
  - if not present, `spack`  will try to build it from source which is absolute overkill and takes forever
- make sure you have `(t)csh` installed on your system
  - you'll need `/bin/csh` to be there, otherwise `./gcm_run.j` and other csh files won't work
  - if you see `bash: ./gcm_run.j: cannot execute: required file not found`, that can be a sign of a missing `csh` shell
- get `spack`
  - check [their docs](https://spack.readthedocs.io/en/latest/) for guidance
  - register system compilers: `spack compiler find`
  - install other build tools as externals: `spack externals find`
  - make sure you have a version of `rust` found as external
- make a spack environment (based on [this `spack.yaml`](./geos_local/spack.yaml)
  - `spack env create geos`
  - "spack install from yaml" (there must be a way for this)
  - if you don't have a GPU, don't build `openmpi` with `cuda` support
  - if you have a GPU and cuda opens an xterm window and complains about `--tmpdir`
    - fall back to `spack` version 1.1.1
    - see https://github.com/spack/spack/issues/52521 for details
  - if `cmake` complains about system `curl` (include dir not found)
    - you might need to install `curl` or ssl development packages
    - ubuntu: https://github.com/rapidsai/node/issues/124
    - opensuse: https://forums.opensuse.org/t/packages-wont-install-on-opensuse-leap-15/175115

## Compile GEOS

With the above `spack` environment, you should have everything to compile and run GEOS.

- activate the `spack` environment: `spack env activate -p geos`
- setup [mepo](https://github.com/GEOS-ESM/mepo/) for blobless clones [1]
  - `mepo config set clone.partial blobless`
  - note: `mepo` is contained in the spack environment
  - see https://github.com/GEOS-ESM/GEOSgcm#setting-up-mepo-to-use-blobless-clones for details
- pull [geos](https://github.com/GEOS-ESM/GEOSgcm) (use a version tag, e.g. below we pull `v11.11.0`)
  - `git clone -b v11.11.0 git@github.com:GEOS-ESM/GEOSgcm.git geos`
- mepo clone things (inside `geos/`)
  - `cd geos`
  - `mepo clone --partial blobless`
- take [this cmake.sh](./geos_local/cmake.sh) and run it from inside `geos/`, e.g. `$ ./cmake.sh debug .` ("debug" | "release" depending on preference)
- take [this `make.sh`](./geos_local/make.sh) and run it from inside `geos/`, e.g. `$ ./make.sh debug .`

Notes

- build a `release` version if you run with more than 72 (vertical) levels

## Restart data

To be able to run GEOS, you'll need so called "restart data". You can get that from [here](https://portal.nccs.nasa.gov/datashare/astg/smt/geos-fp/restarts/).

The folder name of restarts, e.g. `TinyBCs-GitV12`, _cannot_ be changed. They are hard-coded / constructed from options in e.g. the `makeoneday.bash` script (see below).

To be able to run from multiple restarts, we suggest to use a folder structure similar to this:

```none
.
├── GitV10
│   ├── TBC.Feb26
│   │   └── TinyBCs-GitV10
│   └── TBC.Jan26
│       └── TinyBCs-GitV10
└── GitV12
    └── TBC.Sept26
        └── TinyBCs-GitV12
```

One could also use a symbolic link. The above folder structure has the benefit of forcing you to actively choose the restart folder.

## Setup an experiment

You will run GEOS from what is called and "experiment". The experiment is a folder containing the configuration and data needed to run GEOS. Results will also be saved to that folder.

For example, you can put a folder called `build-experiments/` inside your GEOS folder. That folder is the root of all experiments. Since it's prefixed by `build-` it will automatically be ignored by `git` (see the `.gitignore` file for reference).

A simple setup (with a debug build) could look like this

```none
.
├── geos
│   ├── install-debug
│   │   └── bin
│   └── build-experiments
│       ├── experiment_one
│       └── experiment_two
└── geos-restarts
    └── TBC.Sept26
        └── TinyBCs-GitV12
```

To setup experiments,

1. create the `geos/build-experiments/` folder (it will be empty in the beginning)
2. activate the `spack` environment
3. go into `geos/install-{debug,release}/bin`
4. call the script to create experiments (`create_expt.py`): `python ../../../geos-restarts/TBC.Sept26/TinyBCs-GitV12/scripts/create_expt.py --horz c24 --vert 181 --expdir /absolute/path/to/build-experiments/ experiment_one`. This will create a folder `experiment_one` in your `build-experiments` folder.
5. go into your experiment folder `geos/build-experiments/experiment_one`
6. run the `makeoneday.bash` script: `../../../geos-restarts/TBC.Sept26/TinyBCs-GitV12/scripts/makeoneday.bash NOEXT`

Note that in step 4, you need to use a absolute path for the `--expdir`. If not, nothing will complain until you actually call `./gcm_run.j` (see below).

## Running your GEOS experiment

Before running your GEOS experiment, have a look at the manual changes below. You might find those useful.

In case you want to run with NDSL, there's a whole section. Until we have better/deeper integration, you'll need to do those to run with NDSL enabled.

When you are ready, go into your experiment folder (e.g. `geos/build-experiments/experiment_one`) and launch `gcm_run.j`. Be sure that your `spack` (and optionally python) environment is activated.

### Manual changes to generated config files

Before running that experiment, you might want to do some of the following changes:

#### Reduce the number of ranks

By default, scripts setup an experiment that runs on 96 (MPI) ranks. To run on only 6 ranks, got to the `AGCM.rc` and change `NX` and `NY`, e.g.

```diff
-NX: 4
-NY: 24
+NX: 1
+NY: 6
```

`AGCM.rc` is in your experiment folder, e.g. it should be in `geos/build-experiments/experiment_one/AGCM.rc`.

#### Running non-hydrostatic

Apparently, the `--nonhydro` flag isn't respected in `create_expt.py`. You'll have to change `hydrostatic` to `.false.` in `fvcore_layout.rc`, e.g.

```diff
&fv_core_nml
- hydrostatic = .true.
+ hydrostatic = .false.
```

`fvcore_layout.rc` is in your experiment folder, e.g. it should be in `geos/build-experiments/experiment_one/fvcore_layout.rc`.

#### Save commandline output

While GEOS has logging, the entire commandline output is not saved by default. To do so, open `gcm_run.j` and change the following line accordingly

```diff
-   $RUN_CMD $TOTAL_PES $GEOSEXE $IOSERVER_OPTIONS $IOSERVER_EXTRA --logging_config 'logging.yaml'
+   $RUN_CMD $TOTAL_PES $GEOSEXE $IOSERVER_OPTIONS $IOSERVER_EXTRA --logging_config 'logging.yaml' |& tee ../output.log
```

`gcm_run.j` is in your experiment folder, e.g. it should be in `geos/build-experiments/experiment_one/gcm_run.j`. This will save `output.log` in your experiment folder (i.e. one folder above the `scratch/` directory).

### Running with NDSL

We don't have deep integration at the moment. This mean, you'll have to do a lot of work yourself to get started.

#### Provide a python virtual environment

While GOES has a basic Fortran-python bridge built-in, you'll have to provide a virtual environment with `pyFV3/` (and `NDSL`, `gt4py`, `dace`). You can put this wherever, the suggestion is to put it in the GEOS root dir.

From within the `spack` environment, activate that virtual environment.

```bash
~/geos/build-experiments/experiment_one $ source ~/geos/.venv/bin/activate
```

Then, continue reading on how to configure GEOS to run with NDSL.

#### Manual activation in the config files

To run with NDSL, you'll have to do the following manual changes to the configuration files. 

First, open `AGCM.rc` and add the following (anywhere in the file is fine).

```
# Enable / disable NDSL
USE_PYFV3: .True.
```

Then, drop the following in `gcm_run.j` to "activate" running with NDSL. There's a section "DSL configuration". Put it after the `PYTHONPATH` adjustment.

```bash
   # TEMPORARY SOLUTION - ONLY HERE UNTIL FV3 SOURCE IS PROPERLY COPIED INTO INSTALL
   setenv PYTHONPATH       ${GEOSDIR}/../src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp/python/interface:${GEOSDIR}/../src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp/python/@pyFV3:${PYTHONPATH}

   setenv PYTHONWARNINGS         "ignore"
   setenv FV3_DACEMODE           BuildAndRun
   setenv GEOS_DSL_BACKEND       orch:dace:cpu:KJI
   setenv GT_CACHE_ROOT          $EXPDIR/.DSL_CACHE
   setenv GT4PY_COMPILE_OPT_LEVEL 3
   setenv NDSL_CONSTANTS         GEOS
   setenv NDSL_LAYOUT            KJI
   setenv NDSL_LITERAL_PRECISION 32
   setenv GEOS_DSL_PYFV3_BACKEND orch:dace:cpu:KJI
   setenv NDSL_LOGLEVEL          Debug
   setenv PYFV3_TIME_CORE        True
   setenv NDSL_UNSAFE_MODE       True
```

Then, call `gcm_run.j` with `USE_DSL` enabled, e.g.

```bash
$ USE_DSL=1 ./gcm_run.j
```

### Pitfalls

Things you need to (implicitly) know such that GEOS is running.

#### `gcm_run.j` expects `/bin/csh` to be there

In case you are getting the following weird bash output

```bash
$ ./gcm_run.j
bash: ./gcm_run.j: cannot execute: required file not found
```

Make sure you have `/bin/csh` available on your system (e.g. install `tcsh`).

Note: Installing `tcsh` into the `spack` environment isn't enough because `gcm_run.j` (and other scripts) hardcode the hash-bang to `/bin/csh`. This also hold for other scripts that `gcm_run.j` calls, which makes it a lot simpler to just have `/bin/csh` available instead of updating all hashbangs in all scripts that might be (conditionally) called from `gcm_run.j`.

#### GEOS can't run under enforced SELINUX policies

In case you are getting an error along the lines of

```none
libMAPL.generic.so: cannot enable executable stack as shared object requires: Permission denied
```

Then, congratulations, your machine is enforcing SELINUX policies. This is a great idea in general and breaks GEOS execution. To work around it, the simplest is to (temporarily) turn it off. From a root shell, call

```shell
setenforce 0
```

to temporarily deactivate SELINUX' policy enforcement.

You can make that change permanent by changing `SELINUX=enforcing` to `SELINUX=disabled` in `/etc/selinux/config` followed by a reboot.

#### After re-compiling GEOS, my experiment doesn't pick up the changes

This is by design. Experiments were supposed to be self-contained. They aren't anymore. What remains is the fact that e.g. `GEOSgcm.x` and other executables are _copied_ from the install directory into your experiment folder.

You can change this behavior by adding the `--link` flag when calling `create_expt.py`.
