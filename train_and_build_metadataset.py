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

file_name = './data/figures_rc.dat'
file_name = './data/context.data'
#file_name = './data/skating.data'

def build_vocab(filepath):
    classes = set()
    classes_list = []
    event_set = set()
    with open(filepath, "r") as f:
        for line in f:
            tokens = line.strip().split()
            for tok in tokens[1:]:
                if tok not in ("-1", "-2"):  
                    event_set.add(tok)
            classes.add(tokens[0])
            classes_list.append(tokens[0])
    
    event2id = {event: idx+2 for idx, event in enumerate(sorted(event_set))}
    event2id["<PAD>"] = 0
    event2id["<SEP>"] = 1

    return event2id, classes

vocab, classes = build_vocab(file_name)

def parse_flatten(line, event2id):
    tokens = line.strip().split()
    label = tokens[0]
    seq = []
    for tok in tokens[1:]:
        if tok == "-1":
            seq.append(event2id["<SEP>"])
        elif tok == "-2":
            break
        else:
            seq.append(event2id[tok])
    return label, torch.tensor(seq, dtype=torch.long)

def collate_fn(batch):
    labels, seqs = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs])
    padded = pad_sequence(seqs, batch_first=True, padding_value=0)  # PAD=0
    return torch.tensor(list(map(lambda x: int(x) - 1, labels))), padded, lengths

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

dataset = [parse_flatten(line, vocab) for line in lines]

data_loader = DataLoader(dataset, batch_size=16, shuffle=True, collate_fn=collate_fn)

model = FlatLSTMClassifier(vocab_size=len(vocab), emb_dim=32, hidden_dim=64, num_classes=len(classes))
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

num_epochs = 15

print("Starting training... 🚀")
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

print("Finished Training!")

print("\nStarting evaluation on the full dataset...")
all_predictions = []
all_labels = []
all_confidences = []


eval_loader = DataLoader(dataset, batch_size=16, shuffle=False, collate_fn=collate_fn)

r_vocab = {}
for key, val in vocab.items():
    r_vocab[val] = key

def to_kasarok(padded, label, reversed_vocab):
    seq = str(label.item() + 1) + ' '
    temp = []
    for item in padded:
        if item == 0:
            break
        if item.item() == 1:
            seq += (' '.join(temp.copy()) + ' -1 ')
            temp.clear()
            continue
        
        temp.append(reversed_vocab[item.item()])
    return seq + '-2'

metadataset = pd.DataFrame(columns=['sequence', 'y_true', 'confidence'])

model.eval()
with torch.no_grad():
    for labels_batch, padded_batch, lengths_batch in eval_loader:
        outputs = model(padded_batch, lengths_batch)

        seqs = []
        for padded, label in zip(padded_batch, labels_batch):
            seqs.append(to_kasarok(padded, label, r_vocab))

        predictions = torch.argmax(outputs, dim=1)
        probabilities = F.softmax(outputs, dim=1).detach().cpu().numpy().tolist()
    
        _metadataset = pd.DataFrame(data={
            'sequence': seqs,
            'y_true': list(map(lambda i: i.item()+1, labels_batch)),
            #'predictions': list(map(lambda i: i+1, predictions)),
            'confidence': probabilities
        })
        metadataset = pd.concat([metadataset, _metadataset])
    
        all_predictions.extend(predictions.tolist())
        all_labels.extend(labels_batch.tolist())
        all_confidences.extend(probabilities)


print("\n" + "="*30)
print("PERFORMANCE METRICS")
print("="*30)

accuracy = accuracy_score(all_labels, all_predictions)
print(f"Overall Accuracy: {accuracy:.4f}\n")

print("Classification Report:")
print(classification_report(all_labels, all_predictions, target_names=list(map(str, set(all_labels)))))

metadataset_file = f"emm_{file_name.split('/')[-1].split('.')[0]}.csv"
metadataset_sequences = f"emm_{file_name.split('/')[-1].split('.')[0]}.dat"

metadataset.to_csv(metadataset_file, index=False)

np.savetxt(metadataset_sequences, metadataset['sequence'].values, fmt = "%s")
