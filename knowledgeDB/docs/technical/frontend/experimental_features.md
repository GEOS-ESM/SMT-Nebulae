# Experimental "Physics" features

⚠️ This should live in NDSL or GT4Py or DaCe own documentation ⚠️

## Summary

Experimental work drops support for `gt` backends for the forseeable future to allow for quicker iteration

| Feature                                       | debug | numpy | dace:cpu | dace:gpu | test / example |
| --------------------------------------------- | ----- | ----- | -------- | -------- | -------------- |
| [Absolute indexing in K](#1)                  | ✅    | ✅🐞  | ✅       | ✅       | [link](https://github.com/stubbiali/gt4py/blob/de153add38a23076eb59d733b8972c87cd57d644/tests/cartesian_tests/unit_tests/frontend_tests/test_gtscript_frontend.py#L1827) |
| [Parametrizable precision](#2)                | ✅    | ✅    | ✅       | ✅       |      |
| [Generic cast to precision](#3)               |       |       |          |          |      |
| [ROUND function](#4)                          | ✅    | ✅    | ✅       | ✅       |      |
| [ERF function](#4)                            | ✅    | ✅    | ✅       | ✅       |      |
| [Type hinting of temporaries](#5)             | ✅🐞  | ✅🐞  | ✅🐞     | ✅🐞     |      |
| [Variable indexing of data dimensions](#6)    | ✅    | ❓    | ✅       | ✅       |      |
| [Exposing current K level as a scalar](#7)    | ✅🐞  | ✅    | ✅       | ✅       |      |
| [Unrolling for-range loop](#8)                | ❓    | ✅    | ❓       | ❓       |      |
| [Mutable arguments on gtscript.function](#9)  | ❓    | ✅    | ❓       | ❓       |      |
| [Breakpoint injection](#10)                   |       |       |          |          |      |
| [Print](#11)                                  |       |       |          |          |      |
| [2D temporaries](#12)                         |       |       |          |          |      |
| [Runtime Interval](#13)                       |       |       |          |          |      |
| [Higher dim temporaries](#14)                 |       |       |          |          |      |
| [Computation mask](#15)                       |       |       |          |          |      |
| [Nested K interval/loop](#16)                 |       |       |          |          |      |
| [Field save to NetCDF](#17)                   |       |       |          |          |      |
| [Code-flow heatmap](#18)                      |       |       |          |          |      |

## Details

### <a name="1"/></a>Absolute indexing in K

- Usage: `field.at(K=x, ddim=[y])` with `ddim` optional
- Todo:
    - `numpy` doesn't handle data dimensions
    - Unit tests for data dimensions feature
- Merge to `main`: BLOCKED
    - Impossible in `gt:X` backends without changes to GridTools

### <a name="2"/></a>Parametrizable precision

- Usage: `literal_floating_point_precision` in `gt4py.cartesian.config.build_settings` OR `GT4PY_LITERAL_PRECISION` environment variable
- Todo: Unit test
- Ready for merge in `main`

### <a name="3"/></a> Generic cast to precision

- Usage: `a = int(b)` with types `i32`, `i64`, `f32`, `f64`, `int`, `float`
- TO BE IMPLEMENTED

### <a name="4"/></a>ROUND & ERF functions

- Merge to `main`: READY

### <a name="5"></a>Type hinting of temporaries

- Usage: `field: i32 = 0` with types `i32`, `i64`, `f32`, `f64`
- ToDo:
    - missing generic `int`, `float`
    - unit tests
- Merge to `main`: READY

### <a name="6"></a>Variable indexing of data dimensions

- Usage: `field[0,0,0][x]`
- ToDo:
    - Fix unit tests
    - `numpy` might not be working
- Merge to `main`: READY

### <a name="7"></a>Exposing current K level as scalar

- Usage: `THIS_K` as an `int`
- ToDo:
    - Do not default to parametrized precision
- Merge to `main`: BLOCKED (partial)
    - Merge after parametrizable precision

### <a name="8"></a>Unrolling for-range loop

- Usage: `for i in range(x)` all operations will be unrolled
- ToDo: TBD
- Merge to `main`: TBD

### <a name="9"></a>Mutable arguments on gtscript.function

- Usage: functions with no return statements have mutable arguments
- ToDo: TBD
- Merge to `main`: TBD

### <a name="10"></a>Breakpoint injection

- TO BE IMPLEMENTED

### <a name="11"></a>Print

- TO BE IMPLEMENTED

### <a name="12"></a>2D temporaries

- TO BE IMPLEMENTED

### <a name="13"></a>Runtime Interval

- TO BE IMPLEMENTED

### <a name="14"></a>Higher dim temporaries

- TO BE IMPLEMENTED

### <a name="15"></a>Computation mask

- TO BE IMPLEMENTED

### <a name="16"></a>Nested K interval/loop

- TO BE IMPLEMENTED

### <a name="17"></a>Field save to NetCDF

- TO BE IMPLEMENTED

### <a name="18"></a>Code-flow heatmap

- TO BE IMPLEMENTED
