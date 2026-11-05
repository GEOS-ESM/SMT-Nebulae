import click

from .click_support import GroupedOption


def gcm_options(function):
    """GCM-specific options."""
    return click.option(
        "--custom_restart",
        cls=GroupedOption,
        help_group="GCM Specific Options",
        show_default=True,
        is_flag=True,
        default=False,
        help="Use custom restarts instead of copying system-provided restarts. System stops after setup so files can be copied manually.",
    )(function)
