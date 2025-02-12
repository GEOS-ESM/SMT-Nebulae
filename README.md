
# Software Modernization Team: The Code Nebulae

This is the team sandbox repository, storing early PoC, relevant benchmark data, staging `ci` workflows, etc.
Shortname for the package is `tcn`.

🚧 This is a staging/PoC area for code, inherently every code here is unstable. 🚧

Below is a quick summary of the tools/packages present in code. More information is package-level READMEs.

## Knowledge Base

SMT documentation is sourced from the [Knowledge Base](./knowledgeDB/README.md) folder and made available on [Github Pages](https://geos-esm.github.io/SMT-Nebulae).

## `ci`

On-premise CI for the GPU ports of GEOS. Includes validation & benchmark workflows.

Heartbeat insure the workflow to reach Discover is working.
Validation capacities in the case of GEOS is strictly building & running the GPU-enabled version.
Validation capacities for physics compares OACC and original Fortran on.

| Validation                    | Status    |
| ------------------------------------------ | --------- |
| NCCS Discover Heartbeat                    | [![💓](https://github.com/GEOS-ESM/SMT-Nebulae/actions/workflows/discover_heartbeat_nightly.yml/badge.svg)](https://github.com/GEOS-ESM/SMT-Nebulae/actions/workflows/discover_heartbeat_nightly.yml) |
| NCCS Discover GEOS Held-Suarez Validation  | Deactivated |
| NCCS Discover Physics Standalone           | Deactivated |
| NCCS Discover GEOS Aquaplanet Validation   | Deactivated |

## `hws`

Hardware Sampler - software file socket based package to instrument CPU/GPU usage, memory and TPU.

## `benchmark`

Collection of scripts to mine GEOS log for relevant timing information for DSL and Fortran runs.

## `py_ftn_interface`

Generator of Python <> Interface based on CFFI as used in GEOS integration of the DSL. To be used as a starting point.

## `plots`

Collection of scripts to plot various outputs of GEOS and DSL.

## Software stack builder (`sw_stack`)

Scripts to download and build the software stack used for the GEOS port.
