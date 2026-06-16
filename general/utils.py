import json
from collections import Counter

import random
from traceback import print_tb

import general.conf as conf

import functools
import numpy as np
from math import e, log
from sklearn.metrics import roc_auc_score, log_loss

def increase_it_number():
    global ITERATION_NUMBER
    ITERATION_NUMBER += 1


from seqscout.global_var import Model


def parse_expected_patterns(file_path):
    with open(file_path) as f:
        d = json.load(f)

    patterns = list(map(lambda x: x['element'], d))

    fmt_patterns = []
    for pattern in patterns:
        fmt_patterns.append(list(map(lambda x: x.replace("{", "").replace("}", "").split(" "), pattern.split('} {'))))

    return fmt_patterns

def encode_expected_patterns(patterns, encoding):
    encoded_patterns = []
    for pattern in patterns:
        encoded_pattern = []
        for itemset in pattern:
            encoded_itemset = set(map(lambda item: encoding[item], itemset))
            encoded_pattern.append(encoded_itemset)

        encoded_pattern = sequence_mutable_to_immutable(encoded_pattern)
        encoded_patterns.append(encoded_pattern)

    return encoded_patterns

def decode_expected_patterns(pattern, decoding):
    pass


def sequence_mutable_to_immutable(sequence):
    """
    :param sequence: form [{}, {}, ...]
    :return: the same sequence in its immutable form
    """
    return tuple([frozenset(i) for i in sequence])


def sequence_immutable_to_mutable(sequence):
    """
    :param sequence: form (frozenset(), frozenset(), ...)
    :return: the same sequence in its mutable form
    """
    return [set(i) for i in sequence]


def create_s_extension(sequence, item, index):
    """
    Perform an s-extension
    :param sequence: the sequence we are extending
    :param item: the item to insert (not a set, an item !)
    :param index: the index to add the item
    :return: an immutable sequence
    """
    # insert would require a deep copy, which is not performance

    new_sequence = []
    appended = False

    for i, itemset in enumerate(sequence):
        if i == index:
            new_sequence.append(frozenset({item}))
            appended = True
        new_sequence.append(itemset)

    if not appended:
        new_sequence.append(frozenset({item}))

    return tuple(new_sequence)


def create_i_extension(sequence, item, index):
    """
    Perform an i-extension
    :param sequence: the sequence we are extending
    :param item: the item to merge to(not a set, an item !)
    :param index: the index to add the item
    :return: an immutable sequence
    """
    new_sequence = []

    for i, itemset in enumerate(sequence):
        if i == index:
            new_sequence.append(frozenset({item}).union(itemset))
        else:
            new_sequence.append(itemset)

    return tuple(new_sequence)


def is_subsequence_contiguous(a, b):
    if len(a) > len(b):
        return False

    if len(a) == 0:
        return True

    for start_idx in range(len(b) - len(a) + 1):
        match = True
        for i in range(len(a)):
            if not a[i].issubset(b[start_idx + i]):
                match = False
                break
        if match:
            return True

    return False


def is_subsequence_windowed(a, b, max_gap=None):
    if len(a) > len(b):
        return False

    if len(a) == 0:
        return True

    prev_positions = [set()]

    for j in range(len(b)):
        if a[0].issubset(b[j]):
            prev_positions[0].add(j)

    if not prev_positions[0]:
        return False

    for i in range(1, len(a)):
        prev_positions.append(set())

        for prev_j in prev_positions[i-1]:
            for j in range(prev_j + 1, min(prev_j + max_gap + 2, len(b))):
                if a[i].issubset(b[j]):
                    prev_positions[i].add(j)

        if not prev_positions[i]:
            return False

    return True


def is_subsequence_non_contiguous(a, b):
    if len(a) > len(b):
        return False

    if len(a) == 0:
        return True

    i_a, i_b = 0, 0

    while i_a < len(a) and i_b < len(b):
        if a[i_a].issubset(b[i_b]):
            i_a += 1
        i_b += 1

    return i_a == len(a)


def is_subsequence(a, b, max_gap=None):
    if max_gap == 0:
        return is_subsequence_contiguous(a, b)
    elif max_gap == -1:
        return is_subsequence_non_contiguous(a, b)
    else:
        return is_subsequence_windowed(a, b, max_gap)


def encode_data(data, item_to_encoding):
    """
    Replaces all item in data by its encoding
    :param data:
    :param item_to_encoding:
    :return:
    """
    missing_items = set()
    missing_items_count = 0

    for line in data:
        itemsets_to_remove = []
        for i in range(1, len(line)):
            itemset = line[i]
            if len(itemset) == 0:
                itemsets_to_remove.append(i)
                continue

            encoded_itemset = set()
            for item in itemset:
                if item in item_to_encoding:
                    encoded_itemset.add(item_to_encoding[item])
                else:
                    missing_items.add(item)
                    missing_items_count += 1

            if len(encoded_itemset) > 0:
                line[i] = encoded_itemset
            else:
                itemsets_to_remove.append(i)

        for i in sorted(itemsets_to_remove, reverse=True):
            if i < len(line):
                del line[i]

    if missing_items:
        print(f"Warning: {missing_items_count} items not found in vocabulary (skipped): {sorted(list(missing_items))[:10]}{'...' if len(missing_items) > 10 else ''}")

    return data


def decode_sequence(sequence, encoding_to_item):
    """
    Give the true values of sequence
    :param sequence: the sequence to decode in the form [{}, ..., {}]
    :return: the decoded sequence
    """
    return_sequence = []

    for i, itemset in enumerate(sequence):
        decoded_itemset = set()
        for item in itemset:
            decoded_itemset.add(encoding_to_item[item])
        return_sequence.append(decoded_itemset)
    return return_sequence


def decode_sequences(results, encoding_to_item):
    return_results = []
    for result in results:
        return_results.append((result[0], decode_sequence(result[1], encoding_to_item)))
    return return_results


def compute_subgroup_error_stats(extend):
    """
    Per-class soft-error means, stds, and subgroup sizes for coverage indices ``extend``.
    Same definition as ``decode_results`` in ``general.priorityset`` (``y_true`` 0 vs 1 on
    ``target_class[:, 0]``). Returns ``None`` if metrics cannot be computed.
    """
    target_class = Model.get_target_class()
    soft_errors = Model.get_soft_errors()
    if target_class is None or soft_errors is None or len(extend) == 0:
        return None
    extend_arr = np.array(extend, dtype=int)
    y_true = target_class[:, 0]
    subgroup_class_0 = soft_errors[extend_arr][y_true[extend_arr] == 0]
    subgroup_class_1 = soft_errors[extend_arr][y_true[extend_arr] == 1]
    return {
        "error_class_0": float(subgroup_class_0.mean()) if len(subgroup_class_0) > 0 else 0.0,
        "error_class_1": float(subgroup_class_1.mean()) if len(subgroup_class_1) > 0 else 0.0,
        "std_class_0": float(subgroup_class_0.std()) if len(subgroup_class_0) >= 2 else 0.0,
        "std_class_1": float(subgroup_class_1.std()) if len(subgroup_class_1) >= 2 else 0.0,
        "size_class_0": len(subgroup_class_0),
        "size_class_1": len(subgroup_class_1),
    }


def encode_items(items):
    item_to_encoding = {}
    encoding_to_item = {}
    new_items = set()

    for i, item in enumerate(items):
        item_to_encoding[item] = i
        encoding_to_item[i] = item
        new_items.add(i)

    return new_items, item_to_encoding, encoding_to_item


def extract_items(data):
    """
    :param data: date must be on the form [[class, {}, {}, ...], [class, {}, {}, ...]]
    :return: set of items extracted
    """
    items = set()
    for sequence in data:
        for itemset in sequence[1:]:
            for item in itemset:
                items.add(item)
    return sorted(list(items))


def print_results(results):
    if len(results) == 0:
        print('No results to display.')
        return

    sum_result = 0
    for result in results:
        pattern_display = ''
        for itemset in result[1]:
            pattern_display += repr(set(itemset))

        sum_result += result[0]

        print('Quality: {}, Extent: {}, Pattern_Delta: {}, Pattern: {}'.format(result[0], result[2], result[3], pattern_display))

    print('Average score :{}'.format(sum_result / len(results)))


def print_results_retails(results, items_dict):
    if len(results) == 0:
        print('No results to display.')
        return

    sum_result = 0
    for result in results:
        pattern_display = ''
        for itemset in result[1]:
            itemset_display = '{'
            for item in itemset:
                itemset_display += items_dict[item] + ', '
            itemset_display += '} '
            pattern_display += itemset_display

        sum_result += result[0]

        print('Quality: {}, Pattern: {}'.format(result[0], pattern_display))

    print('Average score :{}'.format(sum_result / len(results)))


def print_results_mcts(results, encoding_to_items):
    if len(results) == 0:
        print('No results to display.')
        return

    sum_result = 0
    for result in results:
        pattern_display = ''

        sequence = decode_sequence(result[1].sequence, encoding_to_items)
        for itemset in sequence:
            pattern_display += repr(set(itemset))

        print('WRAcc: {}, Pattern: {}'.format(result[0], pattern_display))
        sum_result += result[0]

    print('Average score :{}'.format(sum_result / len(results)))


def print_results_decode(results, encoding_to_items):
    decoded_results = []
    for result in results:
        decoded_result = []
        decoded_result.append(result[0])
        decoded_result.append(decode_sequence(result[1], encoding_to_items))
        decoded_result.append(len(result[2]))
        decoded_result.append(result[3])
        decoded_results.append(decoded_result)

    print_results(decoded_results)


def average_results(results):
    if len(results) == 0:
        return np.nan

    sum_result = 0
    for result in results:
        sum_result += result[0]

    return sum_result / len(results)


def roc_auc_score_binary(y_trues, confidences):
    if len(set(y_trues)) < 2:
        return np.nan
    else:
        return roc_auc_score(y_trues, confidences)

def accuracy_score_binary(y_trues, confidences):
    if len(set(y_trues)) < 2:
        return np.nan

    y_trues_array = np.array(y_trues)
    confidences_array = np.array(confidences)

    unique_labels = sorted(set(y_trues))
    if len(unique_labels) != 2:
        return np.nan

    positive_class = unique_labels[1]
    negative_class = unique_labels[0]

    predictions = np.where(confidences_array > 0.5, positive_class, negative_class)
    accuracy = np.mean(predictions == y_trues_array)

    return accuracy


def get_quality(support, data, extend, target_class=None):
    if target_class is None:
        target_class = Model.get_target_class()
 
    soft_errors = Model.get_soft_errors()
    y_true = target_class[:, 0]
    extend_arr = np.array(extend, dtype=int)
 
    subgroup_class_0 = soft_errors[extend_arr][y_true[extend_arr] == 0]
    subgroup_class_1 = soft_errors[extend_arr][y_true[extend_arr] == 1]
    
    subgroup_size_class_0 = len(subgroup_class_0)
    subgroup_size_class_1 = len(subgroup_class_1)
    baseline_class_0 = soft_errors[y_true == 0]
    baseline_class_1 = soft_errors[y_true == 1]
 
    if (subgroup_size_class_0 == 0 or subgroup_size_class_1 == 0 or (subgroup_size_class_0 == len(baseline_class_0) and
        subgroup_size_class_1 == len(baseline_class_1))):
        return 0.0, 0.0, subgroup_size_class_0, subgroup_size_class_1

    # separation term
    mean_diff_g = abs(subgroup_class_0.mean() - subgroup_class_1.mean())
    std_0 = subgroup_class_0.std()
    std_1 = subgroup_class_1.std()
    s_g = mean_diff_g / max(std_0, std_1)

    # deviation term
    mean_diff_g0_b = abs(subgroup_class_0.mean() - baseline_class_0.mean())
    d_0 = mean_diff_g0_b / baseline_class_0.std()
    mean_diff_g1_b = abs(subgroup_class_1.mean() - baseline_class_1.mean())
    d_1 = mean_diff_g1_b / baseline_class_1.std()
    d_g = max(d_0, d_1)

    # class balance term
    total_subgroup = subgroup_size_class_0 + subgroup_size_class_1
    p0 = subgroup_size_class_0 / total_subgroup
    p1 = subgroup_size_class_1 / total_subgroup
    class_balance_score = (4 * p0 * p1)
    
    # support penalty term
    support_penalty = (total_subgroup / len(soft_errors)) ** conf.SUPPORT_PENALTY

    # quality
    quality = s_g * d_g * class_balance_score * support_penalty
    sigmoid_quality = 1 / (1 + np.e ** (-(quality - conf.SIGMOID_OFFSET)))

    return sigmoid_quality, mean_diff_g, subgroup_size_class_0, subgroup_size_class_1


def compute_sg_dg_statistic(extend, target_class, soft_errors):
    """
    Compute s_g * d_g only (separation × deviation). Used for statistical validation:
    random subgroups are matched by support and class balance; the test statistic
    is whether the pattern's extent has significantly higher s_g * d_g than those
    random subgroups.
    """
    soft_errors = np.asarray(soft_errors)
    y_true = target_class[:, 0]
    extend_arr = np.array(extend, dtype=int)

    subgroup_class_0 = soft_errors[extend_arr][y_true[extend_arr] == 0]
    subgroup_class_1 = soft_errors[extend_arr][y_true[extend_arr] == 1]

    subgroup_size_class_0 = len(subgroup_class_0)
    subgroup_size_class_1 = len(subgroup_class_1)
    baseline_class_0 = soft_errors[y_true == 0]
    baseline_class_1 = soft_errors[y_true == 1]

    min_per_class = 15
    if (subgroup_size_class_0 < min_per_class or
        subgroup_size_class_1 < min_per_class or
        (subgroup_size_class_0 == len(baseline_class_0) and
         subgroup_size_class_1 == len(baseline_class_1))):
        return 0.0

    std_0 = subgroup_class_0.std()
    std_1 = subgroup_class_1.std()
    if std_0 <= 0 or std_1 <= 0:
        return 0.0
    baseline_std_0 = baseline_class_0.std()
    baseline_std_1 = baseline_class_1.std()
    if baseline_std_0 <= 0 or baseline_std_1 <= 0:
        return 0.0

    mean_diff_g = abs(subgroup_class_0.mean() - subgroup_class_1.mean())
    s_g = mean_diff_g / max(std_0, std_1)

    mean_diff_g0_b = abs(subgroup_class_0.mean() - baseline_class_0.mean())
    d_0 = mean_diff_g0_b / baseline_std_0
    mean_diff_g1_b = abs(subgroup_class_1.mean() - baseline_class_1.mean())
    d_1 = mean_diff_g1_b / baseline_std_1
    d_g = max(d_0, d_1)

    return float(s_g * d_g)


def print_rocket_league(patterns):
    '''
    :param patterns: results of mctsextend
    :return:
    '''
    translator = {'f': 'left', 'g': 'right', 'r': 'jump', 't': 'boost', 'y': 'slide', 'u': 'camera', 'j': 'down',
                  'h': 'up', 'i': 'rotate', 'k': 'accelerate', 'l': 'backward'}

    for pattern in patterns:
        quality, pattern = pattern[0], pattern[1]
        pattern_display = ''
        for itemset in pattern:
            translated_itemset = set()
            for item in itemset:
                translated_itemset.add(translator[item])
            pattern_display += repr(set(translated_itemset))

        print('Quality: {}, Pattern: {}'.format(quality, pattern_display))


@functools.lru_cache(maxsize=10000)
def compute_quality(subsequence):
    data = Model.get_data()
    seqscout.global_var.increase_it_number()

    max_gap = conf.MAX_GAP

    support = 0
    extend = []

    from seqscout.global_var import get_candidate_sequence_indices
    candidates = get_candidate_sequence_indices(subsequence, is_validation=False)

    for i in candidates:
        sequence = data[i]
        if is_subsequence(subsequence, sequence, max_gap=max_gap):
            support += 1
            extend.append(i)

    extend = np.array(extend, dtype=np.uint32)
    quality, pattern_delta, size_class_0, size_class_1 = get_quality(support, data, extend)
    return quality, pattern_delta, extend, size_class_0, size_class_1


@functools.lru_cache(maxsize=1000)
def compute_sequence_expand(intent, extend):
    data = Model.get_data()
    extend_set = set(extend)
    return tuple([i for i in range(len(data)) if i not in extend_set])

import seqscout.global_var


def backtrack_LCS(C, seq1, seq2, i, j, lcs):
    if i == 0 or j == 0:
        return

    inter = seq1[i - 1].intersection(seq2[j - 1])

    if inter != set():
        if C[i - 1][j] == C[i][j]:
            return backtrack_LCS(C, seq1, seq2, i - 1, j, lcs)
        if C[i][j - 1] == C[i][j]:
            return backtrack_LCS(C, seq1, seq2, i, j - 1, lcs)
        else:
            lcs.insert(0, inter)
            return backtrack_LCS(C, seq1, seq2, i - 1, j - 1, lcs)

    if C[i][j - 1] > C[i - 1][j]:
        return backtrack_LCS(C, seq1, seq2, i, j - 1, lcs)
    else:
        return backtrack_LCS(C, seq1, seq2, i - 1, j, lcs)


def find_LCS_contiguous(seq1, seq2):
    m, n = len(seq1), len(seq2)
    if m == 0 or n == 0:
        return []

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_len = 0
    end_i = 0
    end_j = 0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            inter = seq1[i - 1].intersection(seq2[j - 1])
            if inter:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > max_len:
                    max_len = dp[i][j]
                    end_i = i
                    end_j = j
            else:
                dp[i][j] = 0

    if max_len == 0:
        return []

    lcs = []
    i, j = end_i, end_j
    while i > 0 and j > 0 and dp[i][j] > 0:
        inter = seq1[i - 1].intersection(seq2[j - 1])
        if not inter:
            break
        lcs.append(inter)
        i -= 1
        j -= 1

    lcs.reverse()
    return lcs


def find_LCS_windowed(seq1, seq2, max_gap):
    m, n = len(seq1), len(seq2)
    if m == 0 or n == 0:
        return []

    dp = [[None] * (n + 1) for _ in range(m + 1)]

    best_len = 0
    best_end = (0, 0)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            inter = seq1[i - 1].intersection(seq2[j - 1])
            if not inter:
                continue

            best_prev = (1, 0, 0)

            for pi in range(max(0, i - max_gap - 1), i):
                for pj in range(max(0, j - max_gap - 1), j):
                    if pi == i and pj == j:
                        continue
                    if dp[pi][pj] is not None:
                        prev_len, _, _ = dp[pi][pj]
                        gap1 = (i - 1) - pi
                        gap2 = (j - 1) - pj
                        if gap1 <= max_gap and gap2 <= max_gap:
                            if prev_len + 1 > best_prev[0]:
                                best_prev = (prev_len + 1, pi, pj)

            dp[i][j] = best_prev

            if best_prev[0] > best_len:
                best_len = best_prev[0]
                best_end = (i, j)

    if best_len == 0:
        return []

    lcs = []
    i, j = best_end
    while i > 0 and j > 0 and dp[i][j] is not None:
        inter = seq1[i - 1].intersection(seq2[j - 1])
        if inter:
            lcs.append(inter)
        _, pi, pj = dp[i][j]
        if pi == 0 and pj == 0:
            break
        i, j = pi, pj

    lcs.reverse()
    return lcs


def find_LCS_non_contiguous(seq1, seq2, all=False):
    C = [[0 for j in range(len(seq2) + 1)] for i in range(len(seq1) + 1)]

    for i in range(1, len(seq1) + 1):
        for j in range(1, len(seq2) + 1):
            inter = seq1[i - 1].intersection(seq2[j - 1])

            C[i][j] = max([C[i - 1][j - 1] + len(inter),
                           C[i - 1][j],
                           C[i][j - 1]])

    if all:
        all_lcs = backtrack_all_LCS(C, seq1, seq2, len(seq1), len(seq2))
        return {i for i in all_lcs}

    lcs = []
    backtrack_LCS(C, seq1, seq2, len(seq1), len(seq2), lcs)
    return lcs


def find_LCS(seq1, seq2, max_gap=None):
    if max_gap is None:
        max_gap = conf.MAX_GAP

    if max_gap == 0:
        return find_LCS_contiguous(seq1, seq2)
    elif max_gap == -1:
        return find_LCS_non_contiguous(seq1, seq2)
    else:
        return find_LCS_windowed(seq1, seq2, max_gap)


def backtrack_all_LCS(C, seq1, seq2, i, j):
    if i == 0 or j == 0:
        return {(frozenset(['.']),)}

    inter = seq1[i - 1].intersection(seq2[j - 1])

    if inter != set():
        lcs = set()

        partial_lcs = backtrack_all_LCS(C, seq1, seq2, i - 1, j - 1)
        for z in partial_lcs:
            lcs.add(sequence_mutable_to_immutable(z + (inter,)))

        # if the number is the same, we have another way of reaching lcs
        if C[i][j] == C[i][j - 1]:
            partial_lcs = backtrack_all_LCS(C, seq1, seq2, i, j - 1)
            for z in partial_lcs:
                lcs.add(sequence_mutable_to_immutable(z))

        if C[i][j] == C[i - 1][j]:
            partial_lcs = backtrack_all_LCS(C, seq1, seq2, i - 1, j)
            for z in partial_lcs:
                lcs.add(sequence_mutable_to_immutable(z))
        return lcs

    lcs = set()

    if C[i][j - 1] >= C[i - 1][j]:
        lcs = lcs.union(backtrack_all_LCS(C, seq1, seq2, i, j - 1))
    if C[i][j - 1] <= C[i - 1][j]:
        lcs = lcs.union(backtrack_all_LCS(C, seq1, seq2, i - 1, j))

    return lcs


def calculate_item_log_losses(data, log_losses):
    item_loss_sums = {}
    item_counts = {}

    for i, sequence in enumerate(data):
        loss = log_losses[i]
        for itemset in sequence:
            for item in itemset:
                if item not in item_loss_sums:
                    item_loss_sums[item] = 0
                    item_counts[item] = 0
                item_loss_sums[item] += loss
                item_counts[item] += 1

    item_log_losses = {}
    for item in item_loss_sums:
        item_log_losses[item] = item_loss_sums[item] / item_counts[item]

    return item_log_losses


def calculate_log_losses(target_class):
    i = 0
    log_losses = []
    for y_true, confidence in target_class:
        labels = set(target_class[:, 0])
        log_losses.append(log_loss([y_true], [confidence], labels=list(labels)))
        if i % 1000 == 0:
            print(i)
        i+=1

    return log_losses

def filter_empty_sequences(data):
    return tuple([sequence_mutable_to_immutable(i[1:]) for i in data])

@functools.lru_cache(maxsize=5000)
def compute_cumulative_probs(items_tuple):
    cumulative_probs = []
    cumulative_sum = 0
    for loss in items_tuple:
        cumulative_sum += loss
        cumulative_probs.append(cumulative_sum)
    return cumulative_probs

def get_idx_from_cumulative_prop(items):
    items_tuple = tuple(items)
    cumulative_probs = compute_cumulative_probs(items_tuple)
    total_sum = cumulative_probs[-1] if cumulative_probs else 0

    if total_sum == 0:
        return None

    random_object_idx = None
    rand_num = random.uniform(0, total_sum)
    for i, cumulative in enumerate(cumulative_probs):
        if rand_num < cumulative:
            random_object_idx = i
            break

    return random_object_idx
def normalize_scores(scores):
    min_j = min(scores)
    max_j = max(scores)
    j_range = max_j - min_j

    if j_range > 0:
        return [(j - min_j) / j_range for j in scores]

    return [1] * len(scores)
