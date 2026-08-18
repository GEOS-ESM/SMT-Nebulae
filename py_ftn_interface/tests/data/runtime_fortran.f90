module runtime_fortran_mod

    implicit none

    !> Single precision real numbers, 6 digits, range 10⁻³⁷ to 10³⁷-1; 32 bits
    integer, parameter :: sp = selected_real_kind(6, 37)
    !> Double precision real numbers, 15 digits, range 10⁻³⁰⁷ to 10³⁰⁷-1; 64 bits
    integer, parameter :: dp = selected_real_kind(15, 307)


    contains


    subroutine runtime_fortran(scalar, in_array, &
        inout_array, &
        out_array &
        )

        implicit none

        integer, value, intent(in) :: scalar
        real(sp), intent(in) :: in_array(:,:)
        real(sp), intent(inout) :: inout_array(:,:)
        real(sp), intent(out) :: out_array(:,:)

        print*, "> runtime_fortran, out is ", out_array
        out_array = 11
        inout_array = 22

    end subroutine runtime_fortran

    function test_check_data_results(out_array) result(status)

        implicit none

        real(sp), intent(in) :: out_array(:,:)
        integer              :: status

        print*, "> test_check_data_results, out is ", out_array
        status = 0
        if(any(out_array /= 11)) then
            status = -1
        end if

    end function test_check_data_results

end module runtime_fortran_mod
