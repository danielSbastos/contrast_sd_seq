import heapq
import os
import numpy as np
from datetime import datetime
from general.utils import decode_sequence, compute_subgroup_error_stats
import general.conf as conf

from general.utils import is_subsequence, sequence_mutable_to_immutable
from statistical_validation import filter_by_significance
from save_results import save_all_patterns, save_patterns_after_similarity_filter, save_patterns_after_stats_validation, save_iteration_metrics


def jaccard_measure_misere(extend1, extend2):
    set1 = set(extend1)
    set2 = set(extend2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    try:
        return intersection / union
    except ZeroDivisionError:
        return 0


def decode_results(results_list, items_to_encoding):
    encoding_to_items = {v: k for k, v in items_to_encoding.items()} if items_to_encoding else None
    decoded_results = []

    for idx, result in enumerate(results_list):
        if len(result) == 5:
            quality, sequence, extend, pattern_delta, corr_p = result
        else:
            quality, sequence, extend, pattern_delta = result
            corr_p = None
        pattern_display = ''
        decoded_seq = decode_sequence(sequence, encoding_to_items)
        for itemset in decoded_seq:
            pattern_display += repr(set(itemset))

        sg = compute_subgroup_error_stats(extend)

        result_dict = { 
            'pattern': decoded_seq, 
            'quality': quality, 
            'support': len(extend), 
            'pattern_delta': pattern_delta 
        }
        if corr_p is not None:
            result_dict['p_value_bh'] = corr_p
        
        if sg is not None:
            result_dict['error_class_0'] = sg['error_class_0']
            result_dict['error_class_1'] = sg['error_class_1']
            result_dict['size_class_0'] = sg['size_class_0']
            result_dict['size_class_1'] = sg['size_class_1']
            result_dict['std_class_0'] = sg['std_class_0']
            result_dict['std_class_1'] = sg['std_class_1']
        
        decoded_results.append(result_dict)
        
        if sg is not None:
            p_str = f", p_val={corr_p:.6f}" if corr_p is not None else ""
            print(f"  Pattern {idx}: Quality={quality:.4f}, Pattern_Delta={pattern_delta:.4f}, Support={len(extend)}{p_str}, Class0_Error={sg['error_class_0']:.4f} (n={sg['size_class_0']}), Class1_Error={sg['error_class_1']:.4f} (n={sg['size_class_1']}), Class0_Std={sg['std_class_0']:.4f}, Class1_Std={sg['std_class_1']:.4f}, Pattern={pattern_display}")
        else:
            p_str = f", p_val={corr_p:.6f}" if corr_p is not None else ""
            print(f"  Pattern {idx}: Quality={quality:.4f}, Pattern_Delta={pattern_delta:.4f}, Support={len(extend)}{p_str}, Pattern={pattern_display}")
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
                   pattern_max_len=float('inf'), extra={}, run_statistical_validation=True):
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

    hook = extra.get('phase_hook')
    if hook:
        hook('SIMILARITY_FILTER')

    print(f"================\nFILTERING BY SIMILARITY\n================")
    # Pre-convert extends to sets to avoid redundant set conversions in nested loop
    results_sets = [set(r[2]) for r in results_list]
    
    non_redundant_patterns = []
    non_redundant_sets = []
    
    for idx, result in enumerate(results_list):
        print(f"Processing pattern {idx} of {len(results_list)}")
        similar = False
        set1 = results_sets[idx]

        for filtered_set in non_redundant_sets:
            intersection = len(set1.intersection(filtered_set))
            union = len(set1.union(filtered_set))
            jaccard_sim = intersection / union if union > 0 else 0.0

            if jaccard_sim > theta:
                similar = True
                break

        if not similar:
            non_redundant_patterns.append(result)
            non_redundant_sets.append(set1)

        if len(non_redundant_patterns) == 100:
            break

    d_results = decode_results(non_redundant_patterns, items_to_encoding)
    save_patterns_after_similarity_filter(d_results, theta, extra['dataset_name'], timestamp, extra['iteration_count'])

    if hook:
        hook('STATISTICAL_VALIDATION')

    if run_statistical_validation:
        print(f"================\nAPPLYING STATISTICAL VALIDATION\n================")
        significant_patterns, significance_info, p_values_map = filter_by_significance(
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

        final_results = []
        for pattern in non_redundant_patterns[:k]:
            corr_p = p_values_map.get(pattern[1], 1.0)
            final_results.append((pattern[0], pattern[1], pattern[2], pattern[3], corr_p))
    else:
        final_results = []
        for pattern in non_redundant_patterns[:k]:
            final_results.append((pattern[0], pattern[1], pattern[2], pattern[3], 0.0))

    return final_results


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
            if type(extend).__name__ == 'DeletedExtend':
                from general.utils import compute_quality
                _, _, extend, _, _ = compute_quality(sequence)

            limit = max(500, self.k * 5)
            if len(self.heap) < limit:
                heapq.heappush(self.heap, (quality, sequence, extend, pattern_delta))
                self.set.add(sequence)
            else:
                if quality > self.heap[0][0]:
                    removed = heapq.heappushpop(self.heap, (quality, sequence, extend, pattern_delta))
                    self.set.remove(removed[1])
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
