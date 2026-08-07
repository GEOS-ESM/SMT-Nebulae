import argparse
import os
import shutil
import subprocess
from run_helpers.config import MACHINE
from run_helpers.patcher import ScriptPatcher
from run_helpers.copy_restarts import CopyRestarts
import sys


class GCMRunner:
    """Manages directory prep, configuration patching, and execution of a GCM experiment."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.patcher = ScriptPatcher()
        self.env = os.environ.copy()

        self.rundir = os.getcwd()

        self.backend_arch = (self._derive_backend_arch() if len(self.args.pymodules) > 0 else "CPU").upper()
        backend_safe = self.args.backend.replace(":", "_") if self.args.backend else ""
        self.exp_name = self._build_experiment_name(backend_safe)

        self.exp_dir_root = os.path.join(self.rundir, args.exp_dir)
        self.exp_dir = os.path.join(self.exp_dir_root, self.exp_name)
        self.cache_dir = os.path.abspath(os.path.join(self.exp_dir, ".DSL_CACHE"))

        if not self.args.custom_restart:
            self.copy_restarts = CopyRestarts(args, self.exp_dir)

    def _derive_backend_arch(self) -> str:
        if "gpu" in self.args.backend.lower():
            return "GPU"
        if "cpu" in self.args.backend.lower():
            return "CPU"

        raise ValueError(f"Cannot determine hardware target from backend string: {self.args.backend}")

    def _build_experiment_name(self, backend_safe: str) -> str:
        py_suffix = ""
        if "fv3" in self.args.pymodules:
            py_suffix += "_pyFV3"
        if "gfdl1m" in self.args.pymodules:
            py_suffix += "_pyGFDL1M"
        if "gf2020" in self.args.pymodules:
            py_suffix += "_pyGF2020"
        if "uw" in self.args.pymodules:
            py_suffix += "_pyUW"
        if py_suffix and backend_safe:
            py_suffix = f"_{backend_safe.upper()}{py_suffix}"

        return f"{self.args.mode.upper()}_C{self.args.horz}_L{self.args.vert}_NX{self.args.nx}_NY{self.args.ny}{py_suffix}"

    def setup_directory(self) -> None:
        if os.path.isdir(self.exp_dir):
            shutil.rmtree(self.exp_dir)
        os.makedirs(self.exp_dir, exist_ok=True)

        microphysics = {"GFDL_1M": "GFDL", "BACM_1M": "BACM", "MGB2_2M": "MGB2"}.get(self.args.microphysics, self.args.microphysics)

        print(f"[GEOS PYTHON WRAPPER] Initializing experiment directory using Matt Thompson's create_expt.py.")
        subprocess.run(
            [
                "/home/mathomp4/bin/create_expt.py",
                self.exp_name,
                "--expdir",
                self.exp_dir_root,
                "--account",
                self.args.account,
                "--horz",
                f"c{self.args.horz}",
                "--vert",
                str(self.args.vert),
                "--gocart",
                self.args.aerosols,
                "--moist",
                microphysics,
                "--ocean",
                self.args.ocean,
                "--landbcs",
                self.args.land_bcs,
                "--landsurf",
                str(self.args.land_surf),
                "--model",
                self.args.processor,
                *(["--oserver"] if self.args.oserver else ["--nooserver"]),
                *(["--nonhydro"] if self.args.nonhydro else ["--hydro"]),
                *(["--dataatm"] if self.args.data_atmo else []),
                *(["--heartbeat", str(self.args.heartbeat)] if self.args.heartbeat else []),
            ],
            cwd=self.args.geos_dir,
            env=self.env,
            check=True,
        )
        print(f"[GEOS PYTHON WRAPPER] Finished running create_expt.py.")

    def validate_directory(self, with_restarts: bool) -> None:
        """Validates that the expected files and directories were created."""
        base_items = [
            "AGCM.rc",
            "CAP.rc",
            "archive",
            "forecasts",
            "fvcore_layout.rc",
            "GEOSgcm.x",
            "gcm_emip.setup",
            "gcm_run.j",
            "HISTORY.rc",
            "linkbcs",
            "logging.yaml",
            "plot",
            "post",
            "RC",
            "regress",
        ]

        restart_items = [
            "agcm_import_rst",
            "cap_restart",
            "catch_internal_rst",
            "fvcore_internal_rst",
            "lake_internal_rst",
            "landice_internal_rst",
            "moist_internal_rst",
            "openwater_internal_rst",
            "pchem_internal_rst",
            "seaicethermo_internal_rst",
        ]

        expected_items = base_items.copy()

        # if we are on the second check (after restarts are copied), we expect the restart files to be present
        if with_restarts and not self.args.custom_restart:
            expected_items.extend(restart_items)

        missing_items = []
        for item in expected_items:
            item_path = os.path.join(self.exp_dir, item)
            if not os.path.exists(item_path):
                missing_items.append(item)

        if not with_restarts:
            if missing_items:
                # failed on first check
                raise FileNotFoundError(
                    f"[GEOS PYTHON WRAPPER] Validation failed! Missing the following expected items in {self.exp_dir}: {', '.join(missing_items)}. "
                    "Something went wrong during the call to gcm_setup."
                )
            else:
                print(f"[GEOS PYTHON WRAPPER] Experiment directory initialized successfully.")

        elif with_restarts and not self.args.custom_restart:
            if missing_items:
                # failed on second check
                raise FileNotFoundError(
                    f"[GEOS PYTHON WRAPPER] Validation failed! Missing the following expected restart files in {self.exp_dir}: {', '.join(missing_items)}. "
                    "Something went wrong during the copying of restart files. Does the source directory have all the required files?"
                )
            else:
                print(f"[GEOS PYTHON WRAPPER] Restart files copied successfully.")

    def patch_files(self, patch_cap_rc: bool = True, patch_agcm_rc: bool = True, patch_gcm_run_j: bool = True) -> None:

        oserver_nodes = self.patcher.get_observer_nodes(os.path.join(self.exp_dir, "AGCM.rc"))

        if patch_cap_rc:
            # some attributes may not exist, ensure the have a fallback value
            duration = getattr(self.args, "duration", None)
            duration_unit = getattr(self.args, "duration_unit", None)
            end_date = getattr(self.args, "end_date", None)
            # patch and validate CAP.rc
            # only used for GCM and SCM (in progress)
            cap_rc = os.path.join(self.exp_dir, "CAP.rc")
            cap_restart = os.path.join(self.exp_dir, "cap_restart")

            computed_end_date = self.patcher.patch_cap_rc(
                cap_rc_path=cap_rc,
                cap_restart_path=cap_restart,
                custom_restart=self.args.custom_restart,
                job_segment=self.args.job_segment,
                num_segment=self.args.num_segment,
                duration=duration,
                duration_unit=duration_unit,
                end_date=end_date,
            )
            self.patcher.validate_cap_rc(
                cap_rc_path=cap_rc,
                job_segment=self.args.job_segment,
                num_segment=self.args.num_segment,
                duration=self.args.duration,
                end_date=self.args.end_date,
                expected_end_date=computed_end_date,
            )

        if patch_agcm_rc:
            # patch and validate AGCM.rc
            agcm_rc = os.path.join(self.exp_dir, "AGCM.rc")
            self.patcher.patch_agcm_rc(agcm_rc, self.args.nx, self.args.ny, self.args.pymodules)
            self.patcher.validate_agcm_rc(agcm_rc, self.args.nx, self.args.ny, self.args.pymodules)

        if patch_gcm_run_j:
            # grid decomposition for gcm_run.j
            tasks_per_node, required_nodes, process_per_gpu = self.patcher.compute_grid_decomposition(
                self.args.nx,
                self.args.ny,
                oserver_nodes,
                self.backend_arch,
                self.args.processor,
            )

            # make sbatch block for gcm_run.j
            job_name = os.path.basename(self.exp_dir)
            sbatch_block = self.patcher.build_sbatch_block(
                job_name=job_name,
                required_nodes=required_nodes,
                tasks_per_node=tasks_per_node,
                backend_arch=self.backend_arch,
                account=self.args.account,
                processor=self.args.processor,
            )

            # make DSL block for gcm_run.j
            opt_level = "3"
            layout = self.args.backend.rsplit(":", 1)[-1].upper() if self.args.backend else ""
            gh200_block, dsl_block = self.patcher.build_dsl_block(
                args=self.args,
                backend_arch=self.backend_arch,
                cache_dir=self.cache_dir,
                expdir=self.exp_dir,
                layout=layout,
                opt_level=opt_level,
                precision="32",
                process_per_gpu=process_per_gpu,
            )

            # patch and validate gcm_run.j
            gcm_run_j_path = os.path.join(self.exp_dir, "gcm_run.j")
            self.patcher.patch_gcm_run_j(
                gcm_run_j_path=gcm_run_j_path,
                pymodules=self.args.pymodules,
                tasks_per_node=tasks_per_node,
                sbatch_block=sbatch_block,
                gh200_block=gh200_block,
                dsl_block=dsl_block,
                backend_arch=self.backend_arch,
            )
            self.patcher.validate_gcm_run_j(gcm_run_j_path, self.args.pymodules, tasks_per_node, self.backend_arch)

    def execute(self) -> None:
        if self.args.custom_restart:
            sys.exit("[GEOS PYTHON WRAPPER] Completed experiment setup. Custom restarts specified, exiting before execution so they can be provided.")
        else:
            if self.args.execute_on == "compute":
                subprocess.run(["sbatch", "./gcm_run.j"], cwd=self.exp_dir, env=self.env, check=True)
            elif self.args.execute_on == "local":
                subprocess.run(["./gcm_run.j"], cwd=self.exp_dir, env=self.env, check=True)
            elif self.args.execute_on == "none":
                print("[GEOS PYTHON WRAPPER] Completed experiment setup. Exiting without execution as specified.")

    def run(self) -> None:
        self.setup_directory()
        self.validate_directory(with_restarts=False)
        if hasattr(self.args, "custom_restart") and not self.args.custom_restart:
            self.copy_restarts()
            self.validate_directory(with_restarts=True)
        self.patch_files()
        self.execute()
