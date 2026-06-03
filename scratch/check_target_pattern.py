import numpy as np
from mctsextent.main import prepare_mcts_from_files
from seqscout.global_var import Model
from general.utils import is_subsequence, filter_empty_sequences, get_quality, compute_quality
import general.conf as conf

def main():
    filename = 'synth_temp'
    data, target_class, log_losses, extra, encoding_to_items = prepare_mcts_from_files(filename)
    
    data = filter_empty_sequences(data)
    Model.set_data(data)
    
    encoding = extra['items_to_encoding']
    
    # Target pattern: {X, Y} {Z}
    try:
        pattern = (frozenset({encoding['X'], encoding['Y']}), frozenset({encoding['Z']}))
    except KeyError as e:
        print(f"KeyError: {e} not found in encoding. Available items count: {len(encoding)}")
        # Let's search if they are lowercased or present in a different form
        print("X:", [k for k in encoding.keys() if 'x' in k.lower() or 'y' in k.lower() or 'z' in k.lower()])
        return
        
    print(f"Checking pattern: {pattern}")
    
    support = 0
    extend = []
    for i, seq in enumerate(data):
        if is_subsequence(pattern, seq, max_gap=conf.MAX_GAP):
            support += 1
            extend.append(i)
            
    print(f"Support: {support}")
    
    # Calculate quality and class sizes
    quality, mean_diff_g, n0, n1 = get_quality(support, data, extend)
    print(f"Quality (sigmoid): {quality:.6f}")
    print(f"Pattern Delta (mean diff): {mean_diff_g:.6f}")
    print(f"Class 0 size: {n0}")
    print(f"Class 1 size: {n1}")
    
    # Check if it satisfies MCTS valid pattern conditions
    min_per_class = 10
    has_support = support >= conf.MIN_SUPPORT
    has_class_sizes = n0 >= min_per_class and n1 >= min_per_class
    print(f"Has support >= {conf.MIN_SUPPORT}: {has_support}")
    print(f"Has class sizes >= {min_per_class}: {has_class_sizes}")
    print(f"Is quality > 0: {quality > 0}")
    print(f"Is pattern_delta > 0: {mean_diff_g > 0}")

if __name__ == '__main__':
    main()
