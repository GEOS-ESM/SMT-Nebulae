import os
import sys
import subprocess
import re
from run_helpers.template import PipelineStep
from run_helpers.run_gcm import GCMRunner
from run_helpers.setup import SetupDirectory


class EMIPPatchGCMRunJStep(PipelineStep):
    def validate_inputs(self, runner: GCMRunner):
        self.gcm_run_j_path = os.path.join(runner.exp_dir, "gcm_run.j")
        if not os.path.exists(self.gcm_run_j_path):
            raise FileNotFoundError("[GEOS PYTHON WRAPPER] gcm_run.j is missing.")

    def operate(self, runner: GCMRunner):
        with open(self.gcm_run_j_path, "r") as f:
            content = f.read()
        content = content.replace("while( $count < 4 )", f"while( $count < {runner.args.duration + 1} )")
        with open(self.gcm_run_j_path, "w") as f:
            f.write(content)
        return runner

    def validate_outputs(self, runner: GCMRunner):
        with open(self.gcm_run_j_path, "r") as f:
            if f"while( $count < {runner.args.duration + 1} )" not in f.read():
                raise RuntimeError("[GEOS PYTHON WRAPPER] Failed to patch EMIP loop count in gcm_run.j.")


class EMIPPatchSetupStep(PipelineStep):
    def validate_inputs(self, runner: GCMRunner):
        self.setup_path = os.path.join(runner.exp_dir, "gcm_emip.setup")
        if not os.path.exists(self.setup_path):
            raise FileNotFoundError("[GEOS PYTHON WRAPPER] gcm_emip.setup is missing.")

    def operate(self, runner: GCMRunner):
        with open(self.setup_path, "r") as f:
            content = f.read()

        pattern = r"set BYEARS = `seq (\d{4}) (\d{4})`"
        decades = re.findall(pattern, content)

        for start, end in decades:
            base_line = f"set BYEARS = `seq {start} {end}`"
            content = re.sub(rf"#+\s*{re.escape(base_line)}", base_line, content)
            if not (int(start) <= runner.args.start_year <= int(end)):
                content = content.replace(base_line, f"#{base_line}")

        if runner.args.season == "DJF":
            content = content.replace("set SEASON = 'DJF'", "#set SEASON = 'DJF'")
        elif runner.args.season == "JJA":
            content = content.replace("set SEASON = 'JJA'", "#set SEASON = 'JJA'")

        with open(self.setup_path, "w") as f:
            f.write(content)
        return runner

    def validate_outputs(self, runner: GCMRunner):
        with open(self.setup_path, "r") as f:
            content = f.read()
        if not re.search(r"^set BYEARS = `seq \d{4} \d{4}`", content, re.MULTILINE):
            raise RuntimeError(
                "[GEOS PYTHON WRAPPER] No valid active BYEARS configuration found in gcm_emip.setup after the file has been patched. "
                "Ensure your --start_year option is present in the original file."
            )


class EMIPExecuteStep(PipelineStep):
    def validate_inputs(self, runner: GCMRunner):
        if runner.args.execute_on == "local":
            sys.exit("[GEOS PYTHON WRAPPER] EMIP runs require execution on a compute node. Rerun with --execute_on compute")

    def operate(self, runner: GCMRunner):
        result = subprocess.run(["./gcm_emip.setup"], cwd=runner.exp_dir, env=runner.env, capture_output=True, text=True, check=True)
        sbatch_commands = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("sbatch")]

        for cmd in sbatch_commands:
            filename = cmd.split()[1]
            filepath = os.path.join(runner.exp_dir, filename)
            with open(filepath, "r") as f:
                content = f.read()
            _, _, date_suffix = filename.partition("gcm_run.j")
            content = content.replace("#SBATCH --output output.log", f"#SBATCH --output output{date_suffix}.log")
            content = content.replace("set USE_TSE_TMPDIR = TRUE", "set USE_TSE_TMPDIR = FALSE")
            with open(filepath, "w") as f:
                f.write(content)

        if runner.args.execute_on == "compute":
            for cmd in sbatch_commands:
                subprocess.run(cmd.split(), cwd=runner.exp_dir, env=runner.env, check=True)
        else:
            print("[GEOS PYTHON WRAPPER] EMIP setup complete, exiting without launching.")

        return runner

    def validate_outputs(self, runner: GCMRunner):
        pass


class EMIPRunner(GCMRunner):
    """Add-on to the basic GCMRunner for EMIP experiments."""

    def validate_inputs(self):
        # EMIP supplies its own restart files. As far as the system cares, these are custom restarts since they come in at runtime
        self.args.custom_restart = True

        # Call GCMRunner's validation for grid transformations and standard validation
        super().validate_inputs(validate_timing=False)

        # Additional EMIP validation
        if self.args.execute_on == "local":
            sys.exit("[GEOS PYTHON WRAPPER] EMIP runs require execution on a compute node. Rerun with --execute_on compute")

    def run(self) -> None:
        """Compose and execute the EMIP-specific pipeline."""
        SetupDirectory()(self)
        EMIPPatchGCMRunJStep()(self)
        EMIPPatchSetupStep()(self)
        EMIPExecuteStep()(self)
