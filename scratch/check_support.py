from general.reader import read_data_kosarak
import pandas as pd
import numpy as np

path = "data/synth_temp.dat"
target_path = "data/synth_temp.csv"

raw_data = read_data_kosarak(path)
target_file = pd.read_csv(target_path)

print("Raw dataset size:", len(raw_data))
print("Raw targets size:", len(target_file))

# Count unique items
all_items = set()
for seq in raw_data:
    for itemset in seq[1:]:
        for item in itemset:
            all_items.add(item)
print("Raw unique items count:", len(all_items))

# Look at unique sequences in raw data
unique_raw_seqs = set()
for seq in raw_data:
    seq_tuple = tuple(frozenset(itemset) for itemset in seq[1:])
    unique_raw_seqs.add(seq_tuple)

print("Raw unique sequences:", len(unique_raw_seqs))
