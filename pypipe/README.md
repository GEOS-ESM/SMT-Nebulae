# pypipe: GEOS experiment setup and launch

`pypipe` is a Python/Click command-line wrapper for preparing and launching GEOS GCM experiments, preparing EMIP ensembles, and (eventually) setting up SCM cases. The intended interface is the installed `pypipe_geos_exp` command (there is no command named `pypipe`). Running [`run_GEOS.py`](run_GEOS.py) directly from source is a valid fallback, but is not the intended way to use the package. The GCM, EMIP, and SCM pipelines are implemented in [`run_helpers/`](run_helpers/). The system orchestrates GEOS setup and execution, but does *not* load HPC modules or install GEOS. It requires Python 3.12 or newer and the project dependencies (Click, PyYAML, and schema), plus an existing GEOS installation and its external setup scripts/templates.

Machine profiles are selected explicitly; the wrapper does not detect the host. `NONHPC` and `DISCOVER` have setup paths with machine-specific prerequisites. `PRISM` is a recognized option but setup currently stops with `NotImplementedError`.

`pypipe` supports three modes: GCM, EMIP, or SCM; all names are case-insensitive. 

> **Status:** GCM and EMIP have setup/launch implementations, but depend on external GEOS setup scripts, generated GEOS templates, machine-specific data, and the current shell environment. SCM is a work in progress and does not create or run an experiment. Review the operational caveats below before launching jobs.

## Quickstart

From the repository root, install the package into the Python 3.12+ environment you intend to use. This installs the required Python dependencies and registers the `pypipe_geos_exp` command in that environment:

```sh
python -m pip install ./pypipe
pypipe_geos_exp --help
pypipe_geos_exp gcm --help
pypipe_geos_exp emip --help
pypipe_geos_exp scm --help
```

If the console command is unavailable, direct source invocation is a valid fallback from the repository root: use `python pypipe/run_GEOS.py ...` (or `python run_GEOS.py ...` from the `pypipe` directory).

**Current CLI limitation:** each mode invocation currently needs `--config` to avoid a config-loader error, even if all settings are supplied as command-line options. A valid empty YAML mapping (`{}`) is sufficient when using only CLI options. Help commands do not need a config file. This is a workaround for the current implementation.

Save `{}` in a config file (for example `gcm.yaml`; use a corresponding filename for EMIP or SCM), then run a GCM setup-only example (replace settings and paths for your installation):

```sh
pypipe_geos_exp gcm \
  --config gcm.yaml \
  --horz 180 --vert 72 --nx 20 --ny 20 \
  --duration 1 --duration_unit days \
  --geos_dir ../model/install-release/bin \
  --top_exp_dir ./experiments \
  --restart_setup_scripts_dir /path/to/TBC/scripts \
  --execute_on none --account YOUR_ACCOUNT
```

Run commands from the directory you want to use as the base for relative paths. By default, `--geos_dir`, `--top_exp_dir`, and the config-file path are interpreted relative to the current working directory; absolute paths also work.

This creates and patches files in the experiment directory but does not execute the model. `--execute_on none` is not a dry run: setup scripts still run. Inspect the generated files before changing to `--execute_on compute` (submit with `sbatch`) or `local` (run in the current terminal; generally not recommended on HPC). Rerunning the same command may delete and recreate its generated experiment directory, losing manual changes.

Each mode has slightly different CLI. Be sure to check the options for a mode before attempting to create an experiment.

## How The System Works

For a GCM run, `pypipe` performs the following tasks:

1. Creates a named experiment directory by calling the external `create_expt.py` script. With `--machine NONHPC`, it prompts for the Tiny/HugeBC scripts directory unless `--restart_setup_scripts_dir` is supplied, then calls `makeoneday.bash`.
2. Prepares restarts when applicable. `NONHPC` delegates restart preparation to `makeoneday.bash`; `DISCOVER` uses configured system paths. `PRISM` setup is not implemented.
3. Patches generated files such as `CAP.rc`, `AGCM.rc`, and `gcm_run.j` using the selected duration, grid, physics, and DSL options.
4. Launches `gcm_run.j`, if desired.

An EMIP suite follows the setup and patching steps with additional edits to `gcm_emip.setup` and `gcm_run.j`. It runs `gcm_emip.setup`, which generates batch scripts and `sbatch` commands. With `--execute_on compute`, those jobs are submitted; with `--execute_on none`, setup still runs but the jobs are not submitted.

SCM support is in process. More information for launching a SCM run will be included in future versions.

## pypipe Configuration Options

### YAML config files

Pass `--config` after the selected command to provide defaults from a YAML file:

```yaml
horz: 180
vert: 72
nx: 20
ny: 20
duration: 1
duration_unit: days
execute_on: none
pymodules:
  - uw
  - gfdl1m
backend: orch:dace:gpu:KJI
restart_setup_scripts_dir: /path/to/TBC/scripts
```

```sh
pypipe_geos_exp gcm --config gcm.yaml --nx 24
```

The document must be a flat mapping of option names to values for the selected command. Keys match the option names shown in the CLI (without `--`); values use the normal CLI types, including YAML booleans for paired flags and a YAML sequence for `pymodules`. Quote choice values that are numeric-looking strings, such as `start_year`. `horz` and `vert` must be integers in YAML (the CLI accepts them as text). Options not provided in YAML use their CLI defaults. A command-line option always overrides the corresponding YAML value. Unknown keys and keys unsupported by the selected command are errors. An empty mapping (`{}`) is valid when all options are supplied on the command line.

Use the optional `machine` key to select the machine profile used by setup and scheduler generation. Accepted values are `DISCOVER`, `PRISM`, and `NONHPC`; when omitted, the default is `NONHPC`. `PRISM` setup is currently unimplemented; `DISCOVER` relies on hard-coded site paths, so confirm those paths are valid for your account.

The same setting is available as `--machine {DISCOVER,NONHPC,PRISM}`. When both are supplied, the command-line value takes precedence.

The packaged YAML schema is [`cli_options/config.schema.yaml`](cli_options/config.schema.yaml). Its `commands.gcm`, `commands.emip`, and `commands.scm` definitions validate the config shape and value types at runtime using the Python `schema` library; Click validates command-line choices. Click option declarations are grouped by semantic type in `pypipe/cli_options/`.

### Paths, Execution, and DSL

The following options are shared between GCM, EMIP, and SCM modes:

| Option | Default | Description |
| --- | --- | --- |
| `--geos_dir PATH` | `../model/install-release/bin` | GEOS install `bin` directory. Must exist. |
| `--top_exp_dir PATH` | `./experiments` | Parent directory for generated experiments. |
| `--restart_setup_scripts_dir PATH` | unset | NONHPC TBC scripts directory; if omitted, setup prompts for it. |
| `--execute_on {compute,local,none}` | `compute` | Submit with `sbatch`, run in the current terminal, or set up without launching. |
| `--machine {DISCOVER,NONHPC,PRISM}` | `NONHPC` | Machine profile for setup and scheduler behavior. |
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
| `--account TEXT` | unset | Account passed to the GEOS setup script; required for GCM and EMIP `compute` runs. |
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
| `--horz RESOLUTION` | Numeric horizontal resolution, for example `48`, `180`, `360`, or `720`. |
| `--vert LEVELS` | Numeric vertical-level count, for example `72`, `131`, `137`, or `181`. |
| `--nx RANKS` | MPI ranks in X. |
| `--ny RANKS` | MPI ranks in Y per cube face; the AGCM patcher writes `NY = ny × 6`. |

## GCM guide

GCM creates one experiment and optionally runs it.

```sh
pypipe_geos_exp gcm \
  --config gcm.yaml \
  --horz 180 --vert 72 --nx 20 --ny 20 \
  --duration 1 --duration_unit days \
  [shared options]
```

GCM

Provide exactly one of `--duration` or `--end_date`:

| Option | Default | Description |
| --- | --- | --- |
| `--duration INTEGER` | none | Number of --duration_unit units to run; use a positive integer. Mutually exclusive with --end_date. |
| `--duration_unit {days,months,years}` | `days` | Unit for `--duration`. Only considered when `--duration` is supplied. |
| `--end_date YYYYMMDDHHMMSS` | none | Explicit end date. Must be a valid date/time in this format. Mutually exclusive with `--duration`. |
| `--job_time HH:MM:SS` | `01:00:00` | Wall time requested for each sbatch submission. The wrapper passes this value to the generated job script. |
| `--job_segment YYYYMMDDHHMMSS` | none | Explicit `JOB_SGMT` length. If omitted with `--duration`, the wrapper derives it from the duration; with `--end_date`, GEOS uses its template default. |
| `--num_segment INTEGER` | none, GEOS default if omitted | Number of `--job_segment` periods to run per sbatch submission. |
| `--custom_restart` | off | Skip automatic restart copying and stop after setup/patching so you can place custom restarts manually. Requires `--end_date`; it cannot be combined with `--duration`, as duration uses restart files to compute an end date. |

Example with an explicit end date:

```sh
pypipe_geos_exp gcm \
  --config gcm.yaml \
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
| `--duration INTEGER` | `3` | Number of months for each member, used to adjust the generated run loop; use a positive integer. |
| `--job_time HH:MM:SS` | `01:00:00` | Wall time limit for each sbatch submission. Can be up to 12 hours. |
| `--job_segment YYYYMMDDHHMMSS` | none, GEOS default if omitted | Explicit `JOB_SGMT` length. |
| `--num_segment INTEGER` | none, GEOS default if omitted | Number of `--job_segment` periods to run per sbatch submission. |

Example to prepare the ensemble without submitting jobs:

```sh
pypipe_geos_exp emip \
  --config emip.yaml \
  --horz 180 --vert 72 --nx 20 --ny 20 \
  --start_year 2005 --season DJF --duration 3 \
  --execute_on none --account YOUR_ACCOUNT
```

For a NONHPC setup, the example config [`examples/nonhpc_emip.yaml`](examples/nonhpc_emip.yaml) includes the machine profile, paths, grid, and EMIP settings. Replace its placeholder paths, then run from the `pypipe` directory (or adjust the config path if running elsewhere):

```sh
pypipe_geos_exp emip --config examples/nonhpc_emip.yaml
```

EMIP does not support `--execute_on local`; it exits with an error. With `--execute_on none`, including for the NONHPC example above, the wrapper still creates and patches the experiment and runs `gcm_emip.setup` to generate batch files, but does not submit the `sbatch` commands. Review those files before submitting them manually.

**Template sensitivity:** EMIP patching expects specific text in the generated templates (e.g. `while( $count < 4 )` in `gcm_emip.setup`). Changes to GEOS templates can make this step fail.

## SCM guide

SCM accepts `--case`, `--duration`, and `--duration_unit`, as well as the shared path, execution, and DSL options:

```sh
pypipe_geos_exp scm \
  --config scm.yaml \
  --case CASE_NAME --duration 1 --duration_unit days \
  --execute_on none
```

**SCM is not implemented.** The current runner only checks that `--case` was supplied and prints a setup message. It does not create an experiment, use the duration, patch GEOS files, or execute a model. Do not use this command for production runs.

## Operational caveats

- **Select the machine profile explicitly.** The default is `NONHPC`; use `--machine` or the YAML `machine` key as appropriate. `NONHPC` requires the Tiny/HugeBC scripts (provided with `--restart_setup_scripts_dir` or requested interactively). `DISCOVER` uses hard-coded setup and restart paths. `PRISM` is listed as a choice but setup raises `NotImplementedError`.
- **Pass `--config` to every mode command.** The current config callback fails when no config file is supplied. A valid empty YAML mapping (`{}`) works when all settings are passed on the CLI.
- **Use `--execute_on none` to inspect setup output first.** It is not a dry-run: it still creates/patches the experiment and invokes setup scripts (and EMIP's setup script).
- **Experiment directories are destructive on name collision.** Setup deletes an existing directory with the generated experiment name before recreating it.
- **Validate generated files and job status yourself.** The wrapper does not verify that submitted jobs complete successfully. A successful setup or `sbatch` submission is not evidence that the model run completed.
- **Confirm external prerequisites.** The GEOS executable, `create_expt.py`, restart files, appropriate scheduler commands, environment modulefiles, and (if required) Tiny/HugeBC, must be configured before running `pypipe`. The system does not verify external requirements.

## Troubleshooting and implementation references

- Run `pypipe_geos_exp <gcm|emip|scm> --help` for the options accepted by each command. Directly invoking `run_GEOS.py` is a supported source fallback, but the installed command is the intended interface.
- Command wiring is in [`run_GEOS.py`](run_GEOS.py); option groups and the YAML config registry are in [`cli_options/`](cli_options/).
- The GCM orchestration is in [`run_helpers/run_gcm.py`](run_helpers/run_gcm.py); setup and restart handling are in [`run_helpers/setup.py`](run_helpers/setup.py); patching is handled by [`run_helpers/patch.py`](run_helpers/patch.py); and execution is handled by [`run_helpers/execute.py`](run_helpers/execute.py).
- EMIP orchestration and template edits are in [`run_helpers/run_emip.py`](run_helpers/run_emip.py).
- SCM's current placeholder is in [`run_helpers/run_scm.py`](run_helpers/run_scm.py).
