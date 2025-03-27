# Backends

NDSL has a number of "backends" which use can choose from when you execute your code.
The backend can be thought of as the fuel which powers the engine of NDSL. Different fuels
have pros and cons which may make them more appealing to different situations. The following
is a complete list of all supported backends

- `numpy`. This is the default backend for NDSL
- `dace:cpu`
- `dace:gpu`
- `gt:cpu_ifirst`
- `gt:cpu_kfirst`
- `gt:gpu_ifirst`
- `gt:gpu_kfirst`
- `debug`: This backend is used for NDSL development, and does not support GPU execution or
optimized performance. This should not be used unless you are actively developing NDSL.


For more information LINK