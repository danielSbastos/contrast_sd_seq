import heapq
import os
import numpy as np
from datetime import datetime
from general.utils import decode_sequence
import general.conf as conf

from general.utils import is_subsequence, sequence_mutable_to_immutable
from statistical_validation import filter_by_significance
from save_results import save_all_patterns, save_patterns_after_similarity_filter, save_patterns_after_stats_validation, save_iteration_metrics
from seqscout.global_var import Model


def jaccard_measure_misere(sequence1, sequence2, data):
    intersection = 0
    union = 0
    for sequence in data:
        sequence = sequence_mutable_to_immutable(sequence)
        seq1 = False
        seq2 = False

        if is_subsequence(sequence1, sequence, max_gap=conf.MAX_GAP):
            seq1 = True
        if is_subsequence(sequence2, sequence, max_gap=conf.MAX_GAP):
            seq2 = True

        if seq1 or seq2:
            union += 1

        if seq1 and seq2:
            intersection += 1

    try:
        return intersection / union
    except ZeroDivisionError:
        return 0


def decode_results(results_list, items_to_encoding):
    encoding_to_items = {v: k for k, v in items_to_encoding.items()} if items_to_encoding else None
    decoded_results = []

    target_class = Model.get_target_class()
    soft_errors = Model.get_soft_errors()

    for idx, result in enumerate(results_list):
        quality, sequence, extend, pattern_delta = result
        pattern_display = ''
        decoded_seq = decode_sequence(sequence, encoding_to_items)
        for itemset in decoded_seq:
            pattern_display += repr(set(itemset))

        error_class_0 = None
        error_class_1 = None
        std_class_0 = None
        std_class_1 = None
        size_class_0 = 0
        size_class_1 = 0
        
        if target_class is not None and soft_errors is not None and len(extend) > 0:
            extend_arr = np.array(extend, dtype=int)
            y_true = target_class[:, 0]
            
            subgroup_class_0 = soft_errors[extend_arr][y_true[extend_arr] == 0]
            subgroup_class_1 = soft_errors[extend_arr][y_true[extend_arr] == 1]
            
            error_class_0 = subgroup_class_0.mean() if len(subgroup_class_0) > 0 else 0.0
            error_class_1 = subgroup_class_1.mean() if len(subgroup_class_1) > 0 else 0.0
            std_class_0 = float(subgroup_class_0.std()) if len(subgroup_class_0) >= 2 else 0.0
            std_class_1 = float(subgroup_class_1.std()) if len(subgroup_class_1) >= 2 else 0.0
            size_class_0 = len(subgroup_class_0)
            size_class_1 = len(subgroup_class_1)

        result_dict = { 
            'pattern': decoded_seq, 
            'quality': quality, 
            'support': len(extend), 
            'pattern_delta': pattern_delta 
        }
        
        if error_class_0 is not None and error_class_1 is not None:
            result_dict['error_class_0'] = error_class_0
            result_dict['error_class_1'] = error_class_1
            result_dict['size_class_0'] = size_class_0
            result_dict['size_class_1'] = size_class_1
            result_dict['std_class_0'] = std_class_0
            result_dict['std_class_1'] = std_class_1
        
        decoded_results.append(result_dict)
        
        if error_class_0 is not None and error_class_1 is not None:
            print(f"  Pattern {idx}: Quality={quality:.4f}, Pattern_Delta={pattern_delta:.4f}, Support={len(extend)}, Class0_Error={error_class_0:.4f} (n={size_class_0}), Class1_Error={error_class_1:.4f} (n={size_class_1}), Class0_Std={std_class_0:.4f}, Class1_Std={std_class_1:.4f}, Pattern={pattern_display}")
        else:
            print(f"  Pattern {idx}: Quality={quality:.4f}, Pattern_Delta={pattern_delta:.4f}, Support={len(extend)}, Pattern={pattern_display}")
    print(f"{'='*80}\n")
    return decoded_results

def show_results(results, pattern_max_len, extra):
    results_list = list(results)
    results_list.sort(key=lambda x: x[0], reverse=True)
    results_list = [result for result in results_list if len(result[1]) <= pattern_max_len]

    print(f"================\nALL PATTERNS\n================")

    items_to_encoding = extra['items_to_encoding']
    decode_results(results_list, items_to_encoding)


def filter_results(results, data, theta, k, k_prime=100, alpha=0.05,
                   pattern_max_len=float('inf'), extra={}):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results_list = list(results)
    results_list.sort(key=lambda x: x[0], reverse=True)
    results_list = results_list

    results_list = [result for result in results_list if len(result[1]) <= pattern_max_len]
    
    validation_data_path = extra['validation_data_path']
    validation_target_path = extra['validation_target_path']
    train_data_path = extra['train_data_path']
    train_target_path = extra['train_target_path']
    items_to_encoding = extra['items_to_encoding']

    print(f"================\nALL PATTERNS\n================")
    d_results = decode_results(results_list, items_to_encoding)

    synth_data = None
    if extra['noise']:
        synth_data = {
            'iteration_count': extra['iteration_count'],
            'avg_sequence_lenght': extra['avg_sequence_lenght'],
            'noise': extra['noise']
        }

    max_gap = extra.get('max_gap', None)
    support_penalty = extra.get('support_penalty', 0)
    sigmoid_offset = extra.get('sigmoid_offset', 2)
    save_all_patterns(
        d_results,
        len(data),
        extra['dataset_name'],
        timestamp,
        extra['iteration_count'],
        synth_data=synth_data,
        max_gap=max_gap,
        support_penalty=support_penalty,
        sigmoid_offset=sigmoid_offset,
    )

    if 'iteration_metrics' in extra:
        save_iteration_metrics(
            extra['iteration_metrics'],
            extra['dataset_name'],
            timestamp,
            extra['iteration_count'],
        )

    print(f"================\nFILTERING BY SIMILARITY\n================")
    non_redundant_patterns = []
    for _, result in enumerate(results_list):
        print(f"Processing pattern {_} of {len(results_list)}")
        similar = False
        max_jaccard = 0.0

        for _, filtered_element in enumerate(non_redundant_patterns):
            jaccard_sim = jaccard_measure_misere(result[1], filtered_element[1], data)

            if jaccard_sim > max_jaccard:
                max_jaccard = jaccard_sim

            if jaccard_sim > theta:
                similar = True
                break

        if not similar:
            non_redundant_patterns.append(result)

        if len(non_redundant_patterns) == 100:
            break

    d_results = decode_results(non_redundant_patterns, items_to_encoding)
    save_patterns_after_similarity_filter(d_results, theta, extra['dataset_name'], timestamp, extra['iteration_count'])

    print(f"================\nAPPLYING STATISTICAL VALIDATION\n================")
    significant_patterns, significance_info = filter_by_significance(
        non_redundant_patterns[:k_prime],
        validation_data_path=validation_data_path,
        validation_target_path=validation_target_path,
        train_data_path=train_data_path,
        train_target_path=train_target_path,
        items_to_encoding=items_to_encoding,
        alpha=alpha,
        n_subgroups=1000,
    )

    print(f"================\nPATTERNS AFTER STATISTICAL VALIDATION\n================")
    decode_results(significant_patterns, items_to_encoding)

    save_patterns_after_stats_validation(significance_info, extra['dataset_name'], timestamp, extra['iteration_count'])

    return significant_patterns[:k]


class PrioritySet(object):
    """
    This class is a priority queue, removing duplicates and using node wracc
    as the metric to order the priority queue
    """

    def __init__(self, k=conf.TOP_K, theta=conf.THETA):
        self.k = k
        self.heap = []
        self.set = set()
        self.theta = theta
        self.redundant_add_count = 0  # times add() was called with a pattern already in queue (2nd, 3rd, ...)
        self.proposal_count = {}  # sequence -> number of times add() was called with this pattern

    def add(self, sequence, quality, extend, pattern_delta):
        if sequence not in self.set:
            heapq.heappush(self.heap, (quality, sequence, extend, pattern_delta))
            self.set.add(sequence)
            self.proposal_count[sequence] = 1
        else:
            self.redundant_add_count += 1
            self.proposal_count[sequence] += 1

    def get_visit_count_distribution(self):
        """Returns dict: for each visit count >= 2, how many patterns were proposed that many times.
        E.g. {2: 5, 3: 2} means 5 patterns were proposed 2 times, 2 patterns were proposed 3 times."""
        from collections import Counter
        counts = Counter(self.proposal_count.values())
        return {c: n for c, n in counts.items() if c >= 2}

    def get(self):
        quality, sequence, extend = heapq.heappop(self.heap)
        self.set.remove(sequence)
        return (quality, sequence, extend)

    def get_top_k(self, k):
        data = heapq.nlargest(k, self.heap)
        return data

    def show_all(self, extra, pattern_max_len=float('inf')):
        show_results(self.heap, pattern_max_len, extra)

    def get_top_k_non_redundant(self, data, k, pattern_max_len = float('inf'), extra = {}):
        filtered_result = filter_results(self.heap, data, self.theta, k,
                                        pattern_max_len=pattern_max_len, extra=extra)
        return heapq.nlargest(k, filtered_result)


class PrioritySetUCB(object):
    """
    This class is a priority queue, removing duplicates and using node wracc
    as the metric to order the priority queue
    """

    def __init__(self):
        self.heap = []
        self.set = set()

    def add(self, sequence, tuple):
        '''
        :param sequence:
        :param tuple: (UCB, Ni, WRAcc)
        :return:
        '''
        if sequence not in self.set:
            # we use - sign because heapq return the smalest element
            heapq.heappush(self.heap, (-tuple[0], tuple[1], tuple[2], sequence))
            self.set.add(sequence)

    def pop(self):
        '''
        :return: the max element
        '''
        UCB, Ni, wracc, sequence = heapq.heappop(self.heap)
        self.set.remove(sequence)
        return (-UCB, Ni, wracc, sequence)
