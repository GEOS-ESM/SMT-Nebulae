import click

from .click_support import GroupedOption


def common_timing(function, help_group="Execution & Timing"):
    """Shared job timing controls for GCM and EMIP."""
    function = click.option(
        "--job_segment",
        cls=GroupedOption,
        help_group=help_group,
        default=None,
        help="JOB_SGMT length in YYYYMMDDHHMMSS format (uses GEOS default)",
    )(function)
    function = click.option(
        "--job_time",
        cls=GroupedOption,
        help_group=help_group,
        type=str,
        default="01:00:00",
        help="Wall time limit for each sbatch submission. Can be up to 12 hours. Format: HH:MM:SS",
    )(function)
    function = click.option(
        "--num_segment",
        cls=GroupedOption,
        help_group=help_group,
        default=None,
        type=int,
        help="Number of --job_segment periods to run per sbatch submission (uses GEOS default)",
    )(function)
    return function


def gcm_timing(function):
    """Timing options for GCM runs."""
    group = "Execution & Timing"
    function = common_timing(function, help_group=group)
    function = click.option(
        "--end_date",
        cls=GroupedOption,
        help_group=group,
        default=None,
        help="End date of model run in YYYYMMDDHHMMSS format. Mutually exclusive with --duration",
    )(function)
    function = click.option(
        "--duration",
        cls=GroupedOption,
        help_group=group,
        default=None,
        type=int,
        help="Number of --duration_unit units to run (integer > 0). Mutually exclusive with --end_date",
    )(function)
    function = click.option(
        "--duration_unit",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        type=click.Choice(["days", "months", "years"], case_sensitive=False),
        default="days",
        help="Unit for --duration. Only considered when `--duration` is supplied.",
    )(function)
    return function


def emip_timing(function):
    """Timing options for EMIP ensembles."""
    function = common_timing(function, help_group="EMIP Timing")
    function = click.option(
        "--duration",
        cls=GroupedOption,
        help_group="EMIP Timing",
        show_default=True,
        required=True,
        type=int,
        default=3,
        help="Number of months to run each member.",
    )(function)
    return function
