import unittest
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import yaml
from click.testing import CliRunner
from schema import SchemaError

import run_GEOS
from cli_options.config import (
    COMMAND_SCHEMAS,
    COMMAND_VALIDATORS,
    CONFIG_OPTIONS,
    DEFAULT_MACHINE,
)
from cli_options.machine import DEFAULT_MACHINE as CLI_DEFAULT_MACHINE
from run_helpers import config as runtime_config
from run_helpers.setup import SetupDirectory


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        runtime_config.MACHINE = CLI_DEFAULT_MACHINE

    def invoke_gcm(self, config, *arguments):
        with TemporaryDirectory() as directory:
            config_path = Path(directory) / "settings.yaml"
            config_path.write_text(config, encoding="utf-8")
            with patch.object(run_GEOS, "GCMRunner") as runner_class:
                result = self.runner.invoke(
                    run_GEOS.run_GEOS,
                    ["GCM", "--config", str(config_path), *arguments],
                )
        return result, runner_class

    def test_config_supplies_required_values_and_cli_overrides(self):
        result, runner_class = self.invoke_gcm(
            """
horz: 180
vert: 72
nx: 10
ny: 12
duration: 1
backend: orch:dace:gpu:KJI
pymodules: [uw, gfdl1m]
execute_on: none
""",
            "--nx",
            "20",
            "--backend",
            "orch:dace:cpu:KJI",
        )

        self.assertEqual(result.exit_code, 0, result.output)
        arguments = runner_class.call_args.kwargs
        self.assertEqual(arguments["nx"], 20)
        self.assertEqual(arguments["ny"], 12)
        self.assertEqual(arguments["backend"], "orch:dace:cpu:KJI")
        self.assertEqual(arguments["pymodules"], ("uw", "gfdl1m"))
        self.assertEqual(arguments["duration_unit"], "days")
        self.assertTrue(arguments["link"])
        for name in ("microphysics", "aerosols", "oserver", "hydro", "processor"):
            self.assertIsNone(arguments[name])
        runner_class.return_value.run.assert_called_once_with()

    def test_link_can_be_disabled_from_cli(self):
        result, runner_class = self.invoke_gcm(
            "horz: 180\nvert: 72\nnx: 10\nny: 12\nduration: 1\nexecute_on: none\n",
            "--no_link",
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertFalse(runner_class.call_args.kwargs["link"])

    def test_keep_original_restarts_config_and_cli(self):
        base = "horz: 180\nvert: 72\nnx: 10\nny: 12\nduration: 1\nexecute_on: none\n"
        for yaml_value, cli, expected in (
            ("", (), False),
            ("keep_original_restarts: true\n", (), True),
            ("keep_original_restarts: false\n", ("--keep_original_restarts",), True),
            ("keep_original_restarts: true\n", ("--no_keep_original_restarts",), False),
        ):
            with self.subTest(yaml_value=yaml_value, cli=cli):
                result, runner_class = self.invoke_gcm(base + yaml_value, *cli)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIs(
                    runner_class.call_args.kwargs["keep_original_restarts"], expected
                )

    def test_dace_mode_config_cli_and_invalid_values(self):
        base = "horz: 180\nvert: 72\nnx: 10\nny: 12\nduration: 1\nexecute_on: none\n"
        for yaml_value, cli, expected in (
            ("", (), "BuildAndRun"),
            ("dace_mode: Build\n", (), "Build"),
            ("dace_mode: Build\n", ("--dace_mode", "Run"), "Run"),
        ):
            with self.subTest(yaml_value=yaml_value, cli=cli):
                result, runner_class = self.invoke_gcm(base + yaml_value, *cli)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertEqual(runner_class.call_args.kwargs["dace_mode"], expected)
        for yaml_value, cli in (
            ("dace_mode: Other\n", ()),
            ("", ("--dace_mode", "Other")),
        ):
            with self.subTest(yaml_value=yaml_value, cli=cli):
                result, _ = self.invoke_gcm(base + yaml_value, *cli)
                self.assertEqual(result.exit_code, 2)

    def test_config_mode_dispatches_without_subcommand_and_cli_overrides_link(self):
        with TemporaryDirectory() as directory:
            config_path = Path(directory) / "emip.yaml"
            config_path.write_text(
                """mode: EMIP
execute_on: none
horz: 180
vert: 72
nx: 20
ny: 20
start_year: "2005"
season: DJF
duration: 12
link: false
""",
                encoding="utf-8",
            )
            with patch.object(run_GEOS, "EMIPRunner") as runner_class:
                result = self.runner.invoke(
                    run_GEOS.run_GEOS,
                    ["--config", str(config_path), "--link"],
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(runner_class.call_args.kwargs["mode"], "EMIP")
        self.assertTrue(runner_class.call_args.kwargs["link"])
        runner_class.return_value.run.assert_called_once_with()

    def test_config_mode_must_match_explicit_subcommand(self):
        result, _ = self.invoke_gcm(
            "mode: EMIP\nhorz: 180\nvert: 72\nnx: 10\nny: 12\nduration: 1\n"
        )

        self.assertEqual(result.exit_code, 2)
        self.assertIn("does not match the selected GCM command", result.output)

    def test_config_without_command_requires_mode(self):
        with TemporaryDirectory() as directory:
            config_path = Path(directory) / "settings.yaml"
            config_path.write_text("execute_on: none\n", encoding="utf-8")
            result = self.runner.invoke(
                run_GEOS.run_GEOS, ["--config", str(config_path)]
            )

        self.assertEqual(result.exit_code, 2)
        self.assertIn("top-level mode: GCM, EMIP, or SCM is required", result.output)

    def test_unknown_option_is_rejected_before_required_option_checks(self):
        result, _ = self.invoke_gcm("typo: value\n")

        self.assertEqual(result.exit_code, 2)
        self.assertIn("unknown option(s) for gcm: typo", result.output)

    def test_invalid_yaml_is_reported(self):
        result, _ = self.invoke_gcm("horz: [unclosed\n")

        self.assertEqual(result.exit_code, 2)
        self.assertIn("invalid YAML", result.output)

    def test_config_document_must_be_a_mapping(self):
        result, _ = self.invoke_gcm("- one\n- two\n")

        self.assertEqual(result.exit_code, 2)
        self.assertIn("document must be a mapping", result.output)

    def test_invalid_typed_value_is_reported(self):
        result, _ = self.invoke_gcm(
            "horz: 180\nvert: 72\nnx: many\nny: 12\nduration: 1\n"
        )

        self.assertEqual(result.exit_code, 2)
        self.assertIn("invalid gcm config", result.output)

    def test_yaml_schema_covers_command_options(self):
        self.assertEqual(set(COMMAND_SCHEMAS), {"gcm", "emip", "scm"})
        self.assertEqual(set(CONFIG_OPTIONS), set(COMMAND_SCHEMAS))
        with self.assertRaises(SchemaError):
            COMMAND_VALIDATORS["gcm"].validate({"nx": "20"})

    def test_machine_config_sets_global_and_is_not_passed_to_runner(self):
        result, runner_class = self.invoke_gcm(
            "machine: DISCOVER\nhorz: 180\nvert: 72\nnx: 10\nny: 12\nduration: 1\nexecute_on: none\n"
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(runtime_config.MACHINE, "DISCOVER")
        self.assertNotIn("machine", runner_class.call_args.kwargs)

        self.invoke_gcm(
            "horz: 180\nvert: 72\nnx: 10\nny: 12\nduration: 1\nexecute_on: none\n"
        )
        self.assertEqual(runtime_config.MACHINE, DEFAULT_MACHINE)

    def test_machine_cli_option_overrides_config(self):
        result, _ = self.invoke_gcm(
            "machine: NONHPC\nhorz: 180\nvert: 72\nnx: 10\nny: 12\nduration: 1\nexecute_on: none\n",
            "--machine",
            "DISCOVER",
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(runtime_config.MACHINE, "DISCOVER")

    def test_restart_tbc_is_passed_from_config_to_runner(self):
        result, runner_class = self.invoke_gcm(
            "restart_setup_scripts_dir: /path/to/TBC/scripts\nhorz: 180\nvert: 72\nnx: 10\nny: 12\nduration: 1\nexecute_on: none\n"
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            runner_class.call_args.kwargs["restart_setup_scripts_dir"],
            "/path/to/TBC/scripts",
        )

    def test_restart_tbc_config_supplies_nonhpc_setup_scripts(self):
        with TemporaryDirectory() as directory:
            setup_scripts = str(Path(directory) / "TBC" / "scripts")
            experiment_dir = str(Path(directory) / "experiment")
            geos_bin_dir = Path(directory) / "bin"
            geos_bin_dir.mkdir()
            script = geos_bin_dir / "gcm_setup"
            script.touch(mode=0o755)
            runner = SimpleNamespace(
                args=SimpleNamespace(
                    mode="GCM",
                    restart_setup_scripts_dir=setup_scripts,
                    geos_dir=str(Path(directory)),
                    microphysics="GFDL1M",
                    ocean="o2",
                    horz=24,
                    vert=72,
                    account=None,
                    aerosols="C",
                    land_bcs="v12",
                    land_surf="1",
                    processor="mil",
                    oserver=True,
                    hydro=True,
                    data_atmo=False,
                    heartbeat=None,
                ),
                exp_dir=experiment_dir,
                exp_dir_root=directory,
                exp_name="experiment",
                env={},
            )

            with (
                patch.object(runtime_config, "MACHINE", "NONHPC"),
                patch("run_helpers.setup.subprocess.run") as run,
                patch("run_helpers.setup.run_gcm_setup") as setup,
                patch("builtins.input") as prompt,
            ):
                SetupDirectory().operate(runner)
                runner.args.link = False
                SetupDirectory().operate(runner)

        self.assertEqual(setup.call_count, 2)
        self.assertIs(setup.call_args.args[0], runner)
        self.assertEqual(
            run.call_args_list[0].args[0],
            [f"{setup_scripts}/makeoneday.bash", "noext", "noresto", "gitv12"],
        )
        self.assertEqual(run.call_args_list[0].kwargs["cwd"], experiment_dir)
        prompt.assert_not_called()

    def test_saved_config_contains_all_options_and_survives_default_changes(self):
        for mode, mode_arguments in (
            ("GCM", ["--duration", "1", "--keep_original_restarts"]),
            ("EMIP", ["--start_year", "2005", "--season", "DJF"]),
        ):
            for use_config in (False, True):
                with (
                    self.subTest(mode=mode, use_config=use_config),
                    TemporaryDirectory() as directory,
                ):
                    config_path = Path(directory) / "input.yaml"
                    config_path.write_text(
                        "machine: NONHPC\nnx: 4\nlink: true\n", encoding="utf-8"
                    )
                    arguments = [mode]
                    if use_config:
                        arguments += ["--config", str(config_path)]
                    arguments += [
                        "--machine",
                        "DISCOVER",
                        "--top_exp_dir",
                        directory,
                        "--horz",
                        "24",
                        "--vert",
                        "72",
                        "--nx",
                        "2",
                        "--ny",
                        "6",
                        "--execute_on",
                        "none",
                        "--no_link",
                        "--dace_mode",
                        "Run",
                        *mode_arguments,
                    ]
                    if use_config:
                        arguments += ["--pymodules", "uw,gfdl1m"]

                    runner_class = getattr(run_GEOS, f"{mode}Runner")
                    with (
                        patch.object(
                            runner_class,
                            "run",
                            lambda runner: SetupDirectory().operate(runner),
                        ),
                        patch.object(SetupDirectory, "validate_inputs"),
                        patch("run_helpers.setup.run_gcm_setup"),
                        patch("run_helpers.setup.subprocess.run") as subprocess_run,
                    ):
                        result = self.runner.invoke(run_GEOS.run_GEOS, arguments)
                        self.assertEqual(
                            result.exit_code, 0, f"{result.output}\n{result.exception}"
                        )
                        saved_path = next(Path(directory).glob("*/pypipe.yaml"))
                        saved = yaml.safe_load(saved_path.read_text(encoding="utf-8"))
                        self.assertEqual(
                            set(saved), CONFIG_OPTIONS[mode.lower()] | {"mode"}
                        )
                        self.assertEqual(saved["machine"], "DISCOVER")
                        self.assertEqual(saved["dace_mode"], "Run")
                        if mode == "GCM":
                            self.assertTrue(saved["keep_original_restarts"])
                        self.assertEqual(saved["nx"], 2)
                        self.assertFalse(saved["link"])
                        self.assertIsNone(saved["hydro"])
                        self.assertIsNone(saved["microphysics"])
                        self.assertIsNone(saved["processor"])
                        self.assertIsNone(saved["account"])
                        self.assertIsNone(saved["num_segment"])
                        self.assertEqual(saved["land_surf"], "1")
                        self.assertEqual(
                            saved["pymodules"], ["uw", "gfdl1m"] if use_config else []
                        )
                        self.assertIsInstance(saved["job_segment"], str)
                        COMMAND_VALIDATORS[mode.lower()].validate(
                            {
                                name: value
                                for name, value in saved.items()
                                if name != "mode"
                            }
                        )

                        command = run_GEOS.run_GEOS.get_command(None, mode)
                        changed_defaults = {
                            "machine": "NONHPC",
                            "land_surf": "2",
                            "microphysics": "BACM1M",
                            "hydro": False,
                            "link": True,
                            "backend": "changed-backend",
                            "dace_mode": "Build",
                            "pymodules": ("fv3",),
                            "num_segment": 99,
                            "restart_setup_scripts_dir": "/changed/scripts",
                        }
                        with ExitStack() as stack:
                            for parameter in command.params:
                                if parameter.name in changed_defaults:
                                    stack.enter_context(
                                        patch.object(
                                            parameter,
                                            "default",
                                            changed_defaults[parameter.name],
                                        )
                                    )
                            replay = self.runner.invoke(
                                run_GEOS.run_GEOS, ["--config", str(saved_path)]
                            )
                        self.assertEqual(
                            replay.exit_code, 0, f"{replay.output}\n{replay.exception}"
                        )
                        self.assertEqual(
                            yaml.safe_load(saved_path.read_text(encoding="utf-8")),
                            saved,
                        )
                        subprocess_run.assert_not_called()

    def test_saved_config_captures_prompted_restart_directory(self):
        with TemporaryDirectory() as directory:
            with (
                patch.object(
                    run_GEOS.GCMRunner,
                    "run",
                    lambda runner: SetupDirectory().operate(runner),
                ),
                patch.object(SetupDirectory, "validate_inputs"),
                patch("run_helpers.setup.run_gcm_setup"),
                patch("run_helpers.setup.subprocess.run"),
                patch("builtins.input", return_value=directory) as prompt,
            ):
                result = self.runner.invoke(
                    run_GEOS.run_GEOS,
                    [
                        "GCM",
                        "--machine",
                        "NONHPC",
                        "--top_exp_dir",
                        directory,
                        "--horz",
                        "24",
                        "--vert",
                        "72",
                        "--nx",
                        "2",
                        "--ny",
                        "6",
                        "--duration",
                        "1",
                        "--execute_on",
                        "none",
                    ],
                )
            self.assertEqual(
                result.exit_code, 0, f"{result.output}\n{result.exception}"
            )
            saved_path = next(Path(directory).glob("*/pypipe.yaml"))
            saved = yaml.safe_load(saved_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["restart_setup_scripts_dir"], directory)
            prompt.assert_called_once()

    def test_help_and_registry_cover_each_command(self):
        for command_name in ("GCM", "EMIP", "SCM"):
            with self.subTest(command=command_name):
                result = self.runner.invoke(run_GEOS.run_GEOS, [command_name, "--help"])
                command = run_GEOS.run_GEOS.get_command(None, command_name)
                parameter_names = {
                    parameter.name
                    for parameter in command.params
                    if parameter.name != "config_path"
                }

                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("--config FILE", result.output)
                self.assertIn("--machine", result.output)
                self.assertEqual(CONFIG_OPTIONS[command_name.lower()], parameter_names)

    def test_mode_names_require_uppercase(self):
        for command_name in ("gcm", "emip", "scm"):
            with self.subTest(command=command_name):
                result = self.runner.invoke(run_GEOS.run_GEOS, [command_name, "--help"])
                self.assertEqual(result.exit_code, 2)
                self.assertIn("No such command", result.output)


if __name__ == "__main__":
    unittest.main()
