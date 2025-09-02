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
from ndsl.constants import X_DIM, Y_DIM, Z_DIM
from ndsl import DaCeOrchestration

from pyMoist.GFDL_1M.driver.driver import MicrophysicsDriver
from pyMoist.GFDL_1M.config import GFDL1MConfig
from ndsl.stencils.testing.savepoint import DataLoader

import dace
from ndsl.dsl.dace.orchestration import orchestrate, dace_inhibitor


class BenchmarkMicrophysics:
    def __init__(self, dace_config, microphys):
        orchestrate(obj=self, config=dace_config)
        self._microphys = microphys
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
            self._microphys(
                t=inputs["T"],
                w=inputs["W"],
                u=inputs["U"],
                v=inputs["V"],
                dz=inputs["DZ"],
                dp=inputs["DP"],
                area=inputs["AREA"],
                land_fraction=inputs["FRLAND"],
                convection_fraction=inputs["CNV_FRC"],
                surface_type=inputs["SRF_TYPE"],
                estimated_inversion_strength=inputs["EIS"],
                rh_crit=inputs["RHCRIT3D"],
                vapor=inputs["RAD_QV"],
                liquid=inputs["RAD_QL"],
                rain=inputs["RAD_QR"],
                ice=inputs["RAD_QI"],
                snow=inputs["RAD_QS"],
                graupel=inputs["RAD_QG"],
                cloud_fraction=inputs["RAD_CF"],
                ice_concentration=inputs["NACTI"],
                liquid_concentration=inputs["NACTL"],
                dvapor_dt=inputs["DQVDTmic"],
                dliquid_dt=inputs["DQLDTmic"],
                drain_dt=inputs["DQRDTmic"],
                dice_dt=inputs["DQIDTmic"],
                dsnow_dt=inputs["DQSDTmic"],
                dgraupel_dt=inputs["DQGDTmic"],
                dcloud_fraction_dt=inputs["DQADTmic"],
                dt_dt=inputs["DTDTmic"],
                du_dt=inputs["DUDTmic"],
                dv_dt=inputs["DVDTmic"],
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


BENCH_NAME = "Microphys"
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
    CONSTANTS_PATH = c24_config["data_constants"]
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
# ORCHESTRATION = DaCeOrchestration.Run  # DaCeOrchestration.BuildAndRun
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
    constants = DataLoader(rank=0, data_path=CONSTANTS_PATH).load("GFDL_1M-constants")

    GFDL_1M_config = GFDL1MConfig(
        PHYS_HYDROSTATIC=bool(constants["LPHYS_HYDROSTATIC"]),
        HYDROSTATIC=bool(constants["LHYDROSTATIC"]),
        DT_MOIST=constants["DT_MOIST"],
        MP_TIME=constants["MP_TIME"],
        T_MIN=constants["T_MIN"],
        T_SUB=constants["T_SUB"],
        TAU_R2G=constants["TAU_R2G"],
        TAU_SMLT=constants["TAU_SMLT"],
        TAU_G2R=constants["TAU_G2R"],
        DW_LAND=constants["DW_LAND"],
        DW_OCEAN=constants["DW_OCEAN"],
        VI_FAC=constants["VI_FAC"],
        VR_FAC=constants["VR_FAC"],
        VS_FAC=constants["VS_FAC"],
        VG_FAC=constants["VG_FAC"],
        QL_MLT=constants["QL_MLT"],
        DO_QA=bool(constants["DO_QA"]),
        FIX_NEGATIVE=bool(constants["FIX_NEGATIVE"]),
        VI_MAX=constants["VI_MAX"],
        VS_MAX=constants["VS_MAX"],
        VG_MAX=constants["VG_MAX"],
        VR_MAX=constants["VR_MAX"],
        QS_MLT=constants["QS_MLT"],
        QS0_CRT=constants["QS0_CRT"],
        QI_GEN=constants["QI_GEN"],
        QL0_MAX=constants["QL0_MAX"],
        QI0_MAX=constants["QI0_MAX"],
        QI0_CRT=constants["QI0_CRT"],
        QR0_CRT=constants["QR0_CRT"],
        FAST_SAT_ADJ=bool(constants["FAST_SAT_ADJ"]),
        RH_INC=constants["RH_INC"],
        RH_INS=constants["RH_INS"],
        RH_INR=constants["RH_INR"],
        CONST_VI=bool(constants["CONST_VI"]),
        CONST_VS=bool(constants["CONST_VS"]),
        CONST_VG=bool(constants["CONST_VG"]),
        CONST_VR=bool(constants["CONST_VR"]),
        USE_CCN=bool(constants["USE_CCN"]),
        RTHRESHU=constants["RTHRESHU"],
        RTHRESHS=constants["RTHRESHS"],
        CCN_L=constants["CCN_L"],
        CCN_O=constants["CCN_O"],
        QC_CRT=constants["QC_CRT"],
        TAU_G2V=constants["TAU_G2V"],
        TAU_V2G=constants["TAU_V2G"],
        TAU_S2V=constants["TAU_S2V"],
        TAU_V2S=constants["TAU_V2S"],
        TAU_REVP=constants["TAU_REVP"],
        TAU_FRZ=constants["TAU_FRZ"],
        DO_BIGG=bool(constants["DO_BIGG"]),
        DO_EVAP=bool(constants["DO_EVAP"]),
        DO_SUBL=bool(constants["DO_SUBL"]),
        SAT_ADJ0=constants["SAT_ADJ0"],
        C_PIACR=constants["C_PIACR"],
        TAU_IMLT=constants["TAU_IMLT"],
        TAU_V2L=constants["TAU_V2L"],
        TAU_L2V=constants["TAU_L2V"],
        TAU_I2V=constants["TAU_I2V"],
        TAU_I2S=constants["TAU_I2S"],
        TAU_L2R=constants["TAU_L2R"],
        QI_LIM=constants["QI_LIM"],
        QL_GEN=constants["QL_GEN"],
        C_PAUT=constants["C_PAUT"],
        C_PSACI=constants["C_PSACI"],
        C_PGACS=constants["C_PGACS"],
        C_PGACI=constants["C_PGACI"],
        Z_SLOPE_LIQ=bool(constants["Z_SLOPE_LIQ"]),
        Z_SLOPE_ICE=bool(constants["Z_SLOPE_ICE"]),
        PROG_CCN=bool(constants["PROG_CCN"]),
        C_CRACW=constants["C_CRACW"],
        ALIN=constants["ALIN"],
        CLIN=constants["CLIN"],
        PRECIPRAD=bool(constants["PRECIPRAD"]),
        CLD_MIN=constants["CLD_MIN"],
        USE_PPM=bool(constants["USE_PPM"]),
        MONO_PROF=bool(constants["MONO_PROF"]),
        DO_SEDI_HEAT=bool(constants["DO_SEDI_HEAT"]),
        SEDI_TRANSPORT=bool(constants["SEDI_TRANSPORT"]),
        DO_SEDI_W=bool(constants["DO_SEDI_W"]),
        DE_ICE=bool(constants["DE_ICE"]),
        ICLOUD_F=constants["ICLOUD_F"],
        IRAIN_F=constants["IRAIN_F"],
        MP_PRINT=bool(constants["MP_PRINT"]),
        MELTFRZ=bool(constants["LMELTFRZ"]),
        USE_BERGERON=bool(constants["USE_BERGERON"]),
        TURNRHCRIT_PARAM=constants["TURNRHCRIT_PARAM"],
        PDF_SHAPE=constants["PDFSHAPE"],
        ANV_ICEFALL=constants["ANV_ICEFALL"],
        LS_ICEFALL=constants["LS_ICEFALL"],
        LIQ_RADII_PARAM=constants["LIQ_RADII_PARAM"],
        ICE_RADII_PARAM=constants["ICE_RADII_PARAM"],
        FAC_RI=constants["FAC_RI"],
        MIN_RI=constants["MIN_RI"],
        MAX_RI=constants["MAX_RI"],
        FAC_RL=constants["FAC_RL"],
        MIN_RL=constants["MIN_RL"],
        MAX_RL=constants["MAX_RL"],
        CCW_EVAP_EFF=constants["CCW_EVAP_EFF"],
        CCI_EVAP_EFF=constants["CCI_EVAP_EFF"],
    )
    microphys = MicrophysicsDriver(
        stencil_factory,
        quantity_factory,
        GFDL_1M_config,
    )

    # The above garbage because of serialize data if the data was captured
    # none of this would exist
    for input_name, code_name in INPUT_NAME_TO_CODE_NAME.items():
        inputs[code_name] = inputs.pop(input_name)

    for name in INPUTS_TO_REMOVE:
        inputs.pop(name)

    # TODO: turn this on to get orchestration tested without the overhead
    if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
        benchy = BenchmarkMicrophysics(
            microphys=microphys, dace_config=stencil_factory.config.dace_config
        )

with progress(f"🚀 Bench ({BENCH_ITERATION} times)"):
    timings = {}
    if BENCH_WITHOUT_ORCHESTRATION_OVERHEAD:
        itt.resume()
        itt.task_begin(itt_domain, "task_driver_microphys")
        benchy(inputs, BENCH_ITERATION)
        itt.task_end()
        itt.pause()
        timings = benchy.timings
    else:
        for _ in range(BENCH_ITERATION):
            with TimedCUDAProfiler("topline", timings):
                microphys(**inputs)

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
