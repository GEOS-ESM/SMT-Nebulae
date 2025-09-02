# Benchmarker scripts

This folder contains a bunch of benchmarking scripts held together by duct-tape. This is "just for now" and systematic tooling for profiling will be added cleanly in the future at the NDSL level.

## Setup

Create a local (conda, venv) environment and install packages manually as needed. Point your environment to (local) versions of PyFV3, NDSL, ... as it suits you.

Copy `0_config.yaml` to `.config.yaml` and edit the (hard-coded) paths in there to match your setup.

## Run scripts

Entry points for running benchmarks are `run_[component].sh` scripts. Use them to run a specific component. They can also be used together with vtune (see below).

## Intel VTune

Use `vtune.sh` (together with one of the `run_[component].sh`) to gather performance data. We integrate ITT timers in the benchmarkers such that only relevant things show up in profile.
