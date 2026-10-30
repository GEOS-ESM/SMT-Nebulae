import click

from .click_support import GroupedOption

VALID_MODULES = ["gfdl1m", "uw", "gf2020", "fv3"]


def split_csv(ctx, param, value):
    result = []
    for item_group in value:
        result.extend(item.strip() for item in item_group.split(",") if item.strip())
    for item in result:
        if item.lower() not in VALID_MODULES:
            raise click.BadParameter(
                f"'{item}' is not one of {', '.join(VALID_MODULES)}"
            )
    return tuple(result)


def common_python(function):
    """Options for enabling and configuring DSL modules."""
    group = "DSL Architecture"
    function = click.option(
        "--pymodules",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        multiple=True,
        default=[],
        callback=split_csv,
        help="Python DSL modules to enable (comma-separated or repeat flag)",
    )(function)
    function = click.option(
        "--backend",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        default="orch:dace:cpu:KJI",
        help="DSL backend string (considered only if pymodules are specified). Common options: orch:dace:cpu:KJI, orch:dace:gpu:KJI, st:dace:cpu:KJI, st:dace:gpu:KJI",
    )(function)
    return function
