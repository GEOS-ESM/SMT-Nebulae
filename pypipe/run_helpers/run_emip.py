import argparse
import os
import sys
import subprocess
from run_helpers.run_gcm import GCMRunner
import re


class EMIPRunner(GCMRunner):
    """Runner for handling multi-job EMIP experiment suites."""

    def emip_patch_gcm_run_j(self) -> None:
        """Patch the gcm_run.j script to use the correct microphysics scheme."""
        gcm_run_j_path = os.path.join(self.exp_dir, "gcm_run.j")
        with open(gcm_run_j_path, "r") as f:
            content = f.read()

        content = content.replace("while( $count < 4 )", f"while( $count < {self.args.duration + 1} )")

        with open(gcm_run_j_path, "w") as f:
            f.write(content)

    def patch_gcm_emip_setup(self) -> None:
        """Patch the gcm_emip.setup script to use the correct microphysics scheme."""
        setup_path = os.path.join(self.exp_dir, "gcm_emip.setup")
        with open(setup_path, "r") as f:
            content = f.read()

        # define the expected pattern
        pattern = r"set BYEARS = `seq (\d{4}) (\d{4})`"
        # find all instances of the pattern
        decades = re.findall(pattern, content)

        for start, end in decades:
            base_line = f"set BYEARS = `seq {start} {end}`"

            # ensure a standard starting point by removing any leading comments
            content = re.sub(rf"#+\s*{re.escape(base_line)}", base_line, content)

            if not (int(start) <= self.args.start_year <= int(end)):
                content = content.replace(base_line, f"#{base_line}")

        if self.args.season == "DJF":
            content = content.replace("set SEASON = 'DJF'", "#set SEASON = 'DJF'")
        elif self.args.season == "JJA":
            content = content.replace("set SEASON = 'JJA'", "#set SEASON = 'JJA'")

        with open(setup_path, "w") as f:
            f.write(content)

    def execute(self) -> None:
        # call gcm_emip.setup to generate EMIP variant of gcm_run.j
        result = subprocess.run(["./gcm_emip.setup"], cwd=self.exp_dir, env=self.env, capture_output=True, text=True, check=True)

        # extract sbatch commands from the output of gcm_emip.setup
        sbatch_commands = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("sbatch")]

        # update the output log file name so that each sbatch submission has a unique log file
        for cmd in sbatch_commands:
            filename = cmd.split()[1]
            filepath = os.path.join(self.exp_dir, filename)

            with open(filepath, "r") as f:
                content = f.read()

            _, _, date_suffix = filename.partition("gcm_run.j")
            content = content.replace("#SBATCH --output output.log", f"#SBATCH --output output{date_suffix}.log")
            content = content.replace("set USE_TSE_TMPDIR = TRUE", "set USE_TSE_TMPDIR = FALSE")

            with open(filepath, "w") as f:
                f.write(content)

        # launch, if requested
        if self.args.execute_on == "compute":
            for cmd in sbatch_commands:
                subprocess.run(cmd.split(), cwd=self.exp_dir, env=self.env, check=True)
        elif self.args.execute_on == "local":
            sys.exit("EMIP runs require execution on a compute node. Rerun with --execute_on compute")
        else:
            print("EMIP setup complete, exiting without launching.")

    def run(self) -> None:
        self.setup_directory()
        self.validate_directory(with_restarts=False)
        self.patch_files(patch_cap_rc=False)
        self.emip_patch_gcm_run_j()
        self.patch_gcm_emip_setup()
        self.execute()
