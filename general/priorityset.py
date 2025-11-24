import heapq
from datetime import datetime
from general.utils import decode_sequence
import general.conf as conf

from general.utils import is_subsequence, sequence_mutable_to_immutable
from statistical_validation import filter_by_significance
from save_results import save_all_patterns, save_patterns_after_similarity_filter, save_patterns_after_stats_validation


def jaccard_measure_misere(sequence1, sequence2, data):
    intersection = 0
    union = 0
    for sequence in data:
        sequence = sequence_mutable_to_immutable(sequence)
        seq1 = False
        seq2 = False

        if is_subsequence(sequence1, sequence):
            seq1 = True
        if is_subsequence(sequence2, sequence):
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
    
    for idx, result in enumerate(results_list):
        quality, sequence, extend, rocauc = result
        pattern_display = ''
        decoded_seq = decode_sequence(sequence, encoding_to_items)
        for itemset in decoded_seq:
            pattern_display += repr(set(itemset))
        
        decoded_results.append({ 'pattern': decoded_seq, 'quality': quality, 'support': len(extend), 'pattern_auc': rocauc })
        print(f"  Pattern {idx}: Quality={quality:.4f}, ROC-AUC={rocauc:.4f}, Support={len(extend)}, Pattern={pattern_display}")
    print(f"{'='*80}\n")
    return decoded_results


def filter_results(results, data, theta, k, k_prime=100, alpha=0.05,
                   pattern_max_len=float('inf'), extra={}):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results_list = list(results)
    results_list.sort(key=lambda x: x[0], reverse=True)
    results_list = [result for result in results_list if len(result[1]) <= pattern_max_len]

    global_auc = extra['global_auc']
    validation_data_path = extra['validation_data_path']
    validation_target_path = extra['validation_target_path']
    items_to_encoding = extra['items_to_encoding']

    print(f"================\nALL PATTERNS\n================")
    d_results = decode_results(results_list, items_to_encoding)


    results_list = results_list[:50]
    synth_data = None
    if extra['noise']:
        synth_data = {
            'iteration_count': extra['iteration_count'],
            'avg_sequence_lenght': extra['avg_sequence_lenght'],
            'noise': extra['noise']
        }

    save_all_patterns(
        d_results,
        global_auc,
        len(data),
        extra['dataset_name'],
        timestamp,
        synth_data=synth_data,
    )

    print(f"================\nFILTERING BY SIMILARITY\n================")
    non_redundant_patterns = []
    for _, result in enumerate(results_list):
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
    
    d_results = decode_results(non_redundant_patterns, items_to_encoding)
    save_patterns_after_similarity_filter(d_results, global_auc, theta, extra['dataset_name'], timestamp)

    print(f"================\nAPPLYING STATISTICAL VALIDATION\n================")
    significant_patterns, significance_info = filter_by_significance(
        non_redundant_patterns[:k_prime],
        validation_data_path=validation_data_path,
        validation_target_path=validation_target_path,
        items_to_encoding=items_to_encoding,
        alpha=alpha,
        n_subgroups=1000,
    )

    print(f"================\nPATTERNS AFTER STATISTICAL VALIDATION\n================")
    decode_results(significant_patterns, items_to_encoding)

    save_patterns_after_stats_validation(significance_info, global_auc, extra['dataset_name'], timestamp)

    return significant_patterns[:k]

def filter_results_not_singleton(results, data, theta, k):
    """
    Filter redundant elements that are not singletons
    :param results: must be a node
    :param theta:
    :return: filtered list
    """

    results_list = list(results)
    results_list.sort(key=lambda x: x[0], reverse=True)

    filtered_elements = []

    for i, result in enumerate(results_list):
        similar = False

        for filtered_element in filtered_elements:
            if jaccard_measure_misere(result[1],
                                      filtered_element[1], data) > theta:
                similar = True

        if not similar and len(result[1]) > 1:
            filtered_elements.append(result)

        if len(filtered_elements) > k:
            break

    return filtered_elements


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

    def add(self, sequence, wracc, extend, rocauc):
        if sequence not in self.set:
            heapq.heappush(self.heap, (wracc, sequence, extend, rocauc))
            self.set.add(sequence)

    def add_preserve_memory(self, sequence, wracc, data):
        self.add(sequence, wracc)

        # we remove elements that are not in top_k
        self.heap = self.get_top_k(self.k)

        ### UGLY ###
        set_top_k = set()

        for _, seq in self.heap:
            set_top_k.add(seq)

        self.set = set_top_k

    def get(self):
        wracc, sequence, extend = heapq.heappop(self.heap)
        self.set.remove(sequence)
        return (wracc, sequence, extend)

    def get_top_k(self, k):
        data = heapq.nlargest(k, self.heap)
        return data

    def get_top_k_non_redundant(self, data, k, pattern_max_len = float('inf'), extra = {}):
        filtered_result = filter_results(self.heap, data, self.theta, k, 
                                        pattern_max_len=pattern_max_len, extra=extra)
        return heapq.nlargest(k, filtered_result)

    def get_top_k_non_redundant_non_singleton(self, data, k):
        filtered_result = filter_results_not_singleton(self.heap, data, self.theta, k)
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
