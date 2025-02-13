# VSCode Configuration

VSCode has many configuration options and an active plugin ecosystem. Editor configuration (as well as the editor itself) is a user choice and we respect this. This guide thus a a collection of useful snippets, extensions, and debug launch configurations, which we think are worth sharing with the team.

## Extensions

A plethora of extensions are available for VSCode. Most of them target streamlining workflows, which can be a huge time-saver. We found the following to be useful (in no particular order)

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) (language support including `pylance` & debugger) / [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)
- Modern Fortran (without the fortls engine or else the extension dies trying to figure out GEOS)
- [H5Web](https://marketplace.visualstudio.com/items?itemName=h5web.vscode-h5web) for `netcdf` inline viewing
- [DaCe SDFG Editor](https://marketplace.visualstudio.com/items?itemName=phschaad.sdfv) (in case you work with DaCe graphs)
- your standard set of `git` extensions
    - [GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens) (in-code `git blame`)
    - [Git Graph](https://marketplace.visualstudio.com/items?itemName=mhutchie.git-graph) (clean git graphs)
- [Live Share](https://marketplace.visualstudio.com/items?itemName=MS-vsliveshare.vsliveshare) (remote pair-programming)
- [Draw.io Integration](https://marketplace.visualstudio.com/items?itemName=hediet.vscode-drawio) (draw & share graphs directly from within VSCode - we've seen scaling errors when mixed with graphs created from the website)
- [Mermaid support for Markdown preview](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid)

### Format on save

While `pre-commit` is the source of truth, having format on save support in the editor can be a huge time-saver. To enable format on save

1. Install the "Black Formatter" extension (see above)
2. Configure "Black Formatter" as the default formatter for python files and enable format on save. In `.vscode/settings.json` add
```json
{
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true
    },
}
```

### Run pytests in parallel

`pytest` is the de-facto standard for testing in the python stack. VSCode has out-of-the-box support for `pytest`. To speed up test runs, you can run tests in parallel. `--numprocesses=auto` will pick a sensible default. Read more [here](https://pytest-xdist.readthedocs.io/en/stable/distribution.html).

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "--numprocesses=auto",
        "tests"
    ],
    "python.testing.unittestEnabled": false,
}
```

## Debugging

In VSCode, debugging tasks can be configured with so called “launch configurations”, that live in `launch.json` files. Sharing these here will help the team debug faster.

### Translate tests

!!!warning

    Blindly copy/pasting the snippet below will not work because of hard-coded paths in the config. We should clean this up and/or explain them in the snippet.

```json
{
    "name": "Translate - pyMoist",
    "type": "debugpy",
    "request": "launch",
    "module": "pytest",
    "args": [
        "-s",
        "-v",
        "-x",
        "--data_path=/home/mad/work/fp/geos/src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp/pyMoist/test_data/geos_11.5.2/moist",
        "--grid=default",
        "--backend=numpy",
        "--which_modules=evap_subl_pdf",
        "/home/mad/work/fp/geos/src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp/pyMoist/tests"
    ],
    "env": {
        "PACE_TEST_N_THRESHOLD_SAMPLES": "0",
        "PACE_FLOAT_PRECISION": "32"
    }
}
```
