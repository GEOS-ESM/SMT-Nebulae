import os
import shlex
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from run_helpers.gcm_setup import (
    _PROMPTS,
    _set_hydrostatic,
    prepare_gcm_setup,
    run_gcm_setup,
)
from run_helpers.setup import SetupDirectory


class GCMSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / "install" / "bin"
        self.bin.mkdir(parents=True)
        self.home = self.root / "home"
        self.home.mkdir()
        (self.home / ".HOMDIRroot").write_text("original\n")
        self.log = self.root / "answers"
        self.runner = SimpleNamespace(
            args=SimpleNamespace(
                mode="GCM",
                geos_dir=str(self.bin.parent),
                ocean="o2",
                data_atmo=False,
                microphysics="GFDL1M",
                horz=24,
                vert=72,
                oserver=True,
                processor="mil",
                hydro=True,
                land_bcs="v14",
                land_surf="1",
                aerosols="C",
                heartbeat=None,
                account="project",
                link=True,
                restart_setup_scripts_dir=None,
            ),
            exp_name="experiment",
            exp_dir=str(self.root / "experiment"),
            env=dict(os.environ, HOME=str(self.home), TEST_LOG=str(self.log)),
        )
        Path(self.runner.exp_dir).mkdir()

    def write_setup(self, prompts, *, fail=False):
        script = self.bin / "gcm_setup"
        lines = ["#!/bin/sh", 'printf "link=%s\\n" "$*" > "$TEST_LOG"']
        for key in prompts:
            lines += [
                f"printf '%s\\n' {shlex.quote(_PROMPTS[key])}",
                "IFS= read -r answer || exit 3",
                f'printf "%s=%s\\n" {shlex.quote(key)} "$answer" >> "$TEST_LOG"',
            ]
        if fail:
            lines.append("exit 9")
        else:
            lines.append(
                'printf "&fv_core_nml\\n/\\n" > '
                + shlex.quote(str(Path(self.runner.exp_dir) / "fvcore_layout.rc"))
            )
        script.write_text("\n".join(lines) + "\n")
        script.chmod(0o755)

    @staticmethod
    def common_prompts():
        return [
            "expid",
            "description",
            "clone",
            "atmos_horizontal",
            "atmos_vertical",
            "microphysics",
            "oserver",
            "processor",
            "coupled",
            "data_ocean",
            "land_bcs",
            "land_model",
            "aerosols",
            "emissions",
            "heartbeat",
            "history",
            "home",
            "experiment",
            "build",
            "group",
        ]

    def test_direct_setup_answers_and_isolates_home(self):
        self.write_setup(self.common_prompts())
        run_gcm_setup(self.runner, prompt_timeout=3)
        answers = self.log.read_text()
        for entry in (
            "link=--link",
            "microphysics=GFDL_1M",
            "processor=mil",
            "data_ocean=o2",
            "heartbeat=",
            "group=project",
            f"home={self.runner.exp_dir}",
            f"experiment={self.runner.exp_dir}",
        ):
            self.assertIn(entry + "\n", answers)
        self.assertIn(
            "hydrostatic = .true.",
            (Path(self.runner.exp_dir) / "fvcore_layout.rc").read_text(),
        )
        self.assertEqual((self.home / ".HOMDIRroot").read_text(), "original\n")
        self.assertFalse((self.home / ".EXPDIRroot").exists())

    def test_unset_physics_options_use_gcm_setup_defaults(self):
        self.runner.args.microphysics = None
        self.runner.args.oserver = None
        self.runner.args.processor = None
        self.runner.args.hydro = None
        self.runner.args.aerosols = None
        prompts = self.common_prompts()
        prompts.insert(prompts.index("coupled"), "hydro")
        self.write_setup(prompts)

        run_gcm_setup(self.runner, prompt_timeout=3)

        answers = self.log.read_text()
        for key in ("microphysics", "oserver", "processor", "hydro", "aerosols"):
            self.assertIn(f"{key}=\n", answers)
        self.assertNotIn(
            "hydrostatic =",
            (Path(self.runner.exp_dir) / "fvcore_layout.rc").read_text(),
        )

    def test_coupled_data_atmosphere_and_defaults(self):
        self.runner.args.ocean = "MOM5"
        self.runner.args.data_atmo = True
        self.runner.args.link = False
        self.runner.args.hydro = False
        prompts = self.common_prompts()
        prompts[prompts.index("data_ocean") : prompts.index("history")] = [
            "ocean_model",
            "ocean_latlon",
            "seaice",
            "ocean_vertical",
            "data_atmos",
            "heartbeat",
        ]
        self.write_setup(prompts)
        run_gcm_setup(self.runner, prompt_timeout=3)
        answers = self.log.read_text()
        self.assertIn("link=\n", answers)
        self.assertIn("ocean_model=MOM5\n", answers)
        self.assertIn("seaice=CICE4\n", answers)
        self.assertIn("data_atmos=YES\n", answers)
        self.assertIn(
            "hydrostatic = .false.",
            (Path(self.runner.exp_dir) / "fvcore_layout.rc").read_text(),
        )

    def test_repeated_prompt_reports_rejected_answer(self):
        self.write_setup(["expid", "expid"])
        with self.assertRaisesRegex(RuntimeError, "repeated prompt 'expid'"):
            run_gcm_setup(self.runner, prompt_timeout=3)

    def test_nonzero_exit_is_reported(self):
        self.write_setup(self.common_prompts(), fail=True)
        with self.assertRaisesRegex(RuntimeError, "exit=9"):
            run_gcm_setup(self.runner, prompt_timeout=3)

    def test_missing_setup_does_not_remove_existing_experiment(self):
        marker = Path(self.runner.exp_dir) / "keep"
        marker.write_text("keep")
        with self.assertRaises(FileNotFoundError):
            SetupDirectory().operate(self.runner)
        self.assertTrue(marker.exists())

    def test_rejects_data_atmosphere_with_uncoupled_ocean(self):
        self.runner.args.data_atmo = True
        with self.assertRaisesRegex(ValueError, "requires a coupled ocean"):
            prepare_gcm_setup(self.runner)

    def test_existing_hydrostatic_setting_is_replaced(self):
        layout = Path(self.runner.exp_dir) / "fvcore_layout.rc"
        layout.write_text("&fv_core_nml\n hydrostatic = .true.\n/\n")
        _set_hydrostatic(self.runner.exp_dir, False)
        self.assertIn("hydrostatic = .false.", layout.read_text())
        self.assertEqual(layout.read_text().count("hydrostatic"), 1)

    def test_hpc_setup_does_not_require_restart_scripts(self):
        self.write_setup(self.common_prompts())
        with (
            patch("run_helpers.setup.config.MACHINE", "DISCOVER"),
            patch("run_helpers.setup.run_gcm_setup") as setup,
            patch("run_helpers.setup.subprocess.run") as makeoneday,
            patch("builtins.input") as prompt,
        ):
            SetupDirectory().operate(self.runner)
        setup.assert_called_once_with(self.runner)
        makeoneday.assert_not_called()
        prompt.assert_not_called()

    @unittest.skipUnless(
        os.environ.get("PYPIPE_TEST_GEOS_DIR"), "No GEOS installation specified"
    )
    def test_real_geos_installation(self):
        self.runner.args.geos_dir = os.environ["PYPIPE_TEST_GEOS_DIR"]
        self.runner.args.oserver = False
        self.runner.env.setdefault("TERM", "xterm")
        for ocean, data_atmo, horz, hydro in [
            ("o2", False, 24, True),
            ("o1", False, 12, False),
        ]:
            with self.subTest(ocean=ocean):
                self.runner.exp_name = f"test_{ocean}"
                self.runner.exp_dir = str(self.root / self.runner.exp_name)
                self.runner.args.ocean = ocean
                self.runner.args.data_atmo = data_atmo
                self.runner.args.horz = horz
                self.runner.args.hydro = hydro
                run_gcm_setup(self.runner)
                exp = Path(self.runner.exp_dir)
                self.assertTrue((exp / "AGCM.rc").is_file())
                self.assertTrue((exp / "gcm_run.j").is_file())
                self.assertTrue((exp / "GEOSgcm.x").is_symlink())
                value = ".true." if hydro else ".false."
                self.assertIn(
                    f"hydrostatic = {value}", (exp / "fvcore_layout.rc").read_text()
                )


if __name__ == "__main__":
    unittest.main()
