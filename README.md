# MAT
MAT match-action run
```
cd build
cmake ..
make
./MAT
```
Performance Test
```
perf record -e cpu-clock -g ./MAT
perf script > out.perf
stackcollapse-perf.pl out.perf > out.folded
flamegraph.pl out.folded > 1k.svg
```