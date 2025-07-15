# GT4Py development

[Docs](https://gridtools.github.io/gt4py/latest/index.html) | [README](https://github.com/GridTools/gt4py?tab=readme-ov-file#gt4py-gridtools-for-python) | [Contributing](https://github.com/GridTools/gt4py/blob/main/CONTRIBUTING.md) | [Coding guidelines](https://github.com/GridTools/gt4py/blob/main/CODING_GUIDELINES.md)

## Up and running

Getting started: Run

```sh
uv sync --extra cartesian --group dace-cartesian
```

This installs a development environment (containing things like tests and pre-commit hooks) with the cartesian version of [DaCe](./dace.md). Add `--extra cuda12` at the end for GPU support.

## Notes & quirks

- GT4Py cartesian and next live in the same repository. Both share the `eve` framework, `_core` definitions, and the test system.
- GT4Py cartesian uses a DaCe version based on `v1/maintenance`. Install the extra `dace-cartesian` to work with that version (see above).
- GT4Py next uses a DaCe version based on the `main` branch. This version is kept in the extra `dace-next`.
- To run cartesian tests that require DaCe (e.g. for bridge work):

```sh
nox -s "test_cartesian-3.10(dace,cpu)"`
```

- Running tests with `nox` will use the local gt4py code, but install a clean environment.
- Commenting `cscs-ci run` allows to re-run CSCS-CI on PRs.
- To update the DaCe branch in the `uv.lock` file:

```sh
uv sync -P dace --extra cartesian --group dace-cartesian --extra cuda12
```

## Community

- Monthly community meeting (shared between cartesian and next)
- Developers share a Slack channel
