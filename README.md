# SMT Nebulae

Welcome to SMT Nebulae, the sandbox of the Software Modernization Team (SMT).

## Dev setup guide

The teams actively works in a couple of repositories at the same time, sometimes making changes across repositories. This guide explains how to setup multiple repositories in editable mode to ease such workflows.

For this guide, we will assume the following layout:

```none
workspace/
├── dace
├── gt4py
├── NDSL
└── pyFV3
```

We will show how to install `dace`, `gt4py`, `NDSL` and `pyFV3` editable such that running translate tests in `pyFV3/` take changes in all other repositories into account.

We'll start in the `dace/` directory and install `dace` editable

```shell
$ cd dace/
$ pip install -e .[linting,testing]
$ source .venv/bin/activate
(.venv) $
```

Then, let's move on to `gt4py`

```shell
$ cd gt4py/
$ uv sync
$ uv pip install -e ../dace
$ source .venv/bin/activate
(gt4py) $
```

`uv sync` automatically installs `gt4py` editable. Then, use `uv pip` to install your local `dace` into the `uv`-managed virtual environment. The way to work with this "patched" virtual environment is by sourcing the `.venv/` and working in there. This is gives you editor support and all the things you know and love (e.g. installed pre-commit hooks keep working).

NOTE: any call to `uv sync` or `uv run` will re-sync the `uv`-managed virtual environment, removing your local dace installation. So don't use `uv run` and re-install `dace` after every `uv sync` (only necessary when dependencies change).

Do the same in `NDSL/`

```shell
$ cd NDSL/
$ uv sync
$ uv pip install ../gt4py
$ uv pip install ../dace
$ source .venv/bin/activate
(ndsl) $
```

and `pyFV3/` we are back to traditional `pip` (for now).

```shell
$ cd pyFV3/
$ pip install --editable .[dev]
$ pip install ../NDSL
$ pip install ../gt4py
$ pip install ../dace
$ source .venv/bin/activate
(.venv) $
```

## To sort

- `dsl_patterns` should end up in the manual of NDSL
- `hardware_tests` should be completed and end up in some pipeline for GEOS and HPC

## Questions

Reach out to Florian Deconinck: florian.deconinck -at- ssaihq.com
