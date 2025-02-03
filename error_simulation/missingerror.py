"""FLEXIBLE SCRIPT USED TO GENERATE ERRORS"""

# POTENTIAL MISSING ERROR AT stencil_object.py line 490, this script shows a series of cases that
# incorrectly pull data from (potentially) illegal portions of the halo
# NOTE behavior to be verified by someone else, REMOVE ME WHEN VERIFIED or delete file if correct

from gt4py.cartesian.gtscript import (
    computation,
    interval,
    PARALLEL,
    FORWARD,
    i64,
    i32,
    f64,
    f32,
)
from ndsl.boilerplate import get_factories_single_tile
from ndsl.constants import X_DIM, Y_DIM, Z_DIM, Z_INTERFACE_DIM
from ndsl.dsl.typing import FloatField, FloatFieldIJ, Float, IntField, IntFieldIJ, Int
from ndsl import StencilFactory, QuantityFactory, orchestrate
import numpy as np

domain = (3, 3, 4)
nhalo = 0
stencil_factory, quantity_factory = get_factories_single_tile(
    domain[0], domain[1], domain[2], nhalo, backend="debug"
)


def stencil(
    input: FloatField,
    output: FloatField,
    factor: Int,
):
    with computation(PARALLEL), interval(...):
        # NOTE THE FOLLOWING TWO LINES ARE THE CRUX OF THE ISSUE, others are included for completeness
        # output = input[-1, 0, 1]  # works, should fail: X_DIM should be out of bounds at K = 0
        # output = input[-1, 0, 0]  # fails, should fail: X_DIM is out of bounds at K = 0

        # output = input[-1, -1, -1]  # fails, should fail: all three indexes are out of bounds at K = 0
        # output = input[1, 1, 1]  # works, should work: enables pulling from interface dim at K = kend
        # output = input[1, 1, 2]  # fails, should fail: Z_DIM is out of bounds at K = kend
        # output = input[0, 0, 0]  # works, should work: if this fails I quit


class Code:
    def __init__(
        self,
        stencil_factory: StencilFactory,
        quantity_factory: QuantityFactory,
    ):
        orchestrate(obj=self, config=stencil_factory.config.dace_config)
        self.stencil = stencil_factory.from_dims_halo(
            func=stencil,
            compute_dims=[X_DIM, Y_DIM, Z_DIM],
        )
        self.in_data = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
        self.out_data = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")

        self.out_data.view[:] = 42

        for i in range(stencil_factory.grid_indexing.get_shape(X_DIM)[0]):
            for j in range(stencil_factory.grid_indexing.get_shape(Y_DIM)[0]):
                for k in range(stencil_factory.grid_indexing.get_shape(Z_DIM)[0]):
                    self.in_data.view[i, j, k] = i * 100 + j * 10 + k

    def __call__(self, factor):
        self.stencil(self.in_data, self.out_data, factor)


if __name__ == "__main__":
    code = Code(stencil_factory, quantity_factory)

    factor = 2
    code(factor)
    print("INPUT: \n", code.in_data.view[:])
    print("OUTPUT: \n", code.out_data.view[:])
