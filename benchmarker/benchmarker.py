"""Benchmark script, valid for serial or parallel code"""

# TODO list
# - How to expand the dataset knowing we need the Namelist (so GEOS is not an option)
#   - Re-use the C12 namelist and use data from another resolution
#   - Artificially expand C12 into CXX
# - Make it GPU worthy with upload to cupy arrays

import os
from datetime import datetime
import enum
import platform
import numpy as np
import f90nml
from pathlib import Path
import xarray as xr
import yaml
from setup_cube_sphere import setup_fv_cube_grid
from cuda_timer import TimedCUDAProfiler, GPU_AVAILABLE
from progress import TimedProgress
from benchmark_inlined_orch import BenchmarkMe
from data_ingester import raw_data_to_quantity
from ndsl.constants import X_DIM, Y_DIM, Z_DIM
from ndsl import DaCeOrchestration

import pyfv3.stencils.d_sw as d_sw
import pyfv3

# ---- GLOBAL MESS ----#
# In a better world those would becomes options

config_yaml = Path(__file__).absolute().parent / ".config.yaml"
if not config_yaml.exists():
    raise FileNotFoundError(f"Couldn't file config file. Expected one at path {config_yaml}. You can copy `.config-example.yaml` as a starting point.")

with open(config_yaml,"r") as config_file:
    # load machine dependent changes
    config=yaml.load(config_file, Loader=yaml.SafeLoader)

@enum.unique
class Exp(enum.Enum):
    C12_AI2 = enum.auto()
    C24_GEOS = enum.auto()


xp = Exp.C12_AI2

if xp == Exp.C12_AI2:
    GRID = {"IM": 12, "JM": 12, "KM": 79, "halo": 3}
    """The grid size as we expect it in the data."""
    DATA_PATH = config["paths"]["c12_AI2"]["data"]
    """Path to a netcdf with the input data."""
    ETA_FILE = config["paths"]["c12_AI2"]["eta_file"]
    ETA_AK_BK_FILE = None
    """Atmospheric level file to read for initialization of the grid. Generate from `ndsl` or saved from a previous runs (ak, bk)."""
    INPUT_NAME_TO_CODE_NAME = {
        "ucd": "uc",
        "vcd": "vc",
        "wd": "w",
        "delpcd": "delpc",
        "delpd": "delp",
        "ud": "u",
        "vd": "v",
        "xfxd": "xfx",
        "crxd": "crx",
        "yfxd": "yfx",
        "cryd": "cry",
        "mfxd": "mfx",
        "mfyd": "mfy",
        "cxd": "cx",
        "cyd": "cy",
        "heat_sourced": "heat_source",
        "diss_estd": "diss_est",
        "q_cond": "q_con",
        "ptd": "pt",
        "uad": "ua",
        "vad": "va",
        "zhd": "zh",
        "divgdd": "divgd",
    }
    """Mapping of saved named to expected names in the code"""
    INPUTS_TO_REMOVE = ["nq", "nord_v", "damp_vt", "zvir", "ptcd"]
    """List of inputs not used in the code signature"""
elif xp == Exp.C24_GEOS:
    GRID = {"IM": 24, "JM": 24, "KM": 72, "halo": 3}
    DATA_PATH = config["paths"]["c24_GEOS"]["data"]
    ETA_FILE = ""
    ETA_AK_BK_FILE = config["paths"]["c24_GEOS"]["eta_ak_bk_file"]
    INPUT_NAME_TO_CODE_NAME = {
        "ucd": "uc",
        "vcd": "vc",
        "wd": "w",
        "delpcd": "delpc",
        "delpd": "delp",
        "ud": "u",
        "vd": "v",
        "xfxd": "xfx",
        "crxd": "crx",
        "yfxd": "yfx",
        "cryd": "cry",
        "mfxd_R8": "mfx",
        "mfyd_R8": "mfy",
        "cxd_R8": "cx",
        "cyd_R8": "cy",
        "heat_sourced": "heat_source",
        "diss_estd": "diss_est",
        "q_cond": "q_con",
        "ptd": "pt",
        "uad": "ua",
        "vad": "va",
        "zhd": "zh",
        "divgdd": "divgd",
    }
    INPUTS_TO_REMOVE = ["nq", "nord_v", "damp_vt", "zvir", "ptcd", "dpx"]
else:
    raise NotImplementedError(f"Experiment {xp} just is not ")


TILE_LAYOUT = (1, 1)
"""The layout of a single tile, as we expect it into the data (for parallel codes)."""

NAMELIST = config["paths"]["namelist"]
"""Dynamics namelist - sorry."""

IS_SERIALIZE_DATA = True
"""Flag that our data comes from Fortran and therefore need special love."""

BACKEND = "dace:cpu" # ""gt:cpu_ifirst""
"""The One to bring them and in darkness speed them up."""

ORCHESTRATION = DaCeOrchestration.Python # DaCeOrchestration.BuildAndRun # None
"""Tune the orchestration strategy. Set to `None` if you are running `gt:X` backends for comparison."""

BENCH_WITHOUT_ORCHESTRATION_OVERHEAD = False
"""Wrap the bench iteration."""

BENCH_ITERATION = 1000
"""How many execution to measure."""

BENCH_NAME = "D_SW"
"""How many execution to measure."""

PERTUBATE_DATA_MODE = False
"""Copy the data BENCH_ITERATION time and apply a small sigma-noise on it.
This will slow down benchmarks and scale time with BENCH_ITERATION but probably be more
realistic.
"""

MONO_CORE = True
"""Deactivate threading to test the code in a single-core/thread capacity to mimicking
the hyperscaling strategy of GEOS"""

# ---- GLOBAL MESS ----#

# Clean up environment

os.environ["GT4PY_COMPILE_OPT_LEVEL"] = "3"
if MONO_CORE:
    os.environ["OMP_NUM_THREADS"] = "1"


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
    column_namelist = d_sw.get_column_namelist(
        config=dycore_config.acoustic_dynamics.d_grid_shallow_water,
        quantity_factory=quantity_factory,
    )

    d_sw = d_sw.DGridShallowWaterLagrangianDynamics(
        stencil_factory=stencil_factory,
        quantity_factory=quantity_factory,
        grid_data=grid_data,
        damping_coefficients=damping_coefficients,
        column_namelist=column_namelist,
        nested=False,
        stretched_grid=False,
        config=dycore_config.acoustic_dynamics.d_grid_shallow_water,
    )

    # The above garbage because of serialize data if the data was captured
    # none of this would exist
    for input_name, code_name in INPUT_NAME_TO_CODE_NAME.items():
        inputs[code_name] = inputs.pop(input_name)

    for name in INPUTS_TO_REMOVE:
        inputs.pop(name)

# First run - loading/compile/doesn't count

# TODO: turn this on to get orchestration tested without the overhead
if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
    benchy = BenchmarkMe(d_sw=d_sw, dace_config=stencil_factory.config.dace_config)
    with progress("🔥 Warm up: first run - doesn't count"):
        benchy(inputs, BENCH_ITERATION, inputs["dt"])
else:
    with progress("🔥 Warm up: first run - doesn't count"):
        d_sw(**inputs)

if PERTUBATE_DATA_MODE:
    with progress("🔀 Perturb data"):
        # Perturb data
        mean, sigma = 0, 0.01
        dataset = []
        for _ in range(BENCH_ITERATION):
            local_dataset = {}
            for name, input_data in inputs.items():
                local_dataset[name] = input_data + np.random.normal(
                    mean, sigma, size=input_data.shape
                )
            dataset.append(local_dataset)

    with progress(f"🚀 Bench ({BENCH_ITERATION} times)"):
        timings = {}
        # The below for-loop can't be orchestrated because dataset is a dynamic set of data (duh)
        for d in dataset:
            with TimedCUDAProfiler("topline", timings):
                d_sw(**d)
else:
    with progress(f"🚀 Bench ({BENCH_ITERATION} times)"):
        timings = {}
        if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
            benchy(inputs, BENCH_ITERATION, inputs["dt"])
            timings = benchy.timings
        else:
            for _ in range(BENCH_ITERATION):
                with TimedCUDAProfiler("topline", timings):
                    d_sw(**inputs)

with progress("📋 Making report"):
    # Header
    report = f"{BENCH_NAME} benchmark.\n\n"
    report += f"Timestamp: {datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}\n"
    report += f"Machine: {platform.system()} / {platform.machine()}\n"
    report += "CPU: extract CPU info with `lscpu` on Linux and `sysctl -a` on Darwin\n"
    if GPU_AVAILABLE:
        report += "GPU: to extract with cupy\n"
    report += "Code versions\n"
    report += "  ndsl: git hash\n"
    report += "  gt4py: git hash\n"
    report += "  dace: git hash\n"
    report += "Compiler: read in CC?\n"
    report += f"Tile resolution: {grid_shape[0:3]} w/ halo={grid_shape[3]} "
    report += f"({grid_shape[0] * grid_shape[1] * grid_shape[2]} grid points per compute domain)\n"
    qty_zero = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], units="na")
    report += f"Memory strides (IJK): {[s // 8 for s in qty_zero.data.strides]}\n"
    report += f"Backend: {'orch:' if ORCHESTRATION else ''}{BACKEND}\n"
    report += "\n"

    # Timer
    median = np.median(timings["topline"])
    mean = np.mean(timings["topline"])
    min_ = np.min(timings["topline"])
    max_ = np.max(timings["topline"])
    report += f"Executions: {BENCH_ITERATION}.\n"
    report += "Timings in seconds (median [mean / min / max]):\n"
    report += f"  Topline: {median:.3} [{mean:.3}s/ {min_:.3} / {max_:.3}]\n"
    print(report)
