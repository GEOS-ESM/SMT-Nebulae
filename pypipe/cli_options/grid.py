import click

from .click_support import GroupedOption


def common_grid(function):
    """Options for grid resolution and decomposition."""
    group = "Grid Resolution"
    function = click.option(
        "--horz",
        cls=GroupedOption,
        help_group=group,
        required=True,
        help="Horizontal resolution (e.g. 48, 180, 360, 720)",
    )(function)
    function = click.option(
        "--vert",
        cls=GroupedOption,
        help_group=group,
        required=True,
        help="Vertical resolution (e.g. 72, 131, 137, 181)",
    )(function)
    function = click.option(
        "--nx",
        cls=GroupedOption,
        help_group=group,
        required=True,
        type=int,
        help="Number of MPI ranks in X",
    )(function)
    function = click.option(
        "--ny",
        cls=GroupedOption,
        help_group=group,
        required=True,
        type=int,
        help="Number of MPI ranks in Y (will be multiplied by face count later)",
    )(function)
    return function
