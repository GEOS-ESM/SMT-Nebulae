import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

import run_GEOS


class ExperimentNameTests(unittest.TestCase):
    def test_pymodules_label_experiment_directory(self):
        for mode, mode_args in (
            ("GCM", ["--duration", "1"]),
            ("EMIP", ["--start_year", "2005", "--season", "DJF"]),
        ):
            for modules, suffix in (
                (None, ""),
                ("uw", "_ORCH_DACE_CPU_KJI_pyUW"),
                ("shoc", "_ORCH_DACE_CPU_KJI_pySHOC"),
                ("shoc,uw", "_ORCH_DACE_CPU_KJI_pyUW_pySHOC"),
            ):
                with self.subTest(mode=mode, modules=modules):
                    args = [
                        mode,
                        "--machine",
                        "NONHPC",
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
                        *mode_args,
                    ]
                    if modules is not None:
                        args += ["--pymodules", modules]

                    runner_class = getattr(run_GEOS, f"{mode}Runner")
                    with patch.object(runner_class, "run", autospec=True) as run:
                        result = CliRunner().invoke(run_GEOS.run_GEOS, args)

                    self.assertEqual(
                        result.exit_code, 0, f"{result.output}\n{result.exception}"
                    )
                    run.assert_called_once()
                    runner = run.call_args.args[0]
                    self.assertEqual(
                        Path(runner.exp_dir).name,
                        f"{mode}_C24_L72_NX2_NY6{suffix}",
                    )
