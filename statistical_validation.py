import numpy as np
import pandas as pd
from collections import Counter
from statsmodels.stats.multitest import multipletests
from general.utils import accuracy_score_binary, is_subsequence, decode_sequence
from general.reader import read_data_kosarak
from general.utils import encode_data, filter_empty_sequences
from seqscout.global_var import Model
import random
import time


def calculate_class_balance(target_class, extend):
    return Counter(target_class[extend, 0])


def find_matching_subgroups(target_class, class_balance, n_subgroups=1000, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    y_trues = target_class[:, 0]
    
    indices_by_class = {
        label: np.where(y_trues == label)[0].tolist()
        for label in np.unique(y_trues)
    }

    subgroups = []
    for _ in range(n_subgroups):
        subgroup = []
        for label, required_count in class_balance.items():
            candidates = indices_by_class[label]
            sampled = random.sample(candidates, required_count)
            subgroup.extend(sampled)
        random.shuffle(subgroup)
        subgroups.append(subgroup)

    return subgroups


def calculate_p_value(result, validation_target_class, validation_data, n_subgroups=1000, pattern_idx=None, 
                     train_target_class=None, train_data=None):
    intent = result[1]

    validation_extend = [i for i, seq in enumerate(validation_data) if is_subsequence(intent, seq)]
    support = len(validation_extend)
    class_balance = calculate_class_balance(validation_target_class, validation_extend)

    obs_accuracy_sg = accuracy_score_binary(validation_target_class[validation_extend, 0], validation_target_class[validation_extend, 1])
    accuracy_global = accuracy_score_binary(validation_target_class[:, 0], validation_target_class[:, 1])
    obs_accuracy_diff = accuracy_global - obs_accuracy_sg

    random_subgroups = find_matching_subgroups(validation_target_class, 
                                               class_balance, n_subgroups, seed=pattern_idx)

    random_diffs = []
    for sg in random_subgroups:
        accuracy_sg = accuracy_score_binary(validation_target_class[sg, 0], validation_target_class[sg, 1])
        diff = accuracy_global - accuracy_sg
        random_diffs.append(diff)

    random_diffs = np.array(random_diffs)
    p_value = (np.sum(random_diffs >= obs_accuracy_diff) + 1) / (len(random_diffs) + 1)

    print(f"    Support={support}, Class balance={dict(class_balance)}. Pattern Accuracy={obs_accuracy_sg:.4f}, p-value={p_value:.6f}")

    train_extend = [i for i, seq in enumerate(train_data) if is_subsequence(intent, seq)]
    class_balance_train = calculate_class_balance(train_target_class, train_extend)
    return p_value, obs_accuracy_diff, class_balance_train

def filter_by_significance(
    candidate_patterns,
    validation_data_path,
    validation_target_path,
    items_to_encoding,
    alpha=0.05,
    n_subgroups=1000,
    train_data_path=None,
    train_target_path=None
):
    start_time = time.time()
    validation_data_raw = read_data_kosarak(validation_data_path)
    validation_data = filter_empty_sequences(encode_data(validation_data_raw, items_to_encoding))
    validation_target_class = pd.read_csv(validation_target_path)[['y_true', 'confidence']].values
    Model.set_validation_data(validation_data)
    Model.set_validation_target_class(validation_target_class)

    train_data_raw = read_data_kosarak(train_data_path)
    train_data = filter_empty_sequences(encode_data(train_data_raw, items_to_encoding))
    train_target_class = pd.read_csv(train_target_path)[['y_true', 'confidence']].values

    p_values, records = [], []
    valid_count = 0

    for idx, pattern in enumerate(candidate_patterns):
        print(f"\n Pattern {idx}")
        res = calculate_p_value(
            pattern,
            validation_target_class,
            validation_data,
            n_subgroups,
            pattern_idx=idx,
            train_target_class=train_target_class,
            train_data=train_data,
        )

        p, diff, class_balance = res
        if p is None or np.isnan(p) or p <= 0 or p > 1:
            continue

        valid_count += 1
        p_values.append(p)
        records.append((idx, pattern, p, diff, class_balance))

    if not p_values:
        return [], {}

    print(f"\n Applying FDR correction")
    rejected, corrected_p, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')

    encoding_to_items = {v: k for k, v in items_to_encoding.items()}
    info = []
    significant = []
    for (idx, pattern, raw_p, diff, class_balance), is_sig, corr_p in zip(records, rejected, corrected_p):
        info.append({
            'pattern': decode_sequence(pattern[1], encoding_to_items),
            'quality': pattern[0],
            'pattern_accuracy': pattern[3],
            'support': len(pattern[2]),
            'class_balance': dict(class_balance),
            'p_value': raw_p,
            'corrected_p': corr_p,
            'is_sig': is_sig,
        })
        if is_sig:
            print(f"  Pattern {idx}: Accuracy diff={diff:.4f}, p={raw_p:.6f}, adj_p={corr_p:.6f} --> SIGNIFICANT")
            significant.append(pattern)
        else:
            print(f"  Pattern {idx}: Accuracy diff={diff:.4f}, p={raw_p:.6f}, adj_p={corr_p:.6f} --> NOT SIGNIFICANT")

    elapsed = time.time() - start_time
    print(f"\n Found {len(significant)} significant patterns out of {valid_count} tested.")
    print(f"  Validation completed in {elapsed:.2f} seconds.")

    return significant, info
