"""Set up, prep, and submit a single GCM or SCM experiment, or an EMIP suite.

This is the main entry point for the pipeline.
"""

from run_helpers.parser import GEOSArgParser
from run_helpers.run_gcm import GCMRunner
from run_helpers.run_emip import EMIPRunner
from run_helpers.run_scm import SCMRunner


def main() -> None:
    args = GEOSArgParser().parse()

    runners = {
        "GCM": GCMRunner,
        "EMIP": EMIPRunner,
        "SCM": SCMRunner,
    }

    runner_cls = runners.get(args.mode)
    runner_cls(args).run()


if __name__ == "__main__":
    main()
