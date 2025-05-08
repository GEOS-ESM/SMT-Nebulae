import enum
import logging
import os
from datetime import timedelta
from typing import Dict, List, Tuple

import f90nml
import numpy as np
from gt4py.cartesian.config import build_settings as gt_build_settings
from mpi4py import MPI

import pyFV3
from ndsl import (
    CompilationConfig,
    CubedSphereCommunicator,
    CubedSpherePartitioner,
    DaceConfig,
    DaCeOrchestration,
    GridIndexing,
    NullComm,
    PerformanceCollector,
    QuantityFactory,
    StencilConfig,
    StencilFactory,
    SubtileGridSizer,
    TilePartitioner,
    orchestrate,
)
import ndsl.constants
from ndsl.comm.comm_abc import Comm
from ndsl.dsl.dace.build import set_distributed_caches
from ndsl.dsl.gt4py_utils import is_gpu_backend
from ndsl.dsl.typing import floating_point_precision
from ndsl.grid import DampingCoefficients, GridData, MetricTerms
from ndsl.logging import ndsl_log
from ndsl.optional_imports import cupy as cp
from ndsl.utils import safe_assign_array
from fv_flags import FVFlags, FVFlags_to_DycoreConfig
from ndsl.comm.mpi import MPIComm
from pyFV3.tracers import Tracers

from pyMoist.UW.compute_uwshcu import ComputeUwshcuInv

TRACERS_IN_FORTRAN = [
    "vapor",
    "liquid",
    "ice",
    "rain",
    "snow",
    "graupel",
    "cloud",
]

class UWSHCU_Wrapper:

    def __init__(
        self,
    ):
        print("UW_Wrapper.__init__")

        BACKEND = os.environ.get("GEOS_PYFV3_BACKEND", "gt:gpu")

        # Look for an override to run on a single node
        single_rank_override = int(os.getenv("GEOS_PYFV3_SINGLE_RANK_OVERRIDE", -1))
        if single_rank_override >= 0:
            comm = NullComm(single_rank_override, 6, 42)
        comm = MPIComm()

        # Make a custom performance collector for the UW wrapper
        self.perf_collector = PerformanceCollector("UWSHCU wrapper", comm)

        self.backend = BACKEND
        self.dycore_config = pyFV3._config.DynamicalCoreConfig()
        self.layout = self.dycore_config.layout
        
        partitioner = CubedSpherePartitioner(TilePartitioner(self.layout))
        self.communicator = CubedSphereCommunicator(
            comm,
            partitioner,
            timer=self.perf_collector.timestep_timer,
        )

        sizer = SubtileGridSizer.from_tile_params(
            nx_tile=self.dycore_config.npx - 1,  # NX/NY from config are cell-centers
            ny_tile=self.dycore_config.npy - 1,  # NX/NY from config are cell-centers
            nz=self.dycore_config.npz,
            n_halo=ndsl.constants.N_HALO_DEFAULT,
            extra_dim_lengths={},
            layout=self.dycore_config.layout,
            tile_partitioner=partitioner.tile,
            tile_rank=self.communicator.tile.rank,
        )

        quantity_factory = QuantityFactory.from_backend(sizer=sizer, backend=BACKEND)

        stencil_config = StencilConfig(
            compilation_config=CompilationConfig(
                backend=BACKEND, rebuild=False, validate_args=False
            ),
        )

        # Build a DaCeConfig for orchestration.
        # This and all orchestration code are transparent when outside
        # configuration deactivate orchestration
        stencil_config.dace_config = DaceConfig(
            communicator=self.communicator,
            backend=stencil_config.backend,
            tile_nx=self.dycore_config.npx,
            tile_nz=self.dycore_config.npz,
        )
        self._is_orchestrated = stencil_config.dace_config.is_dace_orchestrated()

        self._grid_indexing = GridIndexing.from_sizer_and_communicator(
            sizer=sizer, comm=self.communicator
        )

        stencil_factory = StencilFactory(
            config=stencil_config, grid_indexing=self._grid_indexing
        )

        self.compute_uwshcu = ComputeUwshcuInv(
            stencil_factory,
            quantity_factory,
        )

    def __call__():
        print("UW_Wrapper.__call__")
        # This is where the actual work would be done
        # For now, just return a dummy value
        return 0