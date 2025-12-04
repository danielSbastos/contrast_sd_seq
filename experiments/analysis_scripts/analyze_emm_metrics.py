import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, classification_report
import os

def analyze_experiment(name, train_file, test_file):
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)
    
    train_predictions = (train_df['confidence'].values >= 0.5).astype(int)
    train_labels = train_df['y_true'].values
    
    test_predictions = (test_df['confidence'].values >= 0.5).astype(int)
    test_labels = test_df['y_true'].values
    
    print("\n" + "="*30)
    print(f"TRAIN SET PERFORMANCE METRICS - {name}")
    print("="*30)
    
    train_accuracy = accuracy_score(train_labels, train_predictions)
    print(f"Train Accuracy: {train_accuracy:.4f}\n")
    
    target_names = ['Other', '1']
    print("Train Classification report (binary):")
    print(classification_report(train_labels, train_predictions, target_names=target_names))
    
    print(f"\nTrain Class distribution:")
    print(f"  Class 0 (others): {sum(1 for l in train_labels if l == 0)} samples")
    print(f"  Class 1 (1): {sum(1 for l in train_labels if l == 1)} samples")
    
    print("\n" + "="*30)
    print(f"TEST SET PERFORMANCE METRICS - {name}")
    print("="*30)
    
    test_accuracy = accuracy_score(test_labels, test_predictions)
    print(f"Test Accuracy: {test_accuracy:.4f}\n")
    
    print("Test Classification report (binary):")
    print(classification_report(test_labels, test_predictions, target_names=target_names))
    
    print(f"\nTest Class distribution:")
    print(f"  Class 0 (others): {sum(1 for l in test_labels if l == 0)} samples")
    print(f"  Class 1 (1): {sum(1 for l in test_labels if l == 1)} samples")
    
    return {
        'name': name,
        'train_accuracy': train_accuracy,
        'test_accuracy': test_accuracy,
        'train_size': len(train_df),
        'test_size': len(test_df)
    }

def main():
    experiments = [
        {
            'name': 'emm_twitter-processed',
            'train_file': 'data/emm_twitter-processed_train.csv',
            'test_file': 'data/emm_twitter-processed_test.csv'
        },
        {
            'name': 'emm_student_sequences_plus',
            'train_file': 'data/emm_student_sequences_plus_train.csv',
            'test_file': 'data/emm_student_sequences_plus_test.csv'
        },
        {
            'name': 'emm_dynamic_api_call_sequence_per_malware_100_0_306',
            'train_file': 'data/emm_dynamic_api_call_sequence_per_malware_100_0_306_train.csv',
            'test_file': 'data/emm_dynamic_api_call_sequence_per_malware_100_0_306_test.csv'
        }
    ]
    
    for exp in experiments:
        analyze_experiment(exp['name'], exp['train_file'], exp['test_file'])
        print("\n")

if __name__ == "__main__":
    main()

