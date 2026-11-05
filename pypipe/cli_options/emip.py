import click

from .click_support import GroupedOption


def emip_options(function):
    """EMIP-specific options."""
    function = click.option(
        "--season",
        cls=GroupedOption,
        help_group="EMIP Specific Options",
        required=True,
        type=click.Choice(["DJF", "JJA"], case_sensitive=False),
        help="Choose the starting season for the ensemble. DJF (Nov) or JJA (May).",
    )(function)
    function = click.option(
        "--start_year",
        cls=GroupedOption,
        help_group="EMIP Specific Options",
        required=True,
        type=click.Choice(["1985", "1995", "2005"]),
        help="Choose the set of 10 years for the ensemble, starting at the given year.",
    )(function)
    return function
