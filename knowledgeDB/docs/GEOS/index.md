# GEOS model

[Website](https://gmao.gsfc.nasa.gov/GEOS_systems/) | [GitHub](https://gmao.gsfc.nasa.gov/GEOS_systems/)

The Goddard Earth Observing System (GEOS) model consists of a group of model components that can be connected in a flexible manner in order to address questions related to different aspects of Earth Science.

## Resolution

GEOS uses a spherical cube to as discretization of the earth. Resolution is usually given in the form Cxxx / Lxx, e.g. C1120 / L191, where `L` denotes the number of vertical levels and `C` encodes the horizontal resolution as number of grid points per axis on a cube side. Sticking with the example of C1120 / L191, we have

- 1120 grid points per horizontal axis
- 1120 x 1120 grid points per cube side
- 6 x 1120 x 1120 grid points for the full cube
- and 191 vertical levels (for all sides of the cube)

The following table "translates" Cxxx to approximate horizontal resolution in kilo meters and GEOS common resolutions. Production runs marked with *.

```c
{ 
    'C12'  : 773.91
    'C24'  : 386.52
    'C48'  : 193.07
    'C90'  : 102.91
    'C180' : 51.44
    'C270' : 40
    'C360' : 25.71
    'C540' : 19
    'C720' : 12.86 *
    'C1080': 10    *
    'C1120': 8.26  *
    'C1440': 6.43
    'C1539': 6
    'C2160': 5
    'C2880': 3.21
    'C5760': 1.61
}
```
