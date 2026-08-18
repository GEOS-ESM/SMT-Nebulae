#!/bin/sh

CACHE_DIR=/home/fgdeconi/work/git/smt/benchmarker/.gt_cache_FV3_A/dacecache/BenchmarkMeFVTP2D___call__

cd $CACHE_DIR/build
rm *.so
cmake --build . --config Release
cd --
