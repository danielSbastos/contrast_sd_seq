import time
import numpy as np
from mctsextent.main import prepare_mcts_from_files
from seqscout.global_var import Model
from general.utils import is_subsequence, sequence_mutable_to_immutable
import general.conf as conf

def build_inverted_index(data):
    inv_index = {}
    for idx, seq in enumerate(data):
        for itemset in seq:
            for item in itemset:
                if item not in inv_index:
                    inv_index[item] = set()
                inv_index[item].add(idx)
    return inv_index

def get_candidate_sequence_indices(subsequence, inv_index, data_len):
    if not subsequence:
        return range(data_len)
    
    items = []
    for itemset in subsequence:
        for item in itemset:
            items.append(item)
            
    if not items:
        return range(data_len)
        
    items.sort(key=lambda x: len(inv_index.get(x, ())))
    
    result = inv_index.get(items[0], set())
    if not result:
        return ()
        
    for item in items[1:]:
        result = result.intersection(inv_index.get(item, ()))
        if not result:
            return ()
            
    return result

def jaccard_measure_misere_original(sequence1, sequence2, data):
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

def jaccard_measure_misere_optimized(extend1, extend2):
    set1 = set(extend1)
    set2 = set(extend2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    try:
        return intersection / union
    except ZeroDivisionError:
        return 0

def main():
    filename = 'synth_temp'
    print("Loading data...")
    data, target_class, log_losses, extra, encoding_to_items = prepare_mcts_from_files(filename)
    
    # Filter empty sequences as done in init_mcts_tree
    from general.utils import filter_empty_sequences
    data = filter_empty_sequences(data)
    Model.set_data(data)
    
    print("Building inverted index...")
    t0 = time.time()
    inv_index = build_inverted_index(data)
    print(f"Built inverted index in {time.time() - t0:.4f}s for {len(inv_index)} unique items")
    
    # Pick a few sample sequences (subsequences) to test support/extend computation
    # Pattern E E E F G H I (from patterns.json: {E} {F} {G} {H} {I} encoded)
    # Let's decode and find encoding for E, F, G, H, I
    decoding = {v: k for k, v in extra['items_to_encoding'].items()}
    encoding = extra['items_to_encoding']
    
    # Let's construct a target pattern
    try:
        test_pattern = (frozenset({encoding['E']}), frozenset({encoding['F']}), frozenset({encoding['G']}))
    except KeyError:
        # fallback to first sequence elements
        print("E, F, G not found in vocabulary, using elements from first sequence")
        first_seq = data[0]
        test_pattern = first_seq[:3]
        
    print(f"Testing pattern: {test_pattern}")
    
    # 1. Test correctness of candidate generation
    t0 = time.time()
    candidates = get_candidate_sequence_indices(test_pattern, inv_index, len(data))
    print(f"Found {len(candidates)} candidates using inverted index in {time.time() - t0:.6f}s")
    
    # 2. Compare original support calculation vs candidate-based support calculation
    t0 = time.time()
    extend_orig = []
    for i, seq in enumerate(data):
        if is_subsequence(test_pattern, seq, max_gap=conf.MAX_GAP):
            extend_orig.append(i)
    t_orig = time.time() - t0
    print(f"Original check found support {len(extend_orig)} in {t_orig:.4f}s")
    
    t0 = time.time()
    extend_cand = []
    for i in candidates:
        if is_subsequence(test_pattern, data[i], max_gap=conf.MAX_GAP):
            extend_cand.append(i)
    t_cand = time.time() - t0
    print(f"Candidate check found support {len(extend_cand)} in {t_cand:.4f}s")
    
    assert set(extend_orig) == set(extend_cand), "ERROR: Candidate check extend differs from original!"
    print(f"Verification successful: extends match exactly! Speedup: {t_orig / t_cand:.2f}x")
    
    # 3. Test Jaccard measure correctness and speed
    # Pick two sets of extensions
    ext1 = extend_orig
    # Let's create another one
    try:
        test_pattern2 = (frozenset({encoding['X']}), frozenset({encoding['Y']}), frozenset({encoding['Z']}))
    except KeyError:
        test_pattern2 = data[1][:3]
        
    ext2 = []
    for i, seq in enumerate(data):
        if is_subsequence(test_pattern2, seq, max_gap=conf.MAX_GAP):
            ext2.append(i)
            
    print(f"Support 1: {len(ext1)}, Support 2: {len(ext2)}")
    
    t0 = time.time()
    jac_orig = jaccard_measure_misere_original(test_pattern, test_pattern2, data)
    t_jac_orig = time.time() - t0
    print(f"Original Jaccard: {jac_orig:.6f} in {t_jac_orig:.4f}s")
    
    t0 = time.time()
    jac_opt = jaccard_measure_misere_optimized(ext1, ext2)
    t_jac_opt = time.time() - t0
    print(f"Optimized Jaccard: {jac_opt:.6f} in {t_jac_opt:.6f}s")
    
    assert abs(jac_orig - jac_opt) < 1e-7, f"ERROR: Jaccard values differ! Original={jac_orig}, Opt={jac_opt}"
    print(f"Jaccard verification successful! Speedup: {t_jac_orig / t_jac_opt:.2f}x")

if __name__ == '__main__':
    main()
