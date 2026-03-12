import pandas as pd
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import re
import math
import os
from collections import defaultdict

sys.path.insert(0, '/Users/danielbastos/Code/sequential/MCTSExtent')
from general.reader import read_data_kosarak
from general.utils import encode_items, encode_data, filter_empty_sequences, is_subsequence as utils_is_subsequence, extract_items
import general.conf as conf

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

def find_subsequence_matches(sequence_tokens, pattern_tokens, items_to_encoding=None, max_gap=1):
    matches = []

    seq_len = len(sequence_tokens)
    pattern_len = len(pattern_tokens)

    if pattern_len == 0:
        return matches

    if seq_len < pattern_len:
        return matches

    if items_to_encoding:
        pattern_itemsets = [frozenset([items_to_encoding.get(token)]) for token in pattern_tokens if token in items_to_encoding]
        sequence_itemsets = []
        for token in sequence_tokens:
            if token in items_to_encoding:
                sequence_itemsets.append(frozenset([items_to_encoding[token]]))
            else:
                sequence_itemsets.append(frozenset())  # Unknown token, empty itemset
    else:
        pattern_itemsets = [frozenset([token]) for token in pattern_tokens]
        sequence_itemsets = [frozenset([token]) for token in sequence_tokens]

    if len(pattern_itemsets) != pattern_len:
        return matches

    if max_gap == 0:
        for start_idx in range(seq_len - pattern_len + 1):
            match = True
            for i in range(pattern_len):
                if not pattern_itemsets[i].issubset(sequence_itemsets[start_idx + i]):
                    match = False
                    break

            if match:
                match_indices = list(range(start_idx, start_idx + pattern_len))
                matches.append(match_indices)
    elif max_gap == -1:
        MAX_MATCHES = 50

        def find_first_match(pattern_idx, last_match_pos, current_match):
            if pattern_idx == pattern_len:
                matches.append(current_match[:])
                return True

            for j in range(last_match_pos + 1, seq_len):
                if pattern_itemsets[pattern_idx].issubset(sequence_itemsets[j]):
                    current_match.append(j)
                    if find_first_match(pattern_idx + 1, j, current_match):
                        return True
                    current_match.pop()
            return False

        for start_idx in range(seq_len):
            if len(matches) >= MAX_MATCHES:
                break
            if pattern_itemsets[0].issubset(sequence_itemsets[start_idx]):
                find_first_match(1, start_idx, [start_idx])
    else:
        MAX_MATCHES = 50

        def find_first_match(pattern_idx, last_match_pos, current_match):
            if pattern_idx == pattern_len:
                matches.append(current_match[:])
                return True

            start_search = last_match_pos + 1
            end_search = min(last_match_pos + max_gap + 2, seq_len)

            for j in range(start_search, end_search):
                if pattern_itemsets[pattern_idx].issubset(sequence_itemsets[j]):
                    current_match.append(j)
                    if find_first_match(pattern_idx + 1, j, current_match):
                        return True
                    current_match.pop()
            return False

        for start_idx in range(seq_len):
            if len(matches) >= MAX_MATCHES:
                break
            if pattern_itemsets[0].issubset(sequence_itemsets[start_idx]):
                find_first_match(1, start_idx, [start_idx])

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

        if matches and len(matches) > 0:
            matched_token_indices = matches[0]
            color = match_colors[0]

            # Highlight only the matched tokens individually (not the gaps between them)
            # With max_gap=2, there can be gaps between matched tokens, so we highlight each separately
            if len(matched_token_indices) > 0:
                highlight_width = 6 if num_plots > 20 else 7
                highlight_size = 10 if num_plots > 20 else 12
                label_added = False

                # Highlight each matched token individually
                for token_idx in matched_token_indices:
                    if token_idx in token_to_coords:
                        coord_start_idx, coord_end_idx = token_to_coords[token_idx]

                        # Make sure indices are valid
                        coord_start_idx = max(0, min(coord_start_idx, len(coords) - 1))
                        coord_end_idx = max(coord_start_idx, min(coord_end_idx, len(coords) - 1))

                        # Include the endpoint: slice from start to end+1 to include both endpoints
                        coord_end_idx_to_use = min(coord_end_idx + 1, len(coords))

                        if coord_start_idx < len(coords) and coord_end_idx_to_use > coord_start_idx:
                            # Get coordinates for this token's segment
                            segment_coords = coords[coord_start_idx:coord_end_idx_to_use]

                            if len(segment_coords) > 1:
                                # Token has movement - draw a line segment
                                mx, my = zip(*segment_coords)
                                ax.plot(mx, my, '-', linewidth=highlight_width, alpha=0.6,
                                       color=color,
                                       label='Match' if not label_added else '',
                                       zorder=2)
                                label_added = True
                            elif len(segment_coords) == 1:
                                # Single point match (no movement token) - draw a marker
                                ax.plot(segment_coords[0][0], segment_coords[0][1], 'o',
                                       markersize=highlight_size, alpha=0.6,
                                       color=color,
                                       label='Match' if not label_added else '',
                                       zorder=2)
                                label_added = True

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


def calculate_soft_error(confidence, y_true):
    """
    Calculate soft error: |y_true_binary - confidence|
    where y_true_binary is 1.0 if y_true == 1, 0.0 otherwise
    """
    y_true_binary = 1.0 if y_true == 1 else 0.0
    return abs(y_true_binary - confidence)


def plot_all_by_class(matches_data, pattern_tokens, save_path='pattern_matches_by_class.png'):
    """
    Plot all instances grouped by class (class 1 first, then class 0),
    ordered by soft error within each class.
    """
    if not matches_data:
        print("No matches found to plot")
        return

    # Calculate soft error for each match
    for match in matches_data:
        y_true = match.get('y_true', parse_label(match['label']))
        confidence = float(match['confidence'])
        match['soft_error'] = calculate_soft_error(confidence, y_true)

    # Group by true class label (y_true) - all instances of the same class together,
    # regardless of whether they're correctly classified or misclassified
    class_1_matches = [m for m in matches_data if m.get('y_true', parse_label(m['label'])) == 1]
    class_0_matches = [m for m in matches_data if m.get('y_true', parse_label(m['label'])) == 0]

    # Sort each class by soft error
    # Class 1: ascending (lowest soft error first)
    class_1_matches.sort(key=lambda x: x.get('soft_error', 0))
    # Class 0: descending (highest soft error first)
    class_0_matches.sort(key=lambda x: x.get('soft_error', 0), reverse=True)

    # Combine: class 1 first, then class 0
    all_matches_ordered = class_1_matches + class_0_matches

    num_plots = len(all_matches_ordered)
    if num_plots == 0:
        print("No matches found to plot")
        return

    # Determine grid layout
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

    for plot_idx, match_data in enumerate(all_matches_ordered):
        ax = axes[plot_idx]

        tokens = match_data['tokens']
        movements = match_data['movements']
        matches = match_data['matches']
        label = match_data['label']
        confidence = match_data['confidence']
        y_true = match_data.get('y_true', parse_label(label))
        y_pred = match_data.get('y_pred', 1 if confidence > 0.5 else 0)
        is_correct = match_data.get('is_correct', (y_true == y_pred))
        # Class-based background: class 1 = light red, class 0 = light blue
        bg_color = '#ffebeb' if y_true == 1 else '#ebf2ff'
        ax.set_facecolor(bg_color)

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

        if len(coords) > 1:
            xs, ys = zip(*coords)
            ax.plot(xs, ys, 'b-', linewidth=linewidth_base, alpha=1.0, label='Original stroke', zorder=1)

        if matches and len(matches) > 0:
            matched_token_indices = matches[0]
            color = match_colors[0]

            # Highlight only the matched tokens individually (not the gaps between them)
            if len(matched_token_indices) > 0:
                highlight_width = 6 if num_plots > 20 else 7
                highlight_size = 10 if num_plots > 20 else 12
                label_added = False

                # Highlight each matched token individually
                for token_idx in matched_token_indices:
                    if token_idx in token_to_coords:
                        coord_start_idx, coord_end_idx = token_to_coords[token_idx]

                        # Make sure indices are valid
                        coord_start_idx = max(0, min(coord_start_idx, len(coords) - 1))
                        coord_end_idx = max(coord_start_idx, min(coord_end_idx, len(coords) - 1))

                        # Include the endpoint: slice from start to end+1 to include both endpoints
                        coord_end_idx_to_use = min(coord_end_idx + 1, len(coords))

                        if coord_start_idx < len(coords) and coord_end_idx_to_use > coord_start_idx:
                            # Get coordinates for this token's segment
                            segment_coords = coords[coord_start_idx:coord_end_idx_to_use]

                            if len(segment_coords) > 1:
                                # Token has movement - draw a line segment
                                mx, my = zip(*segment_coords)
                                ax.plot(mx, my, '-', linewidth=highlight_width, alpha=0.6,
                                       color=color,
                                       label='Match' if not label_added else '',
                                       zorder=2)
                                label_added = True
                            elif len(segment_coords) == 1:
                                # Single point match (no movement token) - draw a marker
                                ax.plot(segment_coords[0][0], segment_coords[0][1], 'o',
                                       markersize=highlight_size, alpha=0.6,
                                       color=color,
                                       label='Match' if not label_added else '',
                                       zorder=2)
                                label_added = True

        if coords:
            ax.plot(coords[0][0], coords[0][1], 'go', markersize=marker_size, label='Start', zorder=10)
            ax.plot(coords[-1][0], coords[-1][1], 'ro', markersize=marker_size, label='End', zorder=10)

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.tick_params(axis='both', which='both', bottom=False, top=False, left=False, right=False, labelbottom=False, labelleft=False)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x0, x1 = min(xlim), max(xlim)
        y0, y1 = min(ylim), max(ylim)
        ax.add_patch(mpatches.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=bg_color, zorder=0))

        if plot_idx == 0:
            ax.legend(fontsize=6 if num_plots > 20 else 7, loc='upper right')

    for idx in range(num_plots, len(axes)):
        axes[idx].axis('off')

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
    missing_tokens = []
    for token in pattern_tokens:
        if token in items_to_encoding:
            pattern_itemsets.append(frozenset([items_to_encoding[token]]))
        else:
            missing_tokens.append(token)

    if missing_tokens:
        print(f"Warning: {len(missing_tokens)} token(s) not found in encoding vocabulary:")
        for token in missing_tokens:
            print(f"  - '{token}'")
        print(f"\nAvailable tokens (first 20): {list(items_to_encoding.keys())[:20]}")
        return [], pattern_tokens

    encoded_pattern = tuple(pattern_itemsets)
    print(f"Pattern (encoded): {encoded_pattern}\n")

    # Debug: Check a sample sequence to see its format
    if len(data) > 0:
        sample_sequence = data[0]
        sample_itemsets = sample_sequence[1:]
        print(f"Debug: Sample sequence (first 10 itemsets): {sample_itemsets[:10]}")
        print(f"Debug: Pattern length: {len(encoded_pattern)}, Sample sequence length: {len(sample_itemsets)}")
        if len(sample_itemsets) >= len(encoded_pattern):
            print(f"Debug: Checking if pattern matches at start of sample sequence...")
            match_at_start = True
            for j in range(min(len(encoded_pattern), 5)):  # Check first 5
                pattern_set = encoded_pattern[j]
                seq_set = sample_itemsets[j]
                matches = pattern_set.issubset(seq_set)
                print(f"  Position {j}: pattern={pattern_set}, sequence={seq_set}, match={matches}")
                if not matches:
                    match_at_start = False
            print(f"Debug: Pattern matches at start: {match_at_start}")

    # Read CSV - it should have the same number of rows as sequences in .dat file
    df = pd.read_csv(csv_file)
    print(f"Reading labels/confidence from: {csv_file}")
    print(f"CSV has {len(df)} rows, .dat file has {len(data)} sequences (after filtering)")

    # The .dat and CSV should have the same number of sequences
    if len(data) != len(df):
        print(f"WARNING: Mismatch between .dat file ({len(data)} sequences) and CSV file ({len(df)} rows)")
        print(f"This may cause incorrect support calculation. Using min({len(data)}, {len(df)}) = {min(len(data), len(df))} sequences.")

    # Calculate support for all sequences in data (should match CSV rows)
    support = 0
    matching_indices = []

    # Process sequences - if CSV has fewer rows, only process those
    # If .dat has fewer sequences, that's also handled
    num_sequences = min(len(data), len(df))
    max_gap = conf.MAX_GAP
    for i in range(num_sequences):
        sequence = data[i]
        if utils_is_subsequence(encoded_pattern, sequence, max_gap=max_gap):
            support += 1
            matching_indices.append(i)

    print(f"Support count: {support} (from {num_sequences} sequences)")

    matches_data = []

    for idx in matching_indices:
        if idx < len(df):
            row = df.iloc[idx]
            kosarak_seq = row['sequence']
            sequence_tokens = parse_kosarak_sequence(kosarak_seq)

            max_gap = conf.MAX_GAP
            matches = find_subsequence_matches(sequence_tokens, pattern_tokens, items_to_encoding=items_to_encoding, max_gap=max_gap)
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
        for i, match in enumerate(matches_data[:25]):
            seq_preview = match['sequence']
            #print(f"  {i+1}. {seq_preview}...")
            #print(f"     Tokens: {match['tokens'][:20]}..." if len(match['tokens']) > 20 else f"     Tokens: {match['tokens']}")

    return matches_data, pattern_tokens


def run_find_pattern_and_plot(csv_file, pattern_str, pattern_idx, output_dir, verbose=True):
    """
    Run find_pattern_in_dataset for the given pattern and save only the
    "PLOTTING ALL INSTANCES BY CLASS (ORDERED BY SOFT ERROR)" plot into output_dir.
    pattern_idx is used in filename (e.g. pattern_matches_by_class_1.png).
    """
    if verbose:
        print(f"[Find patterns] Pattern {pattern_idx}: {str(pattern_str)[:60]}...")
    matches_data, pattern_tokens = find_pattern_in_dataset(csv_file, pattern_str)

    if not matches_data:
        if verbose:
            print(f"  No matches found, skipping")
        return

    # Calculate soft_error for each match (needed for plot_all_by_class)
    for match in matches_data:
        confidence = float(match['confidence'])
        y_true = parse_label(match['label'])
        match['soft_error'] = calculate_soft_error(confidence, y_true)
        match['y_true'] = y_true

    os.makedirs(output_dir, exist_ok=True)
    idx_str = str(pattern_idx)

    # Only generate the "by class" plot
    plot_all_by_class(matches_data, pattern_tokens,
                      save_path=os.path.join(output_dir, f'pattern_matches_by_class_{idx_str}.png'))

    if verbose:
        print(f"  Saved pattern match plot to {output_dir}")


if __name__ == '__main__':
    pattern_str = sys.argv[1]
    idx = sys.argv[2]

    csv_file = 'data/emm_mnist_5_again2_train.csv'
    csv_file = 'data/emm_mnist_1_bad_train.csv'
    #csv_file = 'data/emm_mnist_6_9_new_train.csv'
#    csv_file = 'data/emm_mnist_3_and_8_train.csv'

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
            match['soft_error'] = calculate_soft_error(confidence, y_true)
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

            max_error_plots = min(100, len(all_errors))  # Limit to 100 plots max for performance
            plot_matched_strokes(all_errors, pattern_tokens, max_plots=max_error_plots,
                               save_path=f'pattern_matches_errors_{idx}.png')
            if len(all_errors) > max_error_plots:
                print(f"Note: Only plotting first {max_error_plots} of {len(all_errors)} errors for performance")
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

        max_correct_plots = min(100, len(all_correct))  # Limit to 100 plots max for performance
        print(f"\nPlotting {max_correct_plots} of {len(all_correct)} correctly classified examples ({len(correct_class_0)} from class 0, {len(correct_class_1)} from class 1)...")
        if all_correct:
            plot_matched_strokes(all_correct, pattern_tokens, max_plots=max_correct_plots,
                               save_path=f'pattern_matches_correct_{idx}.png')
            if len(all_correct) > max_correct_plots:
                print(f"Note: Only plotting first {max_correct_plots} of {len(all_correct)} correct examples for performance")

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
        print(f"  TP (lowest soft error): {len(balanced_tp)}/{len(true_positives)} available")
        print(f"  TN (lowest soft error): {len(balanced_tn)}/{len(true_negatives)} available")
        print(f"  FP (highest soft error): {len(balanced_fp)}/{len(false_positives)} available")
        print(f"  FN (highest soft error): {len(balanced_fn)}/{len(false_negatives)} available")
        print(f"  Total: {len(balanced_all)} samples")

        if balanced_tp:
            print(f"\n  TP soft error range: {min(m['soft_error'] for m in balanced_tp):.6f} - {max(m['soft_error'] for m in balanced_tp):.6f}")
        if balanced_tn:
            print(f"  TN soft error range: {min(m['soft_error'] for m in balanced_tn):.6f} - {max(m['soft_error'] for m in balanced_tn):.6f}")
        if balanced_fp:
            print(f"  FP soft error range: {min(m['soft_error'] for m in balanced_fp):.6f} - {max(m['soft_error'] for m in balanced_fp):.6f}")
        if balanced_fn:
            print(f"  FN soft error range: {min(m['soft_error'] for m in balanced_fn):.6f} - {max(m['soft_error'] for m in balanced_fn):.6f}")

        if balanced_all:
            plot_matched_strokes(balanced_all, pattern_tokens, max_plots=len(balanced_all),
                               save_path=f'pattern_matches_balanced_{idx}.png')
            print(f"\nSaved balanced plot to: pattern_matches_balanced_{idx}.png")
        else:
            print("\nNo samples available for balanced plot!")

        print("\n" + "="*70)
        print("PLOTTING ALL INSTANCES BY CLASS (ORDERED BY SOFT ERROR)")
        print("="*70)

        # Plot all instances grouped by class, ordered by soft error
        plot_all_by_class(matches_data, pattern_tokens, save_path=f'pattern_matches_by_class_{idx}.png')
        print(f"\nSaved by-class plot to: pattern_matches_by_class_{idx}.png")

        soft_errors = [m['soft_error'] for m in matches_data]

        print("\n" + "="*70)
        print("MATCH STATISTICS")
        print("="*70)

        print(f"\nLabel distribution (all matches):")
        for label, count in sorted(label_counts.items()):
            print(f"  Label {label}: {count} sequences ({100*count/len(matches_data):.1f}%)")

        print(f"\nTotal matches found: {sum(len(m['matches']) for m in matches_data)}")
        print(f"Average matches per sequence: {sum(len(m['matches']) for m in matches_data) / len(matches_data):.2f}")

        print(f"\nSoft Error Range:")
        print(f"  Min soft error: {min(soft_errors):.6f}")
        print(f"  Max soft error: {max(soft_errors):.6f}")
        print(f"  Mean soft error: {sum(soft_errors)/len(soft_errors):.6f}")
        print(f"  Median soft error: {sorted(soft_errors)[len(soft_errors)//2]:.6f}")

        soft_errors_by_class = defaultdict(list)
        for match in matches_data:
            y_true = parse_label(match['label'])
            soft_errors_by_class[y_true].append(match['soft_error'])

        print(f"\nSoft Error by Class:")
        for label in sorted(soft_errors_by_class.keys()):
            class_errors = soft_errors_by_class[label]
            print(f"  Label {label}: min={min(class_errors):.6f}, max={max(class_errors):.6f}, mean={sum(class_errors)/len(class_errors):.6f}")

    else:
        print("\nNo matches found!")

