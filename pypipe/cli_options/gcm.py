import click

from .click_support import GroupedOption


def gcm_options(function):
    """GCM-specific options."""
    function = click.option(
        "--keep_original_restarts/--no_keep_original_restarts",
        cls=GroupedOption,
        help_group="GCM Specific Options",
        show_default=True,
        default=False,
        help="Exit immediately after the model run status, skipping subsequent restart and other post-processing.",
    )(function)
    return click.option(
        "--custom_restart",
        cls=GroupedOption,
        help_group="GCM Specific Options",
        show_default=True,
        is_flag=True,
        default=False,
        help="Use custom restarts instead of copying system-provided restarts. System stops after setup so files can be copied manually.",
    )(function)
