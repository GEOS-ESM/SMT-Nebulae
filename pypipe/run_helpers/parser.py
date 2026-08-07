import argparse
from datetime import datetime
from run_helpers.config import DURATION_UNIT_FIELD_MAX


class _CaseInsensitiveSubParsersAction(argparse._SubParsersAction):
    """Subparsers action that matches the subcommand name case-insensitively."""

    def __call__(self, parser, namespace, values, option_string=None):
        typed_name, *rest = values
        for registered_name in self._name_parser_map:
            if registered_name.lower() == typed_name.lower():
                values = [registered_name, *rest]
                break
        super().__call__(parser, namespace, values, option_string)


class _CaseInsensitiveArgumentParser(argparse.ArgumentParser):
    """ArgumentParser whose 'mode' subcommand choice is validated case-insensitively."""

    def _check_value(self, action, value):
        if isinstance(action, argparse._SubParsersAction) and isinstance(value, str):
            if any(value.lower() == choice.lower() for choice in action.choices):
                return
        super()._check_value(action, value)


class ArgumentValidationError(ValueError):
    """Raised when cross-argument validation fails."""

    pass


class GEOSArgParser:
    """Class to handle argument setup, parsing, and validation for GEOS experiments."""

    def __init__(self):
        self.parser = self._build_parser()

    @staticmethod
    def add_arg(target, *flags, **kwargs) -> argparse.Action:
        """Thin wrapper around `.add_argument()` that keeps help text in sync."""
        help_text = kwargs.get("help")
        required = kwargs.get("required", False)
        default = kwargs.get("default", None)

        if help_text:
            if required and not help_text.rstrip().endswith("(required)"):
                kwargs["help"] = f"{help_text} (required)"
            elif not required and default not in (None, [], "") and "default" not in help_text.lower():
                kwargs["help"] = f"{help_text} (default: {default})"

        return target.add_argument(*flags, **kwargs)

    def _build_paths_parent(self) -> argparse.ArgumentParser:
        """Build the parent parser for path-related arguments"""
        paths = argparse.ArgumentParser(add_help=False)

        paths_group = paths.add_argument_group("Path Arguments", "Point to GEOS bin, set experiment directory, control execution location")
        self.add_arg(
            paths_group,
            "--geos_dir",
            default="../model/install-release/bin",
            help="Location of desired GEOS install (default '../model/install/bin')",
        )
        self.add_arg(
            paths_group,
            "--exp_dir",
            default="experiments",
            help="Location under which experiment directory will be generatred. Relative from current directory (default './experiments')",
        )
        self.add_arg(
            paths_group,
            "--execute_on",
            choices=["compute", "local", "none"],
            default="compute",
            help="Choose where to execute the model: 'compute' to submit with sbatch, 'local' to execute directly on the current node, or 'none' to setup without executing",
        )

        return paths

    def _build_python_parent(self) -> argparse.ArgumentParser:
        """Build the parent parser for Python DSL arguments"""
        dsl = argparse.ArgumentParser(add_help=False)
        dsl_group = dsl.add_argument_group("DSL Arguments", "Toggle and control execution of DSL modules")
        self.add_arg(
            dsl_group,
            "--pymodules",
            nargs="+",
            choices=["gfdl1m", "uw", "gf2020", "fv3"],
            default=[],
            metavar="{gfdl1m,uw,gf2020,fv3}",
            help="Python DSL modules to enable (space-separated, e.g. --pymodules gfdl1m uw)",
        )
        self.add_arg(
            dsl_group,
            "--backend",
            default="orch:dace:gpu:KJI",
            help="DSL backend string. Only considered when one or more pymodules are specified",
        )

        return dsl

    def _build_config_parent(self) -> argparse.ArgumentParser:
        """Build the parent parser for model configuration arguments"""
        config = argparse.ArgumentParser(add_help=False)
        config_group = config.add_argument_group("Model Configuration Arguments")
        self.add_arg(config_group, "--account", default=None, help="Charge account to use when submitting jobs with SBATCH")
        self.add_arg(
            config_group, "--microphysics", choices=["BACK_1M", "GFDL_1M", "MGB2_2M"], default="GFDL_1M", help="Sets the microphysics scheme used in moist physics"
        )
        self.add_arg(config_group, "--ocean", choices=["o1", "o2", "o3", "MOM5", "MOM6", "MIT"], default="o2", help="Sets the ocean model")
        self.add_arg(config_group, "--aerosols", choices=["A", "C"], default="C", help="Sets the aerosol scheme used by GOCART")
        self.add_arg(config_group, "--emissions", choices=["AMIP", "OPS"], default="AMIP", help="GOCART emissions choice")
        self.add_arg(config_group, "--oserver", type=bool, default=False, help="Enable/disable the IO server")
        self.add_arg(config_group, "--nonhydro", type=bool, default=True, help="Enable/disable nonhydrostatic dynamics")
        self.add_arg(config_group, "--data_atmo", type=bool, default=True, help="Use data atmosphere")
        self.add_arg(config_group, "--land_bcs", choices=["ICA", "NL3", "v12", "v14"], default="v12", help="Land Surface BCs: Icarus (ICA), Icarus-NLv3 (NL3), or v12")
        self.add_arg(config_group, "--land_surf", choices=[1, 2], type=int, default=1, help="Land Surface Model: Catchment (1) or CatchmentCN-CLM4.0 (2)")
        self.add_arg(config_group, "--heartbeat", default=None, help="Number of seconds to set heartbeat to (default: 450 s for BACM, resolution-dependent otherwise)")
        self.add_arg(
            config_group,
            "--processor",
            choices=["mil", "cas"],
            default="mil",
            help="Target processor architecture. Milan (mil), Cascade Lake (cas). Default: mil, overriden for GPU DSL runs (must use rome a100 nodes)",
        )

        return config

    def _build_grid_parent(self) -> argparse.ArgumentParser:
        """Build the parent parser for grid/decomposition arguments"""
        grid = argparse.ArgumentParser(add_help=False)

        grid_group = grid.add_argument_group("Grid Control", "Resolution and grid decomposition")
        self.add_arg(grid_group, "--horz", required=True, help="Horizontal resolution (e.g. 48, 180, 360, 720)")
        self.add_arg(grid_group, "--vert", required=True, help="Vertical resolution (e.g. 72, 131, 137, 181)")
        self.add_arg(grid_group, "--nx", required=True, type=int, help="Number of MPI ranks in X")
        self.add_arg(grid_group, "--ny", required=True, type=int, help="Number of MPI ranks in Y (will be multiplied by face count later)")

        return grid

    def _build_timing_parent(self) -> argparse.ArgumentParser:
        """Build the parent parser for timing arguments"""
        timing = argparse.ArgumentParser(add_help=False)

        timing_group = timing.add_argument_group("Timing Control")
        self.add_arg(timing_group, "--end_date", help="End date of model run in YYYYMMDDHHMMSS format. Mutually exclusive with --duration")
        self.add_arg(
            timing_group,
            "--job_segment",
            help="JOB_SGMT length in YYYYMMDDHHMMSS format (default 00000010000000, i.e. 10 days)",
        )
        self.add_arg(timing_group, "--num_segment", type=int, help="Number of --job_segment periods to run per sbatch submission")
        self.add_arg(
            timing_group,
            "--duration",
            type=int,
            help="Number of --duration_unit units to run (integer > 0). Mutually exclusive with --end_date",
        )
        self.add_arg(timing_group, "--duration_unit", choices=["days", "months", "years"], default="days", help="Unit for --duration")

        return timing

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build the main argument parser with subcommands for GCM, SCM, and EMIP."""
        parser = _CaseInsensitiveArgumentParser(
            prog="run_GEOS.py",
            description="Set up and submit a single GCM or SCM experiment, or an entire EMIP experiment suite.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        config = self._build_config_parent()
        grid = self._build_grid_parent()
        paths = self._build_paths_parent()
        python = self._build_python_parent()
        timing = self._build_timing_parent()

        parser.register("action", "parsers", _CaseInsensitiveSubParsersAction)
        subparsers = parser.add_subparsers(dest="mode", required=True, help="Type of run to perform.")

        # ---- gcm ----
        gcm_parser = subparsers.add_parser(
            "GCM",
            parents=[grid, timing, paths, python, config],
            help="Set up and submit a single GCM experiment. Run 'python run_GEOS.py GCM --help' for more detailed information",
            description="Set up and submit a single GCM experiment.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        gcm_group = gcm_parser.add_argument_group("Additional GCM Arguments")
        self.add_arg(
            gcm_group,
            "--custom_restart",
            default=False,
            help="Use custom restarts instead of copying from Matt Thompson's HUGEBCs (default False - use HBC restart). When True, the system will "
            "stop after experiment setup so restart files can be copied manually",
        )

        # ---- scm ----
        scm_parser = subparsers.add_parser(
            "SCM",
            parents=[paths, python],
            help="XXXXX WORK IN PROGRESS - DOES NOT CURRENTLY WORK XXXXX Set up and submit a SCM experiment. Run 'python run_GEOS.py SCM --help' for more detailed information",
            description="Set up and submit a SCM experiment.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        scm_group = scm_parser.add_argument_group("Additional SCM Arguments")
        self.add_arg(scm_group, "--case", required=True, help="SCM case/experiment name.")
        self.add_arg(scm_group, "--duration", type=int, help="Number of --duration_unit units to run (integer > 0)")
        self.add_arg(
            scm_group,
            "--duration_unit",
            choices=["days", "months", "years"],
            default="days",
            help="Unit for --duration",
        )

        # ---- emip ----
        emip_parser = subparsers.add_parser(
            "EMIP",
            parents=[grid, paths, python, config],
            help="Set up and submit an entire EMIP experiment suite. Run 'python run_GEOS.py EMIP --help' for more detailed information",
            description="Set up and submit an entire EMIP experiment suite.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        emip_group = emip_parser.add_argument_group("Additional EMIP Arguments")
        self.add_arg(
            emip_group,
            "--start_year",
            required=True,
            type=int,
            choices=[1985, 1995, 2005],
            help="Choose the set of 10 years for the ensemble, starting at the given year (e.g. 1985 runs 1985-1994)",
        )
        self.add_arg(
            emip_group,
            "--duration",
            required=True,
            type=int,
            default=3,
            help="Number of months to run each member",
        )
        self.add_arg(
            emip_group,
            "--season",
            required=True,
            choices=["DJF", "JJA"],
            help="Choose the starting season for the ensemble. DJF starts in November, JJA starts in May",
        )
        self.add_arg(
            emip_group,
            "--job_segment",
            help="JOB_SGMT length in YYYYMMDDHHMMSS format (default 00000010000000, i.e. 10 days)",
        )
        self.add_arg(emip_group, "--num_segment", type=int, help="Number of --job_segment periods to run per sbatch submission")

        return parser

    def _validate_args(self, args: argparse.Namespace) -> None:
        """Cross-argument validation that argparse can't easily handle."""
        ### grid
        args.ny = args.ny * 6

        ### configuration
        if args.mode == "EMIP":
            # EMIP mode uses its own restart system, called after the GCM init. set custom_restart to True to bypass systems dependent on these restarts in GCMRunner
            args.custom_restart = True

        # ensure account is specified if execution is set for compute node, warn if execution is set to none and account is not specified
        if not args.account:
            if args.execute_on == "compute":
                raise ArgumentValidationError(f"[GEOS PYTHON WRAPPER] Execution on compute node requires an --account to be specified.")
            if args.execute_on == "none":
                # NOTE proper warning system?
                print(
                    "[GEOS PYTHON WRAPPER] WARNING: --account is not specified. This has been allowed because --execute_on none was specified, but be warned: this "
                    "experiment will not run on compute nodes without an account."
                )

        ### timing
        if args.mode == "GCM":
            if args.duration is None and args.end_date is None:
                raise ArgumentValidationError("[GEOS PYTHON WRAPPER] Either --duration or --end_date must be specified.")

            if args.duration is not None and args.end_date is not None:
                raise ArgumentValidationError("[GEOS PYTHON WRAPPER] --duration and --end_date are mutually exclusive; please specify only one of them.")

            if args.custom_restart and args.duration is not None:
                raise ArgumentValidationError(
                    "[GEOS PYTHON WRAPPER] --duration and --custom_restart cannot be used together. A known start date (read from cap_restart) is required "
                    "to compute END_DATE when using --duration. Please use --end_date instead of --duration."
                )
            if args.custom_restart and args.end_date is not None:
                # NOTE proper warning system?
                print(
                    "[GEOS PYTHON WRAPPER] cannot validate timing parameters when --custom_restart is specified. Ensure that the provided end_date, job_segment, "
                    "and num_segment is reasonable for the desired restart date."
                )

            if args.end_date is not None:
                if len(args.end_date) != 14:
                    raise ArgumentValidationError("[GEOS PYTHON WRAPPER] --end_date must be in YYYYMMDDHHMMSS format.")
                try:
                    datetime.strptime(args.end_date, r"%Y%m%d%H%M%S")
                except:
                    raise ArgumentValidationError("[GEOS PYTHON WRAPPER] --end_date must be in YYYYMMDDHHMMSS format.")
            if args.duration is not None:
                max_limit = DURATION_UNIT_FIELD_MAX.get(args.duration_unit)
                if max_limit is not None and args.duration > max_limit:
                    raise ArgumentValidationError(
                        f"--duration ({args.duration}) exceeds character limits in model configuration files "
                        f"(max {max_limit} {args.duration_unit}); use a larger --duration_unit instead."
                    )

        if args.job_segment is not None:
            # job_segment is only present for GCM and EMIP runs
            if len(args.job_segment) != 14:
                raise ArgumentValidationError("[GEOS PYTHON WRAPPER] --job_segment must be in YYYYMMDDHHMMSS format.")

            # if duration is specified but job_segment is not, apply default job_segment = duration
            if args.duration is not None and args.job_segment is None:
                args.job_segment = args.duration

    def parse(self, args_list=None) -> argparse.Namespace:
        """Parses and validates arguments, returning the namespace."""
        args = self.parser.parse_args(args_list)
        args.mode = args.mode.upper()
        self._validate_args(args)
        return args
