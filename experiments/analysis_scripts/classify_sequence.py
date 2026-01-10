#!/usr/bin/env python3
"""
from utils.classify_sequence import MalwareClassifier
classifier = MalwareClassifier('data/malware_model.pkl')
result = classifier.classify([{'LdrGetDllHandle'}, {'LdrGetProcedureAddress'}, {'NtClose'}])
print(f"Prediction: {result['prediction']}, Confidence: {result['confidence']:.4f}")
"""

from torch.nn.utils.rnn import pad_sequence
import pickle
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


class BiLSTMAttentionClassifier(nn.Module):
    def __init__(self, vocab_size, emb_dim, hidden_dim, num_classes, num_layers=1, dropout=0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.lstm = nn.LSTM(emb_dim, hidden_dim, num_layers=num_layers, 
                           batch_first=True, bidirectional=True, dropout=dropout if num_layers > 1 else 0)
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, lengths):
        embedded = self.embedding(x)
        packed = pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        lstm_out, _ = self.lstm(packed)
        lstm_out, _ = pad_packed_sequence(lstm_out, batch_first=True)
        
        attention_weights = self.attention(lstm_out).squeeze(-1)
        mask = (torch.arange(attention_weights.size(1), device=x.device).unsqueeze(0) < lengths.unsqueeze(1))
        attention_weights = attention_weights.masked_fill(~mask, float('-inf'))
        attention_weights = F.softmax(attention_weights, dim=1)
        
        attended = torch.bmm(attention_weights.unsqueeze(1), lstm_out).squeeze(1)
        attended = self.dropout(attended)
        out = self.fc(attended)
        return out


class HierarchicalLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, emb_dim, hidden_dim, num_classes, 
                 num_layers=2, dropout=0.3, chunk_size=500):
        super().__init__()
        
        self.chunk_size = chunk_size
        self.hidden_dim = hidden_dim
        
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        
        self.lstm = nn.LSTM(
            emb_dim, hidden_dim, 
            num_layers=num_layers,
            batch_first=True, 
            bidirectional=True, 
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.num_heads = 4
        self.attention = nn.MultiheadAttention(
            hidden_dim * 2, 
            self.num_heads, 
            dropout=dropout,
            batch_first=True
        )
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(hidden_dim * 2)
        
        self.fc1 = nn.Linear(hidden_dim * 2, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, num_classes)
        
    def forward(self, x, lengths):
        embedded = self.embedding(x)
        
        packed = pack_padded_sequence(
            embedded, lengths.cpu(), 
            batch_first=True, 
            enforce_sorted=False
        )
        
        lstm_out, (hidden, cell) = self.lstm(packed)
        lstm_out, _ = pad_packed_sequence(lstm_out, batch_first=True)
        
        max_len = lstm_out.size(1)
        mask = torch.arange(max_len, device=x.device).unsqueeze(0) >= lengths.unsqueeze(1)
        
        attended, attention_weights = self.attention(
            lstm_out, lstm_out, lstm_out,
            key_padding_mask=mask
        )
        
        attended = self.layer_norm(attended + lstm_out)
        
        attended_masked = attended.masked_fill(mask.unsqueeze(-1), float('-inf'))
        pooled = attended_masked.max(dim=1)[0]
        
        pooled = self.dropout(pooled)
        hidden = F.relu(self.fc1(pooled))
        hidden = self.dropout(hidden)
        out = self.fc2(hidden)
        
        return out


class MalwareClassifier:
    def __init__(self, model_path, device=None):
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"Loading model from {model_path}...")
        with open(model_path, 'rb') as f:
            model_info = pickle.load(f)
        
        self.vocab = model_info['vocab'] 
        self.target_class = model_info.get('target_class', '1')
        self.kosarak = model_info.get('kosarak', True)
        self.max_sequence_length = model_info.get('max_sequence_length', 10000)
        
        vocab_size = model_info.get('vocab_size', len(self.vocab))
        
        if 'config' in model_info:
            config = model_info['config']
            model_class_name = model_info.get('model_class', 'HierarchicalLSTMClassifier')
            
            if model_class_name == 'HierarchicalLSTMClassifier':
                self.model = HierarchicalLSTMClassifier(
                    vocab_size=vocab_size,
                    emb_dim=config.get('emb_dim', 64),
                    hidden_dim=config.get('hidden_dim', 128),
                    num_classes=config.get('num_classes', 2),
                    num_layers=config.get('num_layers', 2),
                    dropout=config.get('dropout', 0.3)
                )
            else:
                self.model = BiLSTMAttentionClassifier(
                    vocab_size=vocab_size,
                    emb_dim=config.get('emb_dim', 32),
                    hidden_dim=config.get('hidden_dim', 32),
                    num_classes=config.get('num_classes', 2),
                    num_layers=config.get('num_layers', 1),
                    dropout=config.get('dropout', 0.1)
                )
        else:
            state_dict = model_info['model_state_dict']
            if 'layer_norm.weight' in state_dict or 'fc1.weight' in state_dict:
                self.model = HierarchicalLSTMClassifier(
                    vocab_size=vocab_size,
                    emb_dim=model_info.get('emb_dim', 64),
                    hidden_dim=model_info.get('hidden_dim', 128),
                    num_classes=model_info.get('num_classes', 2),
                    num_layers=model_info.get('num_layers', 2),
                    dropout=model_info.get('dropout', 0.3)
                )
            else:
                self.model = BiLSTMAttentionClassifier(
                    vocab_size=vocab_size,
                    emb_dim=model_info.get('emb_dim', 32),
                    hidden_dim=model_info.get('hidden_dim', 32),
                    num_classes=model_info.get('num_classes', 2),
                    num_layers=model_info.get('num_layers', 1),
                    dropout=model_info.get('dropout', 0.1)
                )
        
        self.model.load_state_dict(model_info['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        print(f"Model loaded successfully!")
        print(f"  Vocabulary size: {len(self.vocab)}")
        print(f"  Target class: {self.target_class}")
        print(f"  Max sequence length: {self.max_sequence_length}")
        print(f"  Device: {self.device}")
        if 'train_accuracy' in model_info and 'test_accuracy' in model_info:
            print(f"  Train accuracy: {model_info['train_accuracy']:.4f}")
            print(f"  Test accuracy: {model_info['test_accuracy']:.4f}")
    
    def _parse_sequence(self, itemsets):
        seq = []
        
        for i, itemset in enumerate(itemsets):
            if isinstance(itemset, dict):
                tokens = list(itemset.keys())
            elif isinstance(itemset, (list, tuple)):
                tokens = list(itemset)
            elif isinstance(itemset, set):
                tokens = list(itemset)
            else:
                tokens = [itemset]
            
            for tok in tokens:
                if tok in self.vocab:
                    seq.append(self.vocab[tok])
                else:
                    print(f"Warning: Unknown token '{tok}' not in vocabulary, skipping...")
                    continue
            
            if i < len(itemsets) - 1 and "<SEP>" in self.vocab:
                seq.append(self.vocab["<SEP>"])
            
            if self.max_sequence_length and len(seq) >= self.max_sequence_length:
                break
        
        if len(seq) == 0:
            raise ValueError("Sequence is empty after parsing. Check sequence format.")
        
        return torch.tensor(seq, dtype=torch.long)
    
    def classify(self, itemsets, return_probabilities=False):
        seq_tensor = self._parse_sequence(itemsets)
        seq_tensor = seq_tensor.unsqueeze(0).to(self.device)
        lengths = torch.tensor([seq_tensor.size(1)], dtype=torch.long)
        
        with torch.no_grad():
            outputs = self.model(seq_tensor, lengths)
            probabilities = F.softmax(outputs, dim=1).cpu().numpy()[0]
            prediction = int(torch.argmax(outputs, dim=1).cpu().item())
            confidence = float(probabilities[prediction])
        
        result = {
            'prediction': prediction,
            'confidence': confidence,
        }
        
        if return_probabilities:
            result['probabilities'] = {
                'not_malware': float(probabilities[0]),
                'malware': float(probabilities[1])
            }
        
        return result
    
    def classify_batch(self, itemsets_list, return_probabilities=False):
        seq_tensors = []
        lengths = []
        for itemsets in itemsets_list:
            seq_tensor = self._parse_sequence(itemsets)
            seq_tensors.append(seq_tensor)
            lengths.append(len(seq_tensor))
        
        padded = pad_sequence(seq_tensors, batch_first=True, padding_value=0)
        lengths_tensor = torch.tensor(lengths, dtype=torch.long)
        padded = padded.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(padded, lengths_tensor)
            probabilities = F.softmax(outputs, dim=1).cpu().numpy()
            predictions = torch.argmax(outputs, dim=1).cpu().numpy()
        
        results = []
        for i in range(len(itemsets_list)):
            pred = int(predictions[i])
            conf = float(probabilities[i][pred])
            
            result = {
                'prediction': pred,
                'confidence': conf,
            }
            
            if return_probabilities:
                result['probabilities'] = {
                    'not_malware': float(probabilities[i][0]),
                    'malware': float(probabilities[i][1])
                }
            
            results.append(result)
        
        return results
