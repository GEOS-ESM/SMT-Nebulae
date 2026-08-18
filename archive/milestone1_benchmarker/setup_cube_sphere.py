import xarray as xr
from ndsl import (
    CubedSphereCommunicator,
    CubedSpherePartitioner,
    TilePartitioner,
    SubtileGridSizer,
    QuantityFactory,
    MPIComm,
    NullComm,
    StencilConfig,
    CompilationConfig,
    DaceConfig,
    GridIndexing,
    StencilFactory,
    DaCeOrchestration,
)
from ndsl.grid import MetricTerms, GridData, DampingCoefficients


def setup_fv_cube_grid(
    layout: tuple[int, int],
    tile_shape: tuple[int, int, int, int],
    backend: str,
    eta_file: str | None,
    eta_ak_bk_file: str | None,
    orchestrate: DaCeOrchestration | None,
    compute_grid_data: bool = True,
):
    """

    Args:
        layout: X/Y layout of the cube for a single tile, e.g. 2,2 will split a tile in 4 sub-tiles
        tile_shape: 4-element tuple describing the shape of tile of the form (I, J, K, Horizontal Halo)
        backend: the backend
        eta_file: netcdfs with pressure levels
        orchestrate: run in orchestration mode (BuildAndRun)
    """
    comm = MPIComm()
    if comm.Get_size() == 1:
        comm = NullComm(0, 6, 1)

    partitioner = CubedSpherePartitioner(TilePartitioner(layout))
    communicator = CubedSphereCommunicator(
        comm,
        partitioner,
        # timer=self.perf_collector.timestep_timer, # We might want that
    )

    _sizer = SubtileGridSizer.from_tile_params(
        nx_tile=tile_shape[0],
        ny_tile=tile_shape[1],
        nz=tile_shape[2],
        n_halo=tile_shape[3],
        extra_dim_lengths={},  # No NDs
        layout=layout,
        tile_partitioner=partitioner.tile,
        tile_rank=communicator.rank,
    )
    quantity_factory = QuantityFactory.from_backend(sizer=_sizer, backend=backend)

    # set up the metric terms and grid data, we filter warnings because in single tile
    # mode where communicator is NullComm we know we are doing bad calculation on edge of the
    # grid...
    if compute_grid_data:
        if eta_ak_bk_file is not None:
            ak_bk_data = xr.open_dataset(eta_ak_bk_file)
            metric_terms = MetricTerms(
                quantity_factory=quantity_factory,
                communicator=communicator,
                ak=ak_bk_data["ak"].data,
                bk=ak_bk_data["bk"].data,
            )
        else:
            metric_terms = MetricTerms(
                quantity_factory=quantity_factory,
                communicator=communicator,
                eta_file=eta_file,
            )
        grid_data = GridData.new_from_metric_terms(metric_terms)
        damping_coefficients = DampingCoefficients.new_from_metric_terms(metric_terms)
    else:
        grid_data = None
        damping_coefficients = None

    stencil_config = StencilConfig(
        compilation_config=CompilationConfig(
            backend=backend, rebuild=False, validate_args=False
        ),
    )

    # Build a DaCeConfig for orchestration.
    # This and all orchestration code are transparent when outside
    # configuration deactivate orchestration
    if orchestrate is not None:
        stencil_config.dace_config = DaceConfig(
            communicator=communicator,
            backend=stencil_config.backend,
            tile_nx=tile_shape[0],
            tile_nz=tile_shape[1],
            orchestration=orchestrate,
        )

    grid_indexing = GridIndexing.from_sizer_and_communicator(
        sizer=_sizer, comm=communicator
    )
    stencil_factory = StencilFactory(config=stencil_config, grid_indexing=grid_indexing)

    return stencil_factory, quantity_factory, grid_data, damping_coefficients
