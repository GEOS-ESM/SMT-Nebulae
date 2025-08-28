# Timings

## Configurations

Baseline:

- DaCe configuration

```python
            dace.config.Config.set(
                "compiler",
                "cpu",
                "args",
                value=f"-std=c++17 -fPIC -Wall -Wextra -O{optimization_level} -march=native -g",
                # value="-std=c++17 -Wsign-compare -fwrapv -Wall -fPIC -ftemplate-depth=1024 -fsigned-char -O3",
            )
            dace.config.Config.set("compiler", "build_type", value="Release")
```

- `copy_corners_x|y_nord` is very slow on orchestration: timings are _without_ `copy_corners_x|y_nord`

Auto-optimization:

We turn on additional transformation found in the `auto_optimize` function stripped of the crashing `greedy_fuse`.

- Baseline
- Custom auto-optimizer :
    - `TrivialMapElimination` repeated
    - `LoopToMap` + `RefineNestedAccess` repeated
    - `simplify` (-`ScalarToSymbolPromotion`)
    - `tile_wcrs`
    - `MapCollapse` repeated
    - `simplify` (-`ScalarToSymbolPromotion`)

## D_SW

_(Without `copy_corners_x|y_nord` in all codes but Fortran)_

### Baseline

C12

```text
gt:dace:cpu  : 0.00764 [0.00777s/ 0.00717 / 0.0111]
orch:dace:cpu: 0.00725 [0.00732s/ 0.00712 / 0.0115]
gt:cpu_kfirst: 0.00583 [0.00606s/ 0.00552 / 0.0135]
```

C24

```text
orch:dace:cpu: 0.0209 [0.0213/ 0.0201 / 0.0295] (KIJ: 0.0239 [0.0242/ 0.0233 / 0.0526])
gt:dace:cpu  : 0.0201 [0.0203/ 0.0198 / 0.0266] 
gt:cpu_kfirst: 0.0158 [0.016/ 0.0153 / 0.0251]
gt:cpu_ifirst: 0.0186 [0.0189/ 0.0182 / 0.0291]
fortran¹     : 0.0116 [0.0117/0.0102/0.0147]
```

¹ Fortran has `copy_corners_x|y_nord` + is of a different version of code (GEOS 11.4.2) which is close enough we consider it virtually similar for performance

### Auto-optimize

```text
gt:dace:cpu  : 0.0073 [0.00754/ 0.00707 / 0.0159]
orch:dace:cpu: 0.00698 [0.007/ 0.00687 / 0.00854]
gt:cpu_kfirst: 0.00571 [0.0059/ 0.00547 / 0.0142]
```

## FVTP2D (C12)

_(Without `copy_corners_x|y_nord`)_

### Baseline

```text
gt:dace:cpu  : 0.000916 [0.00102s/ 0.000879 / 0.00203]
gt:cpu_kfirst: 0.000866 [0.000885s/ 0.000815 / 0.00209]
orch:dace:cpu: 0.000858 [0.000871s/ 0.00082 / 0.00155]
```

### Auto-optimize

```text
gt:dace:cpu  : 0.00106 [0.00109s/ 0.00101 / 0.00399]
gt:cpu_kfirst: 0.000857 [0.000887s/ 0.000785 / 0.00192]
orch:dace:cpu: 0.000745 [0.000769s/ 0.000707 / 0.00346]
```
