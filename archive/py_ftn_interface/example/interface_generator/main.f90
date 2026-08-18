program test
   use basic_interface_mod

   implicit none

   integer, allocatable, dimension(:,:,:) :: field_3d
   integer, allocatable, dimension(:,:) :: field_2d
   
   ! Allocate field
   ALLOCATE ( field_3d (3,3,3) )
   ALLOCATE ( field_2d (2,2) )
   
   field_3d = 3
   field_2d = 2

   call basic_f_add_scalar_to_3D_quantity(39, field_3d, shape(field_3d), rank(field_3d))
   call basic_f_add_2D_quantity_to_3D_quantity( &
      field_2d, shape(field_2d), rank(field_2d), &
      field_3d, shape(field_3d), rank(field_3d) &
   )

   DEALLOCATE(field_3d)
   DEALLOCATE(field_2d)
   
end program test

