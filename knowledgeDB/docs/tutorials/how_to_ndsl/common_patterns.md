# Common Patterns

Now that we have introduced the core features of NDSL and highlighted features which enable more
complex coding structures, it is prudent to provide examples of how NDSL is implemented.

Below are a plethora of patterns which may be useful when developing code for weather and
climate models. These examples have been generalized, but should be broadly applicable to a
variety of situations. Each example has a "source" Fortran program, and a "ported" NDSL
implementation.

## Writing to a `Z_INTERFACE_DIM` Variable

If working with `Z_INTERFACE_DIM` quantities, one will inevitably need to write to the "extra"
point. The easiest way to achieve this is by declaring your `compute_dims` to operate on
the `Z_INTERFACE_DIM` instead of the `Z_DIM`, and then restrict your interval and offset `Z_DIM`
stencil reads accordingly:

??? Example "Fortran Code"

    ``` fortran linenums="1"
    program compute_height
        implicit none
    
        ! setup domain
        integer, parameter :: X_DIM = 10
        integer, parameter :: Y_DIM = 10
        integer, parameter :: Z_DIM = 10

        ! allocate scalars
        integer :: i, j, k, p_crit
        real :: seed, total

        ! allocate arrays
        real, dimension(X_DIM, Y_DIM, Z_DIM) :: d_height
        real, dimension(X_DIM, Y_DIM, Z_DIM+1) :: height

        ! initalize data
        do i = 1, X_DIM
            do j = 1, Y_DIM
                do k = 1, Z_DIM
                    call RANDOM_NUMBER(seed)
                    ! generate a random change in height for each layer in the range 125:175
                    d_height(i, j, k) = 125 + FLOOR(51*seed)
                enddo
            enddo
        enddo

        height(:, :, 1) = 0
        do i = 1, X_DIM
            do j = 1, Y_DIM
                do k = 2, Z_DIM+1
                    height(i, j, k) = height(i, j, k-1) + d_height(i, j, k-1)
                enddo
            enddo
        enddo

        PRINT *, height(1, 1, :)

    end program compute_height
    ```

??? Example "NDSL Code"

    ``` py linenums="1"
    from gt4py.cartesian.gtscript import (
        computation,
        interval,
        PARALLEL,
    )
    from ndsl import StencilFactory
    from ndsl.boilerplate import get_factories_single_tile
    from ndsl.constants import X_DIM, Y_DIM, Z_DIM, Z_INTERFACE_DIM
    from ndsl.dsl.typing import FloatField
    import random


    def compute_height(
        height: FloatField,
        d_height: FloatField,
    ):
        with computation(PARALLEL), interval(0, 1):
            height = 0

        with computation(PARALLEL), interval(1, None):
            # d_height is offset down one because this field operates on the Z_DIM,
            # while the stencil is computing on the Z_INTERFACE_DIM
            height = height[0, 0, -1] + d_height[0, 0, -1]


    class Code:
        def __init__(self, stencil_factory: StencilFactory):

            # build stencil
            self.constructed_stencil = stencil_factory.from_dims_halo(
                func=compute_height,
                compute_dims=[X_DIM, Y_DIM, Z_INTERFACE_DIM],
            )

        def __call__(
            self,
            height: FloatField,
            d_height: FloatField,
        ):
            # execute stencil
            self.constructed_stencil(
                height,
                d_height,
            )


    if __name__ == "__main__":

        # setup domain and generate factories
        domain = (10, 10, 10)
        nhalo = 0
        stencil_factory, quantity_factory = get_factories_single_tile(
            domain[0],
            domain[1],
            domain[2],
            nhalo,
            backend="debug",
        )

        # initialize data
        height = quantity_factory.zeros([X_DIM, Y_DIM, Z_INTERFACE_DIM], "n/a")

        d_height = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
        for i in range(d_height.view[:].shape[0]):
            for j in range(d_height.view[:].shape[1]):
                for k in range(d_height.view[:].shape[2]):
                    d_height.view[i, j, k] = round(random.uniform(125, 175))

        # build stencil
        code = Code(stencil_factory)

        # execute stencil
        code(height, d_height)

        print(height.view[0, 0, :])
    ```

## K-Dimension Dependent Computations

In weather and climate modeling, it is often necessary to identify a specific level, then perform
one or more operations based on that level (e.g. identify LCL, compute convective parameters).

??? Example "Fortran Code"

    ``` fortran linenums="1"
    program average_below_level
        implicit none
    
        ! setup domain
        integer, parameter :: X_DIM = 10
        integer, parameter :: Y_DIM = 10
        integer, parameter :: Z_DIM = 10

        ! allocate scalars
        integer :: i, j, k, p_crit
        real :: seed, total

        ! allocate arrays
        integer, dimension(X_DIM, Y_DIM, Z_DIM) :: temperature, pressure
        integer, dimension(X_DIM, Y_DIM) :: desired_level
        real, dimension(X_DIM, Y_DIM) :: average_temperature

        ! initalize data
        p_crit = 500
        do k = 1, Z_DIM
            pressure(:, :, k) = 1000 - (k-1) * 100 ! pressure decreases by 100mb per level
            do j = 1, Y_DIM
                do i = 1, X_DIM
                    call RANDOM_NUMBER(seed)
                    ! generate a random temperature in the range 20:30
                    temperature(i, j, k) = 20 + FLOOR(11*seed)
                enddo
            enddo
        enddo


        ! determine k level where pressure meets a critical value
        do i = 1, X_DIM
            do j = 1, Y_DIM
                do k = 1, Z_DIM
                    if (pressure(i, j, k) < p_crit) then
                        desired_level(i, j) = k
                        ! in this simplified example desired level is the same everywhere, but one can
                        ! imagine a case where this is spatially variable (e.g. determine LCL or LFC)
                        exit
                    endif
                enddo
            enddo
        enddo
        
        ! calculate average based on desired_level
        do i = 1, X_DIM
            do j = 1, Y_DIM
                total = 0
                do k = 1, desired_level(i, j)
                    total = total + temperature(i, j, k)
                enddo
                average_temperature(i, j) = total/desired_level(i, j)
            enddo
        enddo

        PRINT *, average_temperature

    end program average_below_level
    ```

??? Example "NDSL Code"

    ``` py linenums="1"
    from gt4py.cartesian.gtscript import (
        FORWARD,
        computation,
        interval,
        THIS_K,
    )
    from ndsl import StencilFactory
    from ndsl.boilerplate import get_factories_single_tile
    from ndsl.constants import X_DIM, Y_DIM, Z_DIM
    from ndsl.dsl.typing import FloatField, FloatFieldIJ, IntFieldIJ, Int, Float
    import random


    def average_layers(
        temperature: FloatField,
        pressure: FloatField,
        average_temperature: FloatFieldIJ,
        desired_level: IntFieldIJ,
    ):
        from __externals__ import p_crit, k_end

        with computation(FORWARD), interval(...):
            # determine critical level
            if pressure > p_crit:
                desired_level = THIS_K

        with computation(FORWARD), interval(...):
            # sum all temperatures below critical level
            if THIS_K <= desired_level:
                average_temperature = average_temperature + temperature
            # calculate the average on the final level
            if THIS_K == k_end:
                average_temperature = average_temperature / desired_level


    class Code:
        def __init__(self, stencil_factory: StencilFactory):

            self.constructed_stencil = stencil_factory.from_dims_halo(
                func=average_layers,
                compute_dims=[X_DIM, Y_DIM, Z_DIM],
                externals={
                    "p_crit": 500,
                },
            )

        def __call__(
            self,
            temperature: FloatField,
            pressure: FloatField,
            average_temperature: FloatFieldIJ,
            desired_level: IntFieldIJ,
        ):
            self.constructed_stencil(
                temperature,
                pressure,
                average_temperature,
                desired_level,
            )


    if __name__ == "__main__":

        # setup domain and generate factories
        domain = (10, 10, 10)
        nhalo = 0
        stencil_factory, quantity_factory = get_factories_single_tile(
            domain[0],
            domain[1],
            domain[2],
            nhalo,
            backend="debug",
        )

        # initialize data
        temperature = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
        for i in range(temperature.view[:].shape[0]):
            for j in range(temperature.view[:].shape[1]):
                for k in range(temperature.view[:].shape[2]):
                    temperature.view[i, j, k] = round(random.uniform(20, 30))

        pressure = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
        for k in range(pressure.view[:].shape[2]):
            pressure.view[:, :, k] = 1000 - k * 100

        average_temperature = quantity_factory.zeros([X_DIM, Y_DIM], "n/a")
        desired_level = quantity_factory.zeros([X_DIM, Y_DIM], "n/a", dtype=Int)

        # build stencil
        code = Code(stencil_factory)

        # execute stencil
        code(temperature, pressure, average_temperature, desired_level)

        print(average_temperature.view[:])
    ```

## Global Tables

There may be situations where a table is needed for referencing throughout the execution of a
component/model. It is highly unlikely that these tables will conform to the grid system used by
the rest of the model in any way. Generating these tables, therefore, requires a somewhat
unconventional use of systems. The following example is an adaptation of code used to generate one
of the saturation vapor pressure tables in the GEOS model, and displays the flexibility of
NDSL systems:

??? Example "Fortran Code"

    ``` fortran linenums="1"
    subroutine qs_tablew (n)

        implicit none

        integer, intent (in) :: n

        real :: delt = 0.1
        real :: tmin, tem, fac0, fac1, fac2

        integer :: i

        tmin = table_ice - 160.

        ! -----------------------------------------------------------------------
        ! compute es over water
        ! -----------------------------------------------------------------------

        do i = 1, n
            tem = tmin + delt * real (i - 1)
            fac0 = (tem - t_ice) / (tem * t_ice)
            fac1 = fac0 * lv0
            fac2 = (dc_vap * log (tem / t_ice) + fac1) / rvgas
            tablew (i) = e00 * exp (fac2)
        enddo

    end subroutine qs_tablew
    ```

??? Example "NDSL Code"

    ``` py linenums="1"
    import gt4py.cartesian.gtscript as gtscript
    from gt4py.cartesian.gtscript import (
        FORWARD,
        PARALLEL,
        THIS_K,
        computation,
        exp,
        interval,
        log,
        log10,
    )

    from ndsl.boilerplate import get_factories_single_tile
    from ndsl.constants import X_DIM, Y_DIM, Z_DIM
    from ndsl.dsl.typing import Float, FloatField, Int

    # In the full implementation of this code, these are read in from a constants file
    LENGTH = Int(2621)
    RVGAS = Float(461.50)
    CP_VAP = Float(4.0) * RVGAS
    C_LIQ = Float(4185.5)
    DC_VAP = CP_VAP - C_LIQ
    T_ICE = Float(273.16)
    LV0 = Float(2.5e6) - DC_VAP * T_ICE
    E_00 = Float(611.21)
    DELT = Float(0.1)
    TMIN = T_ICE - Float(160.0)
    ESBASW = Float(1013246.0)
    TBASW = T_ICE + Float(100.0)
    ESBASI = Float(6107.1)
    
    # Create a GlobalTable object of the desired size
    GlobalTable_driver_qsat = gtscript.GlobalTable[(Float, (int(LENGTH)))]


    def qs_table_2(length: Int, table2: FloatField):
        """
        Compute saturation water vapor pressure table 2
        one phase table

        reference Fortran: gfdl_cloud_microphys.F90: subroutine qs_tablew
        """
        with computation(PARALLEL), interval(...):
            tem = TMIN + DELT * THIS_K
            fac0 = (tem - T_ICE) / (tem * T_ICE)
            fac1 = fac0 * LV0
            fac2 = (DC_VAP * log(tem / T_ICE) + fac1) / RVGAS
            table2 = E_00 * exp(fac2)


    class GFDL_driver_tables:
        """
        Initializes lookup tables for saturation water vapor pressure
        for the utility routines that are designed to return qs
        consistent with the assumptions in FV3.

        Reference Fortran: gfdl_cloud_microphys.F90: qsmith_init.py
        """

        def __init__(self, backend):
            table_compute_domain = (1, 1, LENGTH)

            stencil_factory, quantity_factory = get_factories_single_tile(
                table_compute_domain[0],
                table_compute_domain[1],
                table_compute_domain[2],
                0,
                backend,
            )

            self._table2 = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")

            compute_qs_table_2 = stencil_factory.from_origin_domain(
                func=qs_table_2,
                origin=(0, 0, 0),
                domain=table_compute_domain,
                externals={
                    "LENGTH": LENGTH,
                    "RVGAS": RVGAS,
                    "CP_VAP": CP_VAP,
                    "C_LIQ": C_LIQ,
                    "DC_VAP": DC_VAP,
                    "T_ICE": T_ICE,
                    "LV0": LV0,
                    "E_00": E_00,
                    "DELT": DELT,
                    "TMIN": TMIN,
                    "ESBASW": ESBASW,
                    "TBASW": TBASW,
                    "ESBASI": ESBASI,
                },
            )

            compute_qs_table_2(LENGTH, self._table2)

            self.table2 = self._table2.view[0, 0, :]


    # Table needs to be calculated only once
    _cached_table = {
        "driver_qsat": None,
    }


    def get_tables(backend):
        if _cached_table["driver_qsat"] is None:
            _cached_table["driver_qsat"] = GFDL_driver_tables(backend)

        return _cached_table["driver_qsat"]


    if __name__ == "__main__":
        sat_table = get_tables("debug")
        
        print(sat_table.table2)
    ```

Additionally, the `GlobalTable` object created must be accurately hinted when it is used in a
stencil, and can then be accessed using normal data dimension indexing:

??? Example "NDSL Code"

    ``` py linenums="1"
    def stencil(table: GlobalTable_local_type):
        with computation(PARALLEL), interval(...):
            data = table.A[desired_index]
    ```

## Dynamic Conditionals and Internal Flags

Often there are times where it is necessary to control the execution of specific code paths
dynamically within code execution (e.g. computing precipitation if there is sufficient liquid
water present). There is no way to stop a computation early. Instead, the correct way to control
execution of different coordinates on the X/Y plane is by using two dimensional fields, which act
as flags to turn on/off chunks of code, acting as flags on a per-point basis.

??? Example "NDSL Code"

    ``` py linenums="1"
    import gt4py.cartesian.gtscript as gtscript
    from gt4py.cartesian.gtscript import PARALLEL, FORWARD, computation, interval, exp
    from ndsl import StencilFactory
    from ndsl.boilerplate import get_factories_single_tile
    from ndsl.constants import X_DIM, Y_DIM, Z_DIM
    from ndsl.dsl.typing import FloatField, Float, BoolFieldIJ, Bool
    import random


    def check_value(data: FloatField, flag: BoolFieldIJ):
        from __externals__ import critical_value

        with computation(FORWARD), interval(...):
            # if the data surpasses a critical value anywhere in the column, set the flag to true
            if data > critical_value:
                flag = True


    def computation_stencil(data_in: FloatField, data_out: FloatField, flag: BoolFieldIJ):
        with computation(PARALLEL), interval(...):
            if flag == True:
                data_out = 2 * exp(data_in)
            else:
                data_out = 0


    class DoSomeMath:
        def __init__(self, stencil_factory: StencilFactory):

            self.check_value = stencil_factory.from_dims_halo(
                func=check_value,
                compute_dims=[X_DIM, Y_DIM, Z_DIM],
                externals={
                    "critical_value": 5,
                },
            )

            self.computation_stencil = stencil_factory.from_dims_halo(
                func=computation_stencil,
                compute_dims=[X_DIM, Y_DIM, Z_DIM],
            )

        def __call__(self, in_field: FloatField, out_field: FloatField):
            self.check_value(in_field, flag_field)
            self.computation_stencil(in_field, out_field, flag_field)


    if __name__ == "__main__":

        domain = (5, 5, 3)
        nhalo = 0
        stencil_factory, quantity_factory = get_factories_single_tile(
            domain[0],
            domain[1],
            domain[2],
            nhalo,
        )

        do_some_math = DoSomeMath(stencil_factory)

        in_field = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
        for i in range(in_field.view[:].shape[0]):
            for j in range(in_field.view[:].shape[1]):
                for k in range(in_field.view[:].shape[2]):
                    in_field.view[i, j, k] = round(random.uniform(0, 10), 2)

        out_field = quantity_factory.zeros([X_DIM, Y_DIM, Z_DIM], "n/a")
        out_field.view[:] = -999

        flag_field = quantity_factory.zeros([X_DIM, Y_DIM], "n/a", dtype=Bool)

        do_some_math(in_field, out_field)

        print(out_field.view[:])
    ```

## Nested K Loops

Occasionally there may be situations when a nested K loop is required (such as
accumulating precipitation).

Below is an example of a nested K loop from the lagrangian_contributions stencil. It is not 
currently possible in NDSL to nest a `with computation(PARALLEL)` within a 
`with computation(PARALLEL)`, however a `while`loop can be used to create a nested K loop 
(lines x-x).

    ```py linenums="1"
    def lagrangian_contributions(
        q: FloatField,
        pe1: FloatField,
        pe2: FloatField,
        q4_1: FloatField,
        q4_2: FloatField,
        q4_3: FloatField,
        q4_4: FloatField,
        dp1: FloatField,
        lev: IntFieldIJ,
    ):
        """
        Args:
            q (out):
            pe1 (in):
            pe2 (in):
            q4_1 (in):
            q4_2 (in):
            q4_3 (in):
            q4_4 (in):
            dp1 (in):
            lev (inout):
        """
        with computation(FORWARD), interval(...):
            pl = (pe2 - pe1[0, 0, lev]) / dp1[0, 0, lev]
            if pe2[0, 0, 1] <= pe1[0, 0, lev + 1]:
                pr = (pe2[0, 0, 1] - pe1[0, 0, lev]) / dp1[0, 0, lev]
                q = (
                    q4_2[0, 0, lev]
                    + 0.5
                    * (q4_4[0, 0, lev] + q4_3[0, 0, lev] - q4_2[0, 0, lev])
                    * (pr + pl)
                    - q4_4[0, 0, lev] * 1.0 / 3.0 * (pr * (pr + pl) + pl * pl)
                )
            else:
                qsum = (pe1[0, 0, lev + 1] - pe2) * (
                    q4_2[0, 0, lev]
                    + 0.5
                    * (q4_4[0, 0, lev] + q4_3[0, 0, lev] - q4_2[0, 0, lev])
                    * (1.0 + pl)
                    - q4_4[0, 0, lev] * 1.0 / 3.0 * (1.0 + pl * (1.0 + pl))
                )
                lev = lev + 1
                while pe1[0, 0, lev + 1] < pe2[0, 0, 1]:
                    qsum += dp1[0, 0, lev] * q4_1[0, 0, lev]
                    lev = lev + 1
                dp = pe2[0, 0, 1] - pe1[0, 0, lev]
                esl = dp / dp1[0, 0, lev]
                qsum += dp * (
                    q4_2[0, 0, lev]
                    + 0.5
                    * esl
                    * (
                        q4_3[0, 0, lev]
                        - q4_2[0, 0, lev]
                        + q4_4[0, 0, lev] * (1.0 - (2.0 / 3.0) * esl)
                    )
                )
                q = qsum / (pe2[0, 0, 1] - pe2)
            lev = lev - 1
    ```

## Goto and Exit

As previously mentioned, NDSL is unable to end a computation early. Similarly, NDSL is unable to
"jump" to another part of the code in a behavior similar to the Fortran `goto` statement. These
keywords make code flow extremely difficult to follow, and implementing them in NDSL would have
no performance gain. Rather than relying on these keywords, NDSL has all the tools required to
implement proper code control while maintaining good readability.
