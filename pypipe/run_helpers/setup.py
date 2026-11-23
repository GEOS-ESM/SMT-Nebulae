import os
import pathlib
import shutil
import subprocess
import sys

from cli_options.config import write_config
from run_helpers import config
from run_helpers.gcm_setup import prepare_gcm_setup, run_gcm_setup
from run_helpers.template import PipelineStep


class SetupDirectory(PipelineStep):
    def validate_inputs(self, runner):
        script = os.path.abspath(os.path.join(runner.args.geos_dir, "bin", "gcm_setup"))
        if not os.path.isfile(script) or not os.access(script, os.X_OK):
            raise FileNotFoundError(
                f"GEOS setup script {script} is missing or not executable."
            )
        prepare_gcm_setup(runner)

    def operate(self, runner):
        # Recheck even when operate() is called directly, before removing anything.
        self.validate_inputs(runner)
        setup_script_location = None
        if config.MACHINE == "NONHPC":
            setup_script_location = os.path.abspath(
                runner.args.restart_setup_scripts_dir
                or input(
                    "[GEOS PYTHON WRAPPER] Enter the path to TBC scripts directory:"
                )
            )
            runner.args.restart_setup_scripts_dir = setup_script_location

        if os.path.isdir(runner.exp_dir):
            shutil.rmtree(runner.exp_dir)
        os.makedirs(runner.exp_dir, exist_ok=True)

        print("[GEOS PYTHON WRAPPER] Initializing experiment directory...")
        run_gcm_setup(runner)
        if config.MACHINE == "NONHPC":
            print("[GEOS PYTHON WRAPPER] Running makeoneday.bash...")
            try:
                subprocess.run(
                    [
                        setup_script_location + "/makeoneday.bash",
                        "noext",
                        "noresto",
                        "gitv12",
                    ],
                    cwd=runner.exp_dir,
                    env=runner.env,
                    check=True,
                )
                print("[GEOS PYTHON WRAPPER] makeoneday.bash completed successfully.")
            except subprocess.CalledProcessError as e:
                err = (e.stderr or "").strip()
                last_line = err.splitlines()[-1] if err else "(no stderr output)"
                print(err, file=sys.stderr)  # full child traceback, in one block
                raise SystemExit(
                    f"\n[GEOS PYTHON WRAPPER] makeoneday.bash failed (exit {e.returncode}): {last_line}\n"
                    f"[GEOS PYTHON WRAPPER]   cwd: {runner.args.geos_dir}"
                ) from None
        write_config(
            pathlib.Path(runner.exp_dir) / "pypipe.yaml",
            runner.args.mode,
            vars(runner.args),
        )
        return runner

    def validate_outputs(self, runner):
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
        missing = [
            item
            for item in base_items
            if not os.path.exists(os.path.join(runner.exp_dir, item))
        ]
        if missing:
            raise FileNotFoundError(
                f"[GEOS PYTHON WRAPPER] Experiment directory setup failed. Missing required items: {', '.join(missing)}"
            )


class CopyRestarts(PipelineStep):
    def validate_inputs(self, runner):
        if runner.args.custom_restart:
            return

        ocean_map = {
            "o1": "Reynolds",
            "o2": "MERRA-2",
            "o3": "Ostia",
            "CS": "Ostia-CS",
            "MOM5": "MOM5",
            "MOM6": "MOM6",
            "MIT": "MIT",
        }
        ocean_name = ocean_map.get(runner.args.ocean)

        if config.MACHINE == "PRISM":
            self.restart_src = f"/explore/nobackup/projects/geos-gpu/data/HugeBCs-GitV10/rs/nc4/{ocean_name}/c{runner.args.horz}-L{runner.args.vert}-{runner.args.land_bcs}"
        elif config.MACHINE == "DISCOVER":
            self.restart_src = f"/discover/nobackup/mathomp4/Restarts-GitV12/nc4/{ocean_name}/c{runner.args.horz}-L{runner.args.vert}-{runner.args.land_bcs}"
        elif config.MACHINE == "NONHPC":
            print(
                "[GEOS PYTHON WRAPPER] Restart copying has already been handled by Tiny/HugeBC makeoneday scripts"
            )
            return

        path = pathlib.Path(self.restart_src)

        # if path exists, all is good
        if path.exists():
            return

        # if path does not exist, find the problem
        current = pathlib.Path(path.anchor)  # root directory (e.g., '/')
        for part in path.parts[1:]:  # iterate through levels
            next_path = current / part
            if not next_path.exists():
                raise FileNotFoundError(
                    f"\n[GEOS PYTHON WRAPPER] Source path for restart data does not exist!\n"
                    f"[GEOS PYTHON WRAPPER]   Full path requested: {self.restart_src}\n"
                    f"[GEOS PYTHON WRAPPER]   Path breaks at: '{next_path}'\n"
                    f"[GEOS PYTHON WRAPPER]   The directory '{current}' exists, but '{part}' is missing inside it.\n"
                    f"[GEOS PYTHON WRAPPER]   Please choose another ocean/resolution combination, or enable custom restarts and provide them manually."
                )
            current = next_path

    def operate(self, runner):
        if config.MACHINE == "NONHPC":
            return runner  # no copying needed for non-HPC machine, handled by makeoneday script
        if not runner.args.custom_restart:
            print(
                f"[GEOS PYTHON WRAPPER] Copying restart files from: {self.restart_src}"
            )
            for fname in os.listdir(self.restart_src):
                shutil.copy2(os.path.join(self.restart_src, fname), runner.exp_dir)
        return runner

    def validate_outputs(self, runner):
        if runner.args.custom_restart:
            return

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
        missing = [
            item
            for item in restart_items
            if not os.path.exists(os.path.join(runner.exp_dir, item))
        ]
        if missing:
            raise FileNotFoundError(
                f"[GEOS PYTHON WRAPPER] Validation failed! Missing restarts: {', '.join(missing)}"
            )
