# Merging the serial K as well as the parallel ones

Tile resolution: (24, 24, 72) w/ halo=3 (41472 grid points per compute domain)
Memory strides (IJK): [1131, 36, 0]
Executions: 1000.

**Backend: gt:dace:cpu_kfirst**

- _With only parallel map merged down_
    Timings in seconds (median [mean / min / max]):
        Topline: 0.162 [0.165s/ 0.15 / 0.235]

- _With all K looped merged down_
    Timings in seconds (median [mean / min / max]):
        Topline: 0.112 [0.113s/ 0.105 / 0.146]

**sBackend: orch:dace:cpu_kfirst**

- _With all K looped merged down_
    Timings in seconds (median [mean / min / max]):
        Topline: 0.0415 [0.0417s/ 0.0405 / 0.0543]
        Topline: 0.0322 [0.0334s/ 0.0307 / 0.0534]

- _With UW State & halo==0_
    Timings in seconds (median [mean / min / max]):
        Topline: 0.0667 [0.068s/ 0.0657 / 0.106]
