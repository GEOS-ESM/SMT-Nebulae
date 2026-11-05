# Notes while updating dynamics to GEOS v11.11

_Florian speaking_

> DISCLAIMER: there might be missing code here and there, I ported FV at 11.5.2 then did some adjustments. Most of the big changes are after this,
> but there might be pebbles I missed, so double check the actual code itself vs reference fortran when things gets weird.

We want to move from GEOS [v11.8.2](https://github.com/GEOS-ESM/GEOSgcm/releases/tag/v11.8.2) => [v11.11.0](https://github.com/GEOS-ESM/GEOSgcm/releases/tag/v11.11.0)

## The Fortran code structure

There's two sub-codebase touching the dynamics

### @FVDycore_GridComp

That'sGEOS/GMAO harness - specific code to move from GEOS land into NOAA's GFDL land + option tuning + random magic

We want to go from [2.16.1](https://github.com/GEOS-ESM/FVdycoreCubed_GridComp/releases/tag/v2.16.1) [=>](https://github.com/GEOS-ESM/FVdycoreCubed_GridComp/compare/v2.16.1...v3.1.0) [3.0.0](https://github.com/GEOS-ESM/FVdycoreCubed_GridComp/releases/tag/v3.0.0)

I made the API change to match our interface to `3.1.0`, most changes were carried by `3.0.0`

Our working update branch is: `dsl/update/pyFV3_interface`. Since I didn't do the work more diligently (bad me) there's a before and after the major 3.x series:

- The last commit carrying the 2.x series is: c8720a3
- The first commit carrying the 3.x series is: 1460d5

I can't tag because this is on the GEOS-ESM fork and they have a particular usage of tags (and I am not getting into this discussion)

- :warning: If you are running v11.8.x go to `c8720a3` if you are running `v11.10+` go to `1460d5`
- :warning: (bis) Those are untested changes because I don't have the data of `v11.10+` on my machine atm

### @fvcore

That's NOAA GFDL original dycore + the spins of Bill on top. There's a `develop` (NOAA) and a `geos/develop` (GEOS). The codebase has a different name [GFDL_atmos_cubed_sphere](https://github.com/GEOS-ESM/GFDL_atmos_cubed_sphere)

We want to go (more or less see disclaimer above) from [v2.10.0](https://github.com/GEOS-ESM/GFDL_atmos_cubed_sphere/releases/tag/geos%2Fv2.10.0) [=>](https://github.com/GEOS-ESM/GFDL_atmos_cubed_sphere/compare/geos/v2.10.0...geos/v3.1.0) [v3.1.0](https://github.com/GEOS-ESM/GFDL_atmos_cubed_sphere/releases/tag/geos%2Fv3.1.0)

## Serialization

- `@FVdycoreCubed_GridComp` "new branch": `dsl/serialbox/3.1.0` in `FlorianDeconinck/GFDL_atmos_cubed_sphere`
- `@fvcore` "new branch": `dsl/serialbox/3.1.0` in `FlorianDeconinck/GFDL_atmos_cubed_sphere`
- `@fvcore` "old branch": `geos/dsl/serialbox` in `GEOS-ESM/GFDL_atmos_cubed_sphere`

## Map of code changes

This section is to outline code changes in the diffs above (click on the `=>` to see them). The "map of code changes" will serve as basis for what we need to do and how we can split the work required in `pyFV3`.

### @fvcore

#### `model/dyn_core.F90`

- `subroutine dyn_core()` now gets "Rayleigh Friction tendencies" `dudt_rf, dvdt_rf, dwdt_rf,` as additional inputs
- now local: `d4dmp`
  - why? "higher order hyper-diffusion on divergence"
  - one-time calculation in `dyn_core()` (just before the `d_sw()` call)
  - used in the "d_sw"-part
- "d_sw"-part
  - now uses `d4dmp` (see above)
  - `d_ext` isn't a flag anymore, but a K-array
  - bunch of little? changes in that part of the code (see diff)
  - call to `d_sw()`: now gets `d4dmp(k)` instead of `flagstruct%d4_bg,`

