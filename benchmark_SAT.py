import sys
import multiprocessing
import os
import time
import subprocess
import shutil 

import pty
import errno


solver_binary = "./MapleLCMDistChronoBT/bin/glucose_static"
outs_path = "./outs/"
PHP10cnf = "./PHP10"
PHP11cnf = "./PHP11"
cnf638 = "./6-3-8.cnf"
logfile = "./_benchmark.log"

numproc_max = 8

def launch_solver_rc1(input_data):    
    cnf_file = input_data[0]
    index1 = input_data[1]
    index2 = input_data[2]
    cnf_personalized = cnf_file
    if (index2>1):
        cnf_personalized = cnf_file + "_" + str(index1)    
    outfn = outs_path + cnf_file.split("/")[-1]+"_"+str(index1)+"_"+str(index2)+".out"    
    solverargs = ["timeout",str(3600)+"s",solver_binary,cnf_personalized]    
    master_fd, slave_fd = pty.openpty()

    t1 = time.perf_counter()       
    proc = subprocess.Popen(solverargs,encoding="utf-8", stdout=slave_fd, stderr=subprocess.STDOUT,close_fds=True)
    
    os.close(slave_fd)
    output = []
    try:
        while 1:
            try:
                data = os.read(master_fd, 1024).decode()
            except OSError as e:
                if e.errno != errno.EIO:
                    raise
                break # EIO means EOF on some systems
            else:
                if not data: # EOF
                    break
                output.append(data)
    finally:
        os.close(master_fd)
        if proc.poll() is None:
            proc.kill()
        proc.wait()
    #output = "".join(output)
    #print(str(output))
    t2=time.perf_counter()                    

    status = "INDET"
    
    for line in output:
        if "s SATISFIABLE" in line:
            status = "SAT"
        if "s UNSATISFIABLE" in line:
            status = "UNSAT"

    with open(outfn, "w") as outfile:            
        for line in output:   
            outfile.write(line+"\n")
    res = t2-t1  
    print("Process {} finished solving {} : {} in time {}".format(str(index1),cnf_file.split("/")[-1],status,str(res)))  
    return res

def run_benchmark(number_of_processes, cnf):    
    results = list()
    if (number_of_processes>1):
        print("Launching the solving of {} in {} separate processes\n".format(cnf,str(number_of_processes)))    
        for u in range(number_of_processes):
            shutil.copyfile(cnf, cnf + "_" + str(u))
        input_dataset = list()
        input_dataset = [[cnf,u,number_of_processes] for u in range(number_of_processes)]
        p = multiprocessing.Pool(number_of_processes)   
        results = p.map(launch_solver_rc1,input_dataset)
        p.close()
        p.join()
        #print(results)        
        for u in range(number_of_processes):
            os.remove(cnf + "_" + str(u))        
    else:
        print("Launching the solving of {} in a single process\n".format(cnf))    
        input_data = [cnf, 0, 1]
        results.append(launch_solver_rc1(input_data))

    with open(logfile,'a') as outfile:
        outfile.write("Results for cnf {} and {} process(es): {} \n".format(cnf, str(number_of_processes),", ".join([str(u) for u in results])))
    return results
          
#run_benchmark(1, PHP11cnf)
#run_benchmark(4, PHP11cnf)
#run_benchmark(8, PHP11cnf)
#run_benchmark(16, PHP11cnf)
def get_cpu_info():
    cpu_info = (subprocess.check_output("lscpu",shell=True).strip()).decode()
    with open(logfile,'a') as outfile:
        outfile.write(cpu_info)
    sockets = 0
    cores_per_socket = 0
    total_cpus = 0
    threads_per_core = 0
    for line in cpu_info.split("\n"):
        p = [u.strip() for u in line.split(":")]
        if p[0]=="CPU(s)":            
            total_cpus = int(p[1])        
        if "socket(s)" in p[0] or "Socket(s)" in p[0]:            
            sockets = int(p[1])
        if p[0] == "Core(s) per socket":            
            cores_per_socket = int(p[1])
        if p[0] == "Thread(s) per core":            
            threads_per_core = int(p[1])
    
    return sockets,cores_per_socket,threads_per_core,total_cpus    


with open(logfile,'a') as outfile:
    outfile.write("Launched benchmark @ {} with args {}\n".format(str(time.ctime()), " ".join([str(u) for u in sys.argv])))

cnffile = cnf638
track = "short"
np = 0
for i in range(1, len(sys.argv)):                          
    if (sys.argv[i] == '-cnf'):
        cnffile = sys.argv[i+1]       
    
    if (sys.argv[i] == '-numproc'):
        np = int(sys.argv[i+1])            
            
    if (sys.argv[i] == '-short'):
        track = 'short'

    if (sys.argv[i] == '-medium'):
        track = 'medium'

    if (sys.argv[i] == '-long'):
        track = 'long'


s, cps, tpc, tc = get_cpu_info()

number_of_cores = 0
number_of_threads = 0

if s!=0 and cps!=0:
    number_of_cores = s*cps

if number_of_cores>0 and tpc>0:
    number_of_threads = number_of_cores*tpc

if number_of_cores == 0:
    number_of_cores = os.cpu_count()
    number_of_threads = number_of_cores

if np!=0:
    number_of_cores = np
    number_of_threads = np


benchmarking_np = list()
if (track=="short"):
    #short track
    benchmarking_np.append(1)
    benchmarking_np.append(number_of_cores)

if (track=="medium"):
    #medium track 
    benchmarking_np.append(1)
    benchmarking_np.append(number_of_cores)
    if (number_of_cores != number_of_threads):
        benchmarking_np.append(number_of_threads)

if (track=="long"):
    #long track         
    k = 1
    while k < number_of_cores:
        benchmarking_np.append(k)
        k=k*2

    benchmarking_np.append(number_of_cores)
    if (number_of_cores != number_of_threads):
        benchmarking_np.append(number_of_threads)

print("Found {} processor(s) with {} total cores and {} total threads.".format(str(s),str(number_of_cores),str(number_of_threads)))
print("Running the {} track".format(track))
print("Will launch computations for {} processes".format(", ".join([str(u) for u in benchmarking_np])))
with open(logfile,'a') as outfile:
    outfile.write("Runing {} track: {}\n".format(track,", ".join([str(u) for u in benchmarking_np])))
res = dict()
for u in benchmarking_np:    
    res[u] = run_benchmark(u, cnffile)





