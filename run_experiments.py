#!/usr/bin/env python3
import os
import re
import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple


def parse_config_filename(filename: str) -> Dict[str, str]:
    name = filename.replace('.json', '')
    
    match = re.match(r'd_([0-9k]+)__q_((?:[0-9]+(?:\.[0-9]+)?)%?|[0-9]+)', name)
    if match:
        return {
            'size': match.group(1),
            'quantity': match.group(2)
        }
    return None


def get_data_files(config_file: str, noise: float, l4_only: bool = False) -> Tuple[str, str]:
    base_name = config_file.replace('.json', '')
    noise_str = str(noise) if noise != int(noise) else str(int(noise))
    dat_path = f'data/{base_name}__n_{noise_str}.dat'
    csv_path = f'data/{base_name}__n_{noise_str}.csv'
    
    return dat_path, csv_path


def run_experiment(config_file, iterations, iter_name, noise, dat_path, output_dir = 'experiments/results'):
    time_budget = 2**30
    
    os.makedirs(output_dir, exist_ok=True)
    
    config_stem = Path(config_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    noise_str = str(noise) if noise != int(noise) else str(int(noise))
    exp_name = f"{config_stem}_iter_{iter_name}_n_{noise_str}_{timestamp}"
    output_file = os.path.join(output_dir, f"{exp_name}.txt")
    
    config_path = f"config/{config_file}"
    
    filename = Path(dat_path).stem
    
    python_cmd_str = (
        f"from mctsextent.main import get_patterns; "
        f"get_patterns("
        f"filename='{filename}', "
        f"time_budget={time_budget}, "
        f"top_k=20, "
        f"theta=0.8, "
        f"iterations_limit={iterations}, "
        f"synth_patterns_path='{config_path}'"
        f")"
    )
    
    full_cmd = f"ipython3 -c \"{python_cmd_str}\" 2>&1 | tee {output_file}"
    
    return full_cmd, output_file


def run_experiment_subprocess(cmd, experiment_name):
    print(f"================================================================")
    print(f"++++++++++++++ RUNNING: {experiment_name} ++++++++++++++")
    print(f"================================================================")
    
    start_ts = time.time()
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=False,
        text=True,
        check=False
    )
    duration = time.time() - start_ts
    print(f" duration: {duration:.2f}s")
    if result.returncode == 0:
        return True, duration
    else:
        return False, duration
            

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--l4', action='store_true')
    args = parser.parse_args()
    
    config_dir = "config"
    results_dir = "experiments/results"
    
    config_files = [
        f for f in os.listdir(config_dir)
        if f.endswith('.json') and f != 'signal_rules_example.json'
    ]
    
    if args.l4_only:
        config_files = [f for f in config_files if '__l_4' in f]
        print("Running in l4 mode")
    else:
        config_files = [f for f in config_files if '__l_4' not in f]
        print("Running in normal mode")
    
    config_files.sort()
    
    iteration_counts = ['1k', '5k', '10k', '20k', '50k']
    iterations_mapping = {
        '1k': 1000,
        '5k': 5000,
        '10k': 10000,
        '20k': 20000,
        '50k': 50000
    }
    
    total_experiments = 0
    successful_experiments = 0
    failed_experiments = 0
    experiment_durations = {}
    
    print(f"config_files: {config_files}")
    for config_file in config_files:
        print(f"====================================================")
        print(f"---------- PROCESSING: {config_file} ----------")
        print(f"====================================================")
        
        params = parse_config_filename(config_file)
        if not params:
            print(f"  Skipping {config_file}: Could not parse filename")
            continue
        
        dataset_size = params['size']
        quantity = params['quantity']
        
        print(f"  dataset size: {dataset_size}")
        print(f"  quantity: {quantity}")
        
        noise_values = [0, 0.5, 1]
        
        for noise in noise_values:
            dat_path, csv_path = get_data_files(config_file, noise, args.l4_only)
            print(f"  noise: {noise}")
            print(f"  data files: {dat_path}, {csv_path}")
            
            for iter_name in iteration_counts:
                iterations = iterations_mapping[iter_name]
                total_experiments += 1
                
                noise_str = str(noise) if noise != int(noise) else str(int(noise))
                exp_name = f"{Path(config_file).stem}_iter_{iter_name}_n_{noise_str}"
                
                cmd, output_file = run_experiment(
                    config_file,
                    iterations,
                    iter_name,
                    noise,
                    dat_path,
                    results_dir
                )
                
                success, duration = run_experiment_subprocess(cmd, exp_name)
                experiment_durations[exp_name] = duration
                
                if success:
                    successful_experiments += 1
                else:
                    failed_experiments += 1
    
    print(f"================")
    print("Summary")
    print(f"================")
    print(f"Total experiments: {total_experiments}")
    print(f"Successful: {successful_experiments}")
    print(f"Failed: {failed_experiments}")
    if experiment_durations:
        total_time = sum(experiment_durations.values())
        avg_time = total_time / len(experiment_durations)
        print(f"\nTiming:")
        print(f"- Total time: {total_time:.2f}s")
        print(f"- Average per experiment: {avg_time:.2f}s")

        timings_path = os.path.join(results_dir, "timings.csv")
        with open(timings_path, "w") as f:
            f.write("experiment_name,duration_seconds\n")
            for name, dur in sorted(experiment_durations.items()):
                f.write(f"{name},{dur:.4f}\n")
    print(f"\nResults saved to: {results_dir}/")

if __name__ == "__main__":
    main()