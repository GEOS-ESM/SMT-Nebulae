import os
import shutil
import subprocess
import pathlib
from run_helpers.config import MACHINE
from run_helpers.template import PipelineStep


class SetupDirectory(PipelineStep):
    def validate_inputs(self, runner):
        if not os.path.isdir(runner.args.geos_dir):
            raise FileNotFoundError(f"GEOS dir {runner.args.geos_dir} not found.")

    def operate(self, runner):
        if os.path.isdir(runner.exp_dir):
            shutil.rmtree(runner.exp_dir)
        os.makedirs(runner.exp_dir, exist_ok=True)

        microphysics = {"GFDL1M": "GFDL", "BACM1M": "BACM", "MGB22M": "MGB2"}.get(runner.args.microphysics, runner.args.microphysics)

        print("[GEOS PYTHON WRAPPER] Initializing experiment directory...")

        if MACHINE == "DISCOVER":
            setup_script_location = "/home/mathomp4/bin"
        elif MACHINE == "PRISM":
            raise NotImplementedError("[GEOS PYTHON WRAPPER] NEED TO POINT TO MATT'S SETUP SCRIPT ON PRISM")
        elif MACHINE == "LOCAL":
            setup_script_location = input("[GEOS PYTHON WRAPPER] Enter the path to TBC scripts directory:")
            runner.args.processor = "not applicable"
        subprocess.run(
            [
                setup_script_location + "/create_expt.py",
                runner.exp_name,
                "--expdir",
                runner.exp_dir_root,
                "--account",
                runner.args.account,
                "--horz",
                f"c{runner.args.horz}",
                "--vert",
                str(runner.args.vert),
                "--gocart",
                runner.args.aerosols,
                "--moist",
                microphysics,
                "--ocean",
                runner.args.ocean,
                "--landbcs",
                runner.args.land_bcs,
                "--landsurf",
                str(runner.args.land_surf),
                "--model",
                runner.args.processor,
                *(["--oserver"] if runner.args.oserver else ["--nooserver"]),
                *(["--nonhydro"] if runner.args.nonhydro else ["--hydro"]),
                *(["--dataatm"] if runner.args.data_atmo else []),
                *(["--heartbeat", str(runner.args.heartbeat)] if runner.args.heartbeat else []),
            ],
            cwd=runner.args.geos_dir,
            env=runner.env,
            check=True,
        )
        if MACHINE == "LOCAL":
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
        missing = [item for item in base_items if not os.path.exists(os.path.join(runner.exp_dir, item))]
        if missing:
            raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] Experiment directory setup failed. Missing required items: {', '.join(missing)}")


class CopyRestarts(PipelineStep):
    def validate_inputs(self, runner):
        if runner.args.custom_restart:
            return

        ocean_map = {"o1": "Reynolds", "o2": "MERRA-2", "o3": "Ostia", "CS": "Ostia-CS", "MOM5": "MOM5", "MOM6": "MOM6", "MIT": "MIT"}
        ocean_name = ocean_map.get(runner.args.ocean)

        if MACHINE == "PRISM":
            self.restart_src = (
                f"/explore/nobackup/projects/geos-gpu/data/HugeBCs-GitV10/rs/nc4/{ocean_name}/c{runner.args.horz}-L{runner.args.vert}-{runner.args.land_bcs}"
            )
        elif MACHINE == "DISCOVER":
            self.restart_src = f"/discover/nobackup/mathomp4/Restarts-GitV12/nc4/{ocean_name}/c{runner.args.horz}-L{runner.args.vert}-{runner.args.land_bcs}"
        elif MACHINE == "LOCAL":
            self.restart_src = print("[GEOS PYTHON WRAPPER] Restart copying has already been handled by Tiny/HugeBC makeoneday scripts")
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
        if MACHINE == "LOCAL":
            return runner  # no copying needed for local machine, handled by makeoneday script
        if not runner.args.custom_restart:
            print(f"[GEOS PYTHON WRAPPER] Copying restart files from: {self.restart_src}")
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
        missing = [item for item in restart_items if not os.path.exists(os.path.join(runner.exp_dir, item))]
        if missing:
            raise FileNotFoundError(f"[GEOS PYTHON WRAPPER] Validation failed! Missing restarts: {', '.join(missing)}")
