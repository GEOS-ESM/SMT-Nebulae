import click

from .click_support import GroupedOption


def scm_options(function):
    """SCM-specific case and duration options."""
    function = click.option(
        "--duration_unit",
        cls=GroupedOption,
        help_group="Execution & Timing",
        show_default=True,
        type=click.Choice(["days", "months", "years"], case_sensitive=False),
        default="days",
        help="Unit for --duration. Only considered when `--duration` is supplied.",
    )(function)
    function = click.option(
        "--duration",
        cls=GroupedOption,
        help_group="Execution & Timing",
        type=int,
        help="Number of --duration_unit units to run (integer > 0).",
    )(function)
    function = click.option(
        "--case",
        cls=GroupedOption,
        help_group="SCM Specific Options",
        required=True,
        help="SCM case/experiment name.",
    )(function)
    return function
