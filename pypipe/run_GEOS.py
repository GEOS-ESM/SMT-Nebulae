"""Set up, prep, and submit a single GCM or SCM experiment, or an EMIP suite."""

import click
from run_helpers.run_gcm import GCMRunner
from run_helpers.run_emip import EMIPRunner
from run_helpers.run_scm import SCMRunner


def split_csv(ctx, param, value):
    result = []
    for v in value:
        result.extend(v.split(","))
    return tuple(result)


# ==============================================================================
# Custom Click Behavior
# ==============================================================================


class GroupedOption(click.Option):
    """Custom Option class that stores a help group name."""

    def __init__(self, *args, **kwargs):
        self.help_group = kwargs.pop("help_group", "Options")
        super().__init__(*args, **kwargs)


class CaseInsensitiveGroup(click.Group):
    """Allows subcommands (gcm/scm/emip) to be typed in any case."""

    def get_command(self, ctx, cmd_name):
        # Try exact match first (fast path)
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        # Fall back to case-insensitive match
        cmd_name_lower = cmd_name.lower()
        for name in self.list_commands(ctx):
            if name.lower() == cmd_name_lower:
                return click.Group.get_command(self, ctx, name)
        return None


class AllErrorsCommand(click.Command):
    """A Click Command that reports every missing/invalid option in one
    pass instead of stopping at the first one it finds.

    Also formats and groups the options in the help text.
    """

    def parse_args(self, ctx, args):
        parser = self.make_parser(ctx)
        opts, args, param_order = parser.parse_args(args=args)

        errors = []
        for param in click.core.iter_params_for_processing(param_order, self.get_params(ctx)):
            try:
                value, args = param.handle_parse_result(ctx, opts, args)
            except click.exceptions.MissingParameter:
                errors.append(self._format_missing(param, ctx))
            except click.exceptions.UsageError as e:
                errors.append(str(e))

        if errors:
            ctx.fail("\n".join(errors))

        if args and not ctx.allow_extra_args and not ctx.resilient_parsing:
            ctx.fail(f"Got unexpected extra argument{'s' if len(args) != 1 else ''} ({' '.join(map(str, args))})")

        ctx.args = args
        return args

    @staticmethod
    def _format_missing(param, ctx):
        hint = param.get_error_hint(ctx)
        msg = f"Missing option {hint}."
        if isinstance(param.type, click.Choice):
            choices = ",\n\t".join(param.type.choices)
            msg += f" Choose from:\n\t{choices}"
        return msg

    def format_options(self, ctx, formatter):
        """Override standard help output to group options by their help_group."""
        opts = {}
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                # Group using the assigned attribute, defaulting to "Options" (e.g., for --help)
                group_name = getattr(param, "help_group", "Options")
                opts.setdefault(group_name, []).append(rv)

        # Print each group as a distinct section
        for group_name, group_opts in opts.items():
            with formatter.section(group_name):
                formatter.write_dl(group_opts)


# ==============================================================================
# Argument Decorator Groups
# ==============================================================================


def common_paths(f):
    """Path Arguments: Point to GEOS bin, set exp dir, control execution location"""
    grp = "Path Configuration"
    f = click.option("--geos_dir", cls=GroupedOption, help_group=grp, show_default=True, default="../model/install-release/bin", help="Location of desired GEOS install")(
        f
    )
    f = click.option(
        "--exp_dir",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        default="./experiments",
        help="Location under which experiment directory will be generated (relative to current directory)",
    )(f)
    f = click.option(
        "--execute_on",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["compute", "local", "none"], case_sensitive=False),
        default="compute",
        help="Choose where to execute the model",
    )(f)
    return f


def common_python(f):
    """DSL Arguments: Toggle and control execution of DSL modules"""
    grp = "DSL Architecture"
    f = click.option(
        "--pymodules",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["gfdl1m", "uw", "gf2020", "fv3"], case_sensitive=False),
        multiple=True,
        default=[],
        callback=split_csv,
        help="Python DSL modules to enable (comma-separated or repeat flag)",
    )(f)
    f = click.option(
        "--backend",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        default="orch:dace:cpu:KJI",
        help="DSL backend string (considered only if pymodules are specified)",
    )(f)
    return f


def common_config(f):
    """Model Configuration Arguments"""
    grp = "Model Physics & Settings"
    f = click.option("--account", cls=GroupedOption, help_group=grp, default=None, help="Charge account to use when submitting jobs with SBATCH")(f)
    f = click.option(
        "--microphysics",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["BACK1M", "GFDL1M", "MGB22M"], case_sensitive=False),
        default="GFDL1M",
        help="Sets the microphysics scheme used in moist physics",
    )(f)
    f = click.option(
        "--ocean",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["o1", "o2", "o3", "MOM5", "MOM6", "MIT"], case_sensitive=False),
        default="o2",
        help="Sets the ocean model",
    )(f)
    f = click.option(
        "--aerosols",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["A", "C"], case_sensitive=False),
        default="C",
        help="Sets the aerosol scheme used by GOCART",
    )(f)
    f = click.option(
        "--emissions",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["AMIP", "OPS"], case_sensitive=False),
        default="AMIP",
        help="GOCART emissions choice",
    )(f)
    f = click.option("--oserver", cls=GroupedOption, help_group=grp, show_default=True, is_flag=True, default=False, help="Enable the IO server")(f)
    f = click.option("--nonhydro/--hydro", cls=GroupedOption, help_group=grp, show_default=True, default=True, help="Enable/disable nonhydrostatic dynamics")(f)
    f = click.option("--data_atmo/--no_data_atmo", cls=GroupedOption, help_group=grp, show_default=True, default=False, help="Use data atmosphere")(f)
    f = click.option(
        "--land_bcs",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["ICA", "NL3", "v12", "v14"], case_sensitive=False),
        default="v12",
        help="Land Surface BCs: Icarus (ICA), Icarus-NLv3 (NL3), or v12",
    )(f)
    f = click.option(
        "--land_surf",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["1", "2"]),
        default="1",
        help="Land Surface Model: Catchment (1) or CatchmentCN-CLM4.0 (2)",
    )(f)
    f = click.option(
        "--heartbeat", cls=GroupedOption, help_group=grp, default=None, help="Seconds to set heartbeat to (default: 450s for BACM, resolution-dependent otherwise)"
    )(f)
    f = click.option(
        "--processor",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["mil", "cas"], case_sensitive=False),
        default="mil",
        help="Target processor architecture. Milan (mil), Cascade Lake (cas)",
    )(f)
    return f


def common_grid(f):
    """Grid Control: Resolution and grid decomposition"""
    grp = "Grid Resolution"
    f = click.option("--horz", cls=GroupedOption, help_group=grp, required=True, help="Horizontal resolution (e.g. 48, 180, 360, 720)")(f)
    f = click.option("--vert", cls=GroupedOption, help_group=grp, required=True, help="Vertical resolution (e.g. 72, 131, 137, 181)")(f)
    f = click.option("--nx", cls=GroupedOption, help_group=grp, required=True, type=int, help="Number of MPI ranks in X")(f)
    f = click.option("--ny", cls=GroupedOption, help_group=grp, required=True, type=int, help="Number of MPI ranks in Y (will be multiplied by face count later)")(f)
    return f


def common_timing(f):
    """Timing Control for GCM"""
    grp = "Execution & Timing"
    f = click.option(
        "--end_date", cls=GroupedOption, help_group=grp, default=None, help="End date of model run in YYYYMMDDHHMMSS format. Mutually exclusive with --duration"
    )(f)
    f = click.option(
        "--job_segment", cls=GroupedOption, help_group=grp, default=None, help="JOB_SGMT length in YYYYMMDDHHMMSS format (default 00000010000000, i.e. 10 days)"
    )(f)
    f = click.option(
        "--job_time",
        cls=GroupedOption,
        help_group=grp,
        type=str,
        default="01:00:00",
        help="Wall time limit for each sbatch submission. Can be up to 12 hours. Format: HH:MM:SS",
    )(f)
    f = click.option("--num_segment", cls=GroupedOption, help_group=grp, default=None, type=int, help="Number of --job_segment periods to run per sbatch submission")(f)
    f = click.option(
        "--duration", cls=GroupedOption, help_group=grp, type=int, help="Number of --duration_unit units to run (integer > 0). Mutually exclusive with --end_date"
    )(f)
    f = click.option(
        "--duration_unit",
        cls=GroupedOption,
        help_group=grp,
        show_default=True,
        type=click.Choice(["days", "months", "years"], case_sensitive=False),
        default="days",
        help="Unit for --duration",
    )(f)
    return f


# ==============================================================================
# CLI Entry Points
# ==============================================================================

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(cls=CaseInsensitiveGroup, context_settings=CONTEXT_SETTINGS)
def run_GEOS():
    """Set up and submit GEOS experiments.

    This replaces run_GEOS.py and dynamically manages single GCM/SCM experiments
    or EMIP experiment suites.
    """
    pass


@run_GEOS.command(cls=AllErrorsCommand)
@common_grid
@common_timing
@common_paths
@common_python
@common_config
@click.option(
    "--custom_restart",
    cls=GroupedOption,
    help_group="GCM Specific Options",
    show_default=True,
    is_flag=True,
    default=False,
    help="Use custom restarts instead of copying from HUGEBCs. System stops after setup so files can be copied manually.",
)
def gcm(**kwargs):
    """Set up and submit a single GCM experiment."""
    kwargs["mode"] = "GCM"
    kwargs["land_surf"] = int(kwargs["land_surf"])
    runner = GCMRunner(**kwargs)
    runner.run()


@run_GEOS.command(cls=AllErrorsCommand)
@common_paths
@common_python
@click.option("--case", cls=GroupedOption, help_group="SCM Specific Options", required=True, help="SCM case/experiment name.")
@click.option("--duration", cls=GroupedOption, help_group="Execution & Timing", type=int, help="Number of --duration_unit units to run (integer > 0)")
@click.option(
    "--duration_unit",
    cls=GroupedOption,
    help_group="Execution & Timing",
    show_default=True,
    type=click.Choice(["days", "months", "years"], case_sensitive=False),
    default="days",
    help="Unit for --duration",
)
def scm(**kwargs):
    """XXXXX WORK IN PROGRESS - DOES NOT CURRENTLY WORK XXXXX

    Set up and submit a SCM experiment.
    """
    kwargs["mode"] = "SCM"
    runner = SCMRunner(**kwargs)
    runner.run()


@run_GEOS.command(cls=AllErrorsCommand)
@common_grid
@common_paths
@common_python
@common_config
@click.option(
    "--start_year",
    cls=GroupedOption,
    help_group="EMIP Specific Options",
    required=True,
    type=click.Choice(["1985", "1995", "2005"]),
    help="Choose the set of 10 years for the ensemble, starting at the given year.",
)
@click.option(
    "--duration", cls=GroupedOption, help_group="Execution & Timing", show_default=True, required=True, type=int, default=3, help="Number of months to run each member."
)
@click.option(
    "--season",
    cls=GroupedOption,
    help_group="EMIP Specific Options",
    required=True,
    type=click.Choice(["DJF", "JJA"], case_sensitive=False),
    help="Choose the starting season for the ensemble. DJF (Nov) or JJA (May).",
)
@click.option("--job_segment", cls=GroupedOption, help_group="Execution & Timing", help="JOB_SGMT length in YYYYMMDDHHMMSS format (default 00000010000000, i.e. 10 days)")
@click.option("--num_segment", cls=GroupedOption, help_group="Execution & Timing", type=int, help="Number of --job_segment periods to run per sbatch submission")
def emip(**kwargs):
    """Set up and submit an entire EMIP experiment suite."""
    kwargs["mode"] = "EMIP"
    kwargs["start_year"] = int(kwargs["start_year"])
    kwargs["land_surf"] = int(kwargs["land_surf"])
    runner = EMIPRunner(**kwargs)
    runner.run()


if __name__ == "__main__":
    run_GEOS()
