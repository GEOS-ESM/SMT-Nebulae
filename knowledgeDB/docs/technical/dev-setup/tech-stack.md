# Developer stack

!!! Note

    NDSL users are advised to stick with released versions: <https://github.com/NOAA-GFDL/NDSL/releases/latest>

- **NDSL**<br/>
  Follow branch `develop` in [main repo](https://github.com/NOAA-GFDL/NDSL).
- **GT4Py**<br/>
  Follow branch `physics` on [Stefano's fork](https://github.com/stubbiali/gt4py/tree/physics), which includes experimental features as listed [in this table](../frontend/experimental_features.md).
- **DaCe**<br/>
  default one, as configured in by NDSL
- **[Serialbox](https://github.com/GridTools/serialbox)**<br/>
    Follow brach `feature/data_ijkbuff` on [Florian's fork](https://github.com/FlorianDeconinck/serialbox), which includes the following features:
    - `data_buffered` keyword to allow buffer serialization (scalar by scalar) of Fields
    - `data_writeonly` keyword to allow `real, parameter :: X` style constants to be saved by removing the `read` capacity
    - `data_append` keyword to write scalars in a 1 dimensional field
    - `flush savepoint_name` to dump all data in savepoint irrespective or either or not the buffer is filled up
