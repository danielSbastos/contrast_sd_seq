import numpy as np
from seqscout.global_var import Model
from mctsextent.main import prepare_mcts_from_files
from mctsextent.node import DeletedExtend
from general.priorityset import PrioritySet
from general.utils import filter_empty_sequences

def main():
    filename = 'synth_temp'
    print("Loading data...")
    data, target_class, log_losses, extra, encoding_to_items = prepare_mcts_from_files(filename)
    data = filter_empty_sequences(data)
    Model.set_data(data)
    
    # 1. Create a pattern and a DeletedExtend placeholder
    test_pattern = (frozenset({3}), frozenset({4}))
    # Suppose we have support 50
    deleted_ext = DeletedExtend(50)
    
    # 2. Create a PrioritySet and add the pattern with the DeletedExtend placeholder
    # This should trigger the check and recompute the list of indices on the fly
    pset = PrioritySet(k=10, theta=0.0)
    print("Adding pattern with DeletedExtend to PrioritySet...")
    pset.add(test_pattern, 0.95, deleted_ext, 0.1)
    
    # 3. Check if the extend list was successfully recomputed to a list of ints
    heap_item = pset.heap[0]
    quality, seq, extend, pattern_delta = heap_item
    print(f"Added item: quality={quality}, pattern={seq}, extend type={type(extend).__name__}, len={len(extend)}")
    
    assert isinstance(extend, np.ndarray), f"Expected np.ndarray, got {type(extend)}"
    assert all(isinstance(x, (int, np.integer)) for x in extend), "Expected all elements in extend to be integers"
    print("Verification successful: PrioritySet.add correctly detected and recomputed DeletedExtend!")

if __name__ == '__main__':
    main()
