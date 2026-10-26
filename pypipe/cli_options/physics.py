import click

from .click_support import GroupedOption


def common_config(function):
    """Options for model physics and settings."""
    group = "Model Physics & Settings"
    function = click.option(
        "--account",
        cls=GroupedOption,
        help_group=group,
        default=None,
        help="Charge account to use when submitting jobs with SBATCH",
    )(function)
    function = click.option(
        "--microphysics",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        type=click.Choice(["BACM1M", "GFDL1M", "MGB22M"], case_sensitive=False),
        default="GFDL1M",
        help="Sets the microphysics scheme used in moist physics",
    )(function)
    function = click.option(
        "--ocean",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        type=click.Choice(
            ["o1", "o2", "o3", "MOM5", "MOM6", "MIT"], case_sensitive=False
        ),
        default="o2",
        help="Sets the ocean model",
    )(function)
    function = click.option(
        "--aerosols",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        type=click.Choice(["A", "C"], case_sensitive=False),
        default="C",
        help="Sets the aerosol scheme used by GOCART",
    )(function)
    function = click.option(
        "--oserver/--nooserver",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        default=True,
        help="Enable the IO server",
    )(function)
    function = click.option(
        "--hydro/--nonhydro",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        default=True,
        help="Enable/disable hydrostatic dynamics",
    )(function)
    function = click.option(
        "--data_atmo/--no_data_atmo",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        default=False,
        help="Use data atmosphere",
    )(function)
    function = click.option(
        "--land_bcs",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        type=click.Choice(["ICA", "NL3", "v12", "v14"], case_sensitive=False),
        default="v12",
        help="Land Surface BCs: Icarus (ICA), Icarus-NLv3 (NL3), or v12",
    )(function)
    function = click.option(
        "--land_surf",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        type=click.Choice(["1", "2"]),
        default="1",
        help="Land Surface Model: Catchment (1) or CatchmentCN-CLM4.0 (2)",
    )(function)
    function = click.option(
        "--heartbeat",
        cls=GroupedOption,
        help_group=group,
        default=None,
        help="Seconds to set heartbeat to (default: 450s for BACM, resolution-dependent otherwise)",
    )(function)
    function = click.option(
        "--processor",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        type=click.Choice(["mil", "cas"], case_sensitive=False),
        default="mil",
        help="Target processor architecture. Milan (mil), Cascade Lake (cas)",
    )(function)
    return function
