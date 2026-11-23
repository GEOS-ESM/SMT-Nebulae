# pypipe: GEOS experiment setup

`pypipe` prepares and launches GEOS GCM experiments and EMIP ensembles. Future versions will also support SCM experiments. The wrapper relies on an existing GEOS installation and its setup scripts; it does not install GEOS or load HPC modules.

## Install and get help

Use Python 3.12 or newer. From the repository root, install `pypipe` in the environment you plan to use:

```sh
python -m pip install ./pypipe
pypipe_geos_exp --help
pypipe_geos_exp GCM --help
pypipe_geos_exp EMIP --help
pypipe_geos_exp SCM --help
```

`GCM`, `EMIP`, and `SCM` are case-sensitive and must be uppercase. If the installed command is unavailable, direct source invocation is supported as a fallback: `python pypipe/run_GEOS.py ...` from the repository root.

## Choose a mode and run it

The usual form puts the mode before its options:

```sh
pypipe_geos_exp GCM --config gcm.yaml --execute_on none
pypipe_geos_exp EMIP --config emip.yaml --execute_on none
```

Alternatively, put `mode: GCM`, `mode: EMIP`, or `mode: SCM` at the top level of the YAML file and omit the mode argument:

```sh
pypipe_geos_exp --config emip.yaml --link
```

In this form, put mode-specific settings in YAML. Root-level options such as `--link` can override YAML values. If an explicit mode command and a YAML `mode` are both supplied, they must match.

Example GCM configuration (`gcm.yaml`):

```yaml
mode: GCM # Can be omitted only when using an explicit GCM command.
machine: NONHPC
geos_dir: /path/to/GEOS/install
top_exp_dir: /path/to/experiments
restart_setup_scripts_dir: /path/to/TBC/scripts
execute_on: none
link: true
horz: 180
vert: 72
nx: 20
ny: 20
duration: 1
duration_unit: days
```

Run the config-driven form with `pypipe_geos_exp --config gcm.yaml`, or use an explicit mode and override settings on the command line, for example `pypipe_geos_exp GCM --config gcm.yaml --nx 24`.

Example EMIP configuration (`emip.yaml`):

```yaml
mode: EMIP
machine: NONHPC
geos_dir: /path/to/GEOS/install
top_exp_dir: /path/to/experiments
restart_setup_scripts_dir: /path/to/TBC/scripts
execute_on: none
horz: 180
vert: 72
nx: 20
ny: 20
start_year: "2005"
season: DJF
duration: 3
```

Run it with `pypipe_geos_exp --config emip.yaml` or `pypipe_geos_exp EMIP --config emip.yaml`. EMIP does not support `execute_on: local`; use `none` to prepare files without submitting generated jobs, or `compute` to submit them.

## Common settings

- `machine`: `NONHPC` (default), `DISCOVER`, or `PRISM`. Machine selection is explicit; there is no host auto-detection. PRISM support is in progress and not currently supported.
- `execute_on`: `compute` submits jobs, `local` runs in the current terminal, and `none` prepares the experiment without running/submitting it. `none` is not a dry run: setup scripts still execute.
- `link`: Determines whether the GEOSgcm.x executable is explicitly copied from or symlinked to the install directory. defaults to `true`; set `link: false` or pass `--no_link` to copy instead of linking.
- `restart_setup_scripts_dir`: for NONHPC, points to the Tiny/HugeBC scripts used by `makeoneday.bash`. If omitted, setup prompts for the directory.
- GCM's `keep_original_restarts` defaults to `false`. Set it to `true` or pass `--keep_original_restarts` to insert `exit` immediately after the GEOSgcm run-status message. This skips all subsequent run-script processing, including restart handling; `--no_keep_original_restarts` overrides an enabled YAML setting. If the status line is missing or ambiguous, setup fails rather than silently leaving the script unchanged.
- `geos_dir` is the GEOS installation root (for example, `.../model/install`); pypipe runs its `bin/gcm_setup` directly. Paths such as `geos_dir`, `top_exp_dir`, and `--config` are relative to the current working directory unless absolute paths are used. The GEOS setup script does not support spaces or shell metacharacters in installation and experiment paths.
- Some GEOS setup inputs are optional in pypipe. If you omit these options (or set them to `null` in YAML), pypipe leaves the corresponding `gcm_setup` prompt blank, and GEOS uses its own default. Among these options are `microphysics`, `processor`, `aerosols`, `oserver`, and `hydro`. You can still provide any of them explicitly to override the GEOS default. If GEOS does not prompt for `hydro`, pypipe leaves the generated FV3 namelist unchanged unless you explicitly set `--hydro` or `--nonhydro`. On DISCOVER CPU runs without an explicit `processor`, pypipe uses a conservative task count and lets the scheduler choose processor placement.
- Other setup prompts also use GEOS defaults where applicable: the experiment description matches its name, cloning is disabled, both experiment directories use the generated directory, MOM5/MOM6 use their default resolutions (with CICE4/CICE6 respectively), MIT uses CICE4, and emissions and HISTORY use GEOS defaults.
- GCM requires `horz`, `vert`, `nx`, `ny`, and exactly one of `duration` or `end_date`. EMIP requires the grid values, `start_year` (`1985`, `1995`, or `2005`), and `season` (`DJF` or `JJA`); duration defaults to 3 months.
- `--pymodules` accepts `gfdl1m`, `uw`, `gf2020`, `fv3`, and `shoc` (comma-separated or repeated). Use lowercase names. `shoc` enables `USE_PYTURB_SHOC` in `AGCM.rc`.
- `dace_mode` sets `FV3_DACEMODE` in the generated run script. Choose `Build`, `BuildAndRun` (the default), or `Run`; the corresponding CLI option is `--dace_mode`. The setting does not enable a Python module by itself.

YAML files are flat mappings of option names to values. CLI options override YAML values. Quote choice values that look numeric, such as `start_year`. See [`cli_options/config.schema.yaml`](cli_options/config.schema.yaml) and per-mode `--help` for the supported settings.

### Saved experiment configuration

GCM and EMIP setup automatically writes `pypipe.yaml` inside the generated experiment directory. It contains every mode-specific pypipe option, including unspecified defaults, CLI overrides, the machine profile, computed job segments, and any interactively supplied restart-script directory. Optional values are retained as explicit `null` values and disabled flags as `false`, rather than omitted.

Reuse it with `pypipe_geos_exp --config /path/to/experiment/pypipe.yaml`. Saved values take precedence over future pypipe defaults. Copy the file elsewhere or override `top_exp_dir` if the original experiment must be preserved: setup deletes an existing experiment directory with the same generated name. Relative paths still refer to the current working directory. Reproduction also requires compatible GEOS software and external data; defaults delegated to GEOS itself are not captured by this pypipe configuration.

## Before running

- `--execute_on none` still creates and modifies experiment files and runs external setup scripts.
- Setup deletes an existing experiment directory if its generated name collides. Back up anything you need first.
- Confirm GEOS, restart data, Tiny/HugeBC scripts where required, and scheduler commands are configured and available. NONHPC setup still calls `makeoneday.bash`.
- Review generated files and check job status yourself; successful setup or submission does not confirm the model completed successfully.

SCM currently only prints a setup message. It does not create, patch, or run an experiment.