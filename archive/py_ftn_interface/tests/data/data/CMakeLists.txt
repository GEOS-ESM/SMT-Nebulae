cmake_minimum_required(VERSION 3.5)

#
## Configuration.
#

project(test)
enable_language(Fortran)

if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
    set(dialect "-ffree-form -std=f2008 -fimplicit-none")
    set(bounds "-fbounds-check")
endif()
if(CMAKE_Fortran_COMPILER_ID MATCHES "Intel")
    set(dialect "-stand f08 -free -implicitnone")
    set(bounds "-check bounds")
endif()
if(CMAKE_Fortran_COMPILER_ID MATCHES "PGI")
    set(dialect "-Mfreeform -Mdclchk -Mstandard -Mallocatable=03")
    set(bounds "-C")
endif()

set(CMAKE_Fortran_FLAGS_DEBUG "${CMAKE_Fortran_FLAGS_DEBUG} ${bounds}")
set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} ${dialect}")

#
## Sources.
#

set( sources
    ../fortran_program.f90
    ../runtime_fortran.f90
)

set(py_ftn_test_INTERFACE_DIRECTORY   /home/fgdeconi/work/git/smtn/tmp/py_ftn_test/interface)
set( interface_sources
    ${py_ftn_test_INTERFACE_DIRECTORY}/py_ftn_test_interface.f90
    ${py_ftn_test_INTERFACE_DIRECTORY}/py_ftn_test_interface.c
)

list( APPEND sources ${interface_sources} )


#
## py_ftn_test Interface.
#

message(STATUS "Building GEOS-gtFV3 interface")

add_definitions(-DRUN_GTFV3)

find_package(MPI REQUIRED)
if (MPI_FOUND)
    include_directories(SYSTEM ${MPI_INCLUDE_PATH})
else (MPI_FOUND)
    message(SEND_ERROR "This application cannot compile without MPI")
endif (MPI_FOUND)

find_package(Python COMPONENTS Interpreter REQUIRED)

# Set up some variables in case names change
set(py_ftn_test_INTERFACE_LIBRARY     ${CMAKE_CURRENT_BINARY_DIR}/libpy_ftn_test_interface.so)
set(py_ftn_test_INTERFACE_HEADER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py_ftn_test_interface.h)
set(py_ftn_test_INTERFACE_SRCS        ${py_ftn_test_INTERFACE_DIRECTORY}/py_ftn_test_interface.py)

message(VERBOSE "Python is: ${Python3_EXECUTABLE}")

# This command creates the shared object library from Python
add_custom_command(
    OUTPUT ${py_ftn_test_INTERFACE_LIBRARY}
    COMMAND ${Python3_EXECUTABLE} ${py_ftn_test_INTERFACE_SRCS}
    BYPRODUCTS ${py_ftn_test_INTERFACE_HEADER_FILE}
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    MAIN_DEPENDENCY ${py_ftn_test_INTERFACE_SRCS}
    COMMENT "Building gtfv3 interface library with Python"
    VERBATIM
)

# This creates a target we can use for dependencies and post build
add_custom_target(generate_python_interface_library DEPENDS ${py_ftn_test_INTERFACE_LIBRARY})

# Because of the weird hacking of INTERFACE libraries below, we cannot
# use the "usual" CMake calls to install() the .so. I think it's because
# INTERFACE libraries don't actually produce any artifacts as far as
# CMake is concerned. So we add a POST_BUILD custom command to "install"
# the library into install/lib
add_custom_command(
    TARGET generate_python_interface_library
    POST_BUILD
    # We first need to make a lib dir if it doesn't exist. If not, then
    # the next command can copy the script into a *file* called lib because
    # of a race condition (if install/lib/ isn't mkdir'd first)
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_INSTALL_PREFIX}/lib
    # Now we copy the file (if different...though not sure if this is useful)
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${py_ftn_test_INTERFACE_LIBRARY}" ${CMAKE_INSTALL_PREFIX}/lib
)

# We use INTERFACE libraries to create a sort of "fake" target library we can use
# to make libFVdycoreCubed_GridComp.a depend on. It seems to work!
add_library(py_ftn_test_interface_py INTERFACE)

# The target_include_directories bits were essentially stolen from the esma_add_library
# code...
target_include_directories(
    py_ftn_test_interface_py INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}> # stubs
    # modules and copied *.h, *.inc
    $<BUILD_INTERFACE:${esma_include}/${this}>
    $<INSTALL_INTERFACE:include/${this}>
)
target_link_libraries(py_ftn_test_interface_py INTERFACE ${py_ftn_test_INTERFACE_LIBRARY})

# This makes sure the library is built first
add_dependencies(py_ftn_test_interface_py generate_python_interface_library)

# This bit is to resolve an issue and Google told me to do this. I'm not
# sure that the LIBRARY DESTINATION bit actually does anything since
# this is using INTERFACE
install(
    TARGETS py_ftn_test_interface_py
    EXPORT ${PROJECT_NAME}-targets
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/lib
)

list( APPEND PYTHONPATH "${py_ftn_test_INTERFACE_DIRECTORY}" )

#
## Executable.
#

add_executable(test ${sources})
add_dependencies(test py_ftn_test_interface_py)
target_link_libraries(test py_ftn_test_interface_py)
target_link_libraries(test ${MPI_C_LIBRARIES})
install(
    TARGETS test
    EXPORT ${PROJECT_NAME}-targets
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}
)
