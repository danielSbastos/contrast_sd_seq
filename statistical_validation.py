import numpy as np
import pandas as pd
from collections import Counter
from statsmodels.stats.multitest import multipletests
from general.utils import roc_auc_score_binary, is_subsequence
from general.reader import read_data_kosarak
from general.utils import encode_data, filter_empty_sequences
from seqscout.global_var import Model
import random
import time


# -------------------------------------------------------------------
# 1. Compute AUC difference (SubROC φ₀,₀ statistic)
# -------------------------------------------------------------------
def get_auc_difference(support, data, extend, target_class):
    if len(extend) < 2:
        return None

    subset = target_class[extend]
    auc_subset = roc_auc_score_binary(subset[:, 0], subset[:, 1])
    auc_global = roc_auc_score_binary(target_class[:, 0], target_class[:, 1])
    diff = auc_global - auc_subset
    diff = auc_subset - auc_global


    #print(f"      ↳ Subgroup AUC={auc_subset:.4f}, Global AUC={auc_global:.4f}, ΔAUC={diff:.4f}")
    return diff


def calculate_class_balance(target_class, extend):
    return Counter(target_class[extend, 0])


def find_matching_subgroups(target_class, support, class_balance, n_subgroups=1000, seed=None):
    rng = np.random.default_rng(seed)
    y_trues = target_class[:, 0]
    idx_by_class = {label: np.where(y_trues == label)[0].tolist() for label in np.unique(y_trues)}

    subgroups = []
    for _ in range(n_subgroups):
        subgroup = []
        for label, n_needed in class_balance.items():
            subgroup.extend(rng.choice(idx_by_class[label], size=n_needed, replace=False))
        rng.shuffle(subgroup)
        subgroups.append(subgroup)

    return subgroups


# -------------------------------------------------------------------
# 2. Compute empirical p-value per subgroup (SubROC-style)
# -------------------------------------------------------------------

def calculate_p_value_subroc(result, validation_target_class, validation_data,
                             n_subgroups=1000, pattern_idx=None, verbose=True):
    """
    Calculate empirical p-value using SubROC-style validation
    with rank-transformed ΔAUC for numerical stability.
    """
    intent = result[1]

    # Find coverage in validation set
    validation_extend = [i for i, seq in enumerate(validation_data) if is_subsequence(intent, seq)]
    if not validation_extend:
        if verbose:
            print("    ⚠️  Pattern not found in validation dataset.")
        return None

    support = len(validation_extend)
    class_balance = calculate_class_balance(validation_target_class, validation_extend)

    if verbose:
        print(f"    Support={support}, Class balance={dict(class_balance)}")

    # --- Compute ΔAUC (pattern vs global) ---
    auc_subset = roc_auc_score_binary(validation_target_class[validation_extend, 0],
                                      validation_target_class[validation_extend, 1])
    auc_global = roc_auc_score_binary(validation_target_class[:, 0],
                                      validation_target_class[:, 1])
    obs_auc_diff = auc_subset - auc_global  # ✅ positive = better than global

    if verbose:
        print(f"    Pattern AUC={auc_subset:.4f}, Global AUC={auc_global:.4f}, ΔAUC={obs_auc_diff:.4f}")

    # --- Generate null distribution ---
    random_subgroups = find_matching_subgroups(validation_target_class, support,
                                               class_balance, n_subgroups, seed=pattern_idx)

    random_diffs = []
    for sg in random_subgroups:
        auc_sg = roc_auc_score_binary(validation_target_class[sg, 0], validation_target_class[sg, 1])
        diff = auc_sg - auc_global
        random_diffs.append(diff)

    random_diffs = np.array(random_diffs)
    if len(random_diffs) == 0:
        print("    ⚠️  No valid random subgroups generated.")
        return None

    sorted_diffs = np.sort(random_diffs)
    ranks = np.searchsorted(sorted_diffs, obs_auc_diff, side='right')
    rank_percentile = ranks / len(sorted_diffs)
    p_value = (np.sum(np.abs(random_diffs) >= abs(obs_auc_diff)) + 1) / (len(random_diffs) + 1)

    if verbose:
        print(f"    Rank percentile={rank_percentile:.4f}, empirical p-value={p_value:.6f}")

    return p_value, obs_auc_diff

from statsmodels.stats.multitest import multipletests
import numpy as np
import pandas as pd
import time

def filter_by_significance(
    candidate_patterns,
    validation_data_path,
    validation_target_path,
    items_to_encoding,
    alpha=0.05,
    n_subgroups=1000
):
    """
    Filter candidate patterns by statistical significance using empirical p-values
    and Benjamini–Yekutieli (FDR-BY) correction, as in SubROC.

    Patterns not appearing in the validation dataset are skipped.
    """
    start_time = time.time()
    print("\n=== SubROC-style Statistical Validation (BY correction) ===")

    # --- Load validation data ---
    validation_data_raw = read_data_kosarak(validation_data_path)
    validation_data = filter_empty_sequences(encode_data(validation_data_raw, items_to_encoding))
    validation_target_class = pd.read_csv(validation_target_path)[['y_true', 'confidence']].values
    Model.set_validation_data(validation_data)
    Model.set_validation_target_class(validation_target_class)

    print(f"✅ Loaded {len(validation_data)} validation sequences.")
    print(f"α={alpha}, n_subgroups={n_subgroups}, candidate_patterns={len(candidate_patterns)}")

    # --- Collect p-values ---
    p_values, records = [], []
    valid_count = 0

    for idx, pattern in enumerate(candidate_patterns):
        print(f"\n🔹 Pattern {idx}: evaluating subgroup significance...")
        res = calculate_p_value_subroc(
            pattern,
            validation_target_class,
            validation_data,
            n_subgroups,
            pattern_idx=idx,
        )

        # Skip patterns not found in validation data or invalid AUCs
        if res is None:
            print(f"    ⚠️  Pattern {idx} skipped — not found or invalid in validation dataset.")
            continue

        p, diff = res
        if p is None or np.isnan(p) or p <= 0 or p > 1:
            print(f"    ⚠️  Pattern {idx} skipped — invalid p-value ({p}).")
            continue

        valid_count += 1
        p_values.append(p)
        records.append((idx, pattern, p, diff))

    print(f"\n✅ Retained {valid_count} valid patterns (out of {len(candidate_patterns)}) for FDR correction.")

    if not p_values:
        print("⚠️  No valid patterns to test — skipping FDR correction.")
        return [], {}

    # --- Apply Benjamini–Yekutieli (FDR-BY) correction ---
    print(f"\n📈 Applying FDR correction (Benjamini–Yekutieli)...")
    rejected, corrected_p, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')

    significant = []
    filtered_info = {}

    for (idx, pattern, raw_p, diff), is_sig, corr_p in zip(records, rejected, corrected_p):
        if is_sig:
            print(f"  ✅ Pattern {idx}: ΔAUC={diff:.4f}, p={raw_p:.6f}, adj_p={corr_p:.6f} → SIGNIFICANT")
            significant.append(pattern)
        else:
            filtered_info[idx] = {
                'p_value': raw_p,
                'corrected_p': corr_p,
                'reason': f'corrected_p={corr_p:.6f} > α={alpha}',
            }
            print(f"  ❌ Pattern {idx}: ΔAUC={diff:.4f}, p={raw_p:.6f}, adj_p={corr_p:.6f} → NOT SIGNIFICANT")

    elapsed = time.time() - start_time
    print(f"\n🎯 Found {len(significant)} significant patterns out of {valid_count} tested.")
    print(f"⏱️  Validation completed in {elapsed:.2f} seconds.")

    return significant, filtered_info
