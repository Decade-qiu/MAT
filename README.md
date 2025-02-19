# MAT
MAT match-action run
```
g++ ./src/MAT.cpp ./main.cpp -o main_222 --std=c++11 -mavx2 -O3 -march=native -funroll-all-loops -flto; 
./main_222.exe;
```
Performance Test
```
perf record -e task-clock -g ./MAT
perf script > out.perf
stackcollapse-perf.pl out.perf > out.folded
flamegraph.pl out.folded > 1k.svg
```