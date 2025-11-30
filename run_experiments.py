#!/usr/bin/env python3
import os
import subprocess
import time
from datetime import datetime


def run_experiment(filename, output_dir = 'experiments/results'):
    time_budget = 2**30
    iterations_limit = 15_000

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_name = f"{filename}_{timestamp}"
    output_file = os.path.join(output_dir, f"{exp_name}.txt")

    python_cmd_str = (
        f"from mctsextent.main import get_patterns; "
        f"get_patterns("
        f"filename='{filename}', "
        f"time_budget={time_budget}, "
        f"top_k=20, "
        f"theta=0.5, "
        f"iterations_limit={iterations_limit}"
        f")"
    )
   
    full_cmd = f"ipython3 -c \"{python_cmd_str}\""

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
    results_dir = "experiments/results"

    constrasting_experiment_files = [
       'd_5k__l_10_15__n_0.25__contrasting',
    ]

    dimension_experiment_files = [
       #'d_5k__l_7_10__n_0.25',
       #'d_5k__l_10_15__n_0.25',
       'd_5k__l_25_30__n_0.25',

       'd_15k__l_7_10__n_0.25',
       'd_15k__l_10_15__n_0.25',
       'd_15k__l_25_30__n_0.25',
    ]

    noise_experiment_files = [
       #'d_5k__l_10_15__n_0',
        #'d_5k__l_10_15__n_0.5',
        #'d_5k__l_10_15__n_1'
    ]

    total_experiments = 0
    successful_experiments = 0
    failed_experiments = 0
    experiment_durations = {}

    print(f"====================================================")
    print(f"---------- RUNNING DIMENSION TESTS ----------------")
    print(f"====================================================")
    for file in dimension_experiment_files:
        print(f"+++++++++++ {file} ++++++++++")
        cmd, output_file = run_experiment(
            file,
            results_dir
        )

        success, duration = run_experiment_subprocess(cmd, file)
        experiment_durations[file] = duration

        if success:
            successful_experiments += 1
        else:
            failed_experiments += 1

    print(f"====================================================")
    print(f"---------- RUNNING NOISE TESTS ----------------")
    print(f"====================================================")
    for file in noise_experiment_files:
        print(f"+++++++++++ {file} ++++++++++")
        cmd, output_file = run_experiment(
            file,
            results_dir
        )

        success, duration = run_experiment_subprocess(cmd, file)
        experiment_durations[file] = duration

        if success:
            successful_experiments += 1
        else:
            failed_experiments += 1


    print(f"====================================================")
    print(f"---------- RUNNING CONSTRASTING TESTS ----------------")
    print(f"====================================================")
    for file in constrasting_experiment_files:
        print(f"+++++++++++ {file} ++++++++++")
        cmd, output_file = run_experiment(
            file,
            results_dir
        )

        success, duration = run_experiment_subprocess(cmd, file)
        experiment_durations[file] = duration

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
