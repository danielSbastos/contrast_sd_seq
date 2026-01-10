def sequence_string_to_itemsets(sequence_str):
    tokens = sequence_str.split()
    itemsets = []
    current_itemset = []
    
    for token in tokens[1:]:
        if token == "-1":
            if current_itemset:
                itemsets.append(tuple(sorted(current_itemset)))
                current_itemset = []
        elif token == "-2":
            if current_itemset:
                itemsets.append(tuple(sorted(current_itemset)))
            break
        else:
            current_itemset.append(token)
    
    return itemsets


def sequence_contains_pattern(sequence_str, pattern_itemsets):
    if not pattern_itemsets:
        return False
    
    parsed_sequence = sequence_string_to_itemsets(sequence_str)
    
    if not parsed_sequence:
        return False
    
    pattern_sets = []
    for p_itemset in pattern_itemsets:
        if isinstance(p_itemset, (set, frozenset)):
            pattern_sets.append(p_itemset)
        elif isinstance(p_itemset, (tuple, list)):
            pattern_sets.append(set(p_itemset))
        else:
            pattern_sets.append({p_itemset})
    
    seq_sets = [set(itemset) for itemset in parsed_sequence]
    
    pattern_len = len(pattern_sets)
    seq_len = len(seq_sets)
    
    if pattern_len == 0 or pattern_len > seq_len:
        return False
    
    for start_idx in range(seq_len):
        i_pattern = 0
        i_seq = start_idx
        
        while i_pattern < pattern_len and i_seq < seq_len:
            if pattern_sets[i_pattern].issubset(seq_sets[i_seq]):
                i_pattern += 1
            i_seq += 1
        
        if i_pattern == pattern_len:
            return True
    
    return False

