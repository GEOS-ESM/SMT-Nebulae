import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

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
                    ["gcm", "--config", str(config_path), *arguments],
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
        runner_class.return_value.run.assert_called_once_with()

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
            runner = SimpleNamespace(
                args=SimpleNamespace(
                    restart_setup_scripts_dir=setup_scripts,
                    geos_dir=directory,
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
                patch("builtins.input") as prompt,
            ):
                SetupDirectory().operate(runner)

        self.assertIn(
            f"{setup_scripts}/create_expt.py", run.call_args_list[0].args[0]
        )
        self.assertEqual(
            run.call_args_list[1].args[0][0], f"{setup_scripts}/makeoneday.bash"
        )
        prompt.assert_not_called()

    def test_help_and_registry_cover_each_command(self):
        for command_name in ("gcm", "emip", "scm"):
            with self.subTest(command=command_name):
                result = self.runner.invoke(
                    run_GEOS.run_GEOS, [command_name.upper(), "--help"]
                )
                command = run_GEOS.run_GEOS.get_command(None, command_name)
                parameter_names = {
                    parameter.name
                    for parameter in command.params
                    if parameter.name != "config_path"
                }

                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("--config FILE", result.output)
                self.assertIn("--machine", result.output)
                self.assertEqual(CONFIG_OPTIONS[command_name], parameter_names)


if __name__ == "__main__":
    unittest.main()
