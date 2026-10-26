"""Set up, prep, and submit a single GCM or SCM experiment, or an EMIP suite."""

import click

from cli_options.click_support import AllErrorsCommand, CaseInsensitiveGroup
from cli_options.config import config_option
from cli_options.dsl import common_python
from cli_options.emip import emip_options
from cli_options.gcm import gcm_options
from cli_options.grid import common_grid
from cli_options.machine import common_machine
from cli_options.paths import common_paths
from cli_options.physics import common_config
from cli_options.scm import scm_options
from cli_options.timing import emip_timing, gcm_timing
from run_helpers.run_emip import EMIPRunner
from run_helpers.run_gcm import GCMRunner
from run_helpers.run_scm import SCMRunner

# ==============================================================================
# CLI Entry Points
# ==============================================================================

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(cls=CaseInsensitiveGroup, context_settings=CONTEXT_SETTINGS)
def run_GEOS():
    """Set up and submit GEOS experiments.

    This replaces run_GEOS.py and dynamically manages single GCM/SCM experiments
    or EMIP experiment suites.
    """


@run_GEOS.command(cls=AllErrorsCommand)
@common_grid
@gcm_timing
@common_paths
@common_machine
@common_python
@common_config
@gcm_options
@config_option
def gcm(**kwargs):
    """Set up and submit a single GCM experiment."""
    kwargs["mode"] = "GCM"
    kwargs["land_surf"] = int(kwargs["land_surf"])
    runner = GCMRunner(**kwargs)
    runner.run()


@run_GEOS.command(cls=AllErrorsCommand)
@common_paths
@common_machine
@common_python
@scm_options
@config_option
def scm(**kwargs):
    """XXXXX WORK IN PROGRESS - DOES NOT CURRENTLY WORK XXXXX

    Set up and submit a SCM experiment.
    """
    kwargs["mode"] = "SCM"
    runner = SCMRunner(**kwargs)
    runner.run()


@run_GEOS.command(cls=AllErrorsCommand)
@common_grid
@emip_timing
@common_paths
@common_machine
@common_python
@common_config
@emip_options
@config_option
def emip(**kwargs):
    """Set up and submit an entire EMIP experiment suite."""
    kwargs["mode"] = "EMIP"
    kwargs["start_year"] = int(kwargs["start_year"])
    kwargs["land_surf"] = int(kwargs["land_surf"])
    runner = EMIPRunner(**kwargs)
    runner.run()


if __name__ == "__main__":
    run_GEOS()
