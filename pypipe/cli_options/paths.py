import click

from .click_support import GroupedOption


def common_paths(function):
    """Options for GEOS paths and execution location."""
    group = "Path Configuration"
    function = click.option(
        "--geos_dir",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        default="../model/install-release/bin",
        help="Location of desired GEOS install bin (relative to current directory)",
    )(function)
    function = click.option(
        "--top_exp_dir",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        default="./experiments",
        help="Top level experiments directory (relative to current directory). A dynamically named directory for this experiment will be generated under this directory",
    )(function)
    function = click.option(
        "--restart_setup_scripts_dir",
        "restart_setup_scripts_dir",
        cls=GroupedOption,
        help_group=group,
        default=None,
        help="Optional path to the NONHPC TBC scripts directory; prompts when omitted",
    )(function)
    function = click.option(
        "--execute_on",
        cls=GroupedOption,
        help_group=group,
        show_default=True,
        type=click.Choice(["compute", "local", "none"], case_sensitive=False),
        default="compute",
        help="Choose where to execute the model. 'compute' submits the job via sbatch, 'local' runs the model in the current terminal (ensure you are not on the head node before using this option), and 'none' sets up the experiment but does not execute",
    )(function)
    return function
