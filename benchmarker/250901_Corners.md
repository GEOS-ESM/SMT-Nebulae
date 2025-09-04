# Report: Corners removed from the D_SW

## Hypothesis

- Removed `copy_corners_x|y_nord` from `DelnFlux`
- Removed `copy_corners` from `FiniteVolumeTransport`

## Details

### C12

Backend: orch:dace:cpu_kfirst
Executions: 3000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.00434 [0.00436/ 0.00425 / 0.00582]

Backend: gt:cpu_kfirst
Executions: 3000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.00501 [0.00507/ 0.00485 / 0.0104]
  
Backend: gt:dace:cpu_kfirst
Executions: 3000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.00645 [0.0065/ 0.00617 / 0.0139]

### C24

_Reference Fortan_: 0.0116 - with corner code

Memory strides (IJK): [2263, 73, 1]
Backend: orch:dace:cpu_kfirst
Executions: 1000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.0139 [0.0143/ 0.0133 / 0.0284]

Memory strides (IJK): [2263, 73, 1]
Backend: gt:dace:cpu_kfirst
Executions: 1000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.0182 [0.0184/ 0.0177 / 0.0648]

Memory strides (IJK): [2263, 73, 1]
Backend: gt:cpu_kfirst
Executions: 1000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.0151 [0.0152/ 0.0144 / 0.025]
