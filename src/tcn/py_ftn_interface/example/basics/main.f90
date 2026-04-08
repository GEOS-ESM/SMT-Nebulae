program test
   use stub_interface_mod, only: python_function_f, data_t

   implicit none

   type(data_t) :: d
   integer, allocatable, dimension(:,:,:) :: allocatable_field
   
   ! Type data
   d = data_t(42.42, 24, .true.)

   ! Allocate field
   ALLOCATE ( allocatable_field (2,3,4) )
   
   allocatable_field = 2
   print *,'Allocated field fortran side before python call:', allocatable_field(0, 1, 2)

   call python_function_f(d, 39, allocatable_field)

   print *,'Allocated field fortran side AFTER python call:', allocatable_field(0, 1, 2)

   DEALLOCATE(allocatable_field)
   
end program test

