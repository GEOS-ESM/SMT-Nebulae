# CPU Opt - Drilling into FVTP2D diffs between `gt` and `orch`

## Findings

The entire slowdown is carried by the `copy_corners_x|y_nord` stencils, which are 3x slower on `orch`.
The code difference comes down to the way the memory access are being computed, e.g.

In `gt`

```c++
{
    double gtIN__q_in_jp5 = q_in[((((__K * __i) * (__J + 10)) + (__K * (__j + 5))) + __k_0)];
    double gtOUT__q_out;

    ///////////////////
    // Tasklet code (he_140242045470416_0)
    gtOUT__q_out = gtIN__q_in_jp5;
    ///////////////////

    q_out[((((__J * __K) * __i) + (__K * __j)) + __k_0)] = gtOUT__q_out;
}
```

vs in `orch`:

```c++
{
    double gtIN__q_in_jp5 = q_in[((((2212 * __i) + (79 * __j)) + __k_0) + 395)];
    double gtOUT__q_out;

    ///////////////////
    // Tasklet code (he_140669466667024_0)
    gtOUT__q_out = gtIN__q_in_jp5;
    ///////////////////

    q_out[(((1422 * __i) + (79 * __j)) + __k_0)] = gtOUT__q_out;
}
```

Hypothesis is that the compiler fails to do unroll + predict (?)

## Timing details

Times in s, median [ average/min/max ]

__FVTP2D__

gt: 0.00156 [0.00163s/ 0.00144 / 0.00382]
orch: 0.00326 [0.0034s/ 0.00308 / 0.0115]

__No DelnFlux__

gt:   0.000752 [0.000782s/ 0.000709 / 0.00176]
orch: 0.00063 [0.000646s/ 0.000594 / 0.00142]

__Only DelnFlux__

0.000749 [0.000762s/ 0.000696 / 0.00149]
0.00193 [0.00199s/ 0.00182 / 0.0039]

__No DelnFluxNOSG__

gt:   2.98e-05 [3.34e-05s/ 2.62e-05 / 0.000675]
orch: 8.35e-06 [8.78e-06s/ 7.85e-06 / 0.000115]

__DelnFluxNOSG__

gt  : 0.000708 [0.000731s/ 0.000663 / 0.0016]
orch: 0.0019 [0.00199s/ 0.00176 / 0.00591]

__No `nmax` loop (In DelnFluxNOSG)__

gt  : 0.000274 [0.000291s/ 0.000256 / 0.000873]
orch: 0.000488 [0.000505s/ 0.000473 / 0.001]

__No copy corners (In DelnFluxNOSG)__

gt  : 0.000208 [0.000212s/ 0.000193 / 0.000423]
orch: 0.000146 [0.000148s/ 0.000137 / 0.000392]

__Corners  (In DelnFluxNOSG)__

gt  : 0.000511 [0.000531s/ 0.00049 / 0.00106]
orch: 0.00185 [0.0019s/ 0.00176 / 0.00404]
