from run_helpers.template import BaseRunner


class SCMRunner(BaseRunner):
    """Runner for handling Single Column Model (SCM) experiments."""

    def validate_inputs(self):
        if not getattr(self.args, "case", None):
            raise ValueError("[GEOS PYTHON WRAPPER] SCM runs require a --case to be specified.")

    def run(self) -> None:
        print(f"Setting up SCM experiment for case: {self.args.case}")
        # SCM specific setup routines go here
