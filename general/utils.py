import json

import random

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


def is_subsequence(a, b):
    """ check if sequence a is a subsequence of b
    """
    i_a, i_b = 0, 0

    while i_a < len(a) and i_b < len(b):
        if a[i_a].issubset(b[i_b]):
            i_a += 1
        i_b += 1

    return i_a == len(a)


def subsequence_indices(a, b):
    """ Return itemset indices of b that itemset of a are included in
        Precondition: a is a subset of b
    """
    index_b_mem = 0
    indices_b = []
    for index_a, itemset_a in enumerate(a):
        for index_b in range(index_b_mem, len(b)):
            if index_b == len(b) - 1:
                # we mark as finished
                index_b_mem = len(b)

            itemset_b = b[index_b]

            if itemset_a.issubset(itemset_b):
                indices_b.append(index_b)
                index_b_mem = index_b + 1
                break

        if index_b_mem == len(b):
            return indices_b

    return indices_b


def encode_data(data, item_to_encoding):
    """
    Replaces all item in data by its encoding
    :param data:
    :param item_to_encoding:
    :return:
    """
    has_malformatted_sequences = False

    for line in data:
        for i, itemset in enumerate(line[1:]):
            if len(itemset) == 0:
                has_malformatted_sequences = True
                continue
            encoded_itemset = set()
            for item in itemset:
                encoded_itemset.add(item_to_encoding[item])
            line[i + 1] = encoded_itemset

        if has_malformatted_sequences:
            del line[1]

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
    sum_result = 0
    for result in results:
        pattern_display = ''
        for itemset in result[1]:
            pattern_display += repr(set(itemset))

        sum_result += result[0]

        print('Quality: {}, Extent: {}, ROCAUC: {}, Pattern: {}'.format(result[0], result[2], result[3], pattern_display))

    print('Average score :{}'.format(sum_result / len(results)))


def print_results_retails(results, items_dict):
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
    sum_result = 0
    for result in results:
        sum_result += result[0]

    return sum_result / len(results)


def roc_auc_score_binary(y_trues, confidences):
    if len(set(y_trues)) < 2:
        return np.nan
    else:
        return roc_auc_score(y_trues, confidences)

def get_quality(support, data, extend, target_class=None):
    """
    Calculate quality (WRAcc) for a pattern based on its support and ROC-AUC.
    
    Args:
        support: Number of sequences in extend
        data: Data sequences
        extend: List of indices into target_class
        target_class: Optional target class array. If None, uses Model.get_target_class()
    
    Returns:
        Tuple of (quality, rocauc)
    """
    if target_class is None:
        target_class = Model.get_target_class()
    extend_target_class = target_class[extend]

    y_trues = [item[0] for item in extend_target_class]
    confidences = [item[1] for item in extend_target_class]

    rocauc = roc_auc_score_binary(y_trues, confidences)

    if np.isnan(rocauc) or (rocauc > Model.get_rocauc()):
        return -1, -1

    x = Model.get_rocauc() - rocauc
    s_rel = support/(len(data))
    s = support

    if s == 1 or (x < 0.01): return (-1, -1)

    f = 100 * (x ** 2) * s_rel**0.5

    return f, rocauc


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


@functools.lru_cache(maxsize=512)
def compute_quality(subsequence, data=None):
    if data is None:
        data = Model.get_data()
        seqscout.global_var.increase_it_number()

    support = 0
    extend = []

    for i, sequence in enumerate(data):
        if is_subsequence(subsequence, sequence):
            support += 1
            extend.append(i)

    quality, rocauc = get_quality(support, data, extend)
    return quality, rocauc, extend


@functools.lru_cache(maxsize=512)
def compute_sequence_expand(intent, extend):
    data = Model.get_data()
    if intent is None:
        return tuple([[i, seq] for i, seq in enumerate(data) if i not in extend])
    return tuple([[i, seq] for i, seq in enumerate(data) if i not in extend and not is_subsequence(intent, seq)])

import seqscout.global_var


def backtrack_LCS(C, seq1, seq2, i, j, lcs):
    if i == 0 or j == 0:
        return

    inter = seq1[i - 1].intersection(seq2[j - 1])

    if inter != set():
        # these two cases check what path the DP took
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


def find_LCS(seq1, seq2, all=False):
    """
    find the longest common subsequence. We here consider sequences of itemsets
    Cost a lot if all = True
    :param seq1:
    :param seq2:
    :return: the longest common sequence

    """
    C = [[0 for j in range(len(seq2) + 1)] for i in range(len(seq1) + 1)]

    for i in range(1, len(seq1) + 1):
        for j in range(1, len(seq2) + 1):
            inter = seq1[i - 1].intersection(seq2[j - 1])

            C[i][j] = max([C[i - 1][j - 1] + len(inter),
                           C[i - 1][j],
                           C[i][j - 1]])

    # now we need to backtrack the structure to get the pattern
    if all:
        all_lcs = backtrack_all_LCS(C, seq1, seq2, len(seq1), len(seq2))
        return {i for i in all_lcs}

    lcs = []
    backtrack_LCS(C, seq1, seq2, len(seq1), len(seq2), lcs)
    return lcs


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
    #return tuple([sequence_mutable_to_immutable(i[1:]) for i in data if len(i[1:]) > 0])

@functools.lru_cache(maxsize=512)
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

    random_object_idx = None
    rand_num = random.uniform(0, total_sum)
    for i, cumulative in enumerate(cumulative_probs):
        if rand_num < cumulative:
            random_object_idx = i
            break

    return random_object_idx

@functools.lru_cache(maxsize=512)
def jaccard_similarity(sequence1, sequence2):
    set1 = set(sequence_mutable_to_immutable(sequence1))
    set2 = set(sequence_mutable_to_immutable(sequence2))

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    return len(intersection) / len(union)

def normalize_scores(scores):
    min_j = min(scores)
    max_j = max(scores)
    j_range = max_j - min_j

    if j_range > 0:
        return [(j - min_j) / j_range for j in scores]

    return [1] * len(scores)
