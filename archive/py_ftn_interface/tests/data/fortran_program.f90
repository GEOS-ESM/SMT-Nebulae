program test

    use py_ftn_test_interface_mod, only: py_ftn_test_check_data_f, &
                                         py_ftn_test_check_empty_function_f, &
                                         validate_py_ftn_test_check_data_f
    use runtime_fortran_mod, only: runtime_fortran, test_check_data_results, sp, dp

    implicit none

    real(sp)           :: in(2,2)
    real(sp)           :: inout(2,3)
    real(sp)           :: out(2,2)
    integer            :: status

    status = 0
    in = 1
    inout = 2
    out = 3

    print *, "Test the interface"
    print *, out

    print *, "= Test: Empty"
    call py_ftn_test_check_empty_function_f()

    print *, "= Test: Data modified in py and used in Fortran"
    call py_ftn_test_check_data_f(2, in, inout, out)
    status = test_check_data_results(out)
    if(status /= 0) then
        print*, "Failed."
        stop -1
    end if
    print *, out

    print *, "= Test: Validation"
    call validate_py_ftn_test_check_data_f(2, in, inout, out)

end program test
