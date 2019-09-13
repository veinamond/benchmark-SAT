# benchmark-SAT
This is a SAT-based benchmark aimed at measuring the performance of a computer system for specific workloads that involve launching a multitude of simultaneous SAT solving processes (very similar to what happens during SAT competition)

It uses the MapleLCMDistChronoBT solver (version from the SAT competition 2018 http://sat2018.forsyte.tuwien.ac.at/). The benchmark measures the runtime of the solver on a single instance (or copies of that instance) when launched as N simultaneous processes with N varying from 1 to the number of available threads. 

To launch the benchmark one needs Python3 (I tested it in 3.6). 

To build the SAT solver you need zlib, in case of Ubuntu:
```
sudo apt install zlib1g-dev
```
To build the solver:
```
cd ./MapleLCMDistChronoBT
chmod +x ./starexec_build
./starexec_build
chmod +x ./bin/glucose_static
```
Finally to launch the benchmark:

```
cd ..
python3.6 ./benchmark_SAT.py 
```
The benchmark script parses `lscpu` output to figure out the number of sockets, number of physical cores and number of threads (if SMT|HT is available and enabled).
It can be launched in several modes: short, medium and long.
Short - the default track - launches first a single process and then _nubmer_of_cores_ processes.

Medium - launches first a single process, then _number_of_cores_ processes and finally _number_of_threads_ processes. 

Long - starts from 1 process then multiplies the number to 2 until it exceeds _number_of_cores_, then computes for _number_of_cores_ and _number_of_threads_.

To specify mode type
```
python3.6 ./benchmark_SAT.py -short
python3.6 ./benchmark_SAT.py -medium
python3.6 ./benchmark_SAT.py -long
```
For Ryzen 7 1700 the short track takes about 1000 seconds, medium track about 2500 seconds, long track about 3000 seconds. When _number_of_cores_ and more processes are launched the system starts to respond very slowly.

The benchmarking results are put into the `_benchmark.log` file.
