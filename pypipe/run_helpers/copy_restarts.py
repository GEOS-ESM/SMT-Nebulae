import argparse
import pathlib
from run_helpers.config import MACHINE
import os
import shutil


class CopyRestarts:
    """Copy restart files from Matt Thompson's HugeBCs to an experiment directory"""

    def __init__(self, args: argparse.Namespace, exp_dir: str):
        """
        Ensure the desired restart path exists. If it doesn't, iterates through the path
        level-by-level to raise an error showing exactly where it broke.
        """
        self.exp_dir = exp_dir

        ocean_map = {
            "o1": "Reynolds",
            "o2": "MERRA-2",
            "o3": "Ostia",
            "CS": "Ostia-CS",
            "MOM5": "MOM5",
            "MOM6": "MOM6",
            "MIT": "MIT",
        }
        ocean_name = ocean_map.get(args.ocean)

        if MACHINE == "PRISM":
            self.restart_src = f"/explore/nobackup/projects/geos-gpu/data/HugeBCs-GitV10/rs/nc4/{ocean_name}/c{args.horz}-L{args.vert}-NL3"
        elif MACHINE == "DISCOVER":
            self.restart_src = f"/discover/nobackup/mathomp4/Restarts-GitV12/nc4/{ocean_name}/c{args.horz}-L{args.vert}-NL3"

        # verify the path
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

    def __call__(self) -> None:
        """Copy the restarts"""
        for fname in os.listdir(self.restart_src):
            shutil.copy2(os.path.join(self.restart_src, fname), self.exp_dir)
