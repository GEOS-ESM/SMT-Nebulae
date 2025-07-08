from __future__ import annotations
from ndsl.logging import ndsl_log
import time


class TimedProgress:
    """Rough timer & log for major operations of DaCe build stack."""

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix
        self.label = []

    def __enter__(self) -> None:
        ndsl_log.info(f"{self.prefix} {self.label[-1]}...")
        self.start = time.perf_counter()

    def __exit__(self, _type, _val, _traceback) -> None:
        elapsed = time.perf_counter() - self.start
        ndsl_log.info(f"{self.prefix} {self.label.pop()}...{elapsed}s.")

    def __call__(self, label: str) -> TimedProgress:
        self.label.append(label)
        return self
