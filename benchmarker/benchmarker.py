"""Benchmark script, valid for serial or parallel code"""

from datetime import datetime
import platform
import numpy as np
import f90nml
import xarray as xr
from setup_cube_sphere import setup_fv_cube_grid
from cuda_timer import TimedCUDAProfiler, GPU_AVAILABLE
from progress import TimedProgress
from data_ingester import xarray_data_to_quantity

import pyFV3.stencils.d_sw as d_sw
import pyFV3

# ---- GLOBAL MESS ----#
# In a better world those would becomes options
GRID = {"IM": 12, "JM": 12, "KM": 79, "halo": 3}
"""The grid size as we expect it in the data"""

TILE_LAYOUT = (1, 1)
"""The layout of a single tile, as we expect it into the data (for parallel codes)"""

DATA_DIR = "/home/fgdeconi/work/git/pyfv3/test_data/8.1.3/c12_6ranks_standard/dycore"
"""We expect all data to be nicely put in there. Developed against the serialize workflow."""

DATA_NAME = "D_SW-In.nc"
"""NetCDFs to read in for input data."""

ETA_FILE = "/home/fgdeconi/work/git/ndsl/eta79.nc"
"""Atmospheric level file to read for initialization of the grid. Generate from `ndsl` if need be."""

NAMELIST = (
    "/home/fgdeconi/work/git/pyfv3/test_data/8.1.3/c12_6ranks_standard/dycore/input.nml"
)
"""Dynamics namelist - sorry."""

IS_SERIALIZE_DATA = True
"""Flag that our data comes from Fortran and therefore need special love."""

BACKEND = "dace:cpu"
"""The One to bring them and in darkness speed them up."""

ORCHESTRATION = True
"""Bring all code under a single compiled code."""

BENCH_ITERATION = 1000
"""How many execution to measure."""

BENCH_NAME = "D_SW"
"""How many execution to measure."""

PERTUBATE_DATA_MODE = True
"""Copy the data BENCH_ITERATION time and apply a small sigma-noise on it."""
# ---- GLOBAL MESS ----#


progress = TimedProgress()
grid_shape = (GRID["IM"], GRID["JM"], GRID["KM"], GRID["halo"])

with progress("🌏 Build Cube-Sphere"):
    stencil_factory, quantity_factory, grid_data, damping_coefficients = (
        setup_fv_cube_grid(
            layout=TILE_LAYOUT,
            tile_shape=grid_shape,
            backend=BACKEND,
            eta_file=ETA_FILE,
            orchestrate=ORCHESTRATION,
        )
    )


with progress("🚆 Load & move data to Quantities"):
    raw_data = xr.open_dataset(f"{DATA_DIR}/{DATA_NAME}")

    inputs = {}
    for name in raw_data.keys():
        inputs[name] = xarray_data_to_quantity(
            raw_data[name],
            grid_shape=grid_shape,
            quantity_factory=quantity_factory,
            serialized_data=IS_SERIALIZE_DATA,
        )


with progress("🤸 Setup user code"):
    f90_nml = f90nml.read(NAMELIST)
    dycore_config = pyFV3.DynamicalCoreConfig.from_f90nml(f90_nml)
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
    input_name_to_code_name = {
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
    for input_name, code_name in input_name_to_code_name.items():
        inputs[code_name] = inputs.pop(input_name)

    inputs_to_remove = ["nq", "nord_v", "damp_vt", "zvir", "ptcd"]
    for name in inputs_to_remove:
        inputs.pop(name)

# First run - loading/compile/doesn't count

with progress("🔥 Warm up: first run - doesn't count"):
    d_sw(**inputs)

if PERTUBATE_DATA_MODE:
    with progress("🔀 Pertubate data"):
        # Pertub data
        mean, sigma = 0, 0.01
        dataset = []
        for _n in range(BENCH_ITERATION):
            local_dataset = {}
            for name, input_data in inputs.items():
                local_dataset[name] = input_data + np.random.normal(
                    mean, sigma, size=input_data.shape
                )
            dataset.append(local_dataset)

    with progress(f"🚀 Bench ({BENCH_ITERATION} times)"):
        timings = {}
        with TimedCUDAProfiler("topline", timings) as total_timer:
            # The below for-loop can't be orchestrated because dataset is a dybamic set of data (duh)
            for d in dataset:
                d_sw(**d)
else:
    with progress(f"🚀 Bench ({BENCH_ITERATION} times)"):
        timings = {}
        with TimedCUDAProfiler("topline", timings) as total_timer:
            # ⚠️ This could be orchestrated if we want a "no python" bench ⚠️
            # But that means re-compiling if bench iteration is different
            for _n in range(BENCH_ITERATION):
                d_sw(**inputs)

with progress("📋 Making report"):
    # Header
    report = f"{BENCH_NAME} benchmark.\n\n"
    report += f"Timestamp: {datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}\n"
    report += f"Machine: {platform.machine()} / {platform.processor()}\n"
    report += "CPU: extract CPU info with `lscpu` on Linux and `sysctl -a` on Darwin\n"
    if GPU_AVAILABLE:
        report += "GPU: to extract with cupy\n"
    report += f"Tile resolution: {grid_shape[0:3]} w/ halo={grid_shape[3]} "
    report += f"({grid_shape[0] * grid_shape[1] * grid_shape[2]} grid points per compute domain)\n"
    report += "ndsl version: git hash\n"
    report += "gt4py version: git hash\n"
    report += "dace version: git hash\n"
    report += "\n"

    # Timer
    total = timings["topline"][0]
    time_per_call = total / BENCH_ITERATION
    report += f"Topline: {time_per_call:.3}s (total: {total:.3})"
    print(report)
