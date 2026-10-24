# pypipe: GEOS experiment setup and launch

`pypipe` is a Python/Click command-line wrapper for preparing and launching GEOS GCM experiments, preparing EMIP ensembles, and (eventually) setting up SCM cases. It is a script-based workflow, not a separately installed `pypipe` command. The entry point is [`run_GEOS.py`](run_GEOS.py); its GCM, EMIP, and SCM pipelines are implemented in [`run_helpers/`](run_helpers/). The system orchestrates the setup and execution of GEOS, but does *not* load HPC modules or install GEOS. It expects a version of GEOS has already been installed, and relies on external templates (from the GEOS installation) and setup script (both from GEOS and from the SI team). Future versions of `pypipe` will take over more of the setup process directly, and a sister system (`pycompile`) will handle the installation process.

`pypipe` currently supports execution on Discover, PRISM, and "local" (non-HPC) machines; "local" can also be used for unsupported HPC machines.

> **Status:** GCM and EMIP have setup/launch implementations, but depend on external GEOS setup scripts, generated GEOS templates, machine-specific data, and the current shell environment. SCM is a work in progress and does not create or run an experiment. Review the operational caveats below before launching jobs.

## Quickstart

From the repository root, use the Python environment where Click is available:

```sh
python pypipe/run_GEOS.py --help
python pypipe/run_GEOS.py GCM --help
```

`pypipe` supports three modes: GCM, EMIP, or SCM; all names are case-insensitive. Run it from the directory you want to use as the base for relative paths. By default, `--geos_dir` and `--top_exp_dir` are interpreted relative to the current working directory, though an absolute path can be specified to change this behavior.

A GCM setup-only example (replace paths and settings for your installation):

```sh
python pypipe/run_GEOS.py gcm \
  --horz 180 --vert 72 --nx 20 --ny 20 \
  --duration 1 --duration_unit days \
  --geos_dir ../model/install-release/bin \
  --top_exp_dir ./experiments \
  --execute_on none --account YOUR_ACCOUNT
```

This creates and patches files in the experiment directory to your desired configuration, but will not execute the experiment; `none` means do not execute/submit the GCM run. Check the generated files before changing to `--execute_on compute` (submit a slurm job) or `local` (run directory in the current terminal). Note that rerunning the same command will wipe the directory, so any manual changes made between `pypipe` runs will be lost.

## How The System Works

For a GCM run, `pypipe` performs the following tasks:

1. Creates a named experiment directory by calling the external `create_expt.py` script. If `pypipe` is being run on a local machine, the system expects that you are launching via Tiny/HugeBC, will ask for a path to the scripts directory therein, and will also call `makeoneday.bash` to remove EXTDATA dependencies.
2. Copies restarts when applicable. As previously mentioned, executing on a non-HPC machine, or a non-Discover/non-PRISM HPC expects, Tiny/HugeBC, and delegates restart preparation to `makeoneday.bash`.
3. Patches generated files such as `CAP.rc`, `AGCM.rc`, and `gcm_run.j` using the selected duration, grid, physics, and DSL options.
4. Launches `gcm_run.j`, if desired.

An EMIP suite uses the same experiment setup and common configuration, applies additional edits to `gcm_emip.setup` and `gcm_run.j`, and runs the EMIP setup script. That script generates batch commands; `compute` submits them, while `none` prepares the batch files without submitting them. `local` execution is not supported in this mode, as an ensemble cannot be run on a single node.

SCM support is in process. More information for launching a SCM run will be included in future versions.

## pypipe Configuration Options

### Paths, Execution, and DSL

The following options are shared between GCM, EMIP, and SCM modes:

| Option | Default | Description |
| --- | --- | --- |
| `--geos_dir PATH` | `../model/install-release/bin` | GEOS install `bin` directory. Must exist. |
| `--top_exp_dir PATH` | `./experiments` | Parent directory for generated experiments. |
| `--execute_on {compute,local,none}` | `compute` | Submit with `sbatch`, run in the current terminal, or set up without launching. |
| `--pymodules MODULES` | none | Optional DSL modules: `gfdl1m`, `uw`, `gf2020`, `fv3`. Accepts comma-separated values or repeated flags. Use lowercase names. |
| `--backend STRING` | `orch:dace:cpu:KJI` | Backend string, used when DSL modules are enabled. Common forms include `orch:dace:cpu:KJI`, `orch:dace:gpu:KJI`, `st:dace:cpu:KJI`, and `st:dace:gpu:KJI`. |

Example for enabling two python modules:

```sh
--pymodules gfdl1m,uw --backend orch:dace:gpu:KJI
```

### Model physics and settings

These options are shared by GCM and EMIP modes, and are used to configure the experiment.

| Option | Default | Accepted values / meaning |
| --- | --- | --- |
| `--account TEXT` | unset | Account passed to the GEOS setup script; required for GCM `compute` runs. |
| `--microphysics SCHEME` | `GFDL1M` | `BACM1M`, `GFDL1M`, or `MGB22M`. |
| `--ocean MODEL` | `o2` | `o1`, `o2`, `o3`, `MOM5`, `MOM6`, or `MIT`. |
| `--aerosols {A,C}` | `C` | GOCART aerosol scheme. |
| `--oserver / --nooserver` | enabled | Enable or disable the IO server. |
| `--hydro / --nonhydro` | enabled | Enable or disable hydrostatic dynamics. |
| `--data_atmo / --no_data_atmo` | disabled | Use a data atmosphere. |
| `--land_bcs VERSION` | `v12` | `ICA`, `NL3`, `v12`, or `v14`. |
| `--land_surf {1,2}` | `1` | `1` = Catchment; `2` = CatchmentCN-CLM4.0. |
| `--heartbeat SECONDS` | unset | Optional heartbeat interval. |
| `--processor {mil,cas}` | `mil` | Milan or Cascade Lake target. The local setup path overrides this with `not applicable`. |

### Grid and decomposition

GCM and EMIP require all four grid arguments:

| Option | Description |
| --- | --- |
| `--horz RESOLUTION` | Horizontal resolution, for example `48`, `180`, `360`, or `720`. |
| `--vert LEVELS` | Vertical levels, for example `72`, `131`, `137`, or `181`. |
| `--nx RANKS` | MPI ranks in X. |
| `--ny RANKS` | MPI ranks in Y per cube face; the AGCM patcher writes `NY = ny × 6`. |

## GCM guide

GCM creates one experiment and optionally runs it.

```sh
python pypipe/run_GEOS.py gcm \
  --horz 180 --vert 72 --nx 20 --ny 20 \
  --duration 1 --duration_unit days \
  [shared options]
```

GCM

Provide exactly one of `--duration` or `--end_date`:

| Option | Default | Description |
| --- | --- | --- |
| `--duration INTEGER` | none | Number of --duration_unit units to run (integer > 0). Mutually exclusive with --end_date. |
| `--duration_unit {days,months,years}` | `days` | Unit for `--duration`. Only considered when `--duration` is supplied. |
| `--end_date YYYYMMDDHHMMSS` | none | Explicit end date. Must be a valid date/time in this format. Mutually exclusive with `--duration`. |
| `--job_time HH:MM:SS` | `01:00:00` | Wall time limit for each sbatch submission. Can be up to 12 hours. |
| `--job_segment YYYYMMDDHHMMSS` | none, GEOS default if omitted | Explicit `JOB_SGMT` length. Must be 14 characters. |
| `--num_segment INTEGER` | none, GEOS default if omitted  | Number of --job_segment periods to run per sbatch submission |
| `--custom_restart` | off | Skip automatic restart copying and stop after setup/patching so you can place custom restarts manually. Requires `--end_date`; it cannot be combined with `--duration`, as duration uses restart files to compute an end date. |

Example with an explicit end date:

```sh
python pypipe/run_GEOS.py gcm \
  --horz 180 --vert 72 --nx 20 --ny 20 \
  --end_date 20260120000000 \
  --execute_on none --account YOUR_ACCOUNT
```

The generated experiment name is based on mode, resolution, and decomposition, with a DSL suffix when applicable. **If that experiment directory already exists, setup removes it before recreating it.** Back up any files you need before recreating an existing experiment.

When `--custom_restart` is specified, setup exits before execution (even with `--execute_on compute/local`). Add the necessary restart files to the generated experiment directory and manually submit/run.

## EMIP guide

EMIP prepares an ensemble using the generated `gcm_emip.setup` configuration and scripts. Its additional options are:

| Option | Default | Description |
| --- | --- | --- |
| `--start_year {1985,1995,2005}` | required | Selects the 10-year set containing the requested starting year. |
| `--season {DJF,JJA}` | required | Starting season. |
| `--duration INTEGER` | `3` | Number of months for each member, used to adjust the generated run loop. |
| `--job_time HH:MM:SS` | `01:00:00` | Wall time limit for each sbatch submission. Can be up to 12 hours. |
| `--job_segment YYYYMMDDHHMMSS` | none, GEOS default if omitted | Explicit `JOB_SGMT` length. Must be 14 characters. |
| `--num_segment INTEGER` | none, GEOS default if omitted | Number of --job_segment periods to run per sbatch submission |

Example to prepare the ensemble without submitting jobs:

```sh
python pypipe/run_GEOS.py emip \
  --horz 180 --vert 72 --nx 20 --ny 20 \
  --start_year 2005 --season DJF --duration 3 \
  --execute_on none --account YOUR_ACCOUNT
```

EMIP does not support `--execute_on local`; it exits with an error. With `--execute_on none`, the wrapper still runs `gcm_emip.setup` to generate batch files, but does not submit the `sbatch` commands. Review those files before submitting them manually.

**Template sensitivity:** EMIP patching expects specific text in the generated templates (e.g. `while( $count < 4 )` in `gcm_emip.setup`). Changes to GEOS templates can make this step fail.

## SCM guide

SCM accepts `--case`, `--duration`, and `--duration_unit`, as well as the shared path, execution, and DSL options:

```sh
python pypipe/run_GEOS.py scm \
  --case CASE_NAME --duration 1 --duration_unit days \
  --execute_on none
```

**SCM is not implemented.** The current runner only checks that `--case` was supplied and prints a setup message. It does not create an experiment, use the duration, patch GEOS files, or execute a model. Do not use this command for production runs.

## Operational caveats

- **Check machine configuration before any run.** Machine auto-detection has not been implemented. Check [`run_helpers/config.py`](run_helpers/config.py) to ensure `MACHINE` is set corretly. Supported options are `DISCOVER` and `NONHPC`, with partial support for `PRISM`. 
- **Use `--execute_on none` to inspect setup output first.** It is not a dry-run: it still creates/patches the experiment and invokes setup scripts (and EMIP's setup script).
- **Experiment directories are destructive on name collision.** Setup deletes an existing directory with the generated experiment name before recreating it.
- **Validate generated files and job status yourself.** The wrapper does not verify that submitted jobs complete successfully. A successful setup or `sbatch` submission is not evidence that the model run completed.
- **Confirm external prerequisites.** The GEOS executable, `create_expt.py`, restart files, appropriate scheduler commands, environment modulefiles, and (if required) Tiny/HugeBC, must be configured before running `pypipe`. The system does not verify external requirements.

## Troubleshooting and implementation references

- Run `python pypipe/run_GEOS.py <gcm|emip|scm> --help` for the options accepted by each command.
- The CLI and option declarations are in [`run_GEOS.py`](run_GEOS.py).
- The GCM orchestration is in [`run_helpers/run_gcm.py`](run_helpers/run_gcm.py); setup and restart handling are in [`run_helpers/setup.py`](run_helpers/setup.py); patching is handled by [`run_helpers/patch.py`](run_helpers/patch.py); and execution is handled by [`run_helpers/execute.py`](run_helpers/execute.py).
- EMIP orchestration and template edits are in [`run_helpers/run_emip.py`](run_helpers/run_emip.py).
- SCM's current placeholder is in [`run_helpers/run_scm.py`](run_helpers/run_scm.py).
