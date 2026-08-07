import math
import os
import re
import sys
import argparse
from datetime import datetime

from sympy import content
from run_helpers.config import MACHINE, DurationHelper


class ScriptPatcher:
    """Handles text modifications and configuration patching for generated script files."""

    @staticmethod
    def compute_grid_decomposition(nx: int, ny: int, oserver_nodes: int, backend_arch: str, processor: str) -> tuple[int, int, float]:
        if MACHINE == "PRISM":
            tasks_per_node = 60
            required_nodes = math.ceil(int(nx) * int(ny) / tasks_per_node + oserver_nodes)
            process_per_gpu = tasks_per_node
        elif MACHINE == "DISCOVER" and backend_arch == "CPU":
            tasks_per_node = 46 if processor == "cas" else 126
            required_nodes = math.ceil(int(nx) * int(ny) / tasks_per_node + oserver_nodes)
            process_per_gpu = tasks_per_node / 4
        elif MACHINE == "DISCOVER":
            tasks_per_node = 46
            required_nodes = math.ceil(int(nx) * int(ny) / tasks_per_node + oserver_nodes)
            process_per_gpu = tasks_per_node / 4
        else:
            sys.exit(f"Error: unhandled combination MACHINE={MACHINE!r}, backend={backend_arch!r}")

        return tasks_per_node, required_nodes, process_per_gpu

    @staticmethod
    def get_observer_nodes(agcm_rc_path: str) -> int:
        """Extracts the number of observer nodes from the AGCM.rc file."""
        with open(agcm_rc_path, "r") as f:
            content = f.read()

        oserver_nodes = int(re.search(r"^\s*IOSERVER_NODES:\s*(\d+)", content, re.MULTILINE).group(1))
        return oserver_nodes

    def build_sbatch_block(self, job_name: str, required_nodes: int, tasks_per_node: int, backend_arch: str, account: str, processor: str, time: str = "12:00:00") -> str:
        if MACHINE == "PRISM":
            return "\n".join(
                [
                    f"#SBATCH --job-name={job_name}",
                    f"#SBATCH --account={account}",
                    f"#SBATCH --time={time}",
                    f"#SBATCH --nodes={required_nodes}",
                    f"#SBATCH --ntasks-per-node={tasks_per_node}",
                    "#SBATCH --partition=grace",
                    "#SBATCH --gpus-per-node=1",
                    "#SBATCH --exclusive",
                    "#SBATCH --output output.log",
                ]
            )
        elif MACHINE == "DISCOVER" and backend_arch == "CPU":
            lines = [
                f"#SBATCH --job-name={job_name}",
                f"#SBATCH --account={account}",
                f"#SBATCH --time={time}",
                f"#SBATCH --nodes={required_nodes}",
                f"#SBATCH --ntasks-per-node={tasks_per_node}",
                f"#SBATCH --constraint={processor}",
                "#SBATCH --exclusive",
                "#SBATCH --output output.log",
            ]
            return "\n".join(lines)
        elif MACHINE == "DISCOVER" and backend_arch == "GPU":
            return "\n".join(
                [
                    f"#SBATCH --job-name={job_name}",
                    f"#SBATCH --account={account}",
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
        else:
            sys.exit(f"Error: unhandled combination MACHINE={MACHINE!r}, backend={backend_arch!r}")

    def build_dsl_block(
        self,
        args: argparse.Namespace,
        backend_arch: str,
        cache_dir: str,
        expdir: str,
        layout: str,
        opt_level: str,
        precision: str,
        process_per_gpu: int,
    ) -> tuple[str, str]:
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
            f"   setenv GEOS_DSL_BACKEND {args.backend or ''}\n"
            f"   setenv GT_CACHE_ROOT {cache_dir}\n"
            f"   setenv GT4PY_COMPILE_OPT_LEVEL {opt_level}\n"
            "   setenv NDSL_CONSTANTS GEOS\n"
            f"   setenv NDSL_LAYOUT {layout}\n"
            f"   setenv NDSL_LITERAL_PRECISION {precision}\n"
            f"   setenv GEOS_DSL_PYFV3_BACKEND {(args.backend or '')[:-3]}IJK\n"
            "   setenv NDSL_LOGLEVEL DEBUG\n"
        )

        if backend_arch == "GPU":
            dsl_block += (
                f"   setenv CUPY_CACHE_DIR {expdir}/.CUPY_CACHE\n"
                "   setenv MPS_ON             1\n"
                f"   setenv PER_DEVICE_PROCESS {str(process_per_gpu)}\n"
                f"   setenv GPU_LAUNCHER_SH {gpu_mps_launcher_path}\n"
            )

        dsl_block += "endif\n"
        return gh200_block, dsl_block

    def patch_gcm_run_j(
        self,
        gcm_run_j_path: str,
        pymodules: list[str],
        tasks_per_node: int,
        sbatch_block: str | None,
        gh200_block: str,
        dsl_block: str,
        backend_arch: str,
    ):
        with open(gcm_run_j_path, "r") as f:
            content = f.read()

        use_dsl = "1" if len(pymodules) > 0 else "0"

        if sbatch_block is not None:
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

        if backend_arch == "GPU":
            content = content.replace(
                "$RUN_CMD $TOTAL_PES $GEOSEXE $IOSERVER_OPTIONS $IOSERVER_EXTRA", "$RUN_CMD $TOTAL_PES $GPU_LAUNCHER_SH $GEOSEXE $IOSERVER_OPTIONS $IOSERVER_EXTRA"
            )

        content = content.replace("exit $rc", " ")

        with open(gcm_run_j_path, "w") as f:
            f.write(content)

    def validate_gcm_run_j(self, gcm_run_j_path: str, pymodules: list[str], tasks_per_node: int, backend_arch: str) -> None:
        """Validates that the run script was patched correctly."""
        with open(gcm_run_j_path, "r") as f:
            content = f.read()

        missing_items = []
        # Check DSL flags and runner commands
        use_dsl = "1" if len(pymodules) > 0 else "0"
        if not re.search(rf"setenv USE_DSL {use_dsl}", content):
            missing_items.append("USE_DSL")
        if not re.search(r'setenv RUN_CMD "mpirun -np "', content):
            missing_items.append("RUN_CMD")

        # Check specific GPU launcher insertion
        if backend_arch == "GPU":
            if "$GPU_LAUNCHER_SH" not in content:
                missing_items.append("GPU_LAUNCHER_SH")

        if missing_items:
            raise ValueError(f"[GEOS PYTHON WRAPPER] Validation failed! Run script is missing expected patched values for: {', '.join(missing_items)}.")
        else:
            print(f"[GEOS PYTHON WRAPPER] Run script patched and validated successfully.")

    def patch_cap_rc(
        self,
        cap_rc_path: str,
        cap_restart_path: str,
        custom_restart: bool,
        job_segment: str | None,
        num_segment: int | None,
        duration: int | None,
        duration_unit: str,
        end_date: str | None,
    ) -> str | None:
        """Patches CAP.rc parameters adjusting segments, durations, and hard end dates

        Returns:
            The formatted END_DATE string ("YYYYMMDD HHMMSS") that was written to
            CAP.rc, or None if END_DATE was not modified.
        """
        if job_segment is None and num_segment is None and duration is None and end_date is None:
            print("[GEOS PYTHON WRAPPER] All timing options are unspecified; CAP.rc will remain unchanged.")
            return None

        with open(cap_rc_path, "r") as f:
            content = f.read()

        # Update JOB_SEGMENT and NUM_SEGMENT
        # job_segment is 14 chars (YYYYMMDDHHMMSS) from the parser; CAP.rc needs "YYYYMMDD HHMMSS"
        if job_segment is not None:
            job_sgmt_formatted = f"{job_segment[:8]} {job_segment[8:]}"
            content = re.sub(r"JOB_SGMT:\s+\d+\s+\d+", f"JOB_SGMT:     {job_sgmt_formatted}", content)

        if num_segment is not None:
            content = re.sub(r"NUM_SGMT:\s+\d+", f"NUM_SGMT:     {num_segment}", content)

        computed_end_date: str | None = None

        if end_date:
            end_date_formatted = f"{end_date[:8]} {end_date[8:]}"

            if not custom_restart:
                if not os.path.exists(cap_restart_path):
                    raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] cap_restart missing at {cap_restart_path}")

                with open(cap_restart_path, "r") as rf:
                    raw = rf.read().strip()

                cap_dt = datetime.strptime(raw, "%Y%m%d %H%M%S")
                end_dt = datetime.strptime(end_date_formatted, "%Y%m%d %H%M%S")

                if end_dt <= cap_dt:
                    raise ValueError(f"[GEOS PYTHON WRAPPER] --end_date ({end_date_formatted}) must be after the cap_restart date ({raw}).")

            content = re.sub(r"END_DATE:\s+\d{8}\s+\d{6}", f"END_DATE:     {end_date_formatted}", content)
            computed_end_date = end_date_formatted

        elif duration:
            if not os.path.exists(cap_restart_path):
                raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] cap_restart missing at {cap_restart_path}")

            with open(cap_restart_path, "r") as rf:
                raw = rf.read().strip()

            cap_dt = datetime.strptime(raw, "%Y%m%d %H%M%S")
            new_dt = DurationHelper.add_duration(cap_dt, duration, duration_unit)
            computed_end_date = new_dt.strftime("%Y%m%d %H%M%S")

            content = re.sub(r"END_DATE:\s+\d{8}\s+\d{6}", f"END_DATE:     {computed_end_date}", content)

        with open(cap_rc_path, "w") as f:
            f.write(content)

        return computed_end_date

    def validate_cap_rc(
        self,
        cap_rc_path: str,
        job_segment: str | None,
        num_segment: int | None,
        duration: int | None,
        end_date: str | None,
        expected_end_date: str | None,
    ) -> None:
        """Validates that CAP.rc was patched correctly"""
        if job_segment is None and num_segment is None and duration is None and end_date is None:
            # no changes were made, no need to validate
            return

        with open(cap_rc_path, "r") as f:
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
            if expected_end_date is None:
                raise ValueError(
                    "[GEOS PYTHON WRAPPER] Validation failed: duration/end_date was specified but expected_end_date was returned as None. "
                    "This indicates a problem in the patch_cap_rc logic."
                )
            if not re.search(rf"END_DATE:\s+{re.escape(expected_end_date)}", content):
                missing_items.append("END_DATE")

        if missing_items:
            raise ValueError(f"[GEOS PYTHON WRAPPER] Validation failed! CAP.rc is missing expected patched values for: {', '.join(missing_items)}.")
        else:
            print(f"[GEOS PYTHON WRAPPER] CAP.rc patched and validated successfully.")

    def patch_agcm_rc(self, agcm_rc_path: str, nx: int, ny: int, pymodules: list[str]) -> int:
        with open(agcm_rc_path, "r") as f:
            content = f.read()

        content = re.sub(r"NX:\s*\d+", f"NX: {nx}", content)
        content = re.sub(r"NY:\s*\d+", f"NY: {ny}", content)

        flags_map = {
            "uw": "USE_PYMOIST_UW",
            "gfdl1m": "USE_PYMOIST_GFDL1M",
            "gf2020": "USE_PYMOIST_GF2020",
            "fv3": "USE_PYFV3",
        }
        flags_to_add = [f"{flags_map[m]}: .TRUE." for m in pymodules if m in flags_map]
        if flags_to_add:
            # for now these flags are added at the top of the file, once an official DSL block exists they will go there instead
            content = "\n".join(flags_to_add) + "\n" + content

        with open(agcm_rc_path, "w") as f:
            f.write(content)

    def validate_agcm_rc(self, agcm_rc_path: str, nx: int, ny: int, pymodules: list[str]) -> None:
        """Validates that AGCM.rc was patched correctly."""
        with open(agcm_rc_path, "r") as f:
            content = f.read()

        missing_items = []
        # Check for core grid and physics overrides
        if not re.search(rf"NX:\s*{nx}", content):
            missing_items.append("NX")
        if not re.search(rf"NY:\s*{ny}", content):
            missing_items.append("NY")

        # Check for dynamically added Python modules
        flags_map = {
            "uw": "USE_PYMOIST_UW",
            "gfdl1m": "USE_PYMOIST_GFDL1M",
            "gf2020": "USE_PYMOIST_GF2020",
            "fv3": "USE_PYFV3",
        }
        for m in pymodules:
            if m in flags_map:
                if not re.search(rf"{flags_map[m]}:\s*\.TRUE\.", content):
                    missing_items.append(flags_map[m])

        if missing_items:
            raise ValueError(f"[GEOS PYTHON WRAPPER] Validation failed! AGCM.rc is missing expected patched values for: {', '.join(missing_items)}.")
        else:
            print(f"[GEOS PYTHON WRAPPER] AGCM.rc patched and validated successfully.")
