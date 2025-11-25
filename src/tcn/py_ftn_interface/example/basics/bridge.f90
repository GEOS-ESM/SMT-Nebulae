module stub_interface_mod

   use iso_c_binding, only: c_int, c_float, c_double, c_bool

   implicit none

   private
   public :: python_function_f, data_t

   type, bind(c) :: data_t
      real(c_float) :: x
      integer(c_int) :: y
      logical(c_bool) :: b
      ! Magic number: help guaranteeing layout is kept
      ! consistant through the interface. Imperfect.
      integer(c_int) :: i_am_123456789 = 123456789
   end type

   interface

      subroutine python_function_f(type_data, value, array) bind(c, name='python_function')
         import data_t, c_int

         implicit none
         type(data_t), intent(in) :: type_data
         integer(kind=c_int), intent(in) :: value
         integer(kind=c_int), dimension(*), intent(in) :: array

      end subroutine python_function_f

   end interface

end module stub_interface_mod
