#!/usr/bin/env python3
"""
Script to execute all experiments detailed in experiments/README.md
for each signal rules configuration file in the config/ directory.
"""

import os
import re
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def parse_config_filename(filename: str) -> Dict[str, str]:
    """
    Parse config filename like 'd_1k__q_5%__len_1.json' to extract parameters.
    Returns dict with 'size', 'quantity', and 'length'.
    """
    # Remove .json extension
    name = filename.replace('.json', '')
    
    # Match pattern: d_{size}__q_{quantity}__len_{length}
    # quantity supports integers (e.g., 20), percents (e.g., 5%), and decimals with percent (e.g., 0.5%)
    match = re.match(r'd_([0-9k]+)__q_((?:[0-9]+(?:\.[0-9]+)?)%?|[0-9]+)__len_(\d+)', name)
    if match:
        return {
            'size': match.group(1),
            'quantity': match.group(2),
            'length': match.group(3)
        }
    return None


def get_data_files(config_file: str) -> Tuple[str, str]:
    """
    Get the corresponding .dat and .csv file paths based on config filename.
    Data files have the same name as the config file (without .json extension).
    """
    # Remove .json extension to get base name
    base_name = config_file.replace('.json', '')
    dat_path = f'data/{base_name}.dat'
    csv_path = f'data/{base_name}.csv'
    
    return dat_path, csv_path


def get_iterations_mapping() -> Dict[str, int]:
    """
    Map iteration names to actual iteration counts.
    Based on experiments/README.md
    """
    return {
        '1k': 1000,
        '5k': 5000,
        '10k': 10000,
        '20k': 20000,
        '50k': 50000
    }


def run_experiment(
    config_file: str,
    dataset_size: str,
    iterations: int,
    iter_name: str,
    dat_path: str,
    csv_path: str,
    output_dir: str = 'experiments/results'
) -> Tuple[str, str]:
    """
    Prepare a single experiment command using get_patterns.
    
    Parameters based on experiments/README.md:
    - top_k: 15 (from example in experiments/1.md)
    - time_budget: determined based on dataset size (larger = more time)
    - theta: 0.0 (from examples)
    - iterations_limit: from iterations parameter
    - synth_patterns_path: path to config file
    
    Returns: (command_string, output_file_path)
    """
    time_budget = 1000000
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate experiment name for output file
    config_stem = Path(config_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_name = f"{config_stem}_iter_{iter_name}_{timestamp}"
    output_file = os.path.join(output_dir, f"{exp_name}.txt")
    
    # Build the command (matching pattern from exec.sh)
    config_path = f"config/{config_file}"
    
    # Build python command string
    python_cmd_str = (
        f"from mctsextent.main import get_patterns; "
        f"get_patterns("
        f"path='{dat_path}', "
        f"target_path='{csv_path}', "
        f"time_budget={time_budget}, "
        f"top_k=20, "
        f"theta=0.5, "
        f"iterations_limit={iterations}, "
        f"synth_patterns_path='{config_path}'"
        f")"
    )
    
    # Full command with output redirection
    full_cmd = f"ipython3 -c \"{python_cmd_str}\" | tee {output_file}"
    
    return full_cmd, output_file


def run_experiment_subprocess(cmd: str, experiment_name: str, output_file: str) -> Tuple[bool, float]:
    """
    Run an experiment command and return (success, duration_seconds).
    """
    print(f"\n{'='*80}")
    print(f"Running: {experiment_name}")
    print(f"{'='*80}")
    
    start_ts = time.time()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=False,
            text=True,
            check=False
        )
        duration = time.time() - start_ts
        print(f"⏱ Duration: {duration:.2f}s")
        if result.returncode == 0:
            print(f"✓ Completed: {experiment_name}")
            return True, duration
        else:
            print(f"✗ Failed: {experiment_name} (exit code: {result.returncode})")
            return False, duration
            
    except Exception as e:
        duration = time.time() - start_ts
        print(f"✗ Error running {experiment_name}: {e}")
        print(f"⏱ Duration (until error): {duration:.2f}s")
        return False, duration


def main():
    """
    Main function to run all experiments.
    """
    config_dir = "config"
    results_dir = "experiments/results"
    
    # Get all JSON config files excluding signal_rules_example.json
    config_files = [
        f for f in os.listdir(config_dir)
        if f.endswith('.json') and f != 'signal_rules_example.json'
    ]
    
    config_files.sort()
    
    print(f"Found {len(config_files)} configuration files")
    print(f"Will run experiments for each config file with multiple iteration counts")
    
    # Iteration counts from experiments/README.md
    iteration_counts = ['1k', '5k', '10k', '20k', '50k']
    iterations_mapping = get_iterations_mapping()
    
    # Track results
    total_experiments = 0
    successful_experiments = 0
    failed_experiments = 0
    experiment_durations: Dict[str, float] = {}
    
    print(f"config_files: {config_files}")
    # Process each config file
    for config_file in config_files:
        print(f"\n{'#'*80}")
        print(f"Processing config file: {config_file}")
        print(f"{'#'*80}")
        
        # Parse config filename
        params = parse_config_filename(config_file)
        if not params:
            print(f"  ⚠ Skipping {config_file}: Could not parse filename")
            continue
        
        dataset_size = params['size']
        quantity = params['quantity']
        
        # Get data files (same name as config file)
        dat_path, csv_path = get_data_files(config_file)
        
        # Check if data files exist
        if not os.path.exists(dat_path):
            print(f"  ⚠ Skipping {config_file}: Data file not found: {dat_path}")
            continue
        if not os.path.exists(csv_path):
            print(f"  ⚠ Skipping {config_file}: CSV file not found: {csv_path}")
            continue
        
        print(f"  Dataset size: {dataset_size}")
        print(f"  Quantity: {quantity}")
        print(f"  Data files: {dat_path}, {csv_path}")
        
        # Run experiments for each iteration count
        for iter_name in iteration_counts:
            iterations = iterations_mapping[iter_name]
            total_experiments += 1
            
            # Generate experiment name
            exp_name = f"{Path(config_file).stem}_iter_{iter_name}"
            
            # Build command
            cmd, output_file = run_experiment(
                config_file,
                dataset_size,
                iterations,
                iter_name,
                dat_path,
                csv_path,
                results_dir
            )
            
            # Run experiment
            success, duration = run_experiment_subprocess(cmd, exp_name, output_file)
            experiment_durations[exp_name] = duration
            
            if success:
                successful_experiments += 1
            else:
                failed_experiments += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("EXPERIMENT SUMMARY")
    print(f"{'='*80}")
    print(f"Total experiments: {total_experiments}")
    print(f"Successful: {successful_experiments}")
    print(f"Failed: {failed_experiments}")
    if experiment_durations:
        total_time = sum(experiment_durations.values())
        avg_time = total_time / len(experiment_durations)
        print(f"\nTiming:")
        print(f"- Total time: {total_time:.2f}s")
        print(f"- Average per experiment: {avg_time:.2f}s")
        # Save timings
        timings_path = os.path.join(results_dir, "timings.csv")
        try:
            os.makedirs(results_dir, exist_ok=True)
            with open(timings_path, "w") as f:
                f.write("experiment_name,duration_seconds\n")
                for name, dur in sorted(experiment_durations.items()):
                    f.write(f"{name},{dur:.4f}\n")
            print(f"- Timings saved to: {timings_path}")
        except Exception as e:
            print(f"- Warning: failed to save timings: {e}")
    print(f"\nResults saved to: {results_dir}/")


if __name__ == "__main__":
    main()

