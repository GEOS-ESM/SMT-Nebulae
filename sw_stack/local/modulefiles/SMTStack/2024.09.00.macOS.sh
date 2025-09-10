#!/bin/bash

install_dir=${DSLSW_custom_install_path:-$(dirname "$PWD")/2025.09.00.macOS/install}

# OMPI #
# ompi_pkgdir="$install_dir/ompi"

# export M_MPI_ROOT=$ompi_pkgdir
# export OPENMPI=$ompi_pkgdir
# export MPI_HOME=$ompi_pkgdir

# export PATH="$ompi_pkgdir/bin":$PATH
# export LD_LIBRARY_PATH="$ompi_pkgdir/lib":$LD_LIBRARY_PATH
# export INCLUDE="$ompi_pkgdir/include":$INCLUDE
# export MANPATH="$ompi_pkgdir/share/man":$MANPATH

# export OMPI_MCA_orte_tmpdir_base="/tmp"
# export TMPDIR="/tmp"
# export OMP_STACKSIZE="1G"
# export OMPI_MCA_mca_base_component_show_load_errors="0"
# export PMIX_MCA_mca_base_component_show_load_errors="0"

# Baselibs #
baselibs_pkgdir="$install_dir/baselibs-7.27.0/install/"
export BASEDIR=$baselibs_pkgdir

# Serialbox #
export SERIALBOX_ROOT=$ser_pkgdir
export PATH="$ser_pkgdir/python/pp_ser":$PATH
export LD_LIBRARY_PATH="$ser_pkgdir/lib":$LD_LIBRARY_PATH
export PYTHONPATH="$ser_pkgdir/python":$PYTHONPATH
