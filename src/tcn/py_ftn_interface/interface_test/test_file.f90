program test_file

    use geos_pyfv3_interface_mod

    implicit none

    integer :: int_scalar
    real :: float_scalar

    integer, dimension(:,:,:), allocatable :: int_3D
    integer, dimension(:,:,:), allocatable :: int_3D_dup

    real,    dimension(:,:,:), allocatable :: real_3D
    real,    dimension(:,:,:), allocatable :: real_3D_dup

    integer, dimension(:,:), allocatable :: int_2D
    integer, dimension(:,:), allocatable :: int_2D_dup

    real,    dimension(:,:), allocatable :: real_2D
    real,    dimension(:,:), allocatable :: real_2D_dup

    integer :: N = 3
    integer :: i, j, k
    integer :: scale = 777

    allocate(int_3D(N,N,N))
    allocate(int_3D_dup(N,N,N))
    allocate(real_3D(N,N,N))
    allocate(real_3D_dup(N,N,N))

    allocate(int_2D(N,N))
    allocate(int_2D_dup(N,N))
    allocate(real_2D(N,N))
    allocate(real_2D_dup(N,N))

    call random_number(real_3D)

    real_3D_dup = real_3D

    int_3D = int(real_3D * scale)
    int_3D_dup = int_3D

    int_scalar = 7
    float_scalar = 7.0

    print*, "Initial real_3D = ", real_3D(1:5,1,1)
    print*, "Initial int_3D = ", int_3D(1:5,1,1)
    
    call geos_pyfv3_f_add_scalar_to_3D_quantity(int_scalar, float_scalar, int_3D,  shape(int_3D),  rank(int_3D), &
                                                   real_3D, shape(real_3D), rank(real_3D))

    call add_scalar_to_array(int_scalar, float_scalar, int_3D_dup, real_3D_dup)

    print*, "real_3D after geos_pyfv3_f_add_scalar_to_3D_quantity = ", real_3D(1:5,1,1)
    print*, "real_3d_dup after add_scalar_to_array = ", real_3D_dup(1:5,1,1)

    print*, "int_3D after geos_pyfv3_f_add_scalar_to_3D_quantity = ", int_3D(1:5,1,1)
    print*, "int_3D_dup after add_scalar_to_array = ", int_3D_dup(1:5,1,1)

    print*, "sum(real_3D - real_3D_dup) = ", sum(real_3D - real_3D_dup)
    print*, "sum(int_3D - int_3D_dup) = ", sum(int_3D - int_3D_dup)

    int_scalar = 77
    float_scalar = 77.0

    print*, "***************************"

    print*, "Initial real_3D = ", real_3D(1:5,1,1)
    print*, "Initial int_3D = ", int_3D(1:5,1,1)

    call geos_pyfv3_f_add_scalar_to_3D_quantity(int_scalar, float_scalar, int_3D,  shape(int_3D),  rank(int_3D), &
                                                   real_3D, shape(real_3D), rank(real_3D))
    call add_scalar_to_array(int_scalar, float_scalar, int_3D_dup, real_3D_dup)
    print*, "real_3D after geos_pyfv3_f_add_scalar_to_3D_quantity = ", real_3D(1:5,1,1)
    print*, "real_3d_dup after add_scalar_to_array = ", real_3D_dup(1:5,1,1)

    print*, "int_3D after geos_pyfv3_f_add_scalar_to_3D_quantity = ", int_3D(1:5,1,1)
    print*, "int_3D_dup after add_scalar_to_array = ", int_3D_dup(1:5,1,1)

    print*, "sum(real_3D - real_3D_dup) = ", sum(real_3D - real_3D_dup)
    print*, "sum(int_3D - int_3D_dup) = ", sum(int_3D - int_3D_dup)

    print*, "***************************"

    real_2D = 1.0
    int_2D = 1

    call geos_pyfv3_f_add_2D_quantity_to_3D_quantity(int_2D, shape(int_2D), rank(int_2D), &
                                                   real_2D, shape(real_2D), rank(real_2D), &
                                                   int_3D, shape(int_3D), rank(int_3D), &
                                                   real_3D, shape(real_3D), rank(real_3D))
    call add_2D_array_to_3D_array(int_2D, real_2D, int_3D_dup, real_3D_dup)

    print*, "real_3D after geos_pyfv3_f_add_2D_quantity_to_3D_quantity = ", real_3D(1:5,1,1)
    print*, "real_3d_dup after add_2D_array_to_3D_array = ", real_3D_dup(1:5,1,1)
    print*, "int_3D after geos_pyfv3_f_add_2D_quantity_to_3D_quantity = ", int_3D(1:5,1,1)
    print*, "int_3D_dup after add_2D_array_to_3D_array = ", int_3D_dup(1:5,1,1)
    print*, "sum(real_3D - real_3D_dup) = ", sum(real_3D - real_3D_dup)
    print*, "sum(int_3D - int_3D_dup) = ", sum(int_3D - int_3D_dup)
    print*, "***************************"

    contains

        subroutine add_scalar_to_array(int_scalar, float_scalar, int_3D, real_3D)
            implicit none
            integer, intent(in) :: int_scalar
            real, intent(in) :: float_scalar
            integer, dimension(:,:,:), intent(inout) :: int_3D
            real, dimension(:,:,:), intent(inout) :: real_3D
        
            real_3D = real_3D + float_scalar
            int_3D = int_3D + int_scalar
        end subroutine add_scalar_to_array

        subroutine add_2D_array_to_3D_array(int_2D, real_2D, int_3D, real_3D)
            implicit none
            integer, dimension(:,:), intent(in) :: int_2D
            integer, dimension(:,:,:), intent(inout) :: int_3D
            real, dimension(:,:), intent(in) :: real_2D
            real, dimension(:,:,:), intent(inout) :: real_3D
        
            integer :: k, k_dim
            
            k_dim = size(int_3D, 3)

            do k = 1, k_dim
                int_3D(:,:,k) = int_3D(:,:,k) + int_2D
                real_3D(:,:,k) = real_3D(:,:,k) + real_2D
            end do

        end subroutine add_2D_array_to_3D_array
end program
