# GT4Py development

[Docs](https://gridtools.github.io/gt4py/latest/index.html) | [README](https://github.com/GridTools/gt4py?tab=readme-ov-file#gt4py-gridtools-for-python) | [Contributing](https://github.com/GridTools/gt4py/blob/main/CONTRIBUTING.md) | [Coding guidelines](https://github.com/GridTools/gt4py/blob/main/CODING_GUIDELINES.md)

## Notes & quirks

- GT4Py cartesian and next live in the same repository. Both share the `eve` framework, `_core` definitions, and the test system.
- GT4Py cartesian uses released versions of DaCe. GT4Py next uses a pinned commit from the `main` branch.
- To run cartesian tests that require DaCe (e.g. for bridge work): `nox -s "test_cartesian-3.10(dace,cpu)"`
- Running tests with `nox` will use the local gt4py code, but install a clean environment.
- CSCS CI is twitchy. If you get spurious test failures, try rerunning: comment `cscs-ci run` on your PR to kick off another round.

## Community

- Monthly community meeting (shared between cartesian and next)
- Developers share a Slack channel
