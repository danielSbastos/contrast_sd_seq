import heapq
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


def filter_results(results, data, theta, k, k_prime=100, alpha=0.05, 
                   validation_data_path=None, validation_target_path=None, items_to_encoding=None):
    """
    Filter redundant elements and apply multiple testing correction.
    
    :param results: must be a node
    :param theta: similarity threshold for redundancy
    :param k: final number of patterns to return
    :param k_prime: number of patterns to evaluate (default: 100)
    :param alpha: significance threshold (default: 0.05)
    :param items_to_encoding: Encoding dictionary to encode validation data    
    """
    results_list = list(results)
    results_list.sort(key=lambda x: x[0], reverse=True)

    candidate_patterns = []
    for result in results_list:
        candidate_patterns.append(result)
        if len(candidate_patterns) >= k_prime:
            break

    # Print patterns BEFORE significance filtering
    print(f"\n{'='*80}")
    print(f"PATTERNS BEFORE SIGNIFICANCE FILTERING ({len(candidate_patterns)} patterns):")
    print(f"{'='*80}")
    from general.utils import decode_sequence
    # Create reverse encoding mapping if available
    encoding_to_items = {v: k for k, v in items_to_encoding.items()} if items_to_encoding else None
    
    for idx, result in enumerate(candidate_patterns):
        quality, sequence, extend, rocauc = result
        pattern_display = ''
        if encoding_to_items:
            decoded_seq = decode_sequence(sequence, encoding_to_items)
            for itemset in decoded_seq:
                pattern_display += repr(set(itemset))
        else:
            # Fallback: show encoded pattern
            for itemset in sequence:
                pattern_display += repr(set(itemset))
        
        print(f"  Pattern {idx}: Quality={quality:.4f}, ROC-AUC={rocauc:.4f}, Support={len(extend)}, Pattern={pattern_display}")
    print(f"{'='*80}\n")

    significant_patterns, filtered_out_info = filter_by_significance(
        candidate_patterns,
        validation_data_path=validation_data_path,
        validation_target_path=validation_target_path,
        items_to_encoding=items_to_encoding,
        alpha=alpha,
        n_subgroups=10000,
    )
    
    # Create a set of significant pattern sequences for quick lookup
    significant_patterns_set = {result[1] for result in significant_patterns}
    
    # Print patterns that were FILTERED OUT
    filtered_out_patterns = []
    for idx, result in enumerate(candidate_patterns):
        if result[1] not in significant_patterns_set:
            filtered_out_patterns.append((idx, result, filtered_out_info.get(idx, "No info available")))
    
    if filtered_out_patterns:
        print(f"\n{'='*80}")
        print(f"PATTERNS FILTERED OUT ({len(filtered_out_patterns)} patterns):")
        print(f"{'='*80}")
        for orig_idx, result, filter_info in filtered_out_patterns:
            quality, sequence, extend, rocauc = result
            pattern_display = ''
            if encoding_to_items:
                decoded_seq = decode_sequence(sequence, encoding_to_items)
                for itemset in decoded_seq:
                    pattern_display += repr(set(itemset))
            else:
                for itemset in sequence:
                    pattern_display += repr(set(itemset))
            
            if isinstance(filter_info, str):
                info_str = f" ({filter_info})"
            else:
                p_val = filter_info.get('p_value', 'N/A')
                corr_p = filter_info.get('corrected_p', 'N/A')
                reason = filter_info.get('reason', 'Unknown reason')
                if isinstance(p_val, (int, float)):
                    p_str = f"{p_val:.6f}"
                else:
                    p_str = str(p_val)
                if isinstance(corr_p, (int, float)) and corr_p is not None:
                    corr_p_str = f"{corr_p:.6f}"
                else:
                    corr_p_str = str(corr_p)
                info_str = f" (p={p_str}, corrected_p={corr_p_str}, reason={reason})"
            print(f"  Pattern {orig_idx}: Quality={quality:.4f}, ROC-AUC={rocauc:.4f}, Support={len(extend)}, Pattern={pattern_display}{info_str}")
        print(f"{'='*80}\n")
    else:
        print(f"\nNo patterns were filtered out.\n")
    
    # Print patterns AFTER significance filtering
    print(f"\n{'='*80}")
    print(f"PATTERNS AFTER SIGNIFICANCE FILTERING ({len(significant_patterns)} patterns):")
    print(f"{'='*80}")
    for idx, result in enumerate(significant_patterns):
        quality, sequence, extend, rocauc = result
        pattern_display = ''
        if encoding_to_items:
            decoded_seq = decode_sequence(sequence, encoding_to_items)
            for itemset in decoded_seq:
                pattern_display += repr(set(itemset))
        else:
            # Fallback: show encoded pattern
            for itemset in sequence:
                pattern_display += repr(set(itemset))
        
        print(f"  Pattern {idx}: Quality={quality:.4f}, ROC-AUC={rocauc:.4f}, Support={len(extend)}, Pattern={pattern_display}")
    print(f"{'='*80}\n")
    
    filtered_elements = []
    for result in significant_patterns:
        similar = False

        for filtered_element in filtered_elements:
            if jaccard_measure_misere(result[1], filtered_element[1], data) > theta:
                similar = True
                break
        
        if not similar:
            filtered_elements.append(result)

            if len(filtered_elements) >= k:
                break
    
    print(f"Final result: {len(filtered_elements)} patterns after significance and similarity filtering (target: {k})")
    return filtered_elements


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

    def get_top_k_non_redundant(self, data, k, validation_data_path=None, validation_target_path=None, items_to_encoding=None):
        filtered_result = filter_results(self.heap, data, self.theta, k, 
                                        validation_data_path=validation_data_path,
                                        validation_target_path=validation_target_path,
                                        items_to_encoding=items_to_encoding)
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
