from __future__ import annotations

import math
import os
import re
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from run_helpers import config
from run_helpers.config import DurationHelper
from run_helpers.template import PipelineStep

# only executes when linter is doing typechecking, avoids circular import error
if TYPE_CHECKING:
    from run_helpers.run_gcm import GCMRunner


PYMODULE_FLAGS = {
    "uw": "USE_PYMOIST_UW",
    "gfdl1m": "USE_PYMOIST_GFDL1M",
    "gf2020": "USE_PYMOIST_GF2020",
    "fv3": "USE_PYFV3",
    "shoc": "USE_PYTURB_SHOC",
}


class PatchCAPRC(PipelineStep):
    """Patches CAP.rc parameters adjusting segments, durations, and hard end dates."""

    def validate_inputs(self, runner: GCMRunner):
        self.cap_rc_path = os.path.join(runner.exp_dir, "CAP.rc")
        self.cap_restart_path = os.path.join(runner.exp_dir, "cap_restart")

        if not os.path.exists(self.cap_rc_path):
            raise FileNotFoundError(
                f"[GEOS PYTHON WRAPPER] {self.cap_rc_path} not found."
            )

        # We only strictly need cap_restart if we are 1. computing durations or checking bounds and 2. not using a custom restart.
        if (
            (
                getattr(runner.args, "duration", None)
                or getattr(runner.args, "end_date", None)
            )
            and not runner.args.custom_restart
            and not os.path.exists(self.cap_restart_path)
        ):
            raise FileNotFoundError(
                f"[GEOS PYTHON WRAPPER] {self.cap_restart_path} not found. Required for duration/end_date validation."
            )

    def operate(self, runner: GCMRunner):
        self.computed_end_date = None

        job_segment = getattr(runner.args, "job_segment", None)
        num_segment = getattr(runner.args, "num_segment", None)
        duration = getattr(runner.args, "duration", None)
        duration_unit = getattr(runner.args, "duration_unit", None)
        end_date = getattr(runner.args, "end_date", None)

        if (
            job_segment is None
            and num_segment is None
            and duration is None
            and end_date is None
        ):
            print(
                "[GEOS PYTHON WRAPPER] All timing options are unspecified; CAP.rc will remain unchanged."
            )
            return runner

        with open(self.cap_rc_path, "r") as f:
            content = f.read()

        if job_segment is not None:
            job_segment_str = str(job_segment)
            job_sgmt_formatted = f"{job_segment_str[:8]} {job_segment_str[8:]}"
            content = re.sub(
                r"JOB_SGMT:\s+\d+\s+\d+", f"JOB_SGMT:     {job_sgmt_formatted}", content
            )

        if num_segment is not None:
            content = re.sub(
                r"NUM_SGMT:\s+\d+", f"NUM_SGMT:     {num_segment}", content
            )

        if end_date:
            end_date_formatted = f"{end_date[:8]} {end_date[8:]}"
            if not runner.args.custom_restart:
                with open(self.cap_restart_path, "r") as rf:
                    raw = rf.read().strip()
                cap_dt = datetime.strptime(raw, "%Y%m%d %H%M%S")
                end_dt = datetime.strptime(end_date_formatted, "%Y%m%d %H%M%S")
                if end_dt <= cap_dt:
                    raise ValueError(
                        f"[GEOS PYTHON WRAPPER] --end_date ({end_date_formatted}) must be after the cap_restart date ({raw})."
                    )

            content = re.sub(
                r"END_DATE:\s+\d{8}\s+\d{6}",
                f"END_DATE:     {end_date_formatted}",
                content,
            )
            self.computed_end_date = end_date_formatted

        elif duration:
            with open(self.cap_restart_path, "r") as rf:
                raw = rf.read().strip()
            cap_dt = datetime.strptime(raw, "%Y%m%d %H%M%S")
            new_dt = DurationHelper.add_duration(cap_dt, duration, duration_unit)
            self.computed_end_date = new_dt.strftime("%Y%m%d %H%M%S")
            content = re.sub(
                r"END_DATE:\s+\d{8}\s+\d{6}",
                f"END_DATE:     {self.computed_end_date}",
                content,
            )

        with open(self.cap_rc_path, "w") as f:
            f.write(content)

        return runner

    def validate_outputs(self, runner: GCMRunner):
        job_segment = getattr(runner.args, "job_segment", None)
        num_segment = getattr(runner.args, "num_segment", None)
        duration = getattr(runner.args, "duration", None)
        end_date = getattr(runner.args, "end_date", None)

        # if no modifications were requested, we don't need to validate anything
        if (
            job_segment is None
            and num_segment is None
            and duration is None
            and end_date is None
        ):
            return

        with open(self.cap_rc_path, "r") as f:
            content = f.read()

        missing_items = []
        if job_segment is not None:
            job_sgmt_formatted = f"{job_segment[:8]} {job_segment[8:]}"
            if not re.search(rf"JOB_SGMT:\s+{job_sgmt_formatted}", content):
                missing_items.append("JOB_SGMT")

        if num_segment is not None and not re.search(
            rf"NUM_SGMT:\s+{num_segment}", content
        ):
            missing_items.append("NUM_SGMT")

        if duration is not None or end_date is not None:
            if self.computed_end_date is None:
                raise ValueError(
                    "[GEOS PYTHON WRAPPER] Validation failed: expected_end_date was returned as None."
                )
            if not re.search(
                rf"END_DATE:\s+{re.escape(self.computed_end_date)}", content
            ):
                missing_items.append("END_DATE")

        if missing_items:
            raise RuntimeError(
                f"[GEOS PYTHON WRAPPER] CAP.rc validation failed! Missing expected values for: {', '.join(missing_items)}."
            )


class PatchAGCMRC(PipelineStep):
    def validate_inputs(self, runner: GCMRunner):
        self.agcm_rc_path = os.path.join(runner.exp_dir, "AGCM.rc")
        if not os.path.exists(self.agcm_rc_path):
            raise FileNotFoundError(
                f"[GEOS PYTHON WRAPPER] {self.agcm_rc_path} not found."
            )

    def operate(self, runner: GCMRunner):
        with open(self.agcm_rc_path, "r") as f:
            content = f.read()

        content = re.sub(r"NX:\s*\d+", f"NX: {runner.args.nx}", content)
        content = re.sub(r"NY:\s*\d+", f"NY: {runner.args.ny * 6}", content)

        flags_to_add = []
        for m in runner.args.pymodules:
            if m in PYMODULE_FLAGS:
                flag_name = PYMODULE_FLAGS[m]
                pattern = rf"{flag_name}:\s*\.(?:TRUE|FALSE)\."
                if re.search(pattern, content):
                    content = re.sub(pattern, f"{flag_name}: .TRUE.", content)
                else:
                    flags_to_add.append(f"{flag_name}: .TRUE.")

        if flags_to_add:
            content = "\n".join(flags_to_add) + "\n" + content

        with open(self.agcm_rc_path, "w") as f:
            f.write(content)

        return runner

    def validate_outputs(self, runner: GCMRunner):
        with open(self.agcm_rc_path, "r") as f:
            content = f.read()

        missing_items = []
        if not re.search(rf"NX:\s*{runner.args.nx}", content):
            missing_items.append("NX")
        if not re.search(rf"NY:\s*{runner.args.ny * 6}", content):
            missing_items.append("NY")

        for m in runner.args.pymodules:
            if m in PYMODULE_FLAGS and not re.search(
                rf"{PYMODULE_FLAGS[m]}:\s*\.TRUE\.", content
            ):
                missing_items.append(PYMODULE_FLAGS[m])

        if missing_items:
            raise RuntimeError(
                f"[GEOS PYTHON WRAPPER] AGCM.rc validation failed! Missing expected values for: {', '.join(missing_items)}."
            )


class PatchGCMRUNJ(PipelineStep):
    def validate_inputs(self, runner: GCMRunner):
        self.gcm_run_j_path = os.path.join(runner.exp_dir, "gcm_run.j")
        self.agcm_rc_path = os.path.join(runner.exp_dir, "AGCM.rc")
        if not os.path.exists(self.gcm_run_j_path):
            raise FileNotFoundError(
                f"[GEOS PYTHON WRAPPER] {self.gcm_run_j_path} not found."
            )
        if not os.path.exists(self.agcm_rc_path):
            raise FileNotFoundError(
                f"[GEOS PYTHON WRAPPER] {self.agcm_rc_path} not found."
            )

    def _get_observer_nodes(self) -> int:
        with open(self.agcm_rc_path, "r") as f:
            return int(
                re.search(r"^\s*IOSERVER_NODES:\s*(\d+)", f.read(), re.MULTILINE).group(
                    1
                )
            )

    def _compute_grid_decomposition(
        self, runner, oserver_nodes: int
    ) -> tuple[int, int, float]:
        if config.MACHINE == "PRISM":
            tasks_per_node = 60
            required_nodes = math.ceil(
                int(runner.args.nx) * int(runner.args.ny * 6) / tasks_per_node
                + oserver_nodes
            )
            process_per_gpu = tasks_per_node
        elif config.MACHINE == "DISCOVER" and runner.backend_arch == "CPU":
            tasks_per_node = 46 if runner.args.processor == "cas" else 126
            required_nodes = math.ceil(
                int(runner.args.nx) * int(runner.args.ny * 6) / tasks_per_node
                + oserver_nodes
            )
            process_per_gpu = tasks_per_node / 4
        elif config.MACHINE == "DISCOVER":
            tasks_per_node = 46
            required_nodes = math.ceil(
                int(runner.args.nx) * int(runner.args.ny * 6) / tasks_per_node
                + oserver_nodes
            )
            process_per_gpu = tasks_per_node / 4
        elif config.MACHINE == "NONHPC":
            # numbers don't matter for non-HPC runs, so just set everything to 1
            tasks_per_node = 1
            required_nodes = 1
            process_per_gpu = 1
        else:
            sys.exit(
                f"Error: unhandled combination MACHINE={config.MACHINE!r}, backend={runner.backend_arch!r}"
            )
        return tasks_per_node, required_nodes, process_per_gpu

    def _build_sbatch_block(
        self, runner, job_name: str, required_nodes: int, tasks_per_node: int, time: str
    ) -> str:
        if config.MACHINE == "PRISM":
            return "\n".join(
                [
                    f"#SBATCH --job-name={job_name}",
                    f"#SBATCH --account={runner.args.account}",
                    f"#SBATCH --time={time}",
                    f"#SBATCH --nodes={required_nodes}",
                    f"#SBATCH --ntasks-per-node={tasks_per_node}",
                    "#SBATCH --partition=grace",
                    "#SBATCH --gpus-per-node=1",
                    "#SBATCH --exclusive",
                    "#SBATCH --output output.log",
                    "#SBATCH --no-requeue",
                ]
            )
        elif config.MACHINE == "DISCOVER" and runner.backend_arch == "CPU":
            return "\n".join(
                [
                    f"#SBATCH --job-name={job_name}",
                    f"#SBATCH --account={runner.args.account}",
                    f"#SBATCH --time={time}",
                    f"#SBATCH --nodes={required_nodes}",
                    f"#SBATCH --ntasks-per-node={tasks_per_node}",
                    f"#SBATCH --constraint={runner.args.processor}",
                    "#SBATCH --exclusive",
                    "#SBATCH --output output.log",
                    "#SBATCH --no-requeue",
                ]
            )
        elif config.MACHINE == "DISCOVER" and runner.backend_arch == "GPU":
            return "\n".join(
                [
                    f"#SBATCH --job-name={job_name}",
                    f"#SBATCH --account={runner.args.account}",
                    f"#SBATCH --time={time}",
                    f"#SBATCH --nodes={required_nodes}",
                    f"#SBATCH --ntasks-per-node={tasks_per_node}",
                    "#SBATCH --constraint=rome",
                    "#SBATCH --partition=gpu_a100",
                    "#SBATCH --gpus-per-node=1",
                    "#SBATCH --mem-per-gpu=40G",
                    "#SBATCH --exclusive",
                    "#SBATCH --output output.log",
                    "#SBATCH --no-requeue",
                ]
            )
        elif config.MACHINE == "NONHPC":
            # operate functions needs some sort of string for sbatch block
            return "\n".join(
                [
                    f"#SBATCH --job-name={job_name}",
                    f"#SBATCH --account={runner.args.account}",
                    f"#SBATCH --time={time}",
                    f"#SBATCH --nodes={required_nodes}",
                    f"#SBATCH --ntasks-per-node={tasks_per_node}",
                    "#SBATCH --exclusive",
                    "#SBATCH --output output.log",
                ]
            )
        sys.exit(
            f"[GEOS PYTHON WRAPPER] Error: unhandled combination MACHINE={config.MACHINE!r}, backend={runner.backend_arch!r}"
        )

    @staticmethod
    def _set_dsl_environment(
        block: str, name: str, value: str, additions: list[str]
    ) -> str:
        """Update a template assignment, or queue a missing setting for the end."""
        pattern = re.compile(
            rf"^([ \t]*)setenv[ \t]+{re.escape(name)}\b[^\n]*$", re.MULTILINE
        )
        block, replacements = pattern.subn(
            lambda match: f"{match.group(1)}setenv {name} {value}", block
        )
        if replacements:
            return block

        additions.append(f"   setenv {name} {value}")
        return block

    @staticmethod
    def _remove_dsl_environment(block: str, name: str) -> str:
        return re.sub(
            rf"^[ \t]*setenv[ \t]+{re.escape(name)}\b[^\n]*(?:\n|$)",
            "",
            block,
            flags=re.MULTILINE,
        )

    def _patch_dsl_block(
        self, block: str, runner: GCMRunner, process_per_gpu: float
    ) -> str:
        gpu_mps_launcher_path = ""
        if config.MACHINE == "DISCOVER":
            gpu_mps_launcher_path = (
                "/discover/nobackup/projects/geosongpu/gpu_helpers/gpu_mps_launcher.sh"
            )
        elif config.MACHINE == "PRISM":
            gpu_mps_launcher_path = "/explore/nobackup/people/fgdeconi/work/git/geos_v11/experiments/gpu_mps_launcher.sh"

        pymodules = getattr(runner.args, "pymodules", [])
        additions = []
        if "fv3" in pymodules:
            # not 100% which level is correct, so just throw everything in
            fv3_pythonpath = (
                "${GEOSDIR}/../src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp/python/interface:"
                "${GEOSDIR}/../src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp/python/@pyFV3:"
            )
            fv3_pythonpath_pattern = re.compile(
                r"^([ \t]*)setenv[ \t]+PYTHONPATH[ \t]+[^\n]*@pyFV3:[^\n]*\$\{PYTHONPATH\}[^\n]*$",
                re.MULTILINE,
            )
            fv3_pythonpath_assignment = (
                f"setenv PYTHONPATH       {fv3_pythonpath}${{PYTHONPATH}}"
            )
            if fv3_pythonpath_pattern.search(block):
                block = fv3_pythonpath_pattern.sub(
                    lambda match: f"{match.group(1)}{fv3_pythonpath_assignment}",
                    block,
                )
            else:
                additions.extend(
                    [
                        "   # TEMPORARY SOLUTION - ONLY HERE UNTIL FV3 SOURCE IS PROPERLY COPIED INTO INSTALL",
                        f"   {fv3_pythonpath_assignment}",
                    ]
                )
        else:
            block = re.sub(
                r"^[ \t]*# TEMPORARY SOLUTION - ONLY HERE UNTIL FV3 SOURCE IS PROPERLY COPIED INTO INSTALL\n"
                r"[ \t]*setenv[ \t]+PYTHONPATH[ \t]+\$\{GEOSDIR\}/\.\./src/Components/[^\n]*@pyFV3:\$\{PYTHONPATH\}[ \t]*\n",
                "",
                block,
                flags=re.MULTILINE,
            )

        backend = runner.args.backend or ""
        environment = {
            "GEOS_DSL_BACKEND": backend,
            "GT_CACHE_ROOT": f"${{GEOSDIR}}/.DSL_CACHE/{backend.replace(':', '_')}",
            "GT4PY_COMPILE_OPT_LEVEL": "3",
            "NDSL_UNSAFE_MODE": "True",
            "NDSL_LITERAL_PRECISION": "32",
            "GEOS_DSL_PYFV3_BACKEND": backend,
        }
        if runner.backend_arch == "GPU":
            environment.update(
                {
                    "CUPY_CACHE_DIR": "${EXPDIR}/.CUPY_CACHE",
                    "MPS_ON": "1",
                    "PER_DEVICE_PROCESS": str(math.ceil(process_per_gpu)),
                    "GPU_LAUNCHER_SH": gpu_mps_launcher_path,
                }
            )

        for name, value in environment.items():
            block = self._set_dsl_environment(block, name, value, additions)
        block = self._remove_dsl_environment(block, "NDSL_LAYOUT")
        if runner.backend_arch != "GPU":
            for name in (
                "CUPY_CACHE_DIR",
                "MPS_ON",
                "PER_DEVICE_PROCESS",
                "GPU_LAUNCHER_SH",
            ):
                block = self._remove_dsl_environment(block, name)

        if config.MACHINE == "DISCOVER" and runner.backend_arch == "GPU":
            block = self._set_dsl_environment(block, "I_MPI_OFFLOAD", "1", additions)
            block = self._set_dsl_environment(
                block, "I_MPI_OFFLOAD_MODE", "cuda", additions
            )
        else:
            block = self._remove_dsl_environment(block, "I_MPI_OFFLOAD")
            block = self._remove_dsl_environment(block, "I_MPI_OFFLOAD_MODE")

        if additions:
            final_endif = list(re.finditer(r"^[ \t]*endif[ \t]*$", block, re.MULTILINE))
            if not final_endif:
                raise RuntimeError(
                    "[GEOS PYTHON WRAPPER] Could not find the end of the DSL configuration block."
                )
            insert_at = final_endif[-1].start()
            custom_arguments = "   # Custom arguments\n" + "\n".join(additions) + "\n"
            block = f"{block[:insert_at]}{custom_arguments}{block[insert_at:]}"

        return block

    def operate(self, runner: GCMRunner):
        oserver_nodes = self._get_observer_nodes()
        tasks_per_node, required_nodes, process_per_gpu = (
            self._compute_grid_decomposition(runner, oserver_nodes)
        )

        job_name = os.path.basename(runner.exp_dir)
        sbatch_block = self._build_sbatch_block(
            runner, job_name, required_nodes, tasks_per_node, runner.args.job_time
        )

        with open(self.gcm_run_j_path, "r") as f:
            content = f.read()

        use_dsl = "1" if len(runner.args.pymodules) > 0 else "0"

        batch_pattern = re.compile(
            r"(#{20,}[^\n]*\n[ \t]*#[^\n]*Batch Parameters for Run Job[^\n]*\n[ \t]*#{20,}[^\n]*\n).*?(#{20,}[^\n]*\n[ \t]*#[^\n]*System Settings)",
            re.DOTALL | re.IGNORECASE,
        )

        if batch_pattern.search(content):
            content = batch_pattern.sub(
                r"\g<1>\n" + sbatch_block + r"\n\n\g<2>", content
            )
        else:
            full_batch_block = (
                "#######################################################################\n"
                "#                     Batch Parameters for Run Job\n"
                "#######################################################################\n\n"
                f"{sbatch_block}\n"
            )
            if content.startswith("#!"):
                shebang_end = content.find("\n") + 1
                content = (
                    content[:shebang_end]
                    + "\n"
                    + full_batch_block
                    + content[shebang_end:]
                )
            else:
                content = full_batch_block + "\n" + content

        content = re.sub(
            r"^([ \t]*)(source\s+\$GEOSBIN/g5_modules\b.*)$",
            rf"\1setenv USE_DSL {use_dsl}\n\1\2",
            content,
            flags=re.MULTILINE,
        )

        if runner.args.pymodules:
            dsl_pattern = re.compile(
                r"[ \t]*#{20,}[^\n]*\n[ \t]*#[^\n]*DSL configuration[^\n]*\n[ \t]*#{20,}[^\n]*\n.*?(?=^[ \t]*#{20,}[^\n]*\n[ \t]*#[^\n]*Create Experiment Sub-Directories)",
                re.DOTALL | re.IGNORECASE | re.MULTILINE,
            )
            dsl_match = dsl_pattern.search(content)
            if dsl_match is None:
                raise RuntimeError(
                    "[GEOS PYTHON WRAPPER] Could not find the DSL configuration section in gcm_run.j. You are likely running a version of GEOS that was released before the DSL was introduced."
                )

            dsl_block = self._patch_dsl_block(
                dsl_match.group(), runner, process_per_gpu
            )
            content = (
                content[: dsl_match.start()] + dsl_block + content[dsl_match.end() :]
            )

            if config.MACHINE == "PRISM" and "GH200 MPI configuration" not in content:
                gh200_block = (
                    "#######################################################################\n"
                    "#                          GH200 MPI configuration\n"
                    "#######################################################################\n\n"
                    "source /explore/nobackup/projects/geos-gpu/OMPI_CPU_Infiniband.csh\n"
                    "setenv CUPY_ENABLE_UMP    1\n\n"
                )
                current_dsl_match = dsl_pattern.search(content)
                if current_dsl_match is not None:
                    insert_at = current_dsl_match.start()
                    content = content[:insert_at] + gh200_block + content[insert_at:]
        content = content.replace(
            'setenv RUN_CMD "$GEOSBIN/esma_mpirun -np "', 'setenv RUN_CMD "mpirun -np "'
        )

        # turn off TSE_TMPDIR
        content = content.replace(
            "set USE_TSE_TMPDIR = TRUE", "set USE_TSE_TMPDIR = FALSE"
        )

        if runner.backend_arch == "GPU":
            content = content.replace(
                "$RUN_CMD $TOTAL_PES $GEOSEXE $IOSERVER_OPTIONS $IOSERVER_EXTRA",
                "$RUN_CMD $TOTAL_PES $GPU_LAUNCHER_SH $GEOSEXE $IOSERVER_OPTIONS $IOSERVER_EXTRA",
            )

        content = content.replace("exit $rc", " ")

        with open(self.gcm_run_j_path, "w") as f:
            f.write(content)

        return runner

    def validate_outputs(self, runner: GCMRunner):
        with open(self.gcm_run_j_path, "r") as f:
            content = f.read()

        missing_items = []
        use_dsl = "1" if len(runner.args.pymodules) > 0 else "0"

        if not re.search(rf"setenv USE_DSL {use_dsl}", content):
            missing_items.append("USE_DSL")
        if not re.search(r'setenv RUN_CMD "mpirun -np "', content):
            missing_items.append("RUN_CMD")

        if runner.backend_arch == "GPU" and "$GPU_LAUNCHER_SH" not in content:
            missing_items.append("GPU_LAUNCHER_SH")

        if missing_items:
            raise RuntimeError(
                f"[GEOS PYTHON WRAPPER] gcm_run.j validation failed! Missing values for: {', '.join(missing_items)}."
            )
