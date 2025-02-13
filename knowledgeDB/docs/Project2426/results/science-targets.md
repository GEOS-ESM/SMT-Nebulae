# Science targets

In collaboration with the GMAO we have identified two scenarios to cover weather and climate simulations pragmatically and one moonshot to push the envelop given adequate previous success and resources.

## Forward Processing Weather (GEOS-FP)

- Configuration
    - 8.5 km horizontal resolution (C1120)
    - 191 atmospheric levels
    - No Data Assimilation (DA)
    - All physics
    - All tracers

- Implementation
    - Fortran/Python hybrid
    - Dynamics and moist physics under NDSL

- Expected performance
    - GPU: 2 – 2.5x speed up
    - CPU: within 15%

## CO2 Climate

- Configuration
    - 3 km horizontal resolution (C3072)
    - 191 atmospheric levels
    - No Data Assimilation (DA)
    - All physics minus Grell-Freitas Convection
    - All tracers

- Implementation
    - Fortran/Python hybrid
    - Dynamics, moist physics and gases chemistry (GOCART) under NDSL

- Performance
    - Currently 15-20 SDPD on 200 nodes of NCCS’s Discover, we want to reach 30 SDPD

## Moonshot: CO2 Climate at 1 SYPD

Same configuration as the `CO2 Climate` scenario but we scale up to reach 1 Simulated Year per Day or 365 SDPD.
This will most likely require a _large_ allocation of GPUs at best, more code porting at worst (which in the later case will probably make it our of reach of our timeline).
