import os
from datetime import datetime
from run_helpers.template import BaseRunner, ArgumentValidationError
from run_helpers.patch import PatchCAPRC, PatchAGCMRC, PatchGCMRUNJ
from run_helpers.setup import SetupDirectory, CopyRestarts
from run_helpers.execute import ExecuteGCM
from run_helpers.config import DurationHelper


class GCMRunner(BaseRunner):
    """Manages directory setup, patching, and execution of a GCM experiment."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # setup standard variables
        self.backend_arch = (self._derive_backend_arch() if len(getattr(self.args, "pymodules", [])) > 0 else "CPU").upper()
        self.exp_name = self._build_experiment_name()
        self.exp_dir_root = os.path.join(self.rundir, self.args.top_exp_dir)
        self.exp_dir = os.path.join(self.exp_dir_root, self.exp_name)
        self.cache_dir = os.path.abspath(os.path.join(self.exp_dir, ".DSL_CACHE"))

    def validate_inputs(self, validate_timing: bool = True):
        # execution validation
        if not getattr(self.args, "account", None):
            if self.args.execute_on == "compute":
                raise ArgumentValidationError("[GEOS PYTHON WRAPPER] Execution on compute node requires an --account.")
            if self.args.execute_on == "none":
                print("[GEOS PYTHON WRAPPER] WARNING: --account is not specified. Experiment will not run on compute nodes.")

        # timing validation
        if validate_timing:
            has_duration = getattr(self.args, "duration", None) is not None
            has_end_date = getattr(self.args, "end_date", None) is not None

            if not has_duration and not has_end_date:
                raise ArgumentValidationError("[GEOS PYTHON WRAPPER] Either --duration or --end_date must be specified.")
            if has_duration and has_end_date:
                raise ArgumentValidationError("[GEOS PYTHON WRAPPER] --duration and --end_date are mutually exclusive.")

            if getattr(self.args, "custom_restart", False) and has_duration:
                raise ArgumentValidationError(
                    "[GEOS PYTHON WRAPPER] --duration and --custom_restart cannot be used together. When using a custom restart, END_DATE in CAP.rc can only be set using "
                    "--end_date. A dynamic duration cannot be computed because the setup script will not have a cap_restart runtime."
                )

            if has_end_date:
                if len(str(self.args.end_date)) != 14:
                    raise ArgumentValidationError("[GEOS PYTHON WRAPPER] --end_date must be in YYYYMMDDHHMMSS format.")
                try:
                    datetime.strptime(str(self.args.end_date), r"%Y%m%d%H%M%S")
                except ValueError:
                    raise ArgumentValidationError("[GEOS PYTHON WRAPPER] --end_date must be in YYYYMMDDHHMMSS format.")

        if getattr(self.args, "job_segment", None) is not None:
            # ensure job_segment is a string of the correct length
            self.args.job_segment = str(self.args.job_segment)
            if len(self.args.job_segment) != 14:
                raise ArgumentValidationError("[GEOS PYTHON WRAPPER] --job_segment must be in YYYYMMDDHHMMSS format.")
        elif has_duration:
            # Construct a 14-char string using DurationHelper and strip the space
            dur_str = DurationHelper.build_duration_string(self.args.duration, getattr(self.args, "duration_unit", "days"))
            self.args.job_segment = dur_str.replace(" ", "")

    def _derive_backend_arch(self) -> str:
        if "gpu" in getattr(self.args, "backend", "cpu").lower():
            return "GPU"
        if "cpu" in getattr(self.args, "backend", "cpu").lower():
            return "CPU"
        raise ValueError(f"Cannot determine hardware target from backend string: {self.args.backend}")

    def _build_experiment_name(self) -> str:
        backend_safe = self.args.backend.replace(":", "_") if getattr(self.args, "backend", None) else ""
        py_suffix = ""
        pymodules = getattr(self.args, "pymodules", [])
        if "fv3" in pymodules:
            py_suffix += "_pyFV3"
        if "gfdl1m" in pymodules:
            py_suffix += "_pyGFDL1M"
        if "gf2020" in pymodules:
            py_suffix += "_pyGF2020"
        if "uw" in pymodules:
            py_suffix += "_pyUW"
        if py_suffix and backend_safe:
            py_suffix = f"_{backend_safe.upper()}{py_suffix}"

        return f"{self.args.mode.upper()}_C{self.args.horz}_L{self.args.vert}_NX{self.args.nx}_NY{self.args.ny}{py_suffix}"

    def run(self) -> None:
        """Execute the pipeline steps in sequence."""
        SetupDirectory()(self)
        if hasattr(self.args, "custom_restart") and not self.args.custom_restart:
            CopyRestarts()(self)

        PatchCAPRC()(self)
        PatchAGCMRC()(self)
        PatchGCMRUNJ()(self)
        ExecuteGCM()(self)
