import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from run_helpers.patch import PatchAGCMRC, PatchGCMRUNJ

DSL_TEMPLATE = """#######################################################################
#                          DSL configuration
#######################################################################

# ensure Python path is correct even when DSL is off because of a dependency in MAPLPy
if ( $?PYTHONPATH ) then
   setenv PYTHONPATH       ${PYTHONPATH}:${GEOSDIR}/lib/Python/
else
   setenv PYTHONPATH       ${GEOSDIR}/lib/Python/
endif
if ( $?USE_DSL ) then
   setenv FV3_DACEMODE BuildAndRun
   setenv GEOS_DSL_BACKEND UNSET
   # PYFV3 cannot currently support KJI backends, so force IJK
   setenv GEOS_DSL_PYFV3_BACKEND $GEOS_DSL_BACKEND:s/KJI/IJK/
   setenv GT_CACHE_ROOT ${EXPDIR}/.DSL_CACHE
   setenv GT4PY_COMPILE_OPT_LEVEL 3
   setenv NDSL_CONSTANTS GEOS
   setenv NDSL_LITERAL_PRECISION 32
   setenv NDSL_LOGLEVEL INFO
   setenv NDSL_UNSAFE_MODE True
   setenv PYTHONWARNINGS "ignore"
endif
"""


class PatchGCMRUNJTests(unittest.TestCase):
    def setUp(self):
        self.patcher = PatchGCMRUNJ()

    def make_runner(self, backend, modules, arch):
        return SimpleNamespace(
            args=SimpleNamespace(backend=backend, pymodules=modules),
            backend_arch=arch,
        )

    def test_unset_processor_uses_safe_task_count_without_scheduler_constraint(self):
        runner = SimpleNamespace(
            args=SimpleNamespace(nx=2, ny=1, processor=None, account="project"),
            backend_arch="CPU",
        )
        with patch("run_helpers.patch.config.MACHINE", "DISCOVER"):
            tasks_per_node, _, _ = self.patcher._compute_grid_decomposition(runner, 0)
            block = self.patcher._build_sbatch_block(
                runner, "experiment", 1, tasks_per_node, "01:00:00"
            )

        self.assertEqual(tasks_per_node, 46)
        self.assertNotIn("--constraint=", block)
        self.assertIn("--ntasks-per-node=46", block)

    def test_patches_existing_template_without_replacing_its_structure(self):
        runner = self.make_runner("orch:dace:cpu:KJI", ["uw"], "CPU")
        with patch("run_helpers.patch.config.MACHINE", "DISCOVER"):
            updated = self.patcher._patch_dsl_block(DSL_TEMPLATE, runner, 11.5)

        self.assertIn("# ensure Python path is correct", updated)
        self.assertIn(
            "# PYFV3 cannot currently support KJI backends, so force IJK", updated
        )
        self.assertIn("setenv GEOS_DSL_BACKEND orch:dace:cpu:KJI", updated)
        self.assertIn("setenv FV3_DACEMODE BuildAndRun", updated)
        self.assertIn(
            "setenv GT_CACHE_ROOT ${GEOSDIR}/.DSL_CACHE/orch_dace_cpu_KJI", updated
        )
        self.assertNotIn("NDSL_LAYOUT", updated)
        self.assertNotIn("@pyFV3", updated)
        self.assertNotIn("I_MPI_OFFLOAD", updated)
        self.assertTrue(updated.rstrip().endswith("endif"))

    def test_only_fv3_discover_gpu_adds_fv3_paths_and_mpi_offload(self):
        runner = self.make_runner("orch:dace:gpu:IJK", ["fv3"], "GPU")
        with patch("run_helpers.patch.config.MACHINE", "DISCOVER"):
            updated = self.patcher._patch_dsl_block(DSL_TEMPLATE, runner, 11.5)
            repeated = self.patcher._patch_dsl_block(updated, runner, 11.5)

        self.assertIn("@FVdycoreCubed_GridComp/python/interface", updated)
        self.assertEqual(updated.count("TEMPORARY SOLUTION"), 1)
        self.assertIn("setenv I_MPI_OFFLOAD 1", updated)
        self.assertIn("setenv I_MPI_OFFLOAD_MODE cuda", updated)
        self.assertIn("setenv GPU_LAUNCHER_SH /discover/nobackup/", updated)
        self.assertLess(
            updated.index("# Custom arguments"),
            updated.index("setenv I_MPI_OFFLOAD 1"),
        )
        self.assertTrue(updated.rstrip().endswith("endif"))
        self.assertEqual(repeated, updated)

    def test_non_discover_gpu_does_not_add_mpi_offload(self):
        runner = self.make_runner("orch:dace:gpu:KJI", ["uw"], "GPU")
        with patch("run_helpers.patch.config.MACHINE", "NONHPC"):
            updated = self.patcher._patch_dsl_block(DSL_TEMPLATE, runner, 1)

        self.assertNotIn("I_MPI_OFFLOAD", updated)
        self.assertIn("setenv MPS_ON 1", updated)

    def test_dacemode_added_to_dsl_block_when_assignment_missing(self):
        runner = self.make_runner("orch:dace:cpu:KJI", ["fv3"], "CPU")
        runner.args.dace_mode = "Run"
        template = DSL_TEMPLATE.replace("   setenv FV3_DACEMODE BuildAndRun\n", "")
        with patch("run_helpers.patch.config.MACHINE", "NONHPC"):
            updated = self.patcher._patch_dsl_block(template, runner, 1)
        self.assertIn("   setenv FV3_DACEMODE Run\nendif", updated)

    def test_dacemode_in_generated_script(self):
        for modules in ([], ["fv3"]):
            for mode in ("Build", "BuildAndRun", "Run"):
                with (
                    self.subTest(modules=modules, mode=mode),
                    TemporaryDirectory() as directory,
                ):
                    script = Path(directory) / "gcm_run.j"
                    script.write_text(
                        "#!/bin/csh\nsource $GEOSBIN/g5_modules\n"
                        'setenv RUN_CMD "$GEOSBIN/esma_mpirun -np "\n'
                        + DSL_TEMPLATE
                        + "#######################################################################\n"
                        + "# Create Experiment Sub-Directories\n"
                    )
                    (Path(directory) / "AGCM.rc").write_text("IOSERVER_NODES: 0\n")
                    runner = SimpleNamespace(
                        exp_dir=directory,
                        backend_arch="CPU",
                        args=SimpleNamespace(
                            nx=2,
                            ny=1,
                            account=None,
                            job_time="01:00:00",
                            pymodules=modules,
                            backend="orch:dace:cpu:KJI",
                            dace_mode=mode,
                        ),
                    )
                    with patch("run_helpers.patch.config.MACHINE", "NONHPC"):
                        self.patcher.validate_inputs(runner)
                        self.patcher.operate(runner)
                        self.patcher.validate_outputs(runner)
                    self.assertIn(
                        f"   setenv FV3_DACEMODE {mode}\n", script.read_text()
                    )
                    self.assertEqual(script.read_text().count("setenv FV3_DACEMODE"), 1)

    def test_nondefault_dacemode_requires_matching_assignment_without_modules(self):
        with TemporaryDirectory() as directory:
            script = Path(directory) / "gcm_run.j"
            original = "#!/bin/csh\n"
            script.write_text(original)
            (Path(directory) / "AGCM.rc").write_text("IOSERVER_NODES: 0\n")
            runner = SimpleNamespace(
                exp_dir=directory,
                backend_arch="CPU",
                args=SimpleNamespace(
                    nx=2,
                    ny=1,
                    account=None,
                    job_time="01:00:00",
                    pymodules=[],
                    dace_mode="Run",
                ),
            )
            with patch("run_helpers.patch.config.MACHINE", "NONHPC"):
                self.patcher.validate_inputs(runner)
                with self.assertRaisesRegex(RuntimeError, "FV3_DACEMODE"):
                    self.patcher.operate(runner)
            self.assertEqual(script.read_text(), original)

    def test_keep_original_restarts_patches_status_line_only_when_enabled(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled), TemporaryDirectory() as directory:
                script = Path(directory) / "gcm_run.j"
                script.write_text(
                    "#!/bin/csh\nsource $GEOSBIN/g5_modules\n"
                    'setenv RUN_CMD "$GEOSBIN/esma_mpirun -np "\n'
                    "  echo GEOSgcm Run Status: $rc\n"
                    "echo post-processing\n"
                )
                (Path(directory) / "AGCM.rc").write_text("IOSERVER_NODES: 0\n")
                runner = SimpleNamespace(
                    exp_dir=directory,
                    backend_arch="CPU",
                    args=SimpleNamespace(
                        nx=2,
                        ny=1,
                        account=None,
                        job_time="01:00:00",
                        pymodules=[],
                        keep_original_restarts=enabled,
                    ),
                )
                with patch("run_helpers.patch.config.MACHINE", "NONHPC"):
                    self.patcher.validate_inputs(runner)
                    self.patcher.operate(runner)
                    self.patcher.validate_outputs(runner)
                    self.patcher.operate(runner)

                content = script.read_text()
                expected = "  echo GEOSgcm Run Status: $rc\n"
                expected += "  exit\n" if enabled else ""
                expected += "echo post-processing\n"
                self.assertIn(expected, content)
                self.assertEqual(content.count("  exit\n"), int(enabled))

    def test_keep_original_restarts_rejects_missing_or_ambiguous_marker(self):
        for status_lines in ("", "echo GEOSgcm Run Status: $rc\n" * 2):
            with (
                self.subTest(status_lines=status_lines),
                TemporaryDirectory() as directory,
            ):
                script = Path(directory) / "gcm_run.j"
                original = "#!/bin/csh\n" + status_lines
                script.write_text(original)
                (Path(directory) / "AGCM.rc").write_text("IOSERVER_NODES: 0\n")
                runner = SimpleNamespace(
                    exp_dir=directory,
                    backend_arch="CPU",
                    args=SimpleNamespace(
                        nx=2,
                        ny=1,
                        account=None,
                        job_time="01:00:00",
                        pymodules=[],
                        keep_original_restarts=True,
                    ),
                )
                with patch("run_helpers.patch.config.MACHINE", "NONHPC"):
                    self.patcher.validate_inputs(runner)
                    with self.assertRaisesRegex(RuntimeError, "GEOSgcm Run Status"):
                        self.patcher.operate(runner)
                self.assertEqual(script.read_text(), original)


class PatchAGCMRCTests(unittest.TestCase):
    def test_shoc_module_enables_and_validates_agcm_flag(self):
        with TemporaryDirectory() as directory:
            agcm_rc = Path(directory) / "AGCM.rc"
            agcm_rc.write_text("NX: 2\nNY: 6\nUSE_PYTURB_SHOC: .FALSE.\n")
            runner = SimpleNamespace(
                exp_dir=directory,
                args=SimpleNamespace(nx=2, ny=1, pymodules=["shoc"]),
            )
            patcher = PatchAGCMRC()
            patcher.agcm_rc_path = str(agcm_rc)

            patcher.operate(runner)
            patcher.validate_outputs(runner)

            self.assertIn("USE_PYTURB_SHOC: .TRUE.", agcm_rc.read_text())


if __name__ == "__main__":
    unittest.main()
