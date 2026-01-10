import pandas as pd
import sys
import matplotlib.pyplot as plt
import numpy as np
import re
import math
import os
from collections import defaultdict

sys.path.insert(0, '/Users/danielbastos/Code/MCTSExtent')
from general.reader import read_data_kosarak
from general.utils import encode_items, encode_data, filter_empty_sequences, is_subsequence as utils_is_subsequence, extract_items

def token_to_movement(token):
    if token in ['EOS', 'EOD', 'STAY'] or token.startswith('tensor'):
        return (0, 0)
    
    parts = token.split('_')
    if len(parts) < 3:
        return (0, 0)
    
    direction = parts[0]
    try:
        abs_dx = int(parts[1])
        abs_dy = int(parts[2])
    except ValueError:
        return (0, 0)
    
    if direction == 'STAY':
        dx, dy = 0, 0
    elif direction == 'E':
        dx, dy = abs_dx, 0
    elif direction == 'NE':
        dx, dy = abs_dx, -abs_dy
    elif direction == 'N':
        dx, dy = 0, -abs_dy
    elif direction == 'NW':
        dx, dy = -abs_dx, -abs_dy
    elif direction == 'W':
        dx, dy = -abs_dx, 0
    elif direction == 'SW':
        dx, dy = -abs_dx, abs_dy
    elif direction == 'S':
        dx, dy = 0, abs_dy
    elif direction == 'SE':
        dx, dy = abs_dx, abs_dy
    else:
        dx, dy = 0, 0
    
    return (dx, dy)


def parse_pattern_string(pattern_str):
    tokens = re.findall(r"\{'([^']+)'\}", pattern_str)
    return tokens


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


def is_subsequence(pattern_tokens, sequence_tokens):
    pattern_itemsets = [{token} for token in pattern_tokens]
    sequence_itemsets = [{token} for token in sequence_tokens]
    
    i_a, i_b = 0, 0
    
    while i_a < len(pattern_itemsets) and i_b < len(sequence_itemsets):
        if pattern_itemsets[i_a].issubset(sequence_itemsets[i_b]):
            i_a += 1
        i_b += 1
    
    return i_a == len(pattern_itemsets)


def find_subsequence_matches(sequence_tokens, pattern_tokens):
    matches = []
    
    if not is_subsequence(pattern_tokens, sequence_tokens):
        return matches
    
    seq_len = len(sequence_tokens)
    pattern_len = len(pattern_tokens)
    
    if pattern_len == 0:
        return matches
    
    for start in range(seq_len):
        if sequence_tokens[start] == pattern_tokens[0]:
            seq_idx = start + 1
            pattern_idx = 1
            match_indices = [start]
            
            while seq_idx < seq_len and pattern_idx < pattern_len:
                if sequence_tokens[seq_idx] == pattern_tokens[pattern_idx]:
                    match_indices.append(seq_idx)
                    pattern_idx += 1
                seq_idx += 1
            
            if pattern_idx == pattern_len:
                matches.append(match_indices)
    
    return matches


def movements_to_strokes(movements, start_pos=(0, 0)):
    strokes = []
    current_stroke = []
    
    x, y = start_pos
    current_stroke.append((x, y))
    
    for dx, dy in movements:
        x += dx
        y += dy
        current_stroke.append((x, y))
    
    if current_stroke:
        strokes.append(current_stroke)
    
    return strokes


def parse_label(label):
    label_str = str(label)
    if 'tensor' in label_str:
        label_match = re.search(r'\[(\d+)\]', label_str)
        return int(label_match.group(1)) if label_match else 0
    else:
        return int(float(label_str))


def plot_matched_strokes(matches_data, pattern_tokens, max_plots=20, save_path='pattern_matches.png'):
    num_plots = min(len(matches_data), max_plots)
    if num_plots == 0:
        print("No matches found to plot")
        return
    
    if num_plots <= 20:
        num_cols = min(5, num_plots)
    elif num_plots <= 50:
        num_cols = 8
    else:
        num_cols = 10
    
    num_rows = (num_plots + num_cols - 1) // num_cols
    
    subplot_size = 3.0 if num_plots > 20 else 4.0
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(subplot_size*num_cols, subplot_size*num_rows))
    
    if num_plots == 1:
        axes = np.array([axes])
    if num_rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()
    
    match_colors = ['red', 'orange', 'yellow', 'lime', 'cyan', 'magenta']
    
    for plot_idx, match_data in enumerate(matches_data[:num_plots]):
        ax = axes[plot_idx]
        
        tokens = match_data['tokens']
        movements = match_data['movements']
        matches = match_data['matches']
        label = match_data['label']
        confidence = match_data['confidence']
        y_true = match_data.get('y_true', parse_label(label))
        y_pred = match_data.get('y_pred', 1 if confidence > 0.5 else 0)
        is_correct = match_data.get('is_correct', (y_true == y_pred))
        
        x, y = 0, 0
        coords = [(x, y)]
        token_to_coords = {}
        
        coord_idx = 0
        for token_idx, token in enumerate(tokens):
            coord_start = coord_idx
            dx, dy = token_to_movement(token)
            
            if dx != 0 or dy != 0:
                x += dx
                y += dy
                coord_idx += 1
                coords.append((x, y))
                coord_end = coord_idx
            else:
                coord_end = coord_idx
            
            token_to_coords[token_idx] = (coord_start, coord_end)
        
        linewidth_base = 2.0 if num_plots > 20 else 2.5
        marker_size = 6 if num_plots > 20 else 8
        title_fontsize = 7 if num_plots > 20 else 9
        label_fontsize = 6 if num_plots > 20 else 8
        
        if len(coords) > 1:
            xs, ys = zip(*coords)
            ax.plot(xs, ys, 'b-', linewidth=linewidth_base, alpha=1.0, label='Original stroke', zorder=1)
        
        if matches:
            matched_token_indices = matches[0]
            color = match_colors[0]
            
            for token_idx in matched_token_indices:
                coord_start_idx, coord_end_idx = token_to_coords.get(token_idx, (0, 0))
                
                if coord_start_idx < len(coords) and coord_end_idx < len(coords):
                    segment_coords = coords[coord_start_idx:coord_end_idx + 1]
                    if len(segment_coords) > 1:
                        mx, my = zip(*segment_coords)
                        highlight_width = 4 if num_plots > 20 else 5
                        ax.plot(mx, my, '-', linewidth=highlight_width, alpha=0.6, 
                               color=color, 
                               label='Match' if token_idx == matched_token_indices[0] else None,
                               zorder=2)
        
        if coords:
            ax.plot(coords[0][0], coords[0][1], 'go', markersize=marker_size, label='Start', zorder=10)
            ax.plot(coords[-1][0], coords[-1][1], 'ro', markersize=marker_size, label='End', zorder=10)
        
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        
        digit_true = 3 if y_true == 0 else 8
        digit_pred = 3 if y_pred == 0 else 8
        
        if y_true == 1 and y_pred == 1:
            category = 'TP'
        elif y_true == 0 and y_pred == 0:
            category = 'TN'
        elif y_true == 0 and y_pred == 1:
            category = 'FP'
        elif y_true == 1 and y_pred == 0:
            category = 'FN'
        else:
            category = '?'
        
        status_color = 'green' if is_correct else 'red'
        status_symbol = '✓' if is_correct else '✗'
        match_text = f'First match (of {len(matches)} total)' if len(matches) > 1 else f'{len(matches)} match'
        title_text = f'[{category}] True: {digit_true} | Pred: {digit_pred} {status_symbol}\nConf: {confidence:.3f} | Log Loss: {match_data.get("log_loss", 0):.4f}\n{match_text}'
        
        ax.set_title(title_text, fontsize=title_fontsize, 
                    color=status_color, fontweight='bold' if not is_correct else 'normal')
        ax.set_xlabel('X', fontsize=label_fontsize)
        ax.set_ylabel('Y', fontsize=label_fontsize)
        
        if plot_idx == 0:
            ax.legend(fontsize=6 if num_plots > 20 else 7, loc='upper right')
    
    for idx in range(num_plots, len(axes)):
        axes[idx].axis('off')
    
    plt.suptitle(f'Found {len(matches_data)} sequences containing pattern\n'
                f'Pattern: {" -> ".join(pattern_tokens[:5])}...', 
                fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Saved plot to: {save_path}")
    plt.close()


def find_pattern_in_dataset(csv_file, pattern_str):
    pattern_tokens = parse_pattern_string(pattern_str)
    print(f"Searching for pattern: {' -> '.join(pattern_tokens)}")
    print(f"Pattern length: {len(pattern_tokens)} tokens")
    print(f"Pattern tokens: {pattern_tokens}\n")
    
    dat_file = csv_file.replace('.csv', '.dat')
    if not os.path.exists(dat_file):
        dat_file = csv_file.replace('_filtered.csv', '_filtered_train.dat')
        if not os.path.exists(dat_file):
            dat_file = csv_file.replace('.csv', '_train.dat')
    
    if not os.path.exists(dat_file):
        raise FileNotFoundError(f"Could not find .dat file for {csv_file}. Tried: {dat_file}")
    
    print(f"Reading data from: {dat_file}")
    
    data = read_data_kosarak(dat_file)
    print(f"Read {len(data)} sequences from file")
    
    items = extract_items(data)
    items, items_to_encoding, encoding_to_items = encode_items(items)
    data = encode_data(data, items_to_encoding)
    print(f"Encoded data, vocabulary size: {len(items_to_encoding)}")
    
    data = filter_empty_sequences(data)
    print(f"After filtering: {len(data)} sequences")
    
    pattern_itemsets = []
    for token in pattern_tokens:
        if token in items_to_encoding:
            pattern_itemsets.append(frozenset([items_to_encoding[token]]))
        else:
            print(f"Warning: Token '{token}' not found in encoding vocabulary")
            return [], pattern_tokens
    encoded_pattern = tuple(pattern_itemsets)
    print(f"Pattern (encoded): {encoded_pattern}\n")
    
    support = 0
    matching_indices = []
    
    for i, sequence in enumerate(data):
        sequence_itemsets = sequence[1:]
        if utils_is_subsequence(encoded_pattern, sequence_itemsets):
            support += 1
            matching_indices.append(i)
    
    print(f"Support count: {support}")
    
    df = pd.read_csv(csv_file)
    print(f"Reading labels/confidence from: {csv_file}")
    
    matches_data = []
    
    for idx in matching_indices:
        if idx < len(df):
            row = df.iloc[idx]
            kosarak_seq = row['sequence']
            sequence_tokens = parse_kosarak_sequence(kosarak_seq)
            
            matches = find_subsequence_matches(sequence_tokens, pattern_tokens)
            movements = []
            for token in sequence_tokens:
                dx, dy = token_to_movement(token)
                if dx != 0 or dy != 0:
                    movements.append((dx, dy))
            
            matches_data.append({
                'index': idx,
                'sequence': kosarak_seq,
                'tokens': sequence_tokens,
                'movements': movements,
                'matches': matches,
                'label': row['y_true'],
                'confidence': row['confidence']
            })
    
    print(f"\nFound {len(matches_data)} sequences containing the pattern (support: {support})")
    
    unique_sequences = set()
    for match in matches_data:
        unique_sequences.add(match['sequence'])
    print(f"Verification: {len(unique_sequences)} unique sequences (should match above)")
    
    if len(matches_data) > 0:
        print(f"\nDebug: First 3 matched sequences:")
        for i, match in enumerate(matches_data[:3]):
            seq_preview = match['sequence']
            print(f"  {i+1}. {seq_preview}...")
            print(f"     Tokens: {match['tokens'][:15]}..." if len(match['tokens']) > 15 else f"     Tokens: {match['tokens']}")
    
    return matches_data, pattern_tokens


if __name__ == '__main__':
    pattern_str = sys.argv[1]
    idx = sys.argv[2]
    
    csv_file = 'data/emm_mnist_5_train.csv'
    
    print("="*70)
    print("PATTERN MATCHING IN FILTERED TRAIN DATASET")
    print("="*70)
    print()
    
    matches_data, pattern_tokens = find_pattern_in_dataset(csv_file, pattern_str)
    
    if matches_data:
        epsilon = 1e-15
        
        for match in matches_data:
            confidence = float(match['confidence'])
            y_true = parse_label(match['label'])
            y_pred = 1 if confidence > 0.5 else 0
            confidence_clamped = max(epsilon, min(1 - epsilon, confidence))
            
            if y_true == 1:
                log_loss = -math.log(confidence_clamped)
            else:
                log_loss = -math.log(1 - confidence_clamped)
            
            match['log_loss'] = log_loss
            match['y_true'] = y_true
            match['y_pred'] = y_pred
            match['is_correct'] = (y_true == y_pred)
        
        label_counts = defaultdict(int)
        matches_by_label = defaultdict(list)
        for match in matches_data:
            label = match['label']
            label_counts[label] += 1
            matches_by_label[label].append(match)
        
        true_positives = [] 
        true_negatives = []
        false_positives = []
        false_negatives = []
        
        for match in matches_data:
            if match['y_true'] == 1 and match['y_pred'] == 1:
                true_positives.append(match)
            elif match['y_true'] == 0 and match['y_pred'] == 0:
                true_negatives.append(match)
            elif match['y_true'] == 0 and match['y_pred'] == 1:
                false_positives.append(match)
            elif match['y_true'] == 1 and match['y_pred'] == 0:
                false_negatives.append(match)
        
        all_errors = [m for m in matches_data if not m['is_correct']]
        
        if all_errors:
            print(f"\nTotal errors: {len(all_errors)}")
            print(f"  False Positives (FP): {sum(1 for m in all_errors if m['y_true'] == 0 and m['y_pred'] == 1)}")
            print(f"  False Negatives (FN): {sum(1 for m in all_errors if m['y_true'] == 1 and m['y_pred'] == 0)}")
            
            total = len(matches_data)
            correct = total - len(all_errors)
            accuracy = correct / total if total > 0 else 0
            print(f"\nAccuracy: {accuracy:.4f} ({correct}/{total})")
            
            plot_matched_strokes(all_errors, pattern_tokens, max_plots=len(all_errors),
                               save_path=f'pattern_matches_errors_{idx}.png')
        else:
            print("\nNo errors found!")
        
        print("\n" + "="*70)
        print("PLOTTING ALL CORRECTLY CLASSIFIED EXAMPLES")
        print("="*70)
        
        correct_examples = [m for m in matches_data if m['is_correct']]
        
        correct_class_0 = [m for m in correct_examples if m['y_true'] == 0]
        correct_class_1 = [m for m in correct_examples if m['y_true'] == 1]
        
        correct_class_0.sort(key=lambda x: x['confidence'], reverse=False)
        correct_class_1.sort(key=lambda x: x['confidence'], reverse=True)
        
        all_correct = correct_class_0 + correct_class_1
        
        print(f"\nPlotting {len(all_correct)} correctly classified examples ({len(correct_class_0)} from class 0, {len(correct_class_1)} from class 1)...")
        if all_correct:
            plot_matched_strokes(all_correct, pattern_tokens, max_plots=len(all_correct),
                               save_path=f'pattern_matches_correct_{idx}.png')
        
        print("\n" + "="*70)
        print("PLOTTING BALANCED DATASET")
        print("="*70)
        
        balanced_samples = 5
        true_positives_sorted = sorted(true_positives, key=lambda x: x['log_loss'], reverse=False)
        true_negatives_sorted = sorted(true_negatives, key=lambda x: x['log_loss'], reverse=False)
        false_positives_sorted = sorted(false_positives, key=lambda x: x['log_loss'], reverse=True)
        false_negatives_sorted = sorted(false_negatives, key=lambda x: x['log_loss'], reverse=True)
        
        balanced_tp = true_positives_sorted[:min(balanced_samples, len(true_positives_sorted))]
        balanced_tn = true_negatives_sorted[:min(balanced_samples, len(true_negatives_sorted))]
        balanced_fp = false_positives_sorted[:min(balanced_samples, len(false_positives_sorted))]
        balanced_fn = false_negatives_sorted[:min(balanced_samples, len(false_negatives_sorted))]
        
        balanced_all = balanced_tp + balanced_tn + balanced_fp + balanced_fn
        
        print(f"\nBalanced dataset composition:")
        print(f"  TP (lowest log loss): {len(balanced_tp)}/{len(true_positives)} available")
        print(f"  TN (lowest log loss): {len(balanced_tn)}/{len(true_negatives)} available")
        print(f"  FP (highest log loss): {len(balanced_fp)}/{len(false_positives)} available")
        print(f"  FN (highest log loss): {len(balanced_fn)}/{len(false_negatives)} available")
        print(f"  Total: {len(balanced_all)} samples")
        
        if balanced_tp:
            print(f"\n  TP log loss range: {min(m['log_loss'] for m in balanced_tp):.6f} - {max(m['log_loss'] for m in balanced_tp):.6f}")
        if balanced_tn:
            print(f"  TN log loss range: {min(m['log_loss'] for m in balanced_tn):.6f} - {max(m['log_loss'] for m in balanced_tn):.6f}")
        if balanced_fp:
            print(f"  FP log loss range: {min(m['log_loss'] for m in balanced_fp):.6f} - {max(m['log_loss'] for m in balanced_fp):.6f}")
        if balanced_fn:
            print(f"  FN log loss range: {min(m['log_loss'] for m in balanced_fn):.6f} - {max(m['log_loss'] for m in balanced_fn):.6f}")
        
        if balanced_all:
            plot_matched_strokes(balanced_all, pattern_tokens, max_plots=len(balanced_all),
                               save_path=f'pattern_matches_balanced_{idx}.png')
            print(f"\nSaved balanced plot to: pattern_matches_balanced_{idx}.png")
        else:
            print("\nNo samples available for balanced plot!")
        
        log_losses = [m['log_loss'] for m in matches_data]
        
        print("\n" + "="*70)
        print("MATCH STATISTICS")
        print("="*70)
        
        print(f"\nLabel distribution (all matches):")
        for label, count in sorted(label_counts.items()):
            print(f"  Label {label}: {count} sequences ({100*count/len(matches_data):.1f}%)")
        
        print(f"\nTotal matches found: {sum(len(m['matches']) for m in matches_data)}")
        print(f"Average matches per sequence: {sum(len(m['matches']) for m in matches_data) / len(matches_data):.2f}")
        
        print(f"\nLog Loss Statistics:")
        print(f"  Min log loss: {min(log_losses):.6f}")
        print(f"  Max log loss: {max(log_losses):.6f}")
        print(f"  Mean log loss: {sum(log_losses)/len(log_losses):.6f}")
        print(f"  Median log loss: {sorted(log_losses)[len(log_losses)//2]:.6f}")
        
        log_losses_by_class = defaultdict(list)
        for match, log_loss in zip(matches_data, log_losses):
            y_true = parse_label(match['label'])
            log_losses_by_class[y_true].append(log_loss)
        
        print(f"\nLog Loss by Class:")
        for label in sorted(log_losses_by_class.keys()):
            class_losses = log_losses_by_class[label]
            print(f"  Label {label}: min={min(class_losses):.6f}, max={max(class_losses):.6f}, mean={sum(class_losses)/len(class_losses):.6f}")
        
    else:
        print("\nNo matches found!")

