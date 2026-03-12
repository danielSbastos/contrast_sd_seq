import pandas as pd
import os

def save_all_patterns(
    results,
    dataset_size,
    dataset_name,
    timestamp,
    iteration_count,
    synth_data = {},
    max_gap=None,
    support_penalty=0,
    sigmoid_offset=2,
):
    base_path = f"./experiments/results/{dataset_name}/{iteration_count}/{timestamp}"
    os.makedirs(base_path, exist_ok=True)
    file_name = f"{base_path}/all_patterns.csv"

    df = pd.DataFrame(results)
    df['dataset_size'] = dataset_size

    if synth_data:
        df['noise'] = synth_data['noise']
        df['avg_sequence_lenght'] = synth_data['avg_sequence_lenght']

    if max_gap is None:
        df['max_gap'] = -1
    else:
        df['max_gap'] = max_gap

    df['support_penalty'] = support_penalty
    df['sigmoid_offset'] = sigmoid_offset
    df.to_csv(file_name, index=False)

def save_patterns_after_similarity_filter(
    results,
    theta,
    dataset_name,
    timestamp,
    iteration_count,
):
    base_path = f"./experiments/results/{dataset_name}/{iteration_count}/{timestamp}"
    os.makedirs(base_path, exist_ok=True)
    file_name = f"{base_path}/after_similarity_patterns.csv"

    df = pd.DataFrame(results)
    df['theta'] = theta
    df.to_csv(file_name, index=False)

def save_patterns_after_stats_validation(
    results,
    dataset_name,
    timestamp,
    iteration_count,
):
    base_path = f"./experiments/results/{dataset_name}/{iteration_count}/{timestamp}"
    os.makedirs(base_path, exist_ok=True)
    file_name = f"{base_path}/after_stats_patterns.csv"

    df = pd.DataFrame(results)
    df.to_csv(file_name, index=False)


def save_iteration_metrics(metrics, dataset_name, timestamp, iteration_count):
    base_path = f"./experiments/results/{dataset_name}/{iteration_count}/{timestamp}"
    os.makedirs(base_path, exist_ok=True)
    file_name = f"{base_path}/iteration_metrics.csv"
    df = pd.DataFrame([metrics])
    df.to_csv(file_name, index=False)

