# pyFV3

## Breakdown

Dynamics (FVDynamics)

- compute_preamble
  - fluxes/courant to zero
  - fv_setup
  - == consv_te > 0
    - ComputeTotalEnergy
  - pt_to_potential_density_pt
  - DryMassRoundOff.reset
- =o= K SPLIT loop
  - reset `delp`
  - Acoustics (DynCore)
    - Halos
    - zero_data
   =o= N SPLIT loop
      - gz_from_surface_height_and_thicknesses
      - interface_pressure_from_toa_pressure_and_thickness
      - CGridShallowWaterDynamics (C_SW)
      - UpdateGeopotentialHeightOnCGrid (UpdateDzC)
      - NonhydrostaticVerticalSolverCGrid (RiemanSolverC)
      - p_grad_c
      - DGridShallowWaterLagrangianDynamics (D_SW)
      - UpdateHeightOnDGrid (UpdateDzD)
      - NonhydrostaticVerticalSolver (RiemanSolver3)
      - == remap_step
        - edge_pe
      - compute_geopotential
      - NonHydrostaticPressureGradient (NH_P_GRAD)
      - == rf_fast
        - RayleighDamping (Ray_Fast)
    - == do_del2cubed
      - HyperdiffusionDamping (del2cubed)
      - apply_diffusive_heating (PressureAdjustedTemperature_NonHydrostatic)
  - Copy acoustics fluxes/courant f64 into local f32
  - == Last K
    - DryMassRoundOff.apply
  - == z_tracer
    - TracerAdvection (Tracer2D1L)
  - LagrangianToEulerian_GEOS (Remapping)
  - Increment global fluxes/courant with local f32
  - == Last K
    - omega_from_w
    - == nf_omega > 0
      - HyperdiffusionDamping (Del2Cubed)
- AdjustNegativeTracerMixingRatio (Neg_Adj3)
- CubedToLatLon (CubedToLatLon)

## Links

FV3 docs at NOAA:

- [Global documentation](https://www.gfdl.noaa.gov/fv3/)
- [GFDL Technical documentation](https://repository.library.noaa.gov/view/noaa/30725)
