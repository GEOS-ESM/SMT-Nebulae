# Build cmake

wget https://cmake.org/files/v3.12/cmake-3.12.0.tar.gz
tar -xzf cmake-3.12.0.tar.gz
cd cmake-3.12.0
./bootstrap
make -j$(sysctl -n hw.ncpu)
sudo make install
