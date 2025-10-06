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

import pyMoist.UW as pyUW
from pyMoist.UW.compute_uwshcu import ComputeUwshcuInv
from pyMoist.UW.config import UWConfiguration


import dace
from ndsl.dsl.dace.orchestration import orchestrate, dace_inhibitor


class BenchmarkUWWithState:
    def __init__(self, dace_config, uw):
        orchestrate(obj=self, config=dace_config, dace_compiletime_args=["state"])
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
        state: pyUW.ShallowConvectionState,
        scalars_dict: dace.compiletime,
        iteration: int,
    ):
        for _ in dace.nounroll(range(iteration)):
            self._start_timer()
            self._uw(
                # Field inputs
                state=state,
                # Float/Int inputs
                dotransport=scalars_dict["dotransport"],
                k0=scalars_dict["k0"],
                windsrcavg=scalars_dict["windsrcavg"],
                qtsrchgt=scalars_dict["qtsrchgt"],
                qtsrc_fac=scalars_dict["qtsrc_fac"],
                thlsrc_fac=scalars_dict["thlsrc_fac"],
                frc_rasn=scalars_dict["frc_rasn"],
                rbuoy=scalars_dict["rbuoy"],
                epsvarw=scalars_dict["epsvarw"],
                use_CINcin=scalars_dict["use_CINcin"],
                mumin1=scalars_dict["mumin1"],
                rmaxfrac=scalars_dict["rmaxfrac"],
                PGFc=scalars_dict["PGFc"],
                dt=scalars_dict["dt"],
                niter_xc=scalars_dict["niter_xc"],
                criqc=scalars_dict["criqc"],
                rle=scalars_dict["rle"],
                cridist_opt=scalars_dict["cridist_opt"],
                mixscale=scalars_dict["mixscale"],
                rdrag=scalars_dict["rdrag"],
                rkm=scalars_dict["rkm"],
                use_self_detrain=scalars_dict["use_self_detrain"],
                detrhgt=scalars_dict["detrhgt"],
                use_cumpenent=scalars_dict["use_cumpenent"],
                rpen=scalars_dict["rpen"],
                use_momenflx=scalars_dict["use_momenflx"],
                rdrop=scalars_dict["rdrop"],
                iter_cin=scalars_dict["iter_cin"],
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
    GRID = {"IM": 12, "JM": 12, "KM": 79, "halo": 0}
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
    GRID = {"IM": 24, "JM": 24, "KM": 72, "halo": 0}
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

ORCHESTRATION = DaCeOrchestration.BuildAndRun
# ORCHESTRATION = DaCeOrchestration.Python
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
                inputs[name] = xarray_data.data[0, 5]
            else:
                inputs[name] = xarray_data[0, 5, ::].data
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
            compute_grid_data=False,
        )
    )


# with progress("🚆 Move data to Quantities"):
#     for name, input_ in inputs.items():
#         inputs[name] = raw_data_to_quantity(
#             input_,
#             grid_shape=grid_shape,
#             quantity_factory=quantity_factory,
#         )


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

    scalars_inputs = [
        "dotransport",
        "k0",
        "windsrcavg",
        "qtsrchgt",
        "qtsrc_fac",
        "thlsrc_fac",
        "frc_rasn",
        "rbuoy",
        "epsvarw",
        "use_CINcin",
        "mumin1",
        "rmaxfrac",
        "PGFc",
        "dt",
        "niter_xc",
        "criqc",
        "rle",
        "cridist_opt",
        "mixscale",
        "rdrag",
        "rkm",
        "use_self_detrain",
        "detrhgt",
        "use_cumpenent",
        "rpen",
        "use_momenflx",
        "rdrop",
        "iter_cin",
    ]
    scalars_dict = {}
    for s in scalars_inputs:
        scalars_dict[s] = inputs.pop(s)

    uw_state = pyUW.ShallowConvectionState.zeros(
        quantity_factory, extra_ddims={"ntracers": UW_config.NCNST}
    )
    uw_state.update_copy_memory(inputs)

    # TODO: turn this on to get orchestration tested without the overhead
    if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
        benchy = BenchmarkUW(uw=uw, dace_config=stencil_factory.config.dace_config)
        inputs.update(BenchmarkUW.outputs(quantity_factory))

with progress(f"🔥 Warm bench ({BENCH_ITERATION} times)"):
    benchy(uw_state, scalars_dict, BENCH_ITERATION)

with progress(f"🚀 Bench ({BENCH_ITERATION} times)"):
    timings = {}
    if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
        itt.resume()
        itt.task_begin(itt_domain, "task_uw")
        benchy(uw_state, scalars_dict, BENCH_ITERATION)
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
