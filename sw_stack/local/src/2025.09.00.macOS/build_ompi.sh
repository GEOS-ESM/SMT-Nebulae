#!/bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

echo " === OpenMPI === "

wget https://download.open-mpi.org/release/open-mpi/v$DSLSW_OMPI_MAJOR_VER/openmpi-${DSLSW_OMPI_VER}.tar.gz
tar xfzp openmpi-$DSLSW_OMPI_VER.tar.gz
rm openmpi-$DSLSW_OMPI_VER.tar.gz

# NSL lib (-lnsl) was not symlink from libnsl.so.1 which lead to issues (--disable-getpwuid is an attempt to squash that, which seems unsucessful). Potentially, removing the LSF scheduler build would work.

# libxml2 has a /zero on it's init (https://gitlab.gnome.org/GNOME/libxml2/-/blob/7846b0a677f8d3ce72486125fa281e92ac9970e8/xpath.c#L505) which seems to trigger a sigfpe. Relying on the internal but potentially wobly XML parser of OMPI

# August 24: we had stability issues with linking to the HPC hwloc/pmix. In order to remains stable we flipped all base libraries to `internal`. This should be revisited for performance down the line.


cd $DSLSW_BASE/openmpi-${DSLSW_OMPI_VER}
./configure --prefix=$DSLSW_INSTALL_DIR/ompi \
            --disable-libxml2 \
            --disable-wrapper-rpath \
            --disable-wrapper-runpath \
            --with-pmix=internal \
            --with-hwloc=internal \
            --with-libevent=internal \
            --without-verbs \
            --enable-mpi1-compatibility

# make -j all 
# make install 
