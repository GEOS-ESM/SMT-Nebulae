# GEOS model

[Website](https://gmao.gsfc.nasa.gov/GEOS_systems/) | [GitHub](https://gmao.gsfc.nasa.gov/GEOS_systems/)

The Goddard Earth Observing System (GEOS) model consists of a group of model components that can be connected in a flexible manner in order to address questions related to different aspects of Earth Science.

## Resolution

GEOS uses a spherical cube to as discretization of the earth. Resolution is usually given in the form Cxxx / Lxx, e.g. C1120 / L191, where `L` denotes the number of vertical levels and `C` encodes the horizontal resolution as number of grid points per axis on a cube side. Sticking with the example of C1120 / L191, we have

- 1120 grid points per horizontal axis
- 1120 x 1120 grid points per cube side
- 6 x 1120 x 1120 grid points for the full cube
- and 191 vertical levels (for all sides of the cube)

The following table "translates" Cxxx to approximate horizontal resolution in kilo meters.

|     |  C24  | C96  | C180 | C360 | C720 | C1120 | C3072 | C6144 | C12288 |
| --- |  ---  | ---  | ---  | ---  | ---  |  ---  |  ---  |  ---  |  ---   |
| km  | 384.2 | 96.0 | 51.2 | 25.6 | 12.8 |  8.2  |  3.0  |  1.5  |  0.8   |
