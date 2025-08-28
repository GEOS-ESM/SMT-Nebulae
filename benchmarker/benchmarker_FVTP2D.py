"""Benchmark script, valid for serial or parallel code"""

# TODO list
# - How to expand the dataset knowing we need the Namelist (so GEOS is not an option)
#   - Re-use the C12 namelist and use data from another resolution
#   - Artificially expand C12 into CXX
# - Make it GPU worthy with upload to cupy arrays

import enum
import os

from datetime import datetime
import platform
import numpy as np
import f90nml
from pathlib import Path
import xarray as xr
import yaml
from setup_cube_sphere import setup_fv_cube_grid
from cuda_timer import TimedCUDAProfiler, GPU_AVAILABLE
from progress import TimedProgress
from data_ingester import raw_data_to_quantity
from ndsl.constants import X_DIM, Y_DIM, Z_DIM
from ndsl import DaCeOrchestration

from pyfv3.stencils.fvtp2d import FiniteVolumeTransport
import pyfv3


import dace
from ndsl.dsl.dace.orchestration import orchestrate, dace_inhibitor
from ndsl.dsl.typing import Float


class BenchmarkMeFVTP2D:
    def __init__(self, dace_config, fvtp2d):
        orchestrate(obj=self, config=dace_config)
        self._fvtp2d = fvtp2d
        self.timings = {}
        self._timer = TimedCUDAProfiler("topline", self.timings)

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
            self._fvtp2d(
                q=inputs["q"],
                crx=inputs["crx"],
                cry=inputs["cry"],
                x_area_flux=inputs["x_area_flux"],
                y_area_flux=inputs["y_area_flux"],
                q_x_flux=inputs["q_x_flux"],
                q_y_flux=inputs["q_y_flux"],
                x_mass_flux=inputs["x_mass_flux"],
                y_mass_flux=inputs["y_mass_flux"],
                mass=inputs["mass"],
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
        "You can copy `.config-example.yaml` as a starting point."
    )

with open(config_yaml, "r") as config_file:
    # load machine dependent changes
    config = yaml.load(config_file, Loader=yaml.SafeLoader)


@enum.unique
class Exp(enum.Enum):
    C12_AI2 = enum.auto()
    C24_GEOS = enum.auto()


BENCH_NAME = "FvTp2d"
"""Benchmark name & config key."""
xp = Exp.C12_AI2

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
BACKEND = "dace:cpu"
"""The One to bring them and in darkness speed them up."""

ORCHESTRATION = (
    DaCeOrchestration.BuildAndRun
)  # DaCeOrchestration.Run  # DaCeOrchestration.BuildAndRun # None
# ORCHESTRATION = DaCeOrchestration.BuildAndRun
"""Tune the orchestration strategy. Set to `None` if you are running `gt:X` backends for comparison."""

BENCH_WITHOUT_ORCHESTRATION_OVERHEAD = True
"""Wrap the bench iteration."""

BENCH_ITERATION = 1000
"""How many execution to measure."""


# ---- GLOBAL MESS ----#

# Clean up environment

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
    f90_nml = f90nml.read(NAMELIST)
    dycore_config = pyfv3.DynamicalCoreConfig.from_f90nml(f90_nml)
    # inputs["q_x_flux"] = utils.make_storage_from_shape(
    #     self.maxshape,
    #     self.grid.full_origin(),
    #     backend=self.stencil_factory.backend,
    # )
    # inputs["q_y_flux"] = utils.make_storage_from_shape(
    #     self.maxshape,
    #     self.grid.full_origin(),
    #     backend=self.stencil_factory.backend,
    # )
    inputs["q_x_flux"] = quantity_factory.zeros(
        dims=[X_DIM, Y_DIM, Z_DIM], units="unknown", dtype=Float
    )
    inputs["q_y_flux"] = quantity_factory.zeros(
        dims=[X_DIM, Y_DIM, Z_DIM], units="unknown", dtype=Float
    )

    nord_col = quantity_factory.zeros(dims=[Z_DIM], units="unknown", dtype=Float)
    nord_col.data[:-1] = nord_col.np.asarray(inputs.pop("nord_column"))
    damp_c = quantity_factory.zeros(dims=[Z_DIM], units="unknown", dtype=Float)
    damp_c.data[:-1] = damp_c.np.asarray(inputs.pop("damp_c"))
    for optional_arg in ["mass"]:
        if optional_arg not in inputs:
            inputs[optional_arg] = None
    fvtp2d = FiniteVolumeTransport(  # type: ignore
        stencil_factory=stencil_factory,
        quantity_factory=quantity_factory,
        grid_data=grid_data,
        damping_coefficients=damping_coefficients,
        grid_type=dycore_config.grid_type,
        hord=int(inputs.pop("hord")),
        nord=nord_col,
        damp_c=damp_c,
    )

    # The above garbage because of serialize data if the data was captured
    # none of this would exist
    for input_name, code_name in INPUT_NAME_TO_CODE_NAME.items():
        inputs[code_name] = inputs.pop(input_name)

    for name in INPUTS_TO_REMOVE:
        inputs.pop(name)

    # TODO: turn this on to get orchestration tested without the overhead
    if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
        benchy = BenchmarkMeFVTP2D(
            fvtp2d=fvtp2d, dace_config=stencil_factory.config.dace_config
        )

with progress(f"🚀 Bench ({BENCH_ITERATION} times)"):
    timings = {}
    if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
        benchy(inputs, BENCH_ITERATION)
        timings = benchy.timings
    else:
        for _ in range(BENCH_ITERATION):
            with TimedCUDAProfiler("topline", timings):
                fvtp2d(**inputs)

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
        report += f"Backend: {'orch:' if ORCHESTRATION in [DaCeOrchestration.Run, DaCeOrchestration.BuildAndRun] else 'gt:'}{BACKEND}\n"
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
