import pandas as pd
import numpy as np
import ast
import os
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
import warnings
warnings.filterwarnings('ignore')

sns.set_style("whitegrid")

def analyze_slice_performance(
    y_true,
    y_pred,
    X_slice=None,
    X_global=None,
    y_true_global=None,
    y_pred_global=None,
    slice_name="Slice",
    pattern=None
):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_pred_binary = (y_pred >= 0.5).astype(int)
    
    auc = roc_auc_score(y_true, y_pred) if len(np.unique(y_true)) > 1 else np.nan
    
    accuracy = accuracy_score(y_true, y_pred_binary)
    precision = precision_score(y_true, y_pred_binary, zero_division=0)
    recall = recall_score(y_true, y_pred_binary, zero_division=0)
    f1 = f1_score(y_true, y_pred_binary, zero_division=0)

    y_true_global = np.array(y_true_global)
    y_pred_global = np.array(y_pred_global)
    y_pred_global_binary = (y_pred_global >= 0.5).astype(int)
    global_auc = roc_auc_score(y_true_global, y_pred_global) if len(np.unique(y_true_global)) > 1 else np.nan
    global_accuracy = accuracy_score(y_true_global, y_pred_global_binary)
    global_precision = precision_score(y_true_global, y_pred_global_binary, zero_division=0)
    global_recall = recall_score(y_true_global, y_pred_global_binary, zero_division=0)
    global_f1 = f1_score(y_true_global, y_pred_global_binary, zero_division=0)
    
    cm = confusion_matrix(y_true, y_pred_binary)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    title = f'Slice performance: {slice_name}'
    pattern_display = pattern[:100] + '...' if len(pattern) > 100 else pattern
    title = f'{title}\nPattern: {pattern_display}'
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
                xticklabels=['Predicted 0', 'Predicted 1'],
                yticklabels=['Actual 0', 'Actual 1'], cbar=False)
    axes[0].set_title('Confusion Matrix')

    metrics_comparison = {
        'Slice': [auc if not np.isnan(auc) else 0, accuracy, precision, recall, f1],
        'Global': [global_auc if not np.isnan(global_auc) else 0, global_accuracy,
                    global_precision, global_recall, global_f1]
    }
    metrics_df = pd.DataFrame(metrics_comparison, 
                                index=['AUC', 'Accuracy', 'Precision', 'Recall', 'F1'])
    metrics_df.plot(kind='bar', ax=axes[1], rot=45)
    axes[1].set_title('Metrics comparison: slice vs global')
    axes[1].set_ylabel('Score')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')

    
    plt.tight_layout()
    
    os.makedirs('experiments/results/slice_analysis', exist_ok=True)
    safe_name = slice_name.replace(' ', '_').replace('/', '_')
    safe_name = re.sub(r'emm_dynamic_api_call_sequence_per_malware_100_0_306', 'emm_dynamic_api', safe_name)
    safe_name = re.sub(r'emm_student_sequences_plus', 'emm_student', safe_name)
    safe_name = re.sub(r'emm_twitter-processed', 'emm_twitter', safe_name)
    fig_path = f'experiments/results/slice_analysis/{safe_name}.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()


def parse_pattern(pattern_str):
    try:
        pattern_list = ast.literal_eval(pattern_str)
        itemsets = []
        for itemset in pattern_list:
            if isinstance(itemset, set):
                itemsets.append(itemset)
            elif isinstance(itemset, dict):
                itemsets.append(set(itemset.keys()))
            elif isinstance(itemset, (list, tuple)):
                itemsets.append(set(itemset))
            else:
                itemsets.append(set([itemset]))
        return itemsets
    except Exception as e:
        return []

def parse_sequence(seq_str):
    seq_str = seq_str.strip()
    
    if seq_str.endswith(' -2'):
        seq_str = seq_str[:-3]
    
    parts = seq_str.split(' -1 ')
    itemsets = []
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        
        if i == 0:
            tokens = part.split()
            if len(tokens) > 1 and tokens[0] in ['0', '1']:
                items = [t.strip() for t in tokens[1:] if t.strip()]
            else:
                items = [t.strip() for t in tokens if t.strip()]
        else:
            items = [t.strip() for t in part.split() if t.strip()]
        
        if items:
            itemsets.append(set(items))
    
    return itemsets


def sequence_contains_pattern(sequence_itemsets, pattern_itemsets):
    if len(pattern_itemsets) == 0:
        return False
    
    seq_idx = 0
    pattern_idx = 0
    
    while seq_idx < len(sequence_itemsets) and pattern_idx < len(pattern_itemsets):
        if pattern_itemsets[pattern_idx].issubset(sequence_itemsets[seq_idx]):
            pattern_idx += 1
        seq_idx += 1
    
    return pattern_idx == len(pattern_itemsets)


def find_matching_sequences(pattern_str, data_df):
    pattern_itemsets = parse_pattern(pattern_str)
    if len(pattern_itemsets) == 0:
        return pd.DataFrame()
    
    matches = []
    for idx, row in data_df.iterrows():
        seq_str = str(row['sequence'])
        sequence_itemsets = parse_sequence(seq_str)
        
        if sequence_contains_pattern(sequence_itemsets, pattern_itemsets):
            matches.append(idx)
    
    return data_df.loc[matches] if matches else pd.DataFrame()


def analyze_experiment_slices(experiment_name, stats_file, train_file, test_file, n_top=15):
    stats_df = pd.read_csv(stats_file)
    top_patterns = stats_df.head(n_top)
    
    train_df = pd.read_csv(train_file) if os.path.exists(train_file) else None
    all_data = train_df
    y_true_global = all_data['y_true'].values
    y_pred_global = all_data['confidence'].values
    
    for idx, row in top_patterns.iterrows():
        pattern_str = row['pattern']
        slice_name = f"{experiment_name}_Pattern_{idx+1}"
        
        train_matches = find_matching_sequences(pattern_str, train_df)
        
        if len(train_matches) < 10:
            continue
        
        y_true_slice = train_matches['y_true'].values
        y_pred_slice = train_matches['confidence'].values
        
        X_slice = pd.DataFrame({
            'sequence_length': train_matches['sequence'].str.len(),
            'num_itemsets': train_matches['sequence'].str.count(' -1 ') + 1,
        })
        
        X_global = pd.DataFrame({
            'sequence_length': all_data['sequence'].str.len(),
            'num_itemsets': all_data['sequence'].str.count(' -1 ') + 1,
        })
        
        analyze_slice_performance(
            y_true=y_true_slice,
            y_pred=y_pred_slice,
            X_slice=X_slice,
            X_global=X_global,
            y_true_global=y_true_global,
            y_pred_global=y_pred_global,
            slice_name=slice_name,
            pattern=pattern_str
        )


def main():
    experiments = [
        {
            'name': 'emm_twitter-processed',
            'stats_file': 'experiments/results/emm_twitter-processed/10000/concatenated_deduplicated_stats.csv',
            'train_file': 'data/emm_twitter-processed_train.csv',
            'test_file': 'data/emm_twitter-processed_test.csv'
        },
        {
            'name': 'emm_student_sequences_plus',
            'stats_file': 'experiments/results/emm_student_sequences_plus/15000/concatenated_deduplicated_stats.csv',
            'train_file': 'data/emm_student_sequences_plus_train.csv',
            'test_file': 'data/emm_student_sequences_plus_test.csv'
        },
        {
            'name': 'emm_dynamic_api_call_sequence_per_malware_100_0_306',
            'stats_file': 'experiments/results/emm_dynamic_api_call_sequence_per_malware_100_0_306/20000/concatenated_deduplicated_stats.csv',
            'train_file': 'data/emm_dynamic_api_call_sequence_per_malware_100_0_306_train.csv',
            'test_file': 'data/emm_dynamic_api_call_sequence_per_malware_100_0_306_test.csv'
        }
    ]
    
    for exp in experiments:
        analyze_experiment_slices(
            experiment_name=exp['name'],
            stats_file=exp['stats_file'],
            train_file=exp['train_file'],
            test_file=exp['test_file'],
            n_top=50
        )

if __name__ == "__main__":
    main()
