import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence
from sklearn.metrics import confusion_matrix
import re

def movement_to_token(dx, dy):
    if dx == 0 and dy == 0:
        direction = 'STAY'
    elif dx > 0 and dy == 0:
        direction = 'E'
    elif dx > 0 and dy < 0:
        direction = 'NE'
    elif dx == 0 and dy < 0:
        direction = 'N'
    elif dx < 0 and dy < 0:
        direction = 'NW'
    elif dx < 0 and dy == 0:
        direction = 'W'
    elif dx < 0 and dy > 0:
        direction = 'SW'
    elif dx == 0 and dy > 0:
        direction = 'S'
    elif dx > 0 and dy > 0:
        direction = 'SE'
    else:
        direction = 'STAY'
    
    abs_dx = abs(dx)
    abs_dy = abs(dy)
    
    return f"{direction}_{abs_dx}_{abs_dy}"


def parse_kosarak_sequence(kosarak_str):
    parts = kosarak_str.strip().split()
    
    tokens = []
    i = 0
    
    while i < len(parts) and parts[i] != '-1':
        i += 1
    
    i += 1
    while i < len(parts):
        if parts[i] == '-2':
            break
        elif parts[i] == '-1':
            i += 1
            continue
        else:
            token = parts[i]
            tokens.append(token)
            i += 1
    
    return tokens


def parse_label(label):
    """Parse label from various formats"""
    label_str = str(label)
    if 'tensor' in label_str:
        label_match = re.search(r'\[(\d+)\]', label_str)
        return int(label_match.group(1)) if label_match else 0
    else:
        return int(float(label_str))


def load_mnist_sequences_from_csv(train_csv, test_csv, use_train=True, use_test=True):
    sequences = []
    labels = []
    
    if use_train:
        print("Loading training sequences from CSV...")
        df_train = pd.read_csv(train_csv)
        for idx, row in df_train.iterrows():
            kosarak_seq = row['sequence']
            y_true = parse_label(row['y_true'])
            tokens = parse_kosarak_sequence(kosarak_seq)
            sequences.append(tokens)
            labels.append(y_true)
    
        print(f"  Loaded {len(sequences)} training samples")
    
    if use_test:
        print("Loading test sequences from CSV...")
        start_idx = len(sequences)
        df_test = pd.read_csv(test_csv)
        for idx, row in df_test.iterrows():
            kosarak_seq = row['sequence']
            y_true = parse_label(row['y_true'])
            tokens = parse_kosarak_sequence(kosarak_seq)
            sequences.append(tokens)
            labels.append(y_true)
        print(f"  Loaded {len(sequences) - start_idx} test samples")
    
    return sequences, labels


class MNISTSequenceDatasetFromCSV(Dataset):
    def __init__(self, sequences, labels, token_to_id=None):
        self.sequences = []
        self.labels = []
        self.file_paths = []
        self.token_to_id = token_to_id
        
        if self.token_to_id is None:
            unique_tokens = set()
            for seq in sequences:
                for token in seq:
                    unique_tokens.add(token)
            
            self.token_to_id = {'<PAD>': 0}
            self.id_to_token = {0: '<PAD>'}
            
            for token in ['EOS', 'EOD']:
                if token not in self.token_to_id:
                    idx = len(self.token_to_id)
                    self.token_to_id[token] = idx
                    self.id_to_token[idx] = token
            
            for token in sorted(unique_tokens):
                if token not in self.token_to_id:
                    idx = len(self.token_to_id)
                    self.token_to_id[token] = idx
                    self.id_to_token[idx] = token
            
            print(f"Built vocabulary with {len(self.token_to_id)} unique tokens")
        else:
            self.id_to_token = {v: k for k, v in self.token_to_id.items()}
        
        for seq, label in zip(sequences, labels):
            token_ids = []
            for token in seq:
                token_id = self.token_to_id.get(token, 0)
                token_ids.append(token_id)
            self.sequences.append(token_ids)
            self.labels.append(label)
            self.file_paths.append(None)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return torch.LongTensor(self.sequences[idx]), torch.LongTensor([self.labels[idx]])


def collate_fn(batch):
    sequences, labels = zip(*batch)
    lengths = torch.LongTensor([len(seq) for seq in sequences])
    padded_seqs = pad_sequence(sequences, batch_first=True, padding_value=0)
    labels = torch.cat(labels)
    
    return padded_seqs, labels, lengths


class LSTMSequenceClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim=32, hidden_size=64, num_layers=2, dropout=0.2):
        super(LSTMSequenceClassifier, self).__init__()
        
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
            padding_idx=0
        )
        
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size * 2, 32), 
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 2)
        )
    
    def forward(self, x, lengths):
        embedded = self.embedding(x)
        packed = pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        packed_output, (hidden, cell) = self.lstm(packed)
        forward_hidden = hidden[-2]
        backward_hidden = hidden[-1]
        last_hidden = torch.cat([forward_hidden, backward_hidden], dim=1)
        
        logits = self.fc(last_hidden)
        
        return logits


def load_trained_model(model_path, device='cpu'):
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
    state_dict = checkpoint['model_state_dict']

    model = LSTMSequenceClassifier(
        vocab_size=checkpoint['vocab_size'],
        embedding_dim=checkpoint['embedding_dim'],
        hidden_size=checkpoint['hidden_size'],
        num_layers=checkpoint['num_layers'],
        dropout=checkpoint['dropout']
    )

    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    
    token_to_id = checkpoint['token_to_id']
    if 'id_to_token' in checkpoint:
        id_to_token = checkpoint['id_to_token']
    else:
        id_to_token = {v: k for k, v in token_to_id.items()}
    
    return model, token_to_id, id_to_token, checkpoint


def classify_single_instance(model, token_to_id, instance, device='cpu'):
    if isinstance(instance, str):
        tokens = parse_kosarak_sequence(instance)
    elif isinstance(instance, list):
        tokens = instance
    else:
        raise ValueError("instance must be a string (Kosarak format) or list of token strings")
    
    token_ids = []
    for token in tokens:
        token_id = token_to_id.get(token, 0)
        token_ids.append(token_id)
    
    if len(token_ids) == 0:
        raise ValueError("Instance must contain at least one token")
    
    seq_tensor = torch.LongTensor([token_ids]).to(device)
    length = torch.LongTensor([len(token_ids)])
    
    with torch.no_grad():
        output = model(seq_tensor, length) 
        probabilities = torch.softmax(output, dim=1).cpu().numpy()[0]
        prediction = output.argmax(dim=1).item()
    
    confidence = {
        0: float(probabilities[0]),
        1: float(probabilities[1])
    }
    
    return prediction, confidence, probabilities

def train_model(model, train_loader, val_loader, epochs=20, lr=0.001, device='cpu'):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    model.to(device)
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0
        
        for sequences, labels, lengths in train_loader:
            sequences, labels = sequences.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(sequences, lengths)
            loss = criterion(outputs, labels)
            
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
        
        train_acc = 100 * train_correct / train_total
        avg_train_loss = train_loss / len(train_loader)
        
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for sequences, labels, lengths in val_loader:
                sequences, labels = sequences.to(device), labels.to(device)
                outputs = model(sequences, lengths)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        
        val_acc = 100 * val_correct / val_total
        avg_val_loss = val_loss / len(val_loader)
        
        history['train_loss'].append(avg_train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(avg_val_loss)
        history['val_acc'].append(val_acc)
        
        if (epoch + 1) % 5 == 0:
            print(f'Epoch [{epoch+1}/{epochs}]')
            print(f'  Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.2f}%')
            print(f'  Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.2f}%')
    
    return history


# ====================
# 4. SAVE METADATASET
# ====================

def save_metadataset(dataset_list, predictions, confidences, full_dataset, dataset_indices, output_prefix, class0, class1):
    sequences = []
    y_true_list = []
    confidence_list = []
    
    for idx, ((seq, true_label), pred, conf) in enumerate(zip(dataset_list, predictions, confidences)):
        positive_conf = conf[1] if len(conf) > 1 else conf[0]
        original_idx = dataset_indices[idx]
        token_ids = full_dataset.sequences[original_idx]
        token_strings = []
        for token_id in token_ids:
            if token_id in full_dataset.id_to_token:
                token_strings.append(full_dataset.id_to_token[token_id])
        
        kosarak_parts = [str(parse_label(true_label))]
        for token in token_strings:
            kosarak_parts.append("-1")
            kosarak_parts.append(token)
        kosarak_parts.append("-2")
        kosarak_seq = " ".join(kosarak_parts)
        
        sequences.append(kosarak_seq)
        y_true_list.append(parse_label(true_label))
        confidence_list.append(positive_conf)
    
    metadataset = pd.DataFrame({
        'sequence': sequences,
        'y_true': y_true_list,
        'confidence': confidence_list
    })
    
    csv_file = f'emm_mnist_5_{output_prefix}.csv'
    metadataset.to_csv(csv_file, index=False)
    print(f"  Saved: {csv_file}")
    
    dat_file = f'emm_mnist_5_{output_prefix}.dat'
    np.savetxt(dat_file, metadataset['sequence'].values, fmt='%s')
    print(f"  Saved: {dat_file}")
    
    return metadataset



def main():
    TRAIN_CSV = 'emm_mnist_5_train.csv'
    TEST_CSV = 'emm_mnist_5_test.csv'
    CLASS_0 = '3'
    CLASS_1 = '8'
    BATCH_SIZE = 8
    EPOCHS = 1
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"Using device: {DEVICE}")
    
    print("\nLoading MNIST sequential data from CSV files...")
    sequences, labels = load_mnist_sequences_from_csv(TRAIN_CSV, TEST_CSV, use_train=True, use_test=True)
    
    print(f"\nTotal sequences loaded: {len(sequences)}")
    print(f"Total labels loaded: {len(labels)}")
    
    print("\nBuilding vocabulary from dataset...")
    dataset = MNISTSequenceDatasetFromCSV(sequences, labels)
    vocab_size = len(dataset.token_to_id)
    print(f"Vocabulary size: {vocab_size} unique tokens")
    print(f"\nBinary classification dataset: {len(dataset)} samples")
    print(f"  Class 0 ({CLASS_0}): {sum([1 for l in dataset.labels if l == 0])} samples")
    print(f"  Class 1 ({CLASS_1}): {sum([1 for l in dataset.labels if l == 1])} samples")
    
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    train_dataset.dataset = dataset
    val_dataset.dataset = dataset
    
    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn
    )
    
    print("\nInitializing model...")
    model = LSTMSequenceClassifier(
        vocab_size=vocab_size,
        embedding_dim=32,
        hidden_size=64,
        num_layers=2,
        dropout=0.3
    )
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters())}")
    
    print("\nTraining model...")
    history = train_model(
        model, train_loader, val_loader, 
        epochs=EPOCHS, lr=0.001, device=DEVICE
    )
    
    print("\nSaving trained model...")
    model_save_path = 'lstm_mnist_model_6.pth'
    torch.save({
        'model_state_dict': model.state_dict(),
        'vocab_size': vocab_size,
        'token_to_id': dataset.token_to_id,
        'id_to_token': dataset.id_to_token,
        'embedding_dim': model.embedding_dim,
        'hidden_size': model.hidden_size,
        'num_layers': model.num_layers,
        'dropout': 0.3,
        'history': history
    }, model_save_path)
    print(f"  Saved model to: {model_save_path}")
    
    print("\nGenerating predictions and saving metadatasets...")
    
    model.eval()
    train_preds = []
    train_confs = []
    train_true_labels = []
    with torch.no_grad():
        for seq, label in train_dataset:
            seq_tensor = seq.unsqueeze(0).to(DEVICE)
            length = torch.LongTensor([len(seq)])
            output = model(seq_tensor, length)
            pred = output.argmax().item()
            conf = torch.softmax(output, dim=1).cpu().numpy()[0]
            train_preds.append(pred)
            train_confs.append(conf)
            train_true_labels.append(label.item())
    
    val_preds = []
    val_confs = []
    val_true_labels = []
    with torch.no_grad():
        for seq, label in val_dataset:
            seq_tensor = seq.unsqueeze(0).to(DEVICE)
            length = torch.LongTensor([len(seq)])
            output = model(seq_tensor, length)
            pred = output.argmax().item()
            conf = torch.softmax(output, dim=1).cpu().numpy()[0]
            val_preds.append(pred)
            val_confs.append(conf)
            val_true_labels.append(label.item())
    
    print("\n" + "="*70)
    print("CONFUSION MATRICES")
    print("="*70)
    
    train_cm = confusion_matrix(train_true_labels, train_preds)
    print("\nTrain Confusion Matrix:")
    print(f"                Predicted")
    print(f"                0     1")
    print(f"Actual  0    {train_cm[0][0]:5d}  {train_cm[0][1]:5d}")
    print(f"        1    {train_cm[1][0]:5d}  {train_cm[1][1]:5d}")
    
    train_tn, train_fp, train_fn, train_tp = train_cm.ravel()
    train_accuracy = (train_tp + train_tn) / (train_tp + train_tn + train_fp + train_fn)
    train_precision = train_tp / (train_tp + train_fp) if (train_tp + train_fp) > 0 else 0
    train_recall = train_tp / (train_tp + train_fn) if (train_tp + train_fn) > 0 else 0
    train_f1 = 2 * (train_precision * train_recall) / (train_precision + train_recall) if (train_precision + train_recall) > 0 else 0
    
    print(f"\nTrain Metrics:")
    print(f"  Accuracy:  {train_accuracy:.4f}")
    print(f"  Precision: {train_precision:.4f}")
    print(f"  Recall:    {train_recall:.4f}")
    print(f"  F1-Score:  {train_f1:.4f}")
    
    val_cm = confusion_matrix(val_true_labels, val_preds)
    print("\nTest Confusion Matrix:")
    print(f"                Predicted")
    print(f"                0     1")
    print(f"Actual  0    {val_cm[0][0]:5d}  {val_cm[0][1]:5d}")
    print(f"        1    {val_cm[1][0]:5d}  {val_cm[1][1]:5d}")
    
    val_tn, val_fp, val_fn, val_tp = val_cm.ravel()
    val_accuracy = (val_tp + val_tn) / (val_tp + val_tn + val_fp + val_fn)
    val_precision = val_tp / (val_tp + val_fp) if (val_tp + val_fp) > 0 else 0
    val_recall = val_tp / (val_tp + val_fn) if (val_tp + val_fn) > 0 else 0
    val_f1 = 2 * (val_precision * val_recall) / (val_precision + val_recall) if (val_precision + val_recall) > 0 else 0
    
    print(f"\nTest Metrics:")
    print(f"  Accuracy:  {val_accuracy:.4f}")
    print(f"  Precision: {val_precision:.4f}")
    print(f"  Recall:    {val_recall:.4f}")
    print(f"  F1-Score:  {val_f1:.4f}")
    print("="*70)
    
    print("\nSaving train metadataset...")
    save_metadataset(
        list(train_dataset),
        train_preds,
        train_confs,
        dataset,
        train_dataset.indices,
        'train',
        CLASS_0,
        CLASS_1
    )
    
    print("\nSaving validation metadataset...")
    save_metadataset(
        list(val_dataset),
        val_preds,
        val_confs,
        dataset,
        val_dataset.indices,
        'test',
        CLASS_0,
        CLASS_1
    )


def example_classify_single_instance():
    model_path = 'lstm_mnist_model_5.pth'
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"Loading model from {model_path}...")
    model, token_to_id, id_to_token, checkpoint = load_trained_model(model_path, device=device)
    print("Model loaded successfully!")
    
    kosarak_seq = "0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 SE_1_1 -1 SE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 SE_1_1 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 NE_1_1 -1 N_0_1 -1 N_0_1 -1 NW_1_1 -1 N_0_1 -1 N_0_1 -1 NE_1_1 -1 E_1_0 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 NW_1_1 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 SW_1_1 -1 W_1_0 -1 STAY_0_0 -2"
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")

    kosarak_seq = '0 -1 NE_1_1 -1 NE_1_1 -1 NE_1_1 -1 N_0_1 -1 E_1_0 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 W_1_0 -1 NW_1_1 -1 SW_1_1 -1 W_1_0 -1 SW_1_1 -1 SW_1_1 -1 S_0_1 -1 S_0_1 -1 SW_1_1 -1 S_0_1 -1 SE_1_1 -1 SE_1_1 -1 SE_1_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")

    kosarak_seq = '0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 SE_1_1 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 W_1_0 -1 W_1_0 -1 S_0_1 -1 E_1_0 -1 STAY_0_0 -1 N_0_2 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 N_0_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 N_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 W_1_0 -1 SE_1_1 -1 STAY_0_0 -1 SE_2_2 -1 E_1_0 -1 S_0_1 -1 STAY_0_0 -1 NE_1_2 -1 N_0_1 -1 STAY_0_0 -1 SW_4_3 -1 S_0_1 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")

    kosarak_seq = '0 -1 W_1_0 -1 SW_1_1 -1 SW_1_1 -1 S_0_1 -1 SE_1_1 -1 S_0_1 -1 E_1_0 -1 SE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 NE_1_1 -1 NE_1_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 NW_1_1 -1 W_1_0 -1 W_1_0 -1 STAY_0_0 -1 NE_2_1 -1 NE_1_1 -1 N_0_1 -1 NE_1_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")

    kosarak_seq = '0 -1 S_0_1 -1 S_0_1 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 E_1_0 -1 SE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 NW_1_1 -1 W_1_0 -1 W_1_0 -1 STAY_0_0 -1 NE_3_1 -1 NE_1_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 N_0_1 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 S_0_1 -1 SW_1_1 -1 SW_1_1 -1 S_0_1 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")


    kosarak_seq = '1 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 SE_1_1 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 W_1_0 -1 W_1_0 -1 N_0_1 -1 STAY_0_0 -1 S_0_2 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 SW_1_1 -1 S_0_1 -1 W_1_0 -1 W_1_0 -1 S_0_1 -1 SW_1_1 -1 SW_1_1 -1 S_0_1 -1 SW_1_1 -1 SE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 NE_1_1 -1 N_0_1 -1 N_0_1 -1 NW_1_1 -1 STAY_0_0 -1 NW_3_2 -1 NW_1_1 -1 W_1_0 -1 W_1_0 -1 NW_1_1 -1 W_1_0 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 NW_1_1 -1 NE_1_1 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")

    kosarak_seq = '1 -1 E_1_0 -1 NE_1_1 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 W_1_0 -1 SW_1_1 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 NW_1_1 -1 W_1_0 -1 NW_1_1 -1 N_0_1 -1 N_0_1 -1 STAY_0_0 -1 SE_2_5 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 SW_1_1 -1 W_1_0 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 SW_1_1 -1 S_0_1 -1 S_0_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 NE_1_1 -1 NW_1_1 -1 NW_1_1 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")

    kosarak_seq = '1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 SW_1_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 SW_1_1 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 N_0_1 -1 NW_1_1 -1 NE_1_1 -1 NE_1_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 NW_1_1 -1 N_0_1 -1 W_1_0 -1 NW_1_1 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 N_0_1 -1 NW_1_1 -1 NE_1_1 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")

    kosarak_seq =  '1 -1 SE_1_1 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 W_1_0 -1 S_0_1 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 W_1_0 -1 STAY_0_0 -1 S_0_2 -1 W_1_0 -1 S_0_1 -1 S_0_1 -1 NE_1_1 -1 NE_1_1 -1 STAY_0_0 -1 NW_1_7 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 W_1_0 -1 STAY_0_0 -1 NE_2_2 -1 E_1_0 -1 NW_1_1 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")

    kosarak_seq = '1 -1 E_1_0 -1 N_0_1 -1 NE_1_1 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 NE_1_1 -1 E_1_0 -1 SE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 W_1_0 -1 S_0_1 -1 S_0_1 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 E_1_0 -1 S_0_1 -1 S_0_1 -1 S_0_1 -1 SW_1_1 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 N_0_1 -1 W_1_0 -1 NW_1_1 -1 NW_1_1 -1 NE_1_1 -1 N_0_1 -1 NE_1_1 -1 NE_1_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 S_0_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 N_0_1 -1 E_1_0 -1 E_1_0 -1 E_1_0 -1 STAY_0_0 -1 NW_11_1 -1 N_0_1 -1 N_0_1 -1 STAY_0_0 -2'
    pred, conf, probs = classify_single_instance(model, token_to_id, kosarak_seq, device=device)
    print(f"  Prediction: {pred}")
    print(f"  Confidence class 0: {conf[0]:.4f}")
    print(f"  Confidence class 1: {conf[1]:.4f}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--example':
        example_classify_single_instance()
    else:
        main()
