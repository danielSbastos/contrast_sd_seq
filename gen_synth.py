import numpy as np
import random
from sklearn.metrics import roc_auc_score, log_loss
import pandas as pd

TOTAL_SEQUENCES = 100
SG_LOW_ROCAUC_PERCENTAGE = 0.3
MODEL_ROCAUC_VALUE = 0.95

SG_PATTERN_CHARS = [['a'], ['b', 'c']]

SG_LOW_ROCAUC_VALUE = [0.5, 0.65]

def generate_scores_for_target_rocauc(n_pos, n_neg, target_rocauc):
    alpha = (target_rocauc - 0.5) * 2
    perfect_pos = np.random.uniform(0.5, 1.0, n_pos)
    perfect_neg = np.random.uniform(0.0, 0.5, n_neg)
    random_pos = np.random.uniform(0.0, 1.0, n_pos)
    random_neg = np.random.uniform(0.0, 1.0, n_neg)
    final_pos_scores = alpha * perfect_pos + (1 - alpha) * random_pos
    final_neg_scores = alpha * perfect_neg + (1 - alpha) * random_neg
    return final_pos_scores, final_neg_scores

def create_subgroup_sequence(pattern):
    rest_size_seq = random.randint(4, 6)
    seq_list = random.choices(['z', 'w', 'v'], k=rest_size_seq)
    
    insert_pos = random.randint(0, len(seq_list))
    seq_list[insert_pos:insert_pos] = pattern
    
    return '9 ' + ' -1 '.join(seq_list) + ' -1 -2'

def generate_dataset(total, sg_percentage, sg_chars, sg_rocauc_values):
    n_sg = int(total * sg_percentage)
    n_rest = total - n_sg
    n_sg_per_subgroup = np.diff(np.round(np.linspace(0, n_sg, len(sg_chars) + 1)).astype(int))
    n_rest_pos, n_rest_neg = n_rest // 2, n_rest - (n_rest // 2)

    dataset = []

    for i, pattern in enumerate(sg_chars):
        num_items = n_sg_per_subgroup[i]
        if num_items == 0:
            continue
        
        target_rocauc = sg_rocauc_values[i]
        n_pos = num_items // 2
        n_neg = num_items - n_pos
        pos_scores, neg_scores = generate_scores_for_target_rocauc(n_pos, n_neg, target_rocauc)

        for score in pos_scores:
            seq = create_subgroup_sequence(pattern)
            dataset.append((seq, 1, [1 - score, score]))

        for score in neg_scores:
            seq = create_subgroup_sequence(pattern)
            dataset.append((seq, 0, [1 - score, score]))

    for _ in range(n_rest_pos):
        p1 = np.random.uniform(0.1, 1.0)
        seq = '9 ' + ' -1 '.join(random.choices(['z', 'w', 'v'], k=random.randint(3, 6))) + ' -1 -2'
        dataset.append((seq, 1, [1 - p1, p1]))
    for _ in range(n_rest_neg):
        p1 = np.random.uniform(0.0, 0.1)
        seq = '9 ' + ' -1 '.join(random.choices(['z', 'w', 'v'], k=random.randint(3, 6))) + ' -1 -2'
        dataset.append((seq, 0, [1 - p1, p1]))

    random.shuffle(dataset)
    return dataset, sg_chars, sg_rocauc_values

def verify_and_print(dataset, sg_chars, sg_rocauc_targets):
    subgroups_data = [[] for _ in sg_chars]
    rest_items = []
    
    for item in dataset:
        sequence_tokens = set(item[0].split())
        is_subgroup_member = False
        for i, pattern in enumerate(sg_chars):
            if set(pattern).issubset(sequence_tokens):
                subgroups_data[i].append(item)
                is_subgroup_member = True
                break
        if not is_subgroup_member:
            rest_items.append(item)
    
    print("--- Verification ---")
    for i, items in enumerate(subgroups_data):
        pattern_str = ', '.join(sg_chars[i])
        print(f"\n--- Subgroup {i+1} (Pattern: '{pattern_str}') ---")
        
        sg_y_true = [item[1] for item in items]
        sg_roc_scores = [item[2][1] for item in items]
        
        if len(set(sg_y_true)) > 1:
            subgroup_rocauc = roc_auc_score(sg_y_true, sg_roc_scores)
        else:
            subgroup_rocauc = 0.5
        
        print(f"Items generated: {len(items)}")
        print(f"ROC AUC: {subgroup_rocauc:.4f} (Target: {sg_rocauc_targets[i]})")

    all_y_true = [item[1] for item in dataset]
    all_roc_scores = [item[2][1] for item in dataset]
    overall_rocauc = roc_auc_score(all_y_true, all_roc_scores)
    
    print("\n\n--- Model metrics ---")
    print(f"Model ROC AUC:  {overall_rocauc:.4f} (Target: {MODEL_ROCAUC_VALUE})")
    
    all_logloss_probs = [item[2] for item in dataset]
    overall_logloss = log_loss(all_y_true, all_logloss_probs)
    print(f"Model Log Loss: {overall_logloss:.4f}")
    print("-----------------------")

if __name__ == "__main__":
    generated_data, patterns, targets = generate_dataset(
        total=TOTAL_SEQUENCES,
        sg_percentage=SG_LOW_ROCAUC_PERCENTAGE,
        sg_chars=SG_PATTERN_CHARS,
        sg_rocauc_values=SG_LOW_ROCAUC_VALUE
    )

    sequences = [item[0] for item in generated_data]
    labels = [item[1] for item in generated_data]
    probabilities = [item[2] for item in generated_data]

    import os
    os.makedirs("data", exist_ok=True)
    np.savetxt("data/synth.dat", sequences, fmt="%s")
    metadataset = pd.DataFrame(data={'sequence': sequences, 'y_true': labels, 'confidence': probabilities})
    metadataset.to_csv("data/synth.csv", index=False)
    
    verify_and_print(generated_data, patterns, targets)

