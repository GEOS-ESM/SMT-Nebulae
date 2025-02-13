# Developer stack

!!! Note

    NDSL users are advised to stick with released versions: <https://github.com/NOAA-GFDL/NDSL/releases/latest>

- **NDSL**<br/>
  Follow branch `develop` in [main repo](https://github.com/NOAA-GFDL/NDSL).
- **GT4Py**<br/>
  Follow branch `int_cast_aboslute_k_debug` on [Tobia's fork](https://github.com/twicki/gt4py/tree/int_cast_aboslute_k_debug), which includes the following experimental features:
    - `debug` backend: plain python backend for quick prototyping of new DSL features
    - absolute index in `K`, e.g. `field.at(K=42)` or `field.at(K=KLCL)` where `KLCL` itself is a field (and we are reading at center)
    - mixed precision
        - Cast to integer and float types, e.g. `X = i32(Y)` (works with `i32`, `i64`, `f32`, `f64`)
        - Type hints, e.g. `X: f64 = 0` (works with `i32`, `i64`, `f32`, `f64`)
        - `round`, `erf`, `erfc` native functions
    - Fix to numpy data dimensions access
    - `THIS_K` references the current K index
- **DaCe**<br/>
  default one, as configured in by NDSL
- **[Serialbox](https://github.com/GridTools/serialbox)**<br/>
  Follow brach `feature/data_ijkbuff` on [Florian's fork](https://github.com/FlorianDeconinck/serialbox), which includes the following features:
    - `data_buffered` keyword to allow buffer serialization (scalar by scalar) of Fields
    - `data_writeonly` keyword to allow `real, parameter :: X` style constants to be saved by removing the `read` capacity
    - `data_append` keyword to write scalars in a 1 dimensional field
    - `flush savepoint_name` to dump all data in savepoint irrespective or either or not the buffer is filled up
