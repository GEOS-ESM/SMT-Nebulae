import unittest
from types import SimpleNamespace
from unittest.mock import patch

from run_helpers.patch import PatchGCMRUNJ

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

    def test_patches_existing_template_without_replacing_its_structure(self):
        runner = self.make_runner("orch:dace:cpu:KJI", ["uw"], "CPU")
        with patch("run_helpers.patch.config.MACHINE", "DISCOVER"):
            updated = self.patcher._patch_dsl_block(DSL_TEMPLATE, runner, 11.5)

        self.assertIn("# ensure Python path is correct", updated)
        self.assertIn("# PYFV3 cannot currently support KJI backends, so force IJK", updated)
        self.assertIn("setenv GEOS_DSL_BACKEND orch:dace:cpu:KJI", updated)
        self.assertIn("setenv GT_CACHE_ROOT ${GEOSDIR}/.DSL_CACHE/orch_dace_cpu_KJI", updated)
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


if __name__ == "__main__":
    unittest.main()
