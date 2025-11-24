import pandas as pd
import os

iteration_count = 45_000

def save_all_patterns(
    results,
    global_auc,
    dataset_size,
    dataset_name,
    timestamp,
    synth_data = {},
):
    base_path = f"./experiments/results/{dataset_name}/{iteration_count}/{timestamp}"
    os.makedirs(base_path, exist_ok=True)
    file_name = f"{base_path}/all_patterns.csv"

    df = pd.DataFrame(results)
    df['global_auc'] = global_auc
    df['dataset_size'] = dataset_size

    if synth_data:
        df['noise'] = synth_data['noise']
        df['avg_sequence_lenght'] = synth_data['avg_sequence_lenght']
        df['iteration_count'] = synth_data['iteration_count']
    
    df.to_csv(file_name, index=False)

def save_patterns_after_similarity_filter(
    results,
    global_auc,
    theta,
    dataset_name,
    timestamp
):
    base_path = f"./experiments/results/{dataset_name}/{iteration_count}/{timestamp}"
    os.makedirs(base_path, exist_ok=True)
    file_name = f"{base_path}/after_similarity_patterns.csv"

    df = pd.DataFrame(results)
    df['global_auc'] = global_auc
    df['theta'] = theta
    df.to_csv(file_name, index=False)

def save_patterns_after_stats_validation(
    results,
    global_auc,
    dataset_name,
    timestamp,
):
    base_path = f"./experiments/results/{dataset_name}/{iteration_count}/{timestamp}"
    os.makedirs(base_path, exist_ok=True)
    file_name = f"{base_path}/after_stats_patterns.csv"

    df = pd.DataFrame(results)
    df['global_auc'] = global_auc
    df.to_csv(file_name, index=False)

