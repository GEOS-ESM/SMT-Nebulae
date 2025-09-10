# Microphysics

## C24

_32 bit_

Reference Fortran: 0.0772 [0.0782/0.0649/0.099]

Memory strides (IJK): [1131, 36, 0]
Backend: orch:dace:cpu_kfirst
Executions: 1000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.0646 [0.0654s/ 0.063 / 0.0909]

_64 bit_

Memory strides (IJK): [2263, 73, 1]
Backend: orch:dace:cpu_kfirst
Executions: 1000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.0919 [0.0955s/ 0.0888 / 0.162]

Memory strides (IJK): [31, 1, 961]
Backend: orch:dace:cpu
Executions: 1000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.0911 [0.0914s/ 0.09 / 0.111]

Memory strides (IJK): [31, 1, 961]
Backend: gt:dace:cpu
Executions: 1000.
Timings in seconds (median [mean / min / max]):
  Topline: 0.144 [0.145s/ 0.137 / 0.197]
