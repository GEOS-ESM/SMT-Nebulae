# Common Patterns

Now that we have introduced the core features of NDSL and highlighted features which enable more
complex coding structures, it is prudent to provide examples of how NDSL is implemented.

Below are a plethera of patterns which may be useful when developing code for weather and
climate models. These examples have been generalized, but should be broadly applicable to a
variety of situations.


# Vertical Level Dependent Computations

Suppose we have a Fortran program where we need to identify a specific vertical level, then
operate based on that level

``` fortran linenums="1"
program k_level_condtional
    implicit none
  
    ! setup domain
    integer, parameter :: X_DIM = 10
    integer, parameter :: Y_DIM = 10
    integer, parameter :: Z_DIM = 10

    ! counters
    integer :: i, j, k, p_crit, total
    real :: seed

    ! data arrays
    integer, dimension(X_DIM, Y_DIM, Z_DIM) :: temperature, pressure
    integer, dimension(X_DIM, Y_DIM) :: desired_level, average_temperature

    ! initalize arrays
    p_crit = 500
    do k = 1, Z_DIM
        pressure(:, :, k) = 1000 - (k-1) * 100 ! pressure decreases by 100mb per level
        do j = 1, Y_DIM
            do i = 1, X_DIM
                call random_number(seed)
                ! generate a random temperature between 20 and 30
                temperature(i, j, k) = 20 + FLOOR(11*seed)
            enddo
        enddo
    enddo


    ! determine k level where pressure meets a critical value
    do i = 1, X_DIM
        do j = 1, Y_DIM
            do k = 1, Z_DIM
                if (pressure(i, j, k) <= p_crit) then
                    desired_level(i, j) = k
                    ! in this simplified example desired level is the same everywhere, but one can
                    ! imagine a case where this is spatially variable (e.g. determine LCL or LFC)
                    exit
                endif
            enddo
        enddo
    enddo
    
    ! perform operation based on desired_level
    do i = 1, X_DIM
        do j = 1, Y_DIM
            total = 0
            do k = 1, desired_level(i, j)
                ! average temperature at and below desired_level
                total = total + temperature(i, j, k)
                average_temperature(i, j) = total/desired_level(i, j)
            enddo
        enddo
    enddo

    PRINT *, average_temperature

end program k_level_condtional
```