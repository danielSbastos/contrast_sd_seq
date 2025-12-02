import pandas as pd
import numpy as np

import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from torch.nn.utils.rnn import pad_sequence

from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from functools import partial
from collections import Counter
from tqdm import tqdm

# Configuration
MAX_SEQUENCE_LENGTH = 200  # Truncate sequences longer than this
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

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
#file_name = './data/original/context.data'
#file_name = './data/DNA_train.dat'
file_name = './data/dynamic_api_call_sequence_per_malware_100_0_306.dat'
#file_name = './data/Youtube.dat'
#file_name = './data/pkdd_sequences_rich_expanded.dat'
#file_name = './data/twitter-processed.dat'
file_name = './data/pkdd_sequences_rich_full.dat'
target_class = '1'

print(f"Building vocabulary from {file_name}...")
vocab, classes = build_vocab(file_name, kosarak)
print(f"Vocabulary size: {len(vocab)}")

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

def parse_flatten(line, event2id, kosarak=True, max_length=None):
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
            # Truncate if max_length is set
            if max_length and len(seq) >= max_length:
                break
    else:
        label, _, tokens = line.strip().split(',')
 
        for tok in tokens.strip():
            seq.append(event2id[tok])
            seq.append(event2id["<SEP>"])
            if max_length and len(seq) >= max_length:
                break

    return label, torch.tensor(seq, dtype=torch.long)

def collate_fn(batch, target_class):
    labels, seqs = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs])
    padded = pad_sequence(seqs, batch_first=True, padding_value=0)  # PAD=0
    
    binary_labels = torch.tensor([1 if label == target_class else 0 for label in labels])
    
    return binary_labels, padded, lengths

class BiLSTMAttentionClassifier(nn.Module):
    """
    Bidirectional LSTM with Attention - Best for sequential data with class imbalance.
    Uses attention to focus on important parts of the sequence.
    """
    def __init__(self, vocab_size, emb_dim, hidden_dim, num_classes, num_layers=1, dropout=0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.lstm = nn.LSTM(emb_dim, hidden_dim, num_layers=num_layers, 
                           batch_first=True, bidirectional=True, dropout=dropout if num_layers > 1 else 0)
        self.attention = nn.Linear(hidden_dim * 2, 1)  # *2 because bidirectional
        self.fc = nn.Linear(hidden_dim * 2, num_classes)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, lengths):
        embedded = self.embedding(x)
        packed = pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        lstm_out, _ = self.lstm(packed)
        # Unpack the sequence
        lstm_out, _ = pad_packed_sequence(lstm_out, batch_first=True)
        
        # Attention mechanism
        attention_weights = self.attention(lstm_out).squeeze(-1)  # [batch, seq_len]
        # Mask out padding positions
        mask = (torch.arange(attention_weights.size(1), device=x.device).unsqueeze(0) < lengths.unsqueeze(1))
        attention_weights = attention_weights.masked_fill(~mask, float('-inf'))
        attention_weights = F.softmax(attention_weights, dim=1)
        
        # Weighted sum of LSTM outputs
        attended = torch.bmm(attention_weights.unsqueeze(1), lstm_out).squeeze(1)  # [batch, hidden*2]
        attended = self.dropout(attended)
        out = self.fc(attended)
        return out

print(f"\nLoading and parsing dataset (max sequence length: {MAX_SEQUENCE_LENGTH})...")
lines = []
with open(file_name) as file:
    for line in file:
        lines.append(line)

print(f"Parsing {len(lines)} sequences...")
dataset = []
truncated_count = 0
for line in tqdm(lines, desc="Parsing"):
    label, seq_tensor = parse_flatten(line, vocab, kosarak, max_length=MAX_SEQUENCE_LENGTH)
    if len(seq_tensor) > MAX_SEQUENCE_LENGTH:
        truncated_count += 1
    dataset.append((label, seq_tensor))

if truncated_count > 0:
    print(f"Warning: {truncated_count} sequences were truncated to {MAX_SEQUENCE_LENGTH} tokens")

# Calculate average sequence length
avg_len = sum(len(seq) for _, seq in dataset) / len(dataset)
max_len = max(len(seq) for _, seq in dataset)
print(f"Sequence length stats: avg={avg_len:.1f}, max={max_len}")

# Split dataset into train and test
TEST_SIZE = 0.2
RANDOM_STATE = 42
print(f"\nSplitting dataset into train ({1-TEST_SIZE:.0%}) and test ({TEST_SIZE:.0%}) sets...")
train_dataset, test_dataset = train_test_split(dataset, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=[label for label, _ in dataset])
print(f"Train set: {len(train_dataset)} sequences")
print(f"Test set: {len(test_dataset)} sequences")

collate_fn_with_target = partial(collate_fn, target_class=target_class)

# Adjust batch sizes based on sequence length and dataset size
if MAX_SEQUENCE_LENGTH > 1000:
    train_batch_size = 32 if DEVICE.type == 'cuda' else 16
    eval_batch_size = 16 if DEVICE.type == 'cuda' else 8
else:
    train_batch_size = 128 if DEVICE.type == 'cuda' else 64
    eval_batch_size = 64 if DEVICE.type == 'cuda' else 32

print(f"Batch sizes: train={train_batch_size}, eval={eval_batch_size}")

data_loader = DataLoader(train_dataset, batch_size=train_batch_size, shuffle=True, collate_fn=collate_fn_with_target, num_workers=2 if DEVICE.type == 'cuda' else 0)

# Create model
model = BiLSTMAttentionClassifier(vocab_size=len(vocab), emb_dim=32, hidden_dim=32, num_classes=2, num_layers=1, dropout=0.1)
print(f"Using model: BiLSTM with Attention")

model = model.to(DEVICE)

# Calculate class weights to handle severe imbalance
train_class_counts = Counter([label for label, _ in train_dataset])
total_train = len(train_dataset)

# Map to binary labels based on target_class
binary_class_counts = Counter()
for label, _ in train_dataset:
    binary_label = 1 if label == target_class else 0
    binary_class_counts[binary_label] += 1

class_0_binary_count = binary_class_counts.get(0, 0)  # Other class
class_1_binary_count = binary_class_counts.get(1, 0)  # Target class

print(f"\nBinary class distribution in training set:")
print(f"  Binary Class 0 (Other): {class_0_binary_count} samples")
print(f"  Binary Class 1 (Target '{target_class}'): {class_1_binary_count} samples")
print(f"  Imbalance ratio: {max(class_0_binary_count, class_1_binary_count) / min(class_0_binary_count, class_1_binary_count):.2f}:1")

# Calculate weights: inverse frequency weighting (higher weight for minority class)
if class_0_binary_count > 0 and class_1_binary_count > 0:
    weight_0 = total_train / (2.0 * class_0_binary_count)
    weight_1 = total_train / (2.0 * class_1_binary_count)
    class_weights = torch.tensor([weight_0, weight_1], dtype=torch.float32).to(DEVICE)
    print(f"Class weights: Binary Class 0={weight_0:.3f}, Binary Class 1={weight_1:.3f}")
    print(f"  (Higher weight for minority class to balance training)")
else:
    class_weights = None
    print("Warning: Could not calculate class weights - severe imbalance detected")

# Focal Loss for handling severe class imbalance
class FocalLoss(nn.Module):
    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):
        super().__init__()
        self.alpha = alpha  # Class weights
        self.gamma = gamma  # Focusing parameter
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, weight=self.alpha, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        return focal_loss

# Use Focal Loss for better handling of class imbalance
criterion = FocalLoss(alpha=class_weights, gamma=2.0)
print("Using Focal Loss for imbalanced classification")

optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training epochs
num_epochs = 13

print("\nStarting training")
model.train()

for epoch in range(num_epochs):
    epoch_loss = 0.0
    num_batches = 0
    for labels_batch, padded_batch, lengths_batch in tqdm(data_loader, desc=f"Epoch {epoch+1}/{num_epochs}"):
        labels_batch = labels_batch.to(DEVICE)
        padded_batch = padded_batch.to(DEVICE)
        
        optimizer.zero_grad()

        outputs = model(padded_batch, lengths_batch)
        loss = criterion(outputs, labels_batch)
        loss.backward()
        optimizer.step()
        
        epoch_loss += loss.item()
        num_batches += 1

    print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss / num_batches:.4f}')

print("Finished training")

print("\nStarting evaluation on train and test sets")
eval_loader_train = DataLoader(train_dataset, batch_size=eval_batch_size, shuffle=False, collate_fn=collate_fn_with_target, num_workers=2 if DEVICE.type == 'cuda' else 0)
eval_loader_test = DataLoader(test_dataset, batch_size=eval_batch_size, shuffle=False, collate_fn=collate_fn_with_target, num_workers=2 if DEVICE.type == 'cuda' else 0)

r_vocab = {}
for key, val in vocab.items():
    r_vocab[val] = key

def evaluate_and_build_metadataset(eval_loader, dataset_subset, subset_name):
    """Evaluate model and build metadataset for a given subset"""
    all_predictions = []
    all_labels = []
    all_original_labels = []
    all_confidences = []
    metadataset = pd.DataFrame(columns=['sequence', 'y_true', 'confidence'])
    
    model.eval()
    with torch.no_grad():
        for batch_idx, (labels_batch, padded_batch, lengths_batch) in enumerate(tqdm(eval_loader, desc=f"Evaluating {subset_name}")):
            padded_batch = padded_batch.to(DEVICE)
            
            outputs = model(padded_batch, lengths_batch)
            outputs = outputs.cpu()

            batch_start = batch_idx * eval_loader.batch_size
            batch_end = min(batch_start + len(labels_batch), len(dataset_subset))
            original_labels_batch = [dataset_subset[i][0] for i in range(batch_start, batch_end)]

            seqs = []
            for padded, orig_label in zip(padded_batch.cpu(), original_labels_batch):
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
    
    return metadataset, all_predictions, all_labels, all_original_labels, all_confidences

def to_kasarok(padded, label, reversed_vocab, str_target=True):
    if str_target:
        seq = str(label.item())
    else:
        seq = str(label.item() + 1)
    
    temp = []
    first_separator_seen = False
    for item in padded:
        if item == 0:
            break
        if item.item() == 1:  # Separator
            if not first_separator_seen:
                first_separator_seen = True
                continue
            if temp: 
                seq += ' ' + ' '.join(temp) + ' -1'
            temp.clear()
            continue
        
        temp.append(reversed_vocab[item.item()])
        first_separator_seen = True
    
    if temp:
        seq += ' ' + ' '.join(temp)
    
    seq += ' -2'
    
    return seq

# Evaluate on train and test sets
train_metadataset, train_predictions, train_labels, train_original_labels, train_confidences = evaluate_and_build_metadataset(
    eval_loader_train, train_dataset, "train"
)

test_metadataset, test_predictions, test_labels, test_original_labels, test_confidences = evaluate_and_build_metadataset(
    eval_loader_test, test_dataset, "test"
)

# Print performance metrics for both sets
print("\n" + "="*30)
print("TRAIN SET PERFORMANCE METRICS")
print("="*30)

train_accuracy = accuracy_score(train_labels, train_predictions)
print(f"Train Accuracy: {train_accuracy:.4f}\n")

target_names = ['Other', target_class] 
print("Train Classification report (binary):")
print(classification_report(train_labels, train_predictions, target_names=target_names))

print(f"\nTrain Class distribution:")
print(f"  Class 0 (others): {sum(1 for l in train_labels if l == 0)} samples")
print(f"  Class 1 ({target_class}): {sum(1 for l in train_labels if l == 1)} samples")

print("\n" + "="*30)
print("TEST SET PERFORMANCE METRICS")
print("="*30)

test_accuracy = accuracy_score(test_labels, test_predictions)
print(f"Test Accuracy: {test_accuracy:.4f}\n")

print("Test Classification report (binary):")
print(classification_report(test_labels, test_predictions, target_names=target_names))

print(f"\nTest Class distribution:")
print(f"  Class 0 (others): {sum(1 for l in test_labels if l == 0)} samples")
print(f"  Class 1 ({target_class}): {sum(1 for l in test_labels if l == 1)} samples")

# Save train and test metadatasets
base_name = file_name.split('/')[-1].split('.')[0]

train_metadataset_file = f"data/emm_{base_name}_train.csv"
train_metadataset_sequences = f"data/emm_{base_name}_train.dat"

test_metadataset_file = f"data/emm_{base_name}_test.csv"
test_metadataset_sequences = f"data/emm_{base_name}_test.dat"

print(f"\nSaving train metadataset...")
train_metadataset.to_csv(train_metadataset_file, index=False)
np.savetxt(train_metadataset_sequences, train_metadataset['sequence'].values, fmt="%s")
print(f"  Saved: {train_metadataset_file}")
print(f"  Saved: {train_metadataset_sequences}")

print(f"\nSaving test metadataset...")
test_metadataset.to_csv(test_metadataset_file, index=False)
np.savetxt(test_metadataset_sequences, test_metadataset['sequence'].values, fmt="%s")
print(f"  Saved: {test_metadataset_file}")
print(f"  Saved: {test_metadataset_sequences}")
