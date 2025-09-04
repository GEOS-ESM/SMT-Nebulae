from ndsl import Quantity, QuantityFactory
from ndsl.buffer import safe_assign_array
from ndsl.constants import (
    X_DIM,
    Y_DIM,
    Z_DIM,
    X_INTERFACE_DIM,
    Y_INTERFACE_DIM,
    Z_INTERFACE_DIM,
)
import numpy as np
import numpy.typing as npt

base_dims = [X_DIM, Y_DIM, Z_DIM]
interface_dims = [X_INTERFACE_DIM, Y_INTERFACE_DIM, Z_INTERFACE_DIM]


def raw_data_to_quantity(
    data: npt.ArrayLike,
    grid_shape: tuple[int, int, int, int],
    quantity_factory: QuantityFactory,
) -> Quantity | np.float32 | np.float64 | np.int32 | np.int64:
    shp = data.shape

    if len(data.shape) == 0:
        return data

    # Detect the cartesian dimensions
    dims = []
    slc = []
    halo = grid_shape[3]
    for i, s in enumerate(shp):
        if i > 2:
            break  # Data Dimensions
        if s == grid_shape[i]:
            dims.append(base_dims[i])
            slc.append(slice(halo, -(halo + 1)))
        elif s == grid_shape[i] + 2 * halo:
            dims.append(base_dims[i])
            slc.append(slice(None, -1))
        elif s == grid_shape[i] + 1:
            dims.append(interface_dims[i])
            slc.append(slice(halo, -halo))
        elif s == grid_shape[i] + 2 * halo + 1:
            dims.append(interface_dims[i])
            slc.append(slice(None, None))
        else:
            # Everything failed - we give back the data "as-is"
            return data

    if len(dims) > 2:
        if dims[2] == Z_DIM:
            slc[2] = slice(None, -1)
        else:
            slc[2] = slice(None, None)

    # Append full slice for all other dims (data dims)
    if len(shp) > 4:
        raise NotImplementedError(
            "4D but not more. Change the qty factory and slicing code"
        )

    for _ in range(0, len(shp) - len(slc)):
        slc.append(slice(None, None))
        dims.append("wot")

    if len(shp) > 3:
        import copy

        ddim_quantity_factory = copy.deepcopy(quantity_factory)
        ddim_quantity_factory.set_extra_dim_lengths(wot=shp[3])
        qty = ddim_quantity_factory.empty(
            dims=dims,
            units="BENCH!",
        )
    else:
        qty = quantity_factory.empty(
            dims=dims,
            units="BENCH!",
        )

    safe_assign_array(qty.data[tuple(slc)], data)

    return qty
