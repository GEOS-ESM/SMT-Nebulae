import re
import numpy as np


def _read_numbers(log_file) -> list:
    with open(log_file, "r") as f:
        numbers = []
        log_data = f.readlines()
        for line in log_data:
            if "fv_dynamics: time taken" in line:
                numbers_as_str = re.findall(r"\d+\.?\d*", line)
                numbers.append(float(numbers_as_str[-1]))
    return numbers


ranks: dict[int, list[float]] = {}

for rank in range(0, 6):
    log_path = f"/home/fgdeconi/work/git/smt/benchmarker/reference_fortran/logs_florian_machine/rank.{rank}/stdout"
    print(log_path)
    ranks[rank] = _read_numbers(log_path)

ftn = ranks[0]
print(
    f"Dynamics (read from rank 0): {np.median(ftn):.3} [{np.mean(ftn):.3}/{np.min(ftn):.3}/{np.max(ftn):.3}]"
)
