import re
import numpy as np


def _read_numbers(log_file) -> list:
    with open(log_file, "r") as f:
        numbers = []
        log_data = f.readlines()
        for line in log_data:
            if "gfdl_1m: time taken" in line:
                numbers_as_str = re.findall(
                    r"[+-]?\d+(?:[.]\d+)?(?:[Ee][+-]?\d+)?", line
                )
                numbers.append(float(numbers_as_str[-1]))
    return numbers


ranks: dict[int, list[float]] = {}
all_ranks = []

for rank in range(0, 6):
    log_path = f"/home/fgdeconi/work/git/smt/benchmarker/reference_fortran/logs_florian_machine/gfdl1m/rank.{rank}/stdout"
    ranks[rank] = _read_numbers(log_path)
    all_ranks.append(ranks[rank])

for rank in range(0, 6):
    ftn = ranks[rank]
    print(
        f"Mycrophysics (rank {rank}): {np.median(ftn):.3} [{np.mean(ftn):.3}/{np.min(ftn):.3}/{np.max(ftn):.3}]"
    )

print(
    f"Mycrophysics (all ranks + interface): "
    f"{np.median(all_ranks):.3} "
    f"[{np.mean(all_ranks):.3}/{np.min(all_ranks):.3}/{np.max(all_ranks):.3}]"
)
