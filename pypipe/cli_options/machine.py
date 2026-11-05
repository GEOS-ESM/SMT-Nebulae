import click

from run_helpers import config as runtime_config

from .click_support import GroupedOption

MACHINE_CHOICES = ("DISCOVER", "NONHPC", "PRISM")
DEFAULT_MACHINE = runtime_config.MACHINE


def set_machine(ctx, param, value):
    runtime_config.MACHINE = value or DEFAULT_MACHINE
    return value


def common_machine(function):
    """Add the shared machine profile option."""
    return click.option(
        "--machine",
        cls=GroupedOption,
        help_group="Machine Configuration",
        type=click.Choice(MACHINE_CHOICES, case_sensitive=False),
        default=DEFAULT_MACHINE,
        callback=set_machine,
        expose_value=False,
        help="Machine profile for setup and scheduler behavior; defaults to NONHPC.",
    )(function)
