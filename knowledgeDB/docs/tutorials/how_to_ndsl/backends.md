# Backends

NDSL has a number of "backends" which use can choose from when you execute your code. Different 
backends have pros and cons which may make them more suitable for different situations:

@someone-who-knows-this-better-than-me please write a pros/cons list (or tell me where I can find
this information and I'll do it)

- `numpy`
- `dace:cpu`
- `dace:gpu`
- `gt:cpu_ifirst`
- `gt:cpu_kfirst`
- `gt:gpu_ifirst`
- `gt:gpu_kfirst`
- `debug`: This backend is used for NDSL development and developing with NDSL, and does not support 
GPU execution or optimized performance. This should not be used unless you are actively developing 
NDSL.

## Looking Backwards to Move Forward

review blurb

Next, we will present a number of patterns commonly seen in weather and climate modeling,
and provide examples of how they are implemented in NDSL.
