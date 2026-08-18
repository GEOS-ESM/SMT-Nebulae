from typing import Tuple

import gt4py.cartesian.gtscript as gtscript
from gt4py.cartesian.gtscript import (
    __INLINED,
    PARALLEL,
    computation,
    horizontal,
    interval,
    region,
    I,
    J,
)

from ndsl import (
    CompilationConfig,
    DaceConfig,
    DaCeOrchestration,
    GridIndexing,
    NullComm,
    QuantityFactory,
    RunMode,
    StencilConfig,
    StencilFactory,
    SubtileGridSizer,
    TileCommunicator,
    TilePartitioner,
)
from ndsl.constants import X_DIM, X_INTERFACE_DIM, Y_DIM, Y_INTERFACE_DIM, Z_DIM
from ndsl.dsl.typing import Float, FloatField, FloatField64, FloatFieldIJ, IntField, Int, IntFieldIJ
from ndsl.grid import DampingCoefficients, GridData
from ndsl.quantity import Quantity

import numpy as np

def get_one_tile_factory_orchestrated(
    nx, ny, nz, nhalo, backend
) -> Tuple[StencilFactory, QuantityFactory]:
    """Create a 1 tile grid - no boundaries"""
    dace_config = DaceConfig(
        communicator=None,
        backend=backend,
        orchestration=DaCeOrchestration.Python,
    )

    compilation_config = CompilationConfig(
        backend=backend,
        rebuild=True,
        validate_args=True,
        format_source=False,
        device_sync=False,
        run_mode=RunMode.BuildAndRun,
        use_minimal_caching=False,
    )

    stencil_config = StencilConfig(
        compare_to_numpy=False,
        compilation_config=compilation_config,
        dace_config=dace_config,
    )

    grid_indexing = GridIndexing(
        domain=(nx, ny, nz),
        n_halo=nhalo,
        south_edge=True,
        north_edge=True,
        west_edge=True,
        east_edge=True,
    )

    stencil_factory = StencilFactory(config=stencil_config, grid_indexing=grid_indexing)

    return stencil_factory

def add_scalar_to_quantity_stencil(int_scalar: Int, float_scalar: Float, int_3D: IntField, float_3D : FloatField):
    with computation(PARALLEL), interval(...):
        float_3D = float_3D + float_scalar
        int_3D = int_3D + int_scalar

def add_2D_quantity_to_3D_quantity_stencil(int_2D: IntFieldIJ, float_2D: FloatFieldIJ, int_3D: IntField, float_3D : FloatField):
    with computation(PARALLEL), interval(...):
        float_3D = float_3D + float_2D
        int_3D = int_3D + int_2D

class add_scalar:
    def __init__(self):
        self.stencil_factory = get_one_tile_factory_orchestrated(3, 3, 3, 0, "numpy")

        self._add_scalar = self.stencil_factory.from_origin_domain(
            add_scalar_to_quantity_stencil,
            origin=(0,0,0),
            domain=(3,3,3),
        )

    def __call__(self,
                 int_scalar,
                 float_scalar,
                 int_3D,
                 float_3D):
        
        self._add_scalar(int_scalar, float_scalar, int_3D, float_3D)    

class add_2D_quantity_to_3D_quantity:
    def __init__(self):
        self.stencil_factory = get_one_tile_factory_orchestrated(3, 3, 3, 0, "numpy")

        self._add_2d_quantity_to_3d_quantity = self.stencil_factory.from_origin_domain(
            add_2D_quantity_to_3D_quantity_stencil,
            origin=(0,0,0),
            domain=(3,3,3),
        )

    def __call__(self,
                 int_scalar,
                 float_scalar,
                 int_3D,
                 float_3D):
        
        self._add_2d_quantity_to_3d_quantity(int_scalar, float_scalar, int_3D, float_3D)