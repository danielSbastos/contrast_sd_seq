#!/usr/bin/env python3
"""
Script to remove extra upper right loops (inverted V diagonals) from misclassified threes.
Removes:
1. Long diagonal from right to left (SW_X_Y patterns followed by upward-left movements)
2. Long diagonal from left to right (SE_X_Y patterns followed by upward-right movements)
"""

import os
import pandas as pd
import torch
import matplotlib.pyplot as plt
from mnist_lstm_new import load_trained_model, classify_single_instance


def token_to_movement(token):
    """Convert token to (dx, dy) movement."""
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


def is_inverted_v_diagonal(token):
    """Check if token is SE_X_Y or SW_X_Y with dx>=2 or dy>=2."""
    if not isinstance(token, str) or '_' not in token:
        return False
    parts = token.split('_')
    if len(parts) < 3:
        return False
    try:
        return parts[0] in ['SE', 'SW'] and (int(parts[1]) >= 2 or int(parts[2]) >= 2)
    except (ValueError, IndexError):
        return False


def movement_to_token(dx, dy):
    """Convert (dx, dy) movement to token string."""
    if dx == 0 and dy == 0:
        return 'STAY_0_0'
    elif dx > 0 and dy == 0:
        return f'E_{abs(dx)}_0'
    elif dx > 0 and dy < 0:
        return f'NE_{abs(dx)}_{abs(dy)}'
    elif dx == 0 and dy < 0:
        return f'N_0_{abs(dy)}'
    elif dx < 0 and dy < 0:
        return f'NW_{abs(dx)}_{abs(dy)}'
    elif dx < 0 and dy == 0:
        return f'W_{abs(dx)}_0'
    elif dx < 0 and dy > 0:
        return f'SW_{abs(dx)}_{abs(dy)}'
    elif dx == 0 and dy > 0:
        return f'S_0_{abs(dy)}'
    elif dx > 0 and dy > 0:
        return f'SE_{abs(dx)}_{abs(dy)}'
    else:
        return 'STAY_0_0'


def has_upper_loop(tokens):
    """Check if sequence has both SE and SW long diagonals."""
    if not tokens:
        return False
    diags = [t for t in tokens if is_inverted_v_diagonal(t)]
    return any(t.startswith('SE_') for t in diags) and any(t.startswith('SW_') for t in diags)


def remove_upper_loops(tokens):
    """Remove inverted V: keep before SE, keep SE, remove between SE and SW (including SW), connect end of SE to end of SW, keep after SW."""
    if not tokens or not has_upper_loop(tokens):
        return tokens
    
    se_idx = next((i for i, t in enumerate(tokens) if is_inverted_v_diagonal(t) and t.startswith('SE_')), None)
    sw_idx = next((i for i, t in enumerate(tokens) if is_inverted_v_diagonal(t) and t.startswith('SW_')), None)
    if se_idx is None or sw_idx is None:
        return tokens
    if se_idx > sw_idx:
        se_idx, sw_idx = sw_idx, se_idx
    
    def pos_after(idx):
        x, y = 0, 0
        for i in range(idx + 1):
            dx, dy = token_to_movement(tokens[i])
            x, y = x + dx, y + dy
        return (x, y)
    
    p_se, p_sw = pos_after(se_idx), pos_after(sw_idx)
    result = list(tokens[:se_idx + 1])
    connect = movement_to_token(p_sw[0] - p_se[0], p_sw[1] - p_se[1])
    if connect != 'STAY_0_0':
        result.append(connect)
    result.extend(tokens[sw_idx + 1:])
    return result


def sequence_to_kosarak_format(tokens, label=0):
    """Convert token list to Kosarak format string."""
    parts = [str(label)]
    for token in tokens:
        parts.append("-1")
        parts.append(token)
    parts.append("-2")
    return " ".join(parts)


def tokens_to_coordinates(tokens, start_pos=(0, 0)):
    """Convert tokens to coordinate list."""
    coords = [start_pos]
    x, y = start_pos
    
    for token in tokens:
        dx, dy = token_to_movement(token)
        if dx != 0 or dy != 0:
            x += dx
            y += dy
            coords.append((x, y))
    
    return coords


def plot_before_after(original_tokens, cleaned_tokens, original_pred=None, original_conf=None,
                      cleaned_pred=None, cleaned_conf=None, save_path=None, show_plot=False):
    """Plot original and cleaned sequences side by side."""
    def plot_seq(ax, tokens, title, color='b', pred=None, conf=None):
        coords = tokens_to_coordinates(tokens)
        if len(coords) < 2:
            return
        xs, ys = zip(*coords)
        ax.plot(xs, ys, f'{color}-', linewidth=2.5, alpha=0.8, zorder=1)
        ax.plot(coords[0][0], coords[0][1], 'go', markersize=10, zorder=10)
        ax.plot(coords[-1][0], coords[-1][1], 'ro', markersize=10, zorder=10)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X', fontsize=12)
        ax.set_ylabel('Y', fontsize=12)
        if pred is not None:
            digit = 3 if pred == 0 else 8
            title = f'{title} ({len(tokens)} tokens)\nPred: {digit} (Conf: {conf:.3f})'
        else:
            title = f'{title} ({len(tokens)} tokens)'
        ax.set_title(title, fontsize=14, fontweight='bold')
        margin = 2
        ax.set_xlim(min(xs) - margin, max(xs) + margin)
        ax.set_ylim(min(ys) - margin, max(ys) + margin)
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    if len(original_tokens) > 0:
        plot_seq(axes[0], original_tokens, 'Original', 'b', original_pred, original_conf)
    if len(cleaned_tokens) > 0:
        plot_seq(axes[1], cleaned_tokens, 'After Loop Removal', 'g', cleaned_pred, cleaned_conf)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved plot to: {save_path}")
    plt.close() if not show_plot else plt.show()


def main():
    # Misclassified sequences (all are 3s)
    misclassified_sequences = [
        ['E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'SE_3_4', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'STAY_0_0', 'SW_4_6', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'NW_1_1', 'NW_1_1', 'N_0_1', 'STAY_0_0']
,['W_1_0', 'W_1_0', 'S_0_1', 'S_0_1', 'SE_1_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'S_0_3', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'STAY_0_0']
,['N_0_1', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'SE_5_6', 'E_1_0', 'NE_1_1', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'STAY_0_0', 'SW_4_8', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'NW_1_1', 'STAY_0_0']
,['NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'SE_3_6', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'STAY_0_0', 'SW_4_8', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'N_0_1', 'W_1_0', 'N_0_1', 'N_0_1', 'STAY_0_0']
,['NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'SE_3_5', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'STAY_0_0', 'SW_4_7', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'S_0_1', 'S_0_1', 'SW_1_1', 'SW_1_1', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'S_0_4', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'STAY_0_0', 'SW_7_5', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'NW_1_1', 'STAY_0_0']
,['E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'S_0_1', 'E_1_0', 'SE_1_1', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'SE_1_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'NW_1_1', 'N_0_1', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'STAY_0_0', 'NW_2_4', 'NE_1_1', 'E_1_0', 'STAY_0_0']
,['S_0_1', 'S_0_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'NE_4_2', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0']
,['NE_1_1', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'SW_1_1', 'SW_1_1', 'W_1_0', 'SW_1_1', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'SE_3_6', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SW_5_8', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'S_0_7', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SE_4_1', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'N_0_1', 'NW_1_1', 'N_0_1', 'W_1_0', 'W_1_0', 'N_0_1', 'STAY_0_0']
,['NE_1_1', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'SW_1_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'SE_4_5', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'NE_1_1', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'NW_1_1', 'STAY_0_0', 'SW_6_8', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'SW_1_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SE_6_5', 'E_1_0', 'N_0_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'STAY_0_0', 'SW_2_6', 'SW_1_1', 'SW_1_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'NW_1_1', 'STAY_0_0']
,['E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'SE_5_6', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0', 'NE_7_2', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'N_0_1', 'W_1_0', 'STAY_0_0']
,['E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'SW_1_1', 'S_0_1', 'STAY_0_0', 'SE_4_5', 'E_1_0', 'NE_1_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'STAY_0_0', 'SW_3_8', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0']
,['NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'SE_1_1', 'SE_1_1', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SW_2_5', 'S_0_1', 'S_0_1', 'SE_1_1', 'S_0_1', 'E_1_0', 'SE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'N_0_1', 'NW_1_1', 'NW_1_1', 'STAY_0_0']
,['E_1_0', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'SW_1_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'S_0_1', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'SE_5_6', 'E_1_0', 'NE_1_1', 'NE_1_1', 'E_1_0', 'NE_1_1', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'N_0_1', 'STAY_0_0', 'SW_6_10', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'SE_1_5', 'S_0_1', 'W_1_0', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'N_0_1', 'E_1_0', 'STAY_0_0', 'W_2_0', 'STAY_0_0', 'SE_4_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'N_0_1', 'N_0_1', 'NW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SE_5_2', 'NE_1_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'N_0_1', 'STAY_0_0']
,['E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0', 'S_0_6', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'STAY_0_0', 'SW_9_6', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['N_0_1', 'N_0_1', 'N_0_1', 'E_1_0', 'N_0_1', 'NE_1_1', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'SE_1_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0', 'NE_3_5', 'NE_1_1', 'NE_1_1', 'NE_1_1', 'STAY_0_0']
,['E_1_0', 'E_1_0', 'NE_1_1', 'NE_1_1', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'SE_3_5', 'E_1_0', 'NE_1_1', 'NE_1_1', 'N_0_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'STAY_0_0', 'SW_5_8', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'N_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SW_1_5', 'S_0_1', 'S_0_1', 'SE_1_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'N_0_1', 'W_1_0', 'N_0_1', 'STAY_0_0']
,['NE_1_1', 'E_1_0', 'S_0_1', 'SE_1_1', 'S_0_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'S_0_1', 'S_0_1', 'E_1_0', 'S_0_1', 'E_1_0', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0', 'NE_1_8', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'STAY_0_0', 'NE_2_2', 'NE_1_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['N_0_1', 'NE_1_1', 'N_0_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'E_1_0', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'SW_1_1', 'SW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'N_0_1', 'W_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'STAY_0_0', 'NE_2_6', 'NE_1_1', 'STAY_0_0']
,['E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'NE_4_2', 'N_0_1', 'N_0_1', 'N_0_1', 'NE_1_1', 'E_1_0', 'STAY_0_0']
,['E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'SE_4_6', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'STAY_0_0', 'SW_5_8', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'SW_1_1', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'SE_4_5', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'STAY_0_0', 'SW_8_8', 'W_1_0', 'W_1_0', 'SW_1_1', 'STAY_0_0']
,['N_0_1', 'N_0_1', 'N_0_1', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'S_0_1', 'E_1_0', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'SW_1_1', 'W_1_0', 'STAY_0_0', 'NW_5_5', 'N_0_1', 'NE_1_1', 'STAY_0_0']
,['E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'W_1_0', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SE_2_6', 'E_1_0', 'E_1_0', 'NE_1_1', 'NE_1_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'STAY_0_0', 'SW_5_7', 'W_1_0', 'W_1_0', 'SW_1_1', 'NW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'NW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0']
,['N_0_1', 'N_0_1', 'NE_1_1', 'NE_1_1', 'NE_1_1', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'SE_1_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'E_1_0', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'S_0_1', 'STAY_0_0', 'NW_2_8', 'NE_1_1', 'NE_1_1', 'STAY_0_0']
,['E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'SE_1_1', 'E_1_0', 'SE_1_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'W_1_0', 'S_0_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'STAY_0_0', 'SE_4_6', 'E_1_0', 'NE_1_1', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'STAY_0_0', 'SW_4_7', 'W_1_0', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0']
 
    ]
      
    
    # Indices to process (all sequences 0-28)
    indices_to_process = list(range(len(misclassified_sequences)))  # Process all sequences
    
    print("REMOVING UPPER LOOPS FROM MISCLASSIFIED THREES")
    
    # Load model
    model = token_to_id = None
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model_path = 'data/lstm_mnist_model_5.pth'
    if os.path.exists(model_path):
        try:
            model, token_to_id, _, _ = load_trained_model(model_path, device=device)
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Warning: Could not load model: {e}")
    
    results = []
    
    plot_dir = 'experiments/results/mnist_upper_loops_plots'
    os.makedirs(plot_dir, exist_ok=True)
    
    for idx in indices_to_process:
        if idx >= len(misclassified_sequences):
            continue
        
        original_tokens = misclassified_sequences[idx]
        cleaned_tokens = remove_upper_loops(original_tokens)
        
        # Classify
        original_pred = original_conf = cleaned_pred = cleaned_conf = None
        if model is not None:
            try:
                original_pred, conf_dict, _ = classify_single_instance(model, token_to_id, original_tokens, device)
                original_conf = conf_dict[original_pred]
                if len(cleaned_tokens) > 0:
                    cleaned_pred, conf_dict, _ = classify_single_instance(model, token_to_id, cleaned_tokens, device)
                    cleaned_conf = conf_dict[cleaned_pred]
            except Exception as e:
                print(f"Error classifying sequence {idx + 1}: {e}")
        
        # Plot
        plot_path = os.path.join(plot_dir, f'sequence_{idx + 1}_before_after.png')
        plot_before_after(original_tokens, cleaned_tokens, original_pred, original_conf,
                         cleaned_pred, cleaned_conf, plot_path, show_plot=False)
        
        # Save results
        results.append({
            'sequence_idx': idx + 1,
            'original_sequence': sequence_to_kosarak_format(original_tokens, label=0),
            'cleaned_sequence': sequence_to_kosarak_format(cleaned_tokens, label=0) if cleaned_tokens else None,
            'original_length': len(original_tokens),
            'cleaned_length': len(cleaned_tokens),
            'tokens_removed': len(original_tokens) - len(cleaned_tokens),
            'original_prediction': original_pred,
            'original_confidence': original_conf,
            'cleaned_prediction': cleaned_pred,
            'cleaned_confidence': cleaned_conf,
        })
    
    # Save results
    output_file = 'experiments/results/mnist_upper_loops_removal.csv'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    pd.DataFrame(results).to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    print(f"Plots saved to: experiments/results/mnist_upper_loops_plots/")
    
    if model is not None:
        orig_correct = sum(1 for r in results if r['original_prediction'] == 0)
        clean_correct = sum(1 for r in results if r['cleaned_prediction'] == 0)
        print(f"Original correct: {orig_correct}/{len(results)}, Cleaned correct: {clean_correct}/{len(results)}")
        print(f"Improvement: {clean_correct - orig_correct} sequences")


if __name__ == '__main__':
    main()

