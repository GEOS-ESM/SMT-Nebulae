"""Benchmark script, valid for serial or parallel code"""

import enum
import os

import pyitt.compatibility_layers.itt_python as itt
from datetime import datetime
import platform
import numpy as np
from pathlib import Path
import xarray as xr
import yaml
from setup_cube_sphere import setup_fv_cube_grid
from cuda_timer import TimedCUDAProfiler
from progress import TimedProgress
from data_ingester import raw_data_to_quantity
from ndsl.constants import X_DIM, Y_DIM, Z_DIM, Z_INTERFACE_DIM
from ndsl import DaCeOrchestration, Quantity

from pyMoist.UW.compute_uwshcu import ComputeUwshcuInv
from pyMoist.UW.config import UWConfiguration


import dace
from ndsl.dsl.dace.orchestration import orchestrate, dace_inhibitor


class BenchmarkUW:
    def __init__(self, dace_config, uw):
        orchestrate(obj=self, config=dace_config)
        self._uw = uw
        self.timings = {}
        self._timer = TimedCUDAProfiler("topline", self.timings)

    @classmethod
    def outputs(cls, quantity_factory) -> dict[str, Quantity]:
        outs = {}

        ij_k_interface_fields = [
            "umf_inv",
            "qtflx_inv",
            "slflx_inv",
            "uflx_inv",
            "vflx_inv",
        ]
        for name in ij_k_interface_fields:
            outs[name] = quantity_factory.zeros(
                dims=[X_DIM, Y_DIM, Z_INTERFACE_DIM], units="n/a"
            )

        ijk_fields = [
            "dcm_inv",
            "qvten_inv",
            "qlten_inv",
            "qiten_inv",
            "tten_inv",
            "uten_inv",
            "vten_inv",
            "qrten_inv",
            "qsten_inv",
            "cufrc_inv",
            "fer_inv",
            "fdr_inv",
            "ndrop_inv",
            "nice_inv",
            "qldet_inv",
            "qlsub_inv",
            "qidet_inv",
            "qisub_inv",
        ]
        for name in ijk_fields:
            outs[name] = quantity_factory.zeros(dims=[X_DIM, Y_DIM, Z_DIM], units="n/a")

        ij_fields = ["tpert_out", "qpert_out"]
        for name in ij_fields:
            outs[name] = quantity_factory.zeros(dims=[X_DIM, Y_DIM], units="n/a")

        return outs

    @dace_inhibitor
    def _start_timer(self):
        self._timer.__enter__()

    @dace_inhibitor
    def _end_timer(self):
        self._timer.__exit__([], [], [])

    def __call__(
        self,
        inputs: dace.compiletime,
        iteration: int,
    ):
        for _ in dace.nounroll(range(iteration)):
            self._start_timer()
            self._uw(
                # Field inputs
                pifc0_inv=inputs["pifc0_inv"],
                zifc0_inv=inputs["zifc0_inv"],
                pmid0_inv=inputs["pmid0_inv"],
                zmid0_inv=inputs["zmid0_inv"],
                kpbl_inv=inputs["kpbl_inv"],
                exnmid0_inv=inputs["exnmid0_inv"],
                exnifc0_inv=inputs["exnifc0_inv"],
                dp0_inv=inputs["dp0_inv"],
                u0_inv=inputs["u0_inv"],
                v0_inv=inputs["v0_inv"],
                qv0_inv=inputs["qv0_inv"],
                ql0_inv=inputs["ql0_inv"],
                qi0_inv=inputs["qi0_inv"],
                t0_inv=inputs["t0_inv"],
                frland=inputs["frland"],
                tke_inv=inputs["tke_inv"],
                rkfre=inputs["rkfre"],
                cush=inputs["cush"],
                shfx=inputs["shfx"],
                evap=inputs["evap"],
                cnvtr=inputs["cnvtr"],
                CNV_Tracers=inputs["CNV_Tracers"],
                # Float/Int inputs
                dotransport=inputs["dotransport"],
                k0=inputs["k0"],
                windsrcavg=inputs["windsrcavg"],
                qtsrchgt=inputs["qtsrchgt"],
                qtsrc_fac=inputs["qtsrc_fac"],
                thlsrc_fac=inputs["thlsrc_fac"],
                frc_rasn=inputs["frc_rasn"],
                rbuoy=inputs["rbuoy"],
                epsvarw=inputs["epsvarw"],
                use_CINcin=inputs["use_CINcin"],
                mumin1=inputs["mumin1"],
                rmaxfrac=inputs["rmaxfrac"],
                PGFc=inputs["PGFc"],
                dt=inputs["dt"],
                niter_xc=inputs["niter_xc"],
                criqc=inputs["criqc"],
                rle=inputs["rle"],
                cridist_opt=inputs["cridist_opt"],
                mixscale=inputs["mixscale"],
                rdrag=inputs["rdrag"],
                rkm=inputs["rkm"],
                use_self_detrain=inputs["use_self_detrain"],
                detrhgt=inputs["detrhgt"],
                use_cumpenent=inputs["use_cumpenent"],
                rpen=inputs["rpen"],
                use_momenflx=inputs["use_momenflx"],
                rdrop=inputs["rdrop"],
                iter_cin=inputs["iter_cin"],
                # Outputs
                umf_inv=inputs["umf_inv"],
                dcm_inv=inputs["dcm_inv"],
                qtflx_inv=inputs["qtflx_inv"],
                slflx_inv=inputs["slflx_inv"],
                uflx_inv=inputs["uflx_inv"],
                vflx_inv=inputs["vflx_inv"],
                qvten_inv=inputs["qvten_inv"],
                qlten_inv=inputs["qlten_inv"],
                qiten_inv=inputs["qiten_inv"],
                tten_inv=inputs["tten_inv"],
                uten_inv=inputs["uten_inv"],
                vten_inv=inputs["vten_inv"],
                qrten_inv=inputs["qrten_inv"],
                qsten_inv=inputs["qsten_inv"],
                cufrc_inv=inputs["cufrc_inv"],
                fer_inv=inputs["fer_inv"],
                fdr_inv=inputs["fdr_inv"],
                ndrop_inv=inputs["ndrop_inv"],
                nice_inv=inputs["nice_inv"],
                qldet_inv=inputs["qldet_inv"],
                qlsub_inv=inputs["qlsub_inv"],
                qidet_inv=inputs["qidet_inv"],
                qisub_inv=inputs["qisub_inv"],
                tpert_out=inputs["tpert_out"],
                qpert_out=inputs["qpert_out"],
                # TMP
                testvar3D=inputs["qpert_out"],
            )
            self._end_timer()


# ---- GLOBAL MESS ----#
# In a better world those would becomes options

MONO_CORE = True
"""Deactivate threading to test the code in a single-core/thread capacity to mimicking
the hyperscaling strategy of GEOS"""
os.environ["GT4PY_EXTRA_COMPILE_ARGS"] = "-g"
os.environ["GT4PY_COMPILE_OPT_LEVEL"] = "3"
# if MONO_CORE:
#     os.environ["OMP_NUM_THREADS"] = "1"

config_yaml = Path(__file__).absolute().parent / ".config.yaml"
if not config_yaml.exists():
    raise FileNotFoundError(
        f"Couldn't file config file. Expected one at path {config_yaml}. "
        "You can copy `0_config.yaml` as a starting point."
    )

with open(config_yaml, "r") as config_file:
    # load machine dependent changes
    config = yaml.load(config_file, Loader=yaml.SafeLoader)


@enum.unique
class Exp(enum.Enum):
    C12_AI2 = enum.auto()
    C24_GEOS = enum.auto()


BENCH_NAME = "UW"
"""Benchmark name & config key."""
xp = Exp.C24_GEOS

if xp == Exp.C12_AI2:
    c12_config = config[BENCH_NAME]["c12_AI2"]
    GRID = {"IM": 12, "JM": 12, "KM": 79, "halo": 3}
    """The grid size as we expect it in the data."""
    DATA_PATH = c12_config["data"]
    """Path to a netcdf with the input data."""
    ETA_FILE = c12_config["eta_file"]
    ETA_AK_BK_FILE = None
    """Atmospheric level file to read for initialization of the grid.
    Generate from `ndsl` or saved from a previous runs (ak, bk)."""
    INPUT_NAME_TO_CODE_NAME = c12_config["inputs_name_to_code_name"]
    """Mapping of saved named to expected names in the code"""
    INPUTS_TO_REMOVE = c12_config["inputs_to_remove"]
    """List of inputs not used in the code signature"""
elif xp == Exp.C24_GEOS:
    c24_config = config[BENCH_NAME]["c24_GEOS"]
    GRID = {"IM": 24, "JM": 24, "KM": 72, "halo": 3}
    DATA_PATH = c24_config["data"]
    ETA_FILE = ""
    ETA_AK_BK_FILE = c24_config["eta_ak_bk_file"]
    INPUT_NAME_TO_CODE_NAME = c24_config["inputs_name_to_code_name"]
    INPUTS_TO_REMOVE = c24_config["inputs_to_remove"]
else:
    raise NotImplementedError(f"Experiment {xp} just is not ")


TILE_LAYOUT = (1, 1)
"""The layout of a single tile, as we expect it into the data (for parallel codes)."""

NAMELIST = config[BENCH_NAME]["namelist"]
"""Dynamics namelist - sorry."""

IS_SERIALIZE_DATA = True
"""Flag that our data comes from Fortran and therefore need special love."""

# BACKEND = "gt:cpu_kfirst"  # ""gt:cpu_ifirst""
BACKEND = "dace:cpu_kfirst"
"""The One to bring them and in darkness speed them up."""

# ORCHESTRATION = DaCeOrchestration.Python
ORCHESTRATION = DaCeOrchestration.BuildAndRun  # DaCeOrchestration.Run
"""Tune the orchestration strategy. Set to `None` if you are running `gt:X` backends for comparison."""

BENCH_WITHOUT_ORCHESTRATION_OVERHEAD = True
"""Wrap the bench iteration."""

BENCH_ITERATION = 1000
"""How many execution to measure."""


# ---- GLOBAL MESS ----#

# Clean up environment

itt.pause()
itt_domain = itt.domain_create("benchy.microphys")
progress = TimedProgress()
progress = TimedProgress()

with progress("🔁 Load data and de-serialize"):
    raw_data = xr.open_dataset(DATA_PATH)

    inputs = {}
    for name, xarray_data in raw_data.items():
        if IS_SERIALIZE_DATA:
            # Case of the scalar
            if len(xarray_data.shape) == 2:
                inputs[name] = xarray_data.data[0, 0]
            else:
                inputs[name] = xarray_data[0, 0, ::].data
        else:
            inputs[name] = xarray_data.data

grid_shape = (
    GRID["IM"],
    GRID["JM"],
    GRID["KM"],
    GRID["halo"],
)

with progress("🌏 Build Cube-Sphere"):
    stencil_factory, quantity_factory, grid_data, damping_coefficients = (
        setup_fv_cube_grid(
            layout=TILE_LAYOUT,
            tile_shape=grid_shape,
            backend=BACKEND,
            eta_file=ETA_FILE,
            eta_ak_bk_file=ETA_AK_BK_FILE,
            orchestrate=ORCHESTRATION,
        )
    )


with progress("🚆 Move data to Quantities"):
    for name, input_ in inputs.items():
        inputs[name] = raw_data_to_quantity(
            input_,
            grid_shape=grid_shape,
            quantity_factory=quantity_factory,
        )


with progress("🤸 Setup user code"):
    UW_config = UWConfiguration(inputs["ncnst"], inputs["k0"], inputs["windsrcavg"])
    uw = ComputeUwshcuInv(
        stencil_factory,
        quantity_factory,
        UW_config,
    )

    # The above garbage because of serialize data if the data was captured
    # none of this would exist
    for input_name, code_name in INPUT_NAME_TO_CODE_NAME.items():
        inputs[code_name] = inputs.pop(input_name)

    for name in INPUTS_TO_REMOVE:
        inputs.pop(name)

    inputs["testvar3D"] = quantity_factory.zeros(
        dims=[X_DIM, Y_DIM, Z_DIM], units="n/a"
    )

    # TODO: turn this on to get orchestration tested without the overhead
    if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
        benchy = BenchmarkUW(uw=uw, dace_config=stencil_factory.config.dace_config)
        inputs.update(BenchmarkUW.outputs(quantity_factory))

with progress(f"🔥 Warm bench ({BENCH_ITERATION} times)"):
    benchy(inputs, BENCH_ITERATION)

with progress(f"🚀 Bench ({BENCH_ITERATION} times)"):
    timings = {}
    if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
        itt.resume()
        itt.task_begin(itt_domain, "task_driver_microphys")
        benchy(inputs, BENCH_ITERATION)
        itt.task_end(itt_domain)
        itt.pause()
        timings = benchy.timings
    else:
        for _ in range(BENCH_ITERATION):
            with TimedCUDAProfiler("topline", timings):
                uw(**inputs)

with progress("📋 Making report"):
    # Header
    report = f"{BENCH_NAME} benchmark.\n\n"
    report += f"Timestamp: {datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}\n"
    report += f"Machine: {platform.system()} / {platform.machine()}\n"
    # report += "CPU: extract CPU info with `lscpu` on Linux and `sysctl -a` on Darwin\n"
    # if GPU_AVAILABLE:
    #     report += "GPU: to extract with cupy\n"
    # report += "Code versions\n"
    # report += "  ndsl: git hash\n"
    # report += "  gt4py: git hash\n"
    # report += "  dace: git hash\n"
    # report += "Compiler: read in CC?\n"
    report += f"Tile resolution: {grid_shape[0:3]} w/ halo={grid_shape[3]} "
    report += f"({grid_shape[0] * grid_shape[1] * grid_shape[2]} grid points per compute domain)\n"
    qty_zero = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], units="na")
    report += f"Memory strides (IJK): {[s // 8 for s in qty_zero.data.strides]}\n"
    if "dace" in BACKEND:
        prefix = (
            "orch:"
            if ORCHESTRATION in [DaCeOrchestration.Run, DaCeOrchestration.BuildAndRun]
            else "gt:"
        )
        report += f"Backend: {prefix}{BACKEND}\n"
    else:
        report += f"Backend: {BACKEND}\n"
    report += "\n"

    # # Timer
    median = np.median(timings["topline"])
    mean = np.mean(timings["topline"])
    min_ = np.min(timings["topline"])
    max_ = np.max(timings["topline"])
    report += f"Executions: {BENCH_ITERATION}.\n"
    report += "Timings in seconds (median [mean / min / max]):\n"
    report += f"  Topline: {median:.3} [{mean:.3}s/ {min_:.3} / {max_:.3}]\n"
    print(report)
