# main.py
import os
import stateless.generate as G
from stateless.exceptions import *
from stateless.utils import *
import stateless.config as CONFIG
import random
import time
import json
import sys
import importlib.util
import cProfile
import pstats
import io
import csv

def valid_input(validator):
    parray = b''
    cb_arr = []
    while True:
        created_bits = None
        try:
            created_bits = G.generate(validator, parray, 0)
            if created_bits is None:
                return None
            cb_arr.append(created_bits)
            if random.randrange(len(created_bits)) == 0:
                parray = created_bits
                #print('+>', repr(created_bits), file=sys.stderr)
                continue
        except (InputLimitException, IterationLimitException, BacktrackLimitException) as e:
            print("E:", str(e))
        finally:
            G.SEEN_AT.clear()
        #print(">", repr(created_bits), len(cb_arr), file=sys.stderr)
        return cb_arr[-1] if cb_arr else None

def run_for(validator, name, secs=None):
    start = time.time()
    if secs is None:
        secs = 10
    lst_generated = []
    with open('results/results_%s.json' % name, 'a+') as f:
        while (time.time() - start) < secs:
            i = valid_input(validator)
            if i is None:
                continue
            c = (-1, -1)
            lst_generated.append((i, c, (time.time() - start)))
            print(json.dumps({'output': [j for j in i],
                             'cumcoverage': c,
                             'time': (time.time() - start)}),
                  file=f, flush=True)
    return lst_generated

def main():
    time_to_run = CONFIG.TIME_TO_RUN
    my_module = sys.argv[1]
    name = os.path.basename(my_module)
    spec = importlib.util.spec_from_file_location("decoder", my_module)
    my_decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(my_decoder)
    lst = run_for(my_decoder.validator, name, time_to_run)

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    main()

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()

    s.seek(0)
    csv_filename = 'profiles/profile_results.csv'

    with open(csv_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Function', 'Calls', 'Total Time', 'Per Call', 'Cumulative Time', 'Per Call (Cum)'])

        for line in s:
            if line.startswith('ncalls') or line.strip() == '':
                continue  
            parts = line.strip().split(None, 5)
            if len(parts) < 6:
                continue  
            ncalls, tottime, percall, cumtime, percall_cum, func = parts
            func = func.strip()
            csv_writer.writerow([func, ncalls, tottime, percall, cumtime, percall_cum])

    print(f"Profiling complete. Results saved to {csv_filename}")
