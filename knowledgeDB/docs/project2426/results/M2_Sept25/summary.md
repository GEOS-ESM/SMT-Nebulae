# NDSL powered GEOS: CPU & GPU validation & benchmark

## Table of results

| Science Code               | Numerical Validation(C24) | Scientific Validation(C180) | CPU Benchmark (C180) |   GPU Benchmark (C180) | GPU Benchmark (C720) |
| ------------               | --------------------      | ---------------------       | -------------        |   -------------        | ---------------      |
| Dynamics (Pace)            | ❌: [details](./dynamics_pace.md) |          ❌                 |          ❌          |          ❌            |         ❌           |
| Dynamics (GEOS v11.4.2)    |        ❌                 |          ❌                 |          ❌          |          ❌            |         ❌           |
| Moist - Microphysics       |        ❌                 |          ❌                 |          ❌          |          ❌            |         ❌           |
| Moist - Shallow Convection |        ❌                 |          ❌                 |          ❌          |          ❌            |         ❌           |

C24 resolutions have 72 levels. All other resolutions have 137 levels.

## Methodology

!!! bug
    Expand

### Validation

_Numerical validation:_

Numerical validation is done comparing a single time step between Fortran and NDSL on the CPU. It was the base of the porting.

<INSERT PPT IMAGE TO SHOWCASE TRANSLATE TEST>

- Both codes run with `-O0`, e.g., with compiler optimization turned off.
- A multi-modal metric is used for measuring difference that combines absolute and relative differnces, and ULP measurement.
- Differences are expected (compilers, different codes) and reasonable thresholding will be used.

_Scientific validation:_

Scientific validation is done by comparing the results of 7 days of GEOS runs.

See more details and discussion in the [overview](./validation_overview.md)

<TODO INSERT EXPLANATION ON METRICS USED RMSE, ETC.>

### Benchmark

Benchmark is done both on CPU and GPU at C180 L137. To showcase the difference in device bandwith, we also run GPU on C720 L137.

Benchmark are done online in GEOS but measure several performance which are all interconnected

<TODO INSERT GRAPH SHOWING GEOS / COMP / F-PY INTERFACE / DATA MANIP / NUMERICS >

### Hardware

NCCS's Discover A100 partition, refered as **"Discover"**, per node:

- 4x A100 GPUs – 40 GB (released 2021)
- 1x EPYC 7402 – 96 cores (released 2020)
- Dual HDR Infiniband 2x200 Gbps

NCCS's PRISM GH partition, refered as **"Prism GH"**, per node:

- 1x H100 (96 GB) + 1 Grace (72 cores @ 2GHz- 480 GB) on the same die (released 2022)
- Dual HDR Infiniband 2x100 Gbps

### Software stack

!!! bug
    TODO

## Overviews and earlier results

- [Validation - overview](./validation_overview.md)
- [Benchmark - overview](./benchmark_overview.md)
- [Early GFDL Single Moment microphysics](./early_microphys.md)
