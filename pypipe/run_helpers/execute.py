import os
import subprocess
import sys
from run_helpers.template import PipelineStep


class ExecuteGCM(PipelineStep):
    def validate_inputs(self, runner):
        if runner.args.execute_on in ["compute", "local"] and not runner.args.custom_restart:
            if not os.path.exists(os.path.join(runner.exp_dir, "gcm_run.j")):
                raise FileNotFoundError("[GEOS PYTHON WRAPPER] gcm_run.j missing before execution. This file existed during previous patching step, but is now missing.")

    def operate(self, runner):
        if runner.args.custom_restart:
            print("[GEOS PYTHON WRAPPER] Completed setup. Custom restarts specified, exiting before execution.")
            return runner

        if runner.args.execute_on == "compute":
            subprocess.run(["sbatch", "./gcm_run.j"], cwd=runner.exp_dir, env=runner.env, check=True)
        elif runner.args.execute_on == "local":
            log_path = os.path.join(runner.exp_dir, "output.log")
            with open(log_path, "w") as log_file:
                # Use Popen to capture the output stream in real-time
                process = subprocess.Popen(["./gcm_run.j"], cwd=runner.exp_dir, env=runner.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

                # send output to both the terminal and the log file in real time
                for line in process.stdout:
                    sys.stdout.write(line)  # print to terminal
                    sys.stdout.flush()  # ensure it prints immediately
                    log_file.write(line)  # write to log file
                process.wait()
                # replicate the check=True behavior from subprocess.run
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, process.args)
        elif runner.args.execute_on == "none":
            print("[GEOS PYTHON WRAPPER] Completed setup. Exiting without execution.")
        return runner

    def validate_outputs(self, runner):
        pass  # Execution validation can be expanded here (e.g., checking SLURM status)
