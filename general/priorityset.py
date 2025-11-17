import heapq
from general.utils import decode_sequence
import general.conf as conf

from general.utils import is_subsequence, sequence_mutable_to_immutable
from statistical_validation import filter_by_significance


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


def print_decoded_result(results_list, items_to_encoding):
    encoding_to_items = {v: k for k, v in items_to_encoding.items()} if items_to_encoding else None
    
    for idx, result in enumerate(results_list):
        quality, sequence, extend, rocauc = result
        pattern_display = ''
        if encoding_to_items:
            decoded_seq = decode_sequence(sequence, encoding_to_items)
            for itemset in decoded_seq:
                pattern_display += repr(set(itemset))
        else:
            for itemset in sequence:
                pattern_display += repr(set(itemset))
        print(f"  Pattern {idx}: Quality={quality:.4f}, ROC-AUC={rocauc:.4f}, Support={len(extend)}, Pattern={pattern_display}")
    print(f"{'='*80}\n")


def filter_results(results, data, theta, k, k_prime=100, alpha=0.05, 
                   validation_data_path=None, validation_target_path=None, items_to_encoding=None,
                   pattern_max_len=float('inf')):
    results_list = list(results)
    results_list.sort(key=lambda x: x[0], reverse=True)
    results_list = [result for result in results_list if len(result[1]) <= pattern_max_len]

    print(f"================")
    print(f"ALL PATTERNS")
    print(f"================")
    print_decoded_result(results_list, items_to_encoding)

    print(f"================")
    print(f"APPLYING STATISTICAL VALIDATION")
    print(f"================")

    significant_patterns, _ = filter_by_significance(
        results_list[:k_prime],
        validation_data_path=validation_data_path,
        validation_target_path=validation_target_path,
        items_to_encoding=items_to_encoding,
        alpha=alpha,
        n_subgroups=10000,
    )
    
    candidate_patterns = significant_patterns[:k_prime]

    print(f"================")
    print(f"PATTERNS AFTER STATISTICAL VALIDATION")
    print(f"================")
    print_decoded_result(candidate_patterns, items_to_encoding)

    print(f"================")
    print(f"FILTERING BY SIMILARITY")
    print(f"================")
    non_redundant_patterns = []

    for _, result in enumerate(candidate_patterns):
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
    
    print_decoded_result(non_redundant_patterns, items_to_encoding)

    return non_redundant_patterns[:k]


def _filter_results(results, data, theta, k, k_prime=100, alpha=0.05, 
                   validation_data_path=None, validation_target_path=None, items_to_encoding=None,
                   pattern_max_len=float('inf')):
    results_list = list(results)
    results_list.sort(key=lambda x: x[0], reverse=True)
    results_list = [result for result in results_list if len(result[1]) <= pattern_max_len]

    print(f"\n================")
    print(f"ALL PATTERNS")
    print(f"\n================")
    print_decoded_result(results_list, items_to_encoding)

    print(f"\n================")
    print(f"FILTERING BY SIMILARITY")
    print(f"\n================")

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
    
    print_decoded_result(non_redundant_patterns, items_to_encoding)

    print(f"\n================")
    print(f"APPLYING STATISTICAL VALIDATION")
    print(f"\n================")

    significant_patterns, _ = filter_by_significance(
        non_redundant_patterns[:k_prime],
        validation_data_path=validation_data_path,
        validation_target_path=validation_target_path,
        items_to_encoding=items_to_encoding,
        alpha=alpha,
        n_subgroups=10000,
    )
    
    candidate_patterns = significant_patterns[:k_prime]

    print(f"\n================")
    print(f"PATTERNS AFTER STATISTICAL VALIDATION")
    print(f"\n================")
    print_decoded_result(candidate_patterns, items_to_encoding)

    final_patterns = candidate_patterns[:k]
    
    return final_patterns


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

    def get_top_k_non_redundant(self, data, k, pattern_max_len = float('inf'), validation_data_path=None, validation_target_path=None, items_to_encoding=None):
        filtered_result = filter_results(self.heap, data, self.theta, k, 
                                        validation_data_path=validation_data_path,
                                        validation_target_path=validation_target_path,
                                        items_to_encoding=items_to_encoding,
                                        pattern_max_len=pattern_max_len)
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
