import numpy as np
import pandas as pd
from collections import Counter
from statsmodels.stats.multitest import multipletests
from general.utils import is_subsequence, decode_sequence, compute_sg_dg_statistic
from general.reader import read_data_kosarak
from general.utils import encode_data, filter_empty_sequences
from seqscout.global_var import Model
import general.conf as conf
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


def _validation_soft_errors(validation_target_class):
    """Compute soft errors from validation (y_true, confidence) using same definition as main.py."""
    positive_class = int(np.max(validation_target_class[:, 0]))
    soft_errors = []
    for y, confidence in validation_target_class:
        p = confidence if y == positive_class else (1.0 - confidence)
        soft_errors.append(abs(1.0 - p))
    return np.array(soft_errors)


def calculate_p_value(result, validation_target_class, validation_data, validation_soft_errors,
                     n_subgroups=1000, pattern_idx=None, train_target_class=None, train_data=None):
    intent = result[1]

    from seqscout.global_var import get_candidate_sequence_indices
    val_candidates = get_candidate_sequence_indices(intent, is_validation=True)
    validation_extend = [i for i in val_candidates if is_subsequence(intent, validation_data[i], max_gap=conf.MAX_GAP)]
    support = len(validation_extend)
    class_balance = calculate_class_balance(validation_target_class, validation_extend)

    # Test statistic: s_g * d_g only. Random subgroups match support & class balance (as for accuracy before).
    obs_sg_dg = compute_sg_dg_statistic(
        validation_extend, validation_target_class, validation_soft_errors
    )

    random_subgroups = find_matching_subgroups(validation_target_class,
                                               class_balance, n_subgroups, seed=pattern_idx)

    random_sg_dg = []
    for sg in random_subgroups:
        stat = compute_sg_dg_statistic(sg, validation_target_class, validation_soft_errors)
        random_sg_dg.append(stat)

    random_sg_dg = np.array(random_sg_dg)
    p_value = (np.sum(random_sg_dg >= obs_sg_dg) + 1) / (len(random_sg_dg) + 1)

    print(f"    Support={support}, Class balance={dict(class_balance)}. s_g*d_g={obs_sg_dg:.4f}, p-value={p_value:.6f}")

    train_candidates = get_candidate_sequence_indices(intent, is_validation=False)
    train_extend = [i for i in train_candidates if is_subsequence(intent, train_data[i], max_gap=conf.MAX_GAP)]
    class_balance_train = calculate_class_balance(train_target_class, train_extend)
    return p_value, obs_sg_dg, class_balance_train


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
    
    # Load or reuse validation data
    if Model.get_validation_data() is not None:
        validation_data = Model.get_validation_data()
        validation_target_class = Model.get_validation_target_class()
    else:
        if validation_data_path == train_data_path:
            validation_data = Model.get_data()
            validation_target_class = Model.get_target_class()
        else:
            validation_data_raw = read_data_kosarak(validation_data_path)
            validation_data = filter_empty_sequences(encode_data(validation_data_raw, items_to_encoding))
            validation_target_class = pd.read_csv(validation_target_path)[['y_true', 'confidence']].values
        Model.set_validation_data(validation_data)
        Model.set_validation_target_class(validation_target_class)
        
    validation_soft_errors = _validation_soft_errors(validation_target_class)

    # Load or reuse train data
    train_data = Model.get_data()
    train_target_class = Model.get_target_class()
    if train_data is None:
        train_data_raw = read_data_kosarak(train_data_path)
        train_data = filter_empty_sequences(encode_data(train_data_raw, items_to_encoding))
        train_target_class = pd.read_csv(train_target_path)[['y_true', 'confidence']].values
        Model.set_data(train_data)
        Model.set_target_class(train_target_class)

    p_values, records = [], []
    valid_count = 0

    for idx, pattern in enumerate(candidate_patterns):
        print(f"\n Pattern {idx}")
        res = calculate_p_value(
            pattern,
            validation_target_class,
            validation_data,
            validation_soft_errors,
            n_subgroups=n_subgroups,
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
        return [], {}, {}

    print(f"\n Applying FDR correction")
    rejected, corrected_p, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')

    encoding_to_items = {v: k for k, v in items_to_encoding.items()}
    info = []
    significant = []
    p_values_map = {}
    for (idx, pattern, raw_p, diff, class_balance), is_sig, corr_p in zip(records, rejected, corrected_p):
        p_values_map[pattern[1]] = float(corr_p)
        info.append({
            'pattern': decode_sequence(pattern[1], encoding_to_items),
            'quality': pattern[0],
            'pattern_delta': pattern[3],
            'support': len(pattern[2]),
            'class_balance': dict(class_balance),
            'p_value': raw_p,
            'corrected_p': corr_p,
            'is_sig': is_sig,
        })
        if is_sig:
            print(f"  Pattern {idx}: s_g*d_g={diff:.4f}, p={raw_p:.6f}, adj_p={corr_p:.6f} --> SIGNIFICANT")
            significant.append((pattern[0], pattern[1], pattern[2], pattern[3], corr_p))
        else:
            print(f"  Pattern {idx}: s_g*d_g={diff:.4f}, p={raw_p:.6f}, adj_p={corr_p:.6f} --> NOT SIGNIFICANT")

    elapsed = time.time() - start_time
    print(f"\n Found {len(significant)} significant patterns out of {valid_count} tested.")
    print(f"  Validation completed in {elapsed:.2f} seconds.")

    return significant, info, p_values_map
