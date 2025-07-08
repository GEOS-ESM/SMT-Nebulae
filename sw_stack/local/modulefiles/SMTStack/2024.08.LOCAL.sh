#!/bin/bash

# >>>>>>>>>> SET TO LOCAL PATHS <<<<<<<<<<<<<< #
install_dir="/Users/ckropiew/GEOS_dependencies/install"
ser_pkgdir="/Users/ckropiew/GEOS_dependencies/install/serialbox"
homebrew_install_dir="/opt/homebrew/Cellar"
# >>>>>>>>>>>>>>><<<<<<<<<<<<<< #

# Fix: GT4Py expects CUDA_HOME to be set #
# export CUDA_HOME= $os/etenv("NVHPC_ROOT"), "cuda")

# UCX #
ucx_pkgdir="$install_dir/ucx"
export LD_LIBRARY_PATH="$ucx_pkgdir/lib":$LD_LIBRARY_PATH

# OMPI #
ompi_pkgdir="$install_dir/ompi"

export M_MPI_ROOT=$ompi_pkgdir
export OPENMPI=$ompi_pkgdir
export MPI_HOME=$ompi_pkgdir

export PATH="$ompi_pkgdir/bin":$PATH
export LD_LIBRARY_PATH="$ompi_pkgdir/lib":$LD_LIBRARY_PATH
export INCLUDE="$ompi_pkgdir/include":$INCLUDE
export MANPATH="$ompi_pkgdir/share/man":$MANPATH

export OMPI_MCA_orte_tmpdir_base="/tmp"
export TMPDIR="/tmp"
export OMP_STACKSIZE="1G"
export OMPI_MCA_mca_base_component_show_load_errors="0"
export PMIX_MCA_mca_base_component_show_load_errors="0"

# BOOST HEADERS (as expected by gt4py)
# boost_pkgdir="$install_dir/boost"
boost_pkgdir="$homebrew_install_dir/boost/1.86.0_1"
export BOOST_ROOT=$boost_pkgdir

# Baselibs at a BASEDIR #
baselibs_pkgdir="$install_dir/baselibs-7.27.0/install/"
export BASEDIR=$baselibs_pkgdir

# Serialbox #
export SERIALBOX_ROOT=$ser_pkgdir
export PATH="$ser_pkgdir/python/pp_ser":$PATH
export LD_LIBRARY_PATH="$ser_pkgdir/lib":$LD_LIBRARY_PATH
export PYTHONPATH="$ser_pkgdir/python":$PYTHONPATH

# Python 3
# py_pkgdir="/Library/Frameworks/Python.framework/Versions/3.11"
# export PATH="$py_pkgdir/bin":$PATH
# export LD_LIBRARY_PATH="$py_pkgdir/lib":$LD_LIBRARY_PATH
# export LD_LIBRARY_PATH="$py_pkgdir/lib64":$LD_LIBRARY_PATH

# Enforce proper compilers
export FC=/opt/homebrew/opt/gcc@14/bin/gfortran-14
export CC=/opt/homebrew/opt/gcc@14/bin/gcc-14
export CXX=/opt/homebrew/opt/gcc@14/bin/g++-14

# Weird Mac necessity
export SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX14.sdk/

