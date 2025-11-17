import pandas as pd
import numpy as np

import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.nn.utils.rnn import pack_padded_sequence
from torch.nn.utils.rnn import pad_sequence

from sklearn.metrics import classification_report, accuracy_score
from functools import partial
from collections import Counter

def build_vocab(filepath, kosarak=True):
    classes = set()
    classes_list = []
    event_set = set()

    with open(filepath, "r") as f:
        if kosarak:
            for line in f:
                tokens = line.strip().split()
                for tok in tokens[1:]:
                    if tok not in ("-1", "-2"):
                        event_set.add(tok)
                classes.add(tokens[0])
                classes_list.append(tokens[0])
        else:
            for line in f:
                label, _, tokens = line.strip().split(',')
                for tok in tokens.strip():
                    event_set.add(tok)
                classes.add(label)
                classes_list.append(label)

        event2id = {event: idx+2 for idx, event in enumerate(sorted(event_set))}
        event2id["<PAD>"] = 0
        event2id["<SEP>"] = 1

    return event2id, classes

kosarak=True
file_name = './data/original/splice_bin.dat'
file_name = './data/original/sequences-TZ-45.txt'
file_name = './data/original/figures_rc.dat'
file_name = './data/original/context.data'
target_class = '1'

vocab, classes = build_vocab(file_name, kosarak)

classes_counter = Counter()
with open(file_name, "r") as f:
    if kosarak:
        for line in f:
            tokens = line.strip().split()
            if tokens:
                classes_counter[tokens[0]] += 1
    else:
        for line in f:
            label, _, tokens = line.strip().split(',')
            classes_counter[label] += 1

total_samples = sum(classes_counter.values())
print(f"\nClass Distribution (Total samples: {total_samples}):")
for class_label in sorted(classes_counter.keys()):
    count = classes_counter[class_label]
    proportion = count / total_samples
    print(f"  Class '{class_label}': {count} samples ({proportion:.4f} or {proportion*100:.2f}%)")
print()

if target_class not in classes:
    available_classes = ', '.join(sorted(classes))
    raise ValueError(f"Target class '{target_class}' not found in dataset. Available classes: {available_classes}")

print(f"Binary classification mode: target_class='{target_class}' (class 1), all others (class 0)")
print(f"Available classes in dataset: {sorted(classes)}")

def parse_flatten(line, event2id, kosarak=True):
    seq = []
    if kosarak:
        tokens = line.strip().split()
        label = tokens[0]
        for tok in tokens[1:]:
            if tok == "-1":
                seq.append(event2id["<SEP>"])
            elif tok == "-2":
                break
            else:
                seq.append(event2id[tok])
    else:
        label, _, tokens = line.strip().split(',')
 
        for tok in tokens.strip():
            seq.append(event2id[tok])
            seq.append(event2id["<SEP>"])

    return label, torch.tensor(seq, dtype=torch.long)

def collate_fn(batch, target_class):
    labels, seqs = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs])
    padded = pad_sequence(seqs, batch_first=True, padding_value=0)  # PAD=0
    
    binary_labels = torch.tensor([1 if label == target_class else 0 for label in labels])
    
    return binary_labels, padded, lengths

class FlatLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, emb_dim, hidden_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.lstm = nn.LSTM(emb_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x, lengths):
        embedded = self.embedding(x)
        packed = pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, (h_n, _) = self.lstm(packed)
        out = self.fc(h_n.squeeze(0))
        return out

lines = []
with open(file_name) as file:
    for line in file:
        lines.append(line)

dataset = [parse_flatten(line, vocab, kosarak) for line in lines]

collate_fn_with_target = partial(collate_fn, target_class=target_class)

data_loader = DataLoader(dataset, batch_size=16, shuffle=True, collate_fn=collate_fn_with_target)

model = FlatLSTMClassifier(vocab_size=len(vocab), emb_dim=32, hidden_dim=64, num_classes=2)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

num_epochs = 10

print("Starting training")
model.train()

for epoch in range(num_epochs):
    epoch_loss = 0.0
    for labels_batch, padded_batch, lengths_batch in data_loader:
        optimizer.zero_grad()
        outputs = model(padded_batch, lengths_batch)
        loss = criterion(outputs, labels_batch)
        loss.backward()
        optimizer.step()
        
        epoch_loss += loss.item()

    print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss / len(data_loader):.4f}')

print("Finished training")

print("\nStarting evaluation on the full dataset")
all_predictions = []
all_labels = []
all_original_labels = []
all_confidences = []

eval_loader = DataLoader(dataset, batch_size=16, shuffle=False, collate_fn=collate_fn_with_target)

r_vocab = {}
for key, val in vocab.items():
    r_vocab[val] = key

def to_kasarok(padded, label, reversed_vocab, str_target=True):
    if str_target:
        seq = str(label.item())
    else:
        seq = str(label.item() + 1)
    
    seq += ' -1'

    temp = []
    first_item = True
    for item in padded:
        if item == 0:
            break
        if item.item() == 1:  # Separator
            if first_item:
                first_item = False
                continue
            if temp: 
                seq += ' ' + ' '.join(temp) + ' -1'
            else:
                seq += ' -1'
            temp.clear()
            first_item = False
            continue
        
        temp.append(reversed_vocab[item.item()])
        first_item = False
    
    if temp:
        seq += ' ' + ' '.join(temp) + ' -2'
    else:
        seq += ' -2'
    
    return seq

metadataset = pd.DataFrame(columns=['sequence', 'y_true', 'confidence'])

model.eval()
with torch.no_grad():
    for batch_idx, (labels_batch, padded_batch, lengths_batch) in enumerate(eval_loader):
        outputs = model(padded_batch, lengths_batch)

        batch_start = batch_idx * eval_loader.batch_size
        batch_end = min(batch_start + len(labels_batch), len(dataset))
        original_labels_batch = [dataset[i][0] for i in range(batch_start, batch_end)]

        seqs = []
        for padded, orig_label in zip(padded_batch, original_labels_batch):
            binary_label_value = 1 if orig_label == target_class else 0
            binary_label_tensor = torch.tensor(binary_label_value, dtype=torch.long)
            seqs.append(to_kasarok(padded, binary_label_tensor, r_vocab))

        predictions = torch.argmax(outputs, dim=1)
        probabilities = F.softmax(outputs, dim=1).detach().cpu().numpy()
        
        positive_class_probs = [prob[1] for prob in probabilities]
        
        binary_labels_batch = [1 if orig_label == target_class else 0 for orig_label in original_labels_batch]
    
        _metadataset = pd.DataFrame(data={
            'sequence': seqs,
            'y_true': binary_labels_batch,
            'confidence': positive_class_probs 
        })
        metadataset = pd.concat([metadataset, _metadataset])
    
        all_predictions.extend(predictions.tolist())
        all_labels.extend(labels_batch.tolist())
        all_original_labels.extend(original_labels_batch)
        all_confidences.extend(probabilities.tolist())


print("\n" + "="*30)
print("PERFORMANCE METRICS")
print("="*30)

accuracy = accuracy_score(all_labels, all_predictions)
print(f"Overall Accuracy: {accuracy:.4f}\n")

target_names = ['Other', target_class] 
print("Classification report (binary):")
print(classification_report(all_labels, all_predictions, target_names=target_names))

# Print class distribution
print(f"\nClass distribution:")
print(f"  Class 0 (others): {sum(1 for l in all_labels if l == 0)} samples")
print(f"  Class 1 ({target_class}): {sum(1 for l in all_labels if l == 1)} samples")


metadataset_file = f"data/emm_{file_name.split('/')[-1].split('.')[0]}.csv"
metadataset_sequences = f"data/emm_{file_name.split('/')[-1].split('.')[0]}.dat"

metadataset.to_csv(metadataset_file, index=False)

np.savetxt(metadataset_sequences, metadataset['sequence'].values, fmt = "%s")
