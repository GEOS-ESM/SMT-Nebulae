"""Set up, prep, and submit a single GCM or SCM experiment, or an EMIP suite."""

from pathlib import Path

import click

from cli_options.click_support import AllErrorsCommand
from cli_options.config import config_option, read_config_values
from cli_options.dsl import common_python
from cli_options.emip import emip_options
from cli_options.gcm import gcm_options
from cli_options.grid import common_grid
from cli_options.machine import common_machine
from cli_options.paths import common_experiment_setup
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


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    help="YAML config containing a top-level mode (GCM, EMIP, or SCM).",
)
@click.option(
    "--link/--no_link",
    default=None,
    help="Override the config's executable link setting.",
)
@click.pass_context
def run_GEOS(ctx, config_path, link):
    """Set up and submit GEOS experiments.

    This replaces run_GEOS.py and dynamically manages single GCM/SCM experiments
    or EMIP experiment suites.
    """
    if ctx.invoked_subcommand is not None:
        if config_path is not None or link is not None:
            raise click.UsageError(
                "When specifying a mode command, put --config and --link after the command."
            )
        return

    if config_path is None:
        click.echo(ctx.get_help())
        return

    config_values = read_config_values(config_path, "config")
    mode = config_values.get("mode")
    if not isinstance(mode, str) or mode not in ("GCM", "EMIP", "SCM"):
        raise click.BadParameter(
            "a top-level mode: GCM, EMIP, or SCM is required when no command is given",
            param_hint="--config",
        )

    command = ctx.command.get_command(ctx, mode)
    child_args = ["--config", str(config_path)]
    if link is True:
        child_args.append("--link")
    elif link is False:
        child_args.append("--no_link")
    return command.main(
        args=child_args,
        prog_name=f"{ctx.command_path} {mode}",
        standalone_mode=False,
    )


@run_GEOS.command("GCM", cls=AllErrorsCommand)
@common_grid
@gcm_timing
@common_experiment_setup
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


@run_GEOS.command("SCM", cls=AllErrorsCommand)
@common_experiment_setup
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


@run_GEOS.command("EMIP", cls=AllErrorsCommand)
@common_grid
@emip_timing
@common_experiment_setup
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
