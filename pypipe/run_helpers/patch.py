from __future__ import annotations
import math
import os
import re
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from run_helpers.config import MACHINE, DurationHelper
from run_helpers.template import PipelineStep

# only executes when linter is doing typechecking, avoids circular import error
if TYPE_CHECKING:
    from run_helpers.run_gcm import GCMRunner


class PatchCAPRC(PipelineStep):
    """Patches CAP.rc parameters adjusting segments, durations, and hard end dates."""

    def validate_inputs(self, runner: GCMRunner):
        self.cap_rc_path = os.path.join(runner.exp_dir, "CAP.rc")
        self.cap_restart_path = os.path.join(runner.exp_dir, "cap_restart")

        if not os.path.exists(self.cap_rc_path):
            raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] {self.cap_rc_path} not found.")

        # We only strictly need cap_restart if we are 1. computing durations or checking bounds and 2. not using a custom restart.
        if (getattr(runner.args, "duration", None) or getattr(runner.args, "end_date", None)) and not runner.args.custom_restart:
            if not os.path.exists(self.cap_restart_path):
                raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] {self.cap_restart_path} not found. Required for duration/end_date validation.")

    def operate(self, runner: GCMRunner):
        self.computed_end_date = None

        job_segment = getattr(runner.args, "job_segment", None)
        num_segment = getattr(runner.args, "num_segment", None)
        duration = getattr(runner.args, "duration", None)
        duration_unit = getattr(runner.args, "duration_unit", None)
        end_date = getattr(runner.args, "end_date", None)

        if job_segment is None and num_segment is None and duration is None and end_date is None:
            print("[GEOS PYTHON WRAPPER] All timing options are unspecified; CAP.rc will remain unchanged.")
            return runner

        with open(self.cap_rc_path, "r") as f:
            content = f.read()

        if job_segment is not None:
            job_segment_str = str(job_segment)
            job_sgmt_formatted = f"{job_segment_str[:8]} {job_segment_str[8:]}"
            content = re.sub(r"JOB_SGMT:\s+\d+\s+\d+", f"JOB_SGMT:     {job_sgmt_formatted}", content)

        if num_segment is not None:
            content = re.sub(r"NUM_SGMT:\s+\d+", f"NUM_SGMT:     {num_segment}", content)

        if end_date:
            end_date_formatted = f"{end_date[:8]} {end_date[8:]}"
            if not runner.args.custom_restart:
                with open(self.cap_restart_path, "r") as rf:
                    raw = rf.read().strip()
                cap_dt = datetime.strptime(raw, "%Y%m%d %H%M%S")
                end_dt = datetime.strptime(end_date_formatted, "%Y%m%d %H%M%S")
                if end_dt <= cap_dt:
                    raise ValueError(f"[GEOS PYTHON WRAPPER] --end_date ({end_date_formatted}) must be after the cap_restart date ({raw}).")

            content = re.sub(r"END_DATE:\s+\d{8}\s+\d{6}", f"END_DATE:     {end_date_formatted}", content)
            self.computed_end_date = end_date_formatted

        elif duration:
            with open(self.cap_restart_path, "r") as rf:
                raw = rf.read().strip()
            cap_dt = datetime.strptime(raw, "%Y%m%d %H%M%S")
            new_dt = DurationHelper.add_duration(cap_dt, duration, duration_unit)
            self.computed_end_date = new_dt.strftime("%Y%m%d %H%M%S")
            content = re.sub(r"END_DATE:\s+\d{8}\s+\d{6}", f"END_DATE:     {self.computed_end_date}", content)

        with open(self.cap_rc_path, "w") as f:
            f.write(content)

        return runner

    def validate_outputs(self, runner: GCMRunner):
        job_segment = getattr(runner.args, "job_segment", None)
        num_segment = getattr(runner.args, "num_segment", None)
        duration = getattr(runner.args, "duration", None)
        end_date = getattr(runner.args, "end_date", None)

        # if no modifications were requested, we don't need to validate anything
        if job_segment is None and num_segment is None and duration is None and end_date is None:
            return

        with open(self.cap_rc_path, "r") as f:
            content = f.read()

        missing_items = []
        if job_segment is not None:
            job_sgmt_formatted = f"{job_segment[:8]} {job_segment[8:]}"
            if not re.search(rf"JOB_SGMT:\s+{job_sgmt_formatted}", content):
                missing_items.append("JOB_SGMT")

        if num_segment is not None:
            if not re.search(rf"NUM_SGMT:\s+{num_segment}", content):
                missing_items.append("NUM_SGMT")

        if duration is not None or end_date is not None:
            if self.computed_end_date is None:
                raise ValueError("[GEOS PYTHON WRAPPER] Validation failed: expected_end_date was returned as None.")
            if not re.search(rf"END_DATE:\s+{re.escape(self.computed_end_date)}", content):
                missing_items.append("END_DATE")

        if missing_items:
            raise RuntimeError(f"[GEOS PYTHON WRAPPER] CAP.rc validation failed! Missing expected values for: {', '.join(missing_items)}.")


class PatchAGCMRC(PipelineStep):
    def validate_inputs(self, runner: GCMRunner):
        self.agcm_rc_path = os.path.join(runner.exp_dir, "AGCM.rc")
        if not os.path.exists(self.agcm_rc_path):
            raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] {self.agcm_rc_path} not found.")

    def operate(self, runner: GCMRunner):
        with open(self.agcm_rc_path, "r") as f:
            content = f.read()

        content = re.sub(r"NX:\s*\d+", f"NX: {runner.args.nx}", content)
        content = re.sub(r"NY:\s*\d+", f"NY: {runner.args.ny*6}", content)

        flags_map = {"uw": "USE_PYMOIST_UW", "gfdl1m": "USE_PYMOIST_GFDL1M", "gf2020": "USE_PYMOIST_GF2020", "fv3": "USE_PYFV3"}
        flags_to_add = [f"{flags_map[m]}: .TRUE." for m in runner.args.pymodules if m in flags_map]

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
        if not re.search(rf"NY:\s*{runner.args.ny*6}", content):
            missing_items.append("NY")

        flags_map = {"uw": "USE_PYMOIST_UW", "gfdl1m": "USE_PYMOIST_GFDL1M", "gf2020": "USE_PYMOIST_GF2020", "fv3": "USE_PYFV3"}
        for m in runner.args.pymodules:
            if m in flags_map and not re.search(rf"{flags_map[m]}:\s*\.TRUE\.", content):
                missing_items.append(flags_map[m])

        if missing_items:
            raise RuntimeError(f"[GEOS PYTHON WRAPPER] AGCM.rc validation failed! Missing expected values for: {', '.join(missing_items)}.")


class PatchGCMRUNJ(PipelineStep):
    def validate_inputs(self, runner: GCMRunner):
        self.gcm_run_j_path = os.path.join(runner.exp_dir, "gcm_run.j")
        self.agcm_rc_path = os.path.join(runner.exp_dir, "AGCM.rc")
        if not os.path.exists(self.gcm_run_j_path):
            raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] {self.gcm_run_j_path} not found.")
        if not os.path.exists(self.agcm_rc_path):
            raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] {self.agcm_rc_path} not found.")

    def _get_observer_nodes(self) -> int:
        with open(self.agcm_rc_path, "r") as f:
            return int(re.search(r"^\s*IOSERVER_NODES:\s*(\d+)", f.read(), re.MULTILINE).group(1))

    def _compute_grid_decomposition(self, runner, oserver_nodes: int) -> tuple[int, int, float]:
        if MACHINE == "PRISM":
            tasks_per_node = 60
            required_nodes = math.ceil(int(runner.args.nx) * int(runner.args.ny * 6) / tasks_per_node + oserver_nodes)
            process_per_gpu = tasks_per_node
        elif MACHINE == "DISCOVER" and runner.backend_arch == "CPU":
            tasks_per_node = 46 if runner.args.processor == "cas" else 126
            required_nodes = math.ceil(int(runner.args.nx) * int(runner.args.ny * 6) / tasks_per_node + oserver_nodes)
            process_per_gpu = tasks_per_node / 4
        elif MACHINE == "DISCOVER":
            tasks_per_node = 46
            required_nodes = math.ceil(int(runner.args.nx) * int(runner.args.ny * 6) / tasks_per_node + oserver_nodes)
            process_per_gpu = tasks_per_node / 4
        else:
            sys.exit(f"Error: unhandled combination MACHINE={MACHINE!r}, backend={runner.backend_arch!r}")
        return tasks_per_node, required_nodes, process_per_gpu

    def _build_sbatch_block(self, runner, job_name: str, required_nodes: int, tasks_per_node: int, time: str) -> str:
        if MACHINE == "PRISM":
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
                ]
            )
        elif MACHINE == "DISCOVER" and runner.backend_arch == "CPU":
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
                ]
            )
        elif MACHINE == "DISCOVER" and runner.backend_arch == "GPU":
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
                ]
            )
        sys.exit(f"[GEOS PYTHON WRAPPER] Error: unhandled combination MACHINE={MACHINE!r}, backend={runner.backend_arch!r}")

    def _build_dsl_blocks(self, runner, process_per_gpu: float) -> tuple[str, str]:
        layout = runner.args.backend.rsplit(":", 1)[-1].upper() if runner.args.backend else ""
        opt_level = "3"
        precision = "32"

        gh200_block = ""
        if MACHINE == "PRISM":
            gh200_block = (
                "#######################################################################\n"
                "#                          GH200 MPI configuration\n"
                "#######################################################################\n\n"
                "source /explore/nobackup/projects/geos-gpu/OMPI_CPU_Infiniband.csh\n"
                "setenv CUPY_ENABLE_UMP    1\n\n"
            )

        gpu_mps_launcher_path = ""
        if MACHINE == "DISCOVER":
            gpu_mps_launcher_path = "/discover/nobackup/projects/geosongpu/gpu_helpers/gpu_mps_launcher.sh"
        elif MACHINE == "PRISM":
            gpu_mps_launcher_path = "/explore/nobackup/people/fgdeconi/work/git/geos_v11/experiments/gpu_mps_launcher.sh"

        dsl_block = (
            "#######################################################################\n"
            "#                          DSL configuration\n"
            "#######################################################################\n\n"
            "if ( $?USE_DSL ) then\n"
            "   if ( $?PYTHONPATH ) then\n"
            "      setenv PYTHONPATH       ${PYTHONPATH}:${GEOSDIR}/lib/Python/\n"
            "   else\n"
            "      setenv PYTHONPATH       ${GEOSDIR}/lib/Python/\n"
            "   endif\n\n"
            "   setenv PYTHONPATH ${GEOSDIR}/../src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp/pyMoist:${PYTHONPATH}\n"
            "   setenv PYTHONPATH ${GEOSDIR}/../src/Components/@GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSsuperdyn_GridComp/@FVdycoreCubed_GridComp/python/interface:${PYTHONPATH}\n\n"
            '   setenv PYTHONWARNINGS "ignore"\n'
            "   setenv FV3_DACEMODE BuildAndRun\n"
            f"   setenv GEOS_DSL_BACKEND {runner.args.backend or ''}\n"
            f"   setenv GT_CACHE_ROOT {runner.cache_dir}\n"
            f"   setenv GT4PY_COMPILE_OPT_LEVEL {opt_level}\n"
            "   setenv NDSL_CONSTANTS GEOS\n"
            f"   setenv NDSL_LAYOUT {layout}\n"
            f"   setenv NDSL_LITERAL_PRECISION {precision}\n"
            f"   setenv GEOS_DSL_PYFV3_BACKEND {(runner.args.backend or '')[:-3]}IJK\n"
            "   setenv NDSL_LOGLEVEL DEBUG\n"
        )

        if runner.backend_arch == "GPU":
            dsl_block += (
                f"   setenv CUPY_CACHE_DIR {runner.exp_dir}/.CUPY_CACHE\n"
                "   setenv MPS_ON             1\n"
                f"   setenv PER_DEVICE_PROCESS {str(math.ceil(process_per_gpu))}\n"
                f"   setenv GPU_LAUNCHER_SH {gpu_mps_launcher_path}\n"
            )

        dsl_block += "endif\n"
        return gh200_block, dsl_block

    def operate(self, runner: GCMRunner):
        oserver_nodes = self._get_observer_nodes()
        tasks_per_node, required_nodes, process_per_gpu = self._compute_grid_decomposition(runner, oserver_nodes)

        job_name = os.path.basename(runner.exp_dir)
        sbatch_block = self._build_sbatch_block(runner, job_name, required_nodes, tasks_per_node, runner.args.job_time)
        gh200_block, dsl_block = self._build_dsl_blocks(runner, process_per_gpu)

        with open(self.gcm_run_j_path, "r") as f:
            content = f.read()

        use_dsl = "1" if len(runner.args.pymodules) > 0 else "0"

        batch_pattern = re.compile(
            r"(#{20,}[^\n]*\n[ \t]*#[^\n]*Batch Parameters for Run Job[^\n]*\n[ \t]*#{20,}[^\n]*\n).*?(#{20,}[^\n]*\n[ \t]*#[^\n]*System Settings)",
            re.DOTALL | re.IGNORECASE,
        )

        if batch_pattern.search(content):
            content = batch_pattern.sub(r"\g<1>\n" + sbatch_block + r"\n\n\g<2>", content)
        else:
            full_batch_block = (
                "#######################################################################\n"
                "#                     Batch Parameters for Run Job\n"
                "#######################################################################\n\n"
                f"{sbatch_block}\n"
            )
            if content.startswith("#!"):
                shebang_end = content.find("\n") + 1
                content = content[:shebang_end] + "\n" + full_batch_block + content[shebang_end:]
            else:
                content = full_batch_block + "\n" + content

        content = re.sub(
            r"^([ \t]*)(source\s+\$GEOSBIN/g5_modules\b.*)$",
            rf"\1setenv USE_DSL {use_dsl}\n\1\2",
            content,
            flags=re.MULTILINE,
        )

        dsl_pattern = re.compile(
            r"#{20,}[^\n]*\n[ \t]*#[^\n]*DSL configuration[^\n]*\n[ \t]*#{20,}[^\n]*\n.*?(?=\n[ \t]*#{20,}[^\n]*\n[ \t]*#[^\n]*Create Experiment Sub-Directories)",
            re.DOTALL | re.IGNORECASE,
        )
        content = dsl_pattern.sub(gh200_block + dsl_block, content)
        content = content.replace('setenv RUN_CMD "$GEOSBIN/esma_mpirun -np "', 'setenv RUN_CMD "mpirun -np "')

        if runner.backend_arch == "GPU":
            content = content.replace(
                "$RUN_CMD $TOTAL_PES $GEOSEXE $IOSERVER_OPTIONS $IOSERVER_EXTRA", "$RUN_CMD $TOTAL_PES $GPU_LAUNCHER_SH $GEOSEXE $IOSERVER_OPTIONS $IOSERVER_EXTRA"
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

        if runner.backend_arch == "GPU":
            if "$GPU_LAUNCHER_SH" not in content:
                missing_items.append("GPU_LAUNCHER_SH")

        if missing_items:
            raise RuntimeError(f"[GEOS PYTHON WRAPPER] gcm_run.j validation failed! Missing values for: {', '.join(missing_items)}.")
