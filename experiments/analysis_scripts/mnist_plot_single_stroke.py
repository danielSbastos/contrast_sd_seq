#!/usr/bin/env python3
import matplotlib.pyplot as plt
import sys
import torch
import os

from mnist_lstm_new import load_trained_model, classify_single_instance


def invert_direction_token(token):
    """
    Invert a direction token (e.g., 'NE_1_1' -> 'SW_1_1', 'N_0_1' -> 'S_0_1').
    
    Direction mapping:
    - N <-> S
    - E <-> W
    - NE <-> SW
    - NW <-> SE
    - STAY -> STAY
    """
    if token in ['EOS', 'EOD'] or token.startswith('tensor'):
        return token
    
    parts = token.split('_')
    if len(parts) < 3:
        return token
    
    direction = parts[0]
    abs_dx = parts[1]
    abs_dy = parts[2]
    
    direction_map = {
        'N': 'S',
        'S': 'N',
        'E': 'W',
        'W': 'E',
        'NE': 'SW',
        'SW': 'NE',
        'NW': 'SE',
        'SE': 'NW',
        'STAY': 'STAY'
    }
    
    inverted_direction = direction_map.get(direction, direction)
    
    return f"{inverted_direction}_{abs_dx}_{abs_dy}"


def invert_sequence(tokens):
    return [invert_direction_token(token) for token in reversed(tokens)]


def rotate_180_sequence(tokens):
    return [invert_direction_token(token) for token in tokens]


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


def tokens_to_coordinates(tokens, start_pos=(0, 0)):
    coords = [start_pos]
    x, y = start_pos
    
    for token in tokens:
        dx, dy = token_to_movement(token)
        if dx != 0 or dy != 0:
            x += dx
            y += dy
            coords.append((x, y))
    
    return coords


def plot_stroke(tokens, title="Stroke", save_path=None, show_plot=True, plot_inverted=True, plot_rotated=True, 
                 model=None, token_to_id=None, device='cpu'):
    if isinstance(tokens, str):
        tokens = tokens.split()
    
    coords = tokens_to_coordinates(tokens)
    
    if len(coords) < 2:
        print("Warning: Not enough coordinates to plot (need at least 2 points)")
        return
    
    xs, ys = zip(*coords)
    
    original_pred = None
    original_conf = None
    inverted_pred = None
    inverted_conf = None
    rotated_pred = None
    rotated_conf = None
    inverted_tokens = None
    rotated_tokens = None
    
    if model is not None and token_to_id is not None and classify_single_instance is not None:
        try:
            original_pred, original_conf_dict, _ = classify_single_instance(model, token_to_id, tokens, device)
            original_conf = original_conf_dict[original_pred]
            
            if plot_inverted:
                inverted_tokens = invert_sequence(tokens)
                inverted_pred, inverted_conf_dict, _ = classify_single_instance(model, token_to_id, inverted_tokens, device)
                inverted_conf = inverted_conf_dict[inverted_pred]
            
            if plot_rotated:
                rotated_tokens = rotate_180_sequence(tokens)
                rotated_pred, rotated_conf_dict, _ = classify_single_instance(model, token_to_id, rotated_tokens, device)
                rotated_conf = rotated_conf_dict[rotated_pred]
        except Exception as e:
            print(f"Warning: Classification failed: {e}")
    
    if plot_inverted or plot_rotated:
        num_plots = 1 + (1 if plot_inverted else 0) + (1 if plot_rotated else 0)
        
        fig, axes = plt.subplots(1, num_plots, figsize=(10 * num_plots, 10))
        if num_plots == 1:
            axes = [axes]
        
        plot_idx = 0
        
        ax = axes[plot_idx]
        ax.plot(xs, ys, 'b-', linewidth=2.5, alpha=0.8, label='Original', zorder=1)
        ax.plot(coords[0][0], coords[0][1], 'go', markersize=10, label='Start', zorder=10)
        ax.plot(coords[-1][0], coords[-1][1], 'ro', markersize=10, label='End', zorder=10)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X', fontsize=12)
        ax.set_ylabel('Y', fontsize=12)
        
        if original_pred is not None:
            digit = 3 if original_pred == 0 else 8
            title_text = f'Original Stroke ({len(tokens)} tokens)\nPred: {digit} (Conf: {original_conf:.3f})'
        else:
            title_text = f'Original Stroke ({len(tokens)} tokens)'
        ax.set_title(title_text, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='upper right')
        margin = 2
        ax.set_xlim(min(xs) - margin, max(xs) + margin)
        ax.set_ylim(min(ys) - margin, max(ys) + margin)
        plot_idx += 1
        
        if plot_inverted:
            if inverted_tokens is None:
                inverted_tokens = invert_sequence(tokens)
            inverted_coords = tokens_to_coordinates(inverted_tokens)
            
            if len(inverted_coords) >= 2:
                ax = axes[plot_idx]
                inv_xs, inv_ys = zip(*inverted_coords)
                ax.plot(inv_xs, inv_ys, 'r-', linewidth=2.5, alpha=0.8, label='Inverted', zorder=1)
                ax.plot(inverted_coords[0][0], inverted_coords[0][1], 'go', markersize=10, label='Start', zorder=10)
                ax.plot(inverted_coords[-1][0], inverted_coords[-1][1], 'ro', markersize=10, label='End', zorder=10)
                ax.set_aspect('equal')
                ax.grid(True, alpha=0.3)
                ax.set_xlabel('X', fontsize=12)
                ax.set_ylabel('Y', fontsize=12)
                
                if inverted_pred is not None:
                    digit = 3 if inverted_pred == 0 else 8
                    title_text = f'Inverted Stroke ({len(inverted_tokens)} tokens)\nPred: {digit} (Conf: {inverted_conf:.3f})'
                else:
                    title_text = f'Inverted Stroke ({len(inverted_tokens)} tokens)'
                ax.set_title(title_text, fontsize=14, fontweight='bold')
                ax.legend(fontsize=10, loc='upper right')
                ax.set_xlim(min(inv_xs) - margin, max(inv_xs) + margin)
                ax.set_ylim(min(inv_ys) - margin, max(inv_ys) + margin)
                plot_idx += 1
        
        if plot_rotated:
            if rotated_tokens is None:
                rotated_tokens = rotate_180_sequence(tokens)
            rotated_coords = tokens_to_coordinates(rotated_tokens)
            
            if len(rotated_coords) >= 2:
                ax = axes[plot_idx]
                rot_xs, rot_ys = zip(*rotated_coords)
                ax.plot(rot_xs, rot_ys, 'g-', linewidth=2.5, alpha=0.8, label='Rotated 180°', zorder=1)
                ax.plot(rotated_coords[0][0], rotated_coords[0][1], 'go', markersize=10, label='Start', zorder=10)
                ax.plot(rotated_coords[-1][0], rotated_coords[-1][1], 'ro', markersize=10, label='End', zorder=10)
                ax.set_aspect('equal')
                ax.grid(True, alpha=0.3)
                ax.set_xlabel('X', fontsize=12)
                ax.set_ylabel('Y', fontsize=12)
                
                if rotated_pred is not None:
                    digit = 3 if rotated_pred == 0 else 8
                    title_text = f'Rotated 180° ({len(rotated_tokens)} tokens)\nPred: {digit} (Conf: {rotated_conf:.3f})'
                else:
                    title_text = f'Rotated 180° ({len(rotated_tokens)} tokens)'
                ax.set_title(title_text, fontsize=14, fontweight='bold')
                ax.legend(fontsize=10, loc='upper right')
                ax.set_xlim(min(rot_xs) - margin, max(rot_xs) + margin)
                ax.set_ylim(min(rot_ys) - margin, max(rot_ys) + margin)
        
        plt.suptitle(title, fontsize=16, fontweight='bold', y=1.02)
    else:
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.plot(xs, ys, 'b-', linewidth=2.5, alpha=0.8, label='Stroke', zorder=1)
        ax.plot(coords[0][0], coords[0][1], 'go', markersize=10, label='Start', zorder=10)
        ax.plot(coords[-1][0], coords[-1][1], 'ro', markersize=10, label='End', zorder=10)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X', fontsize=12)
        ax.set_ylabel('Y', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='upper right')
        margin = 2
        ax.set_xlim(min(xs) - margin, max(xs) + margin)
        ax.set_ylim(min(ys) - margin, max(ys) + margin)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved plot to: {save_path}")
    
    # Show plot
    if show_plot:
        plt.show()
    else:
        plt.close()


if __name__ == '__main__':
    default_sequence = [
        ['S_0_1', 'S_0_1', 'S_0_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'W_1_0', 'NW_1_1', 'NW_1_1', 'W_1_0', 'N_0_1', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'STAY_0_0', 'SW_5_3', 'STAY_0_0', 'W_2_0', 'S_0_1', 'W_1_0', 'N_0_1', 'W_1_0', 'STAY_0_0' ],
        ['S_0_1', 'S_0_1', 'SE_1_1', 'S_0_1', 'E_1_0', 'E_1_0', 'SE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'NE_1_1', 'NW_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'NE_1_1', 'N_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'SW_1_1', 'W_1_0', 'SW_1_1', 'SW_1_1', 'S_0_1', 'STAY_0_0', 'S_0_4', 'E_1_0', 'E_1_0', 'STAY_0_0', 'W_3_0', 'SW_1_1', 'STAY_0_0', ],
        ['S_0_1', 'S_0_1', 'S_0_1', 'E_1_0', 'E_1_0', 'SE_1_1', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SW_4_6', 'W_1_0', 'W_1_0', 'SW_1_1', 'STAY_0_0', ],
        ['SE_1_1', 'NE_1_1', 'E_1_0', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'N_0_1', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'NE_1_1', 'NW_1_1', 'NW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'STAY_0_0', ],
        [ 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'NW_1_1', 'NW_1_1', 'N_0_1', 'N_0_1', 'NE_1_1', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'W_1_0', 'W_1_0', 'S_0_1', 'STAY_0_0', ],

        [ 'NE_1_1', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'N_0_1', 'W_1_0', 'N_0_1', 'W_1_0', 'NW_1_1', 'SW_1_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'STAY_0_0', 'NE_7_1', 'E_1_0', 'SE_1_1', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0', ],
        [ 'N_0_1', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'NE_1_1', 'N_0_1', 'E_1_0', 'N_0_1', 'N_0_1', 'NW_1_1', 'NW_1_1', 'W_1_0', 'N_0_1', 'NW_1_1', 'N_0_1', 'N_0_1', 'NE_1_1', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'SE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'S_0_1', 'SE_1_1', 'SE_1_1', 'S_0_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'SW_1_1', 'W_1_0', 'S_0_1', 'W_1_0', 'SW_1_1', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0', 'SE_3_1', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'SW_1_1', 'SW_1_1', 'W_1_0', 'W_1_0', 'STAY_0_0', ],
        [ 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'W_1_0', 'NW_1_1', 'N_0_1', 'N_0_1', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'W_1_0', 'STAY_0_0', 'SW_2_4', 'SW_1_1', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'STAY_0_0', ],
        [ 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'NE_1_1', 'N_0_1', 'NW_1_1', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'W_1_0', 'S_0_1', 'S_0_1', 'S_0_1', 'S_0_1', 'E_1_0', 'S_0_1', 'STAY_0_0', 'S_0_2', 'SW_1_1', 'W_1_0', 'SW_1_1', 'SW_1_1', 'W_1_0', 'SW_1_1', 'S_0_1', 'STAY_0_0', ],
        [ 'NE_1_1', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'N_0_1', 'N_0_1', 'E_1_0', 'N_0_1', 'E_1_0', 'NE_1_1', 'E_1_0', 'NE_1_1', 'NE_1_1', 'N_0_1', 'N_0_1', 'NW_1_1', 'N_0_1', 'W_1_0', 'N_0_1', 'W_1_0', 'NW_1_1', 'SW_1_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'S_0_1', 'SW_1_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'SE_1_1', 'E_1_0', 'E_1_0', 'STAY_0_0', 'NE_7_1', 'E_1_0', 'SE_1_1', 'S_0_1', 'E_1_0', 'S_0_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'SW_1_1', 'S_0_1', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'S_0_1', 'W_1_0', 'W_1_0', 'W_1_0', 'STAY_0_0', ],
    ]

    if len(sys.argv) > 1:
        tokens_str = sys.argv[1]
        tokens = tokens_str.split()
        title = f"Stroke ({len(tokens)} tokens)"
    else:
        tokens = default_sequence
        title = f"Stroke Example ({len(tokens)} tokens)"
    
    for tokens in default_sequence:
        save_path = sys.argv[2] if len(sys.argv) > 2 else 'single_stroke.png'
        
        print(f"Plotting stroke with {len(tokens)} tokens...")
        print(f"Original - First 5 tokens: {tokens[:10]}")
        print(f"Original - Last 5 tokens: {tokens[-10:]}")
        
        inverted_tokens = invert_sequence(tokens)
        print(f"\nInverted - First 5 tokens: {inverted_tokens[:10]}")
        print(f"Inverted - Last 5 tokens: {inverted_tokens[-10:]}")
        
        rotated_tokens = rotate_180_sequence(tokens)
        print(f"\nRotated 180° - First 5 tokens: {rotated_tokens[:10]}")
        print(f"Rotated 180° - Last 5 tokens: {rotated_tokens[-10:]}")
        
        model = None
        token_to_id = None
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        if load_trained_model is not None:
            model_path = 'data/lstm_mnist_model_5.pth'
            if os.path.exists(model_path):
                print(f"\nLoading model from {model_path}...")
                try:
                    model, token_to_id, id_to_token, checkpoint = load_trained_model(model_path, device=device)
                    print("Model loaded successfully! Classifying strokes...")
                except Exception as e:
                    print(f"Warning: Could not load model: {e}")
                    print("Plotting without classification.")
            else:
                print(f"\nModel file {model_path} not found. Plotting without classification.")
        else:
            print("\nModel loading functions not available. Plotting without classification.")
        
        plot_stroke(tokens, title=title, save_path=save_path, show_plot=True, plot_inverted=True, plot_rotated=True,
                    model=model, token_to_id=token_to_id, device=device)

