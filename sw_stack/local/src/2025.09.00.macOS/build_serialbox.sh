#!/bin/bash

# Source the share basics
source ./basics.sh

cd $DSLSW_BASE

echo " === Serialbox === "

# Clone the repository only if the directory does not already exist
[ ! -d "serialbox" ] && git clone https://github.com/GridTools/serialbox.git serialbox
cd serialbox
# Add remote only if it doesn't exist
git remote | grep -q "^$DSLSW_SERIALBOX_REMOTE_NAME$" || git remote add $DSLSW_SERIALBOX_REMOTE_NAME https://github.com/GridTools/serialbox.git
# Checkout the branch safely
if git show-ref --quiet refs/heads/feature/data_ijkbuff; then
    git checkout feature/data_ijkbuff
else
    git checkout -b feature/data_ijkbuff
fi
cd $DSLSW_BASE

cd $DSLSW_BASE/serialbox
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=$DSLSW_INSTALL_DIR/serialbox \
    -DSERIALBOX_ENABLE_FORTRAN=ON \
    -DSERIALBOX_EXAMPLES=OFF \
    ..
make -j install
