
# PCHEM NOTES

- All the code is in one file: GEOS_PChemGridComp.F90
- Pchem is a simple parameterization of the Aerochem species
- Work on three types of species: chemical species (oxygen, nitrous oxide, CFC-11, CFC-12, CFC-22, methane, water vapor), diagnostic species (age-of-air), and aerosols
- Chemical species can be treated in one of two ways: 
    - parameterized prediction from tabled zonally-symmetric production and loss (P-L) data
    - or specification from zonally-symmetric values (see Resources section)
    - A single flat file containing both the P-L and climatology data must be provided
- Aerosols are set to 3-dimensional climatological values.
- The ``age-of-air'' is predicted by setting the surface values of this tracer to the to zero and advancing other levels by dt
  - All of these quantities except water vapor are INTERNAL state variables of PCHEM 
- Water vapor is assumed to be a Friendly Import and PChem leaves it unmodified below the tropopause, or the 200 hPa level if the tropopause is below this level
- For chemical species, the production rate is tabled directly. For the loss, a rate coefficient is tabled.
- See summary at top of GEOS_PChemGridComp.F90 for description of how species are updated based on P-L rates
- Ozone is diagnosed from $O_x$ by assuming that it accounts for all $O_x$ at pressures greater than 100 Pa (1 hPa) during the day and at all pressures at night. For those day lit cells where pressures are less than 1 hPa, we assume that the ozone fraction in $O_x$ decreases exponentially with decreasing pressure.
- Aerosols are read from 3-dimensional data files that have to be on model levels but may be on any regular lat-lon grid. These are hdf files and horizontal interpolation is done through CFIO. The aerosols are read into a bundle that is exported, and the number and names of the aerosols in the bundle are set from the CFIO file. 
- Resources section contains names/descriptions of files/variables that are needed to run PChem
- From what I have gathered so far, it seems that PChem Run reads in pretabulated concentration data, interpolates the data to GEOS grid, and then updates the concentrations if certain conditions are met.


# QUESTIONS/CONCERNS

1. PChem seems to be reading in a data file that contains tabulated concentrations of the 7 species - I am not exactly where this file is located, but it must exist somewhere.
2. PChem is very MAPL heavy and contains a lot of MAPL calls, mixed in with some math. We will need to at some point find a way to replicate these MAPL calls (there may be more):
- MAPL_GetPointer 
- MAPL_GetResource
- MAPL_AM_I_ROOT()
- MAPL_INTERP
- MAPL_SunGetInsolation
- MAPL_VerifyFriendly
- MAPL_Get
- MAPL_GetObjectFromGC
- MAPL_MetaComp
- MAPL_SunOrbit
- MAPL_ClimInterpFac
3. What do we want to port? Everything in GEOS_PChemGridComp.F90 or just the stuff in Run? Run is responsible for about 40% of the total compute time, the time it takes to read in the data files is neglibible. PChem Run seems portable, and we have already started to port the `Update` subroutine in Run (dsl/PChem branch). However, `interp_no_extrap` involves some MAPL calls, which make the port more difficult. 