import re
import numpy as np
import pandas as pd
import os
import math
import datetime
from datetime import timezone
import sys
import random
import copy
import math
import select as select_module
import threading
import heapq
import time

from sklearn.metrics import accuracy_score

import general.conf as conf

from general.reader import read_data_kosarak
from general.utils import parse_expected_patterns, sequence_mutable_to_immutable, compute_quality, \
    sequence_immutable_to_mutable, calculate_log_losses, filter_empty_sequences, encode_items, \
    encode_data, print_results_decode, extract_items, decode_sequences, get_idx_from_cumulative_prop, \
    calculate_item_log_losses, encode_expected_patterns

from general.priorityset import PrioritySet
from mctsextent.node import Node
from seqscout.global_var import Model
sys.setrecursionlimit(15000)


def best_child(node, node_weights=None):
    if node.is_dead_end() and len(node.parents) == 0:
        # Root is dead-end - should not happen normally
        return 'finished'

    best_node = None
    max_score = -float("inf")
    dead_end_candidates = []

    mgr = None
    has_pattern_weights = False
    has_attribute_weights = False
    try:
        from auditlens_weights import get_weight_manager
        mgr = get_weight_manager()
        has_pattern_weights = bool(mgr.pattern_weights)
        has_attribute_weights = bool(mgr.attribute_weights)
    except Exception:
        pass

    # Extract quality and support algorithm weights
    global algorithm_weights
    w_quality = algorithm_weights.get("quality", 1.0) if 'algorithm_weights' in globals() else 1.0
    w_support = algorithm_weights.get("support", 0.0) if 'algorithm_weights' in globals() else 0.0

    # Fallback to global if node_weights parameter is None
    effective_node_weights = node_weights if node_weights is not None else current_node_weights

    for child in node.children:
        if child.is_dead_end():
            dead_end_candidates.append(child)
            continue

        # Calculate child quality factor and support factor
        quality_factor = w_quality
        support_factor = 1.0
        if w_support != 0.0:
            try:
                total_data = Model.get_data()
                if total_data and child.extend:
                    support_ratio = len(child.extend) / len(total_data)
                    support_factor = support_ratio ** w_support
            except Exception:
                pass

        # Apply weights to normalized quality
        child_quality = child.get_normalized_quality() * quality_factor * support_factor
        a = child_quality / child.number_visits
        uct_factor = getattr(conf, "UCT_FACTOR", 0.5)
        b = uct_factor * math.sqrt(2 * math.log(node.number_visits) / child.number_visits)
        current_ucb = a + b
        
        # Apply weights dynamically (node weight, pattern weight, attribute weight)
        weight = 1.0
        if effective_node_weights and id(child) in effective_node_weights:
            weight *= effective_node_weights[id(child)]
            
        if mgr is not None:
            try:
                # Pattern-based weights (only computed and checked if pattern_weights is not empty)
                if has_pattern_weights and child.intent and current_encoding_to_items:
                    if not hasattr(child, '_pattern_str'):
                        from general.utils import decode_sequence
                        decoded_seq = decode_sequence(child.intent, current_encoding_to_items)
                        child._pattern_str = " -> ".join(["(" + ",".join(map(str, s)) + ")" for s in decoded_seq])
                    
                    if child._pattern_str in mgr.pattern_weights:
                        weight *= mgr.pattern_weights[child._pattern_str]
                
                # Attribute-based weights (only checked if attribute_weights is not empty)
                if has_attribute_weights:
                    for attr, op, threshold, attr_weight in mgr.parsed_attribute_weights:
                        val = mgr._get_attribute_value(child, attr)
                        if op == '>':
                            if val > threshold:
                                weight *= attr_weight
                        elif op == '<':
                            if val < threshold:
                                weight *= attr_weight
                        elif op == '=':
                            if abs(val - threshold) < 1e-5:
                                weight *= attr_weight
            except Exception:
                pass

        current_ucb = current_ucb * weight

        if current_ucb > max_score:
            max_score = current_ucb
            best_node = child

    # If no non-dead children found, return a dead-end child for re-exploration
    # This prevents premature termination when search space becomes exhausted
    if best_node is None:
        if dead_end_candidates:
            # Return one of the dead-end children for continued exploration
            # Select the one with lowest visit count to ensure continued search
            best_node = min(dead_end_candidates, key=lambda n: n.number_visits)
            return best_node
        
        if len(node.parents) == 0:
            # Root has no non-dead children and no dead-end children
            return 'finished'
        return node.parents[0]

    return best_node


def select(node, node_weights=None):
    while node != 'finished':
        if len(node.children) == 0:
            return (node, False)  # exploitation: descended to leaf via best_child
        if (random.random() < 0.5) and (not node.is_fully_expanded()):
            return (node, True)   # exploration: chose to expand this node
        node = best_child(node, node_weights=node_weights)
    return ('finished', None)


computed_rollouts = {}
current_node_weights = {}  # Global weights dict: maps node id -> weight
algorithm_weights = {"quality": 1.0, "support": 0.0}  # Global algorithm weights dict
current_encoding_to_items = {}  # Global item encoding map


def roll_out(node, item_log_losses=None):
    """
    Fast rollout: Remove a contiguous chunk from the sequence to generate a smaller
    candidate subsequence. This includes removing items from the start, end, middle,
    or keeping a smaller random window for broader exploration.
    """
    sequence = copy.deepcopy(node.intent)
    sequence = sequence_immutable_to_mutable(sequence)

    if not sequence or len(sequence) <= 1:
        return sequence, 1

    # How many itemsets to remove (up to 80% of length)
    num_to_remove = random.randint(
        1,
        max(1, int(len(sequence) * 0.8))
    )

    choice = random.randint(0, 3)
    if choice == 0:
        sequence = sequence[num_to_remove:]
    elif choice == 1:
        sequence = sequence[:-num_to_remove]
    elif choice == 2:
        if len(sequence) > num_to_remove:
            start = random.randint(0, len(sequence) - num_to_remove)
            sequence = sequence[:start] + sequence[start + num_to_remove:]
        else:
            sequence = sequence[:1]
    else:
        keep_len = random.randint(1, max(1, len(sequence) // 3))
        start = random.randint(0, len(sequence) - keep_len)
        sequence = sequence[start:start + keep_len]

    if not sequence:
        return [], 0

    immutable_sequence = tuple(sequence_mutable_to_immutable(sequence))
    reward, _, _, _, _ = compute_quality(immutable_sequence)

    return sequence, reward

def update(node, reward):
    update_nodes = {node}
    parents_seen = set()

    while len(update_nodes) != 0:
        node = random.sample(list(update_nodes), 1)[0]
        parents_seen.add(node)
        for parent in node.parents:
            if parent not in parents_seen:
                update_nodes.add(parent)

        node.update(reward)
        update_nodes.remove(node)

def prepare_mcts_from_files(filename, max_gap=conf.MAX_GAP, support_penalty=conf.SUPPORT_PENALTY,
                            sigmoid_offset=conf.SIGMOID_OFFSET, synth_patterns_path=None):
    conf.MAX_GAP = max_gap
    conf.SUPPORT_PENALTY = support_penalty
    conf.SIGMOID_OFFSET = sigmoid_offset
    path = f"data/{filename}_train.dat"
    target_path = f"data/{filename}_train.csv"

    if not os.path.isfile(path):
        path = f"data/{filename}.dat"
        target_path = f"data/{filename}.csv"

    data = read_data_kosarak(path)
    target_file = pd.read_csv(target_path)[['y_true', 'confidence']]
    target_class = target_file.values

    log_losses_file = f"data/log_losses/log_losses_{filename}.txt"
    try:
        log_losses = np.loadtxt(log_losses_file)
    except FileNotFoundError:
        log_losses = calculate_log_losses(target_class)
        np.savetxt(log_losses_file, log_losses)

    # Count raw item frequencies across sequences for Support Pre-Filtering
    from collections import Counter
    item_counts = Counter()
    for sequence in data:
        seen = set()
        for itemset in sequence[1:]:
            for item in itemset:
                seen.add(item)
        for item in seen:
            item_counts[item] += 1

    # Keep only items meeting baseline minimum support threshold
    min_support = getattr(conf, 'MIN_SUPPORT', 10)
    items = set()
    for sequence in data:
        for itemset in sequence[1:]:
            for item in itemset:
                if item_counts[item] >= min_support:
                    items.add(item)
    items = sorted(list(items))
    items, items_to_encoding, encoding_to_items = encode_items(items)

    # Determine contrast log-loss threshold
    contrast_threshold = getattr(conf, 'LOG_LOSS_THRESHOLD', 0)
    if contrast_threshold == 0:
        contrast_threshold = max(0.01, np.percentile(log_losses, 10)) if len(log_losses) > 0 else 0.0
    
    # Update conf so it's available to all nodes during search
    conf.LOG_LOSS_THRESHOLD = contrast_threshold

    # Encode and filter sequences in parallel
    encoded_data = []
    non_empty_indices = []
    for i, line in enumerate(data):
        if log_losses[i] < contrast_threshold:
            continue

        encoded_line = [line[0]] # keep class label
        for itemset in line[1:]:
            encoded_itemset = {items_to_encoding[item] for item in itemset if item in items_to_encoding}
            if len(encoded_itemset) > 0:
                encoded_line.append(encoded_itemset)

        if len(encoded_line) > 1:
            encoded_data.append(encoded_line)
            non_empty_indices.append(i)

    data = encoded_data
    target_class = target_class[non_empty_indices]
    log_losses = log_losses[non_empty_indices]

    print(f"Loaded log losses for {len(log_losses)} filtered sequences")

    Model.set_labels(list(target_file['y_true'].unique()))
    positive_class_scores = target_file['confidence']
    y_true = target_file['y_true'].tolist()

    unique_labels = sorted(target_file['y_true'].unique())
    positive_class = unique_labels[1] if len(unique_labels) == 2 else unique_labels[-1]
    negative_class = unique_labels[0]

    predictions = (positive_class_scores > 0.5).map(lambda x: positive_class if x else negative_class).tolist()
    accuracy = accuracy_score(y_true, predictions)

    Model.set_accuracy(accuracy)
    Model.set_positive_class(positive_class)
    Model.set_target_class(target_class)

    prediction_errors = []
    for y, confidence in target_class:
        if y == positive_class:
            p = confidence
        else:
            p = 1.0 - confidence
        prediction_error = abs(1.0 - p)
        prediction_errors.append(prediction_error)

    prediction_errors = np.array(prediction_errors)
    global_mean_error = np.mean(prediction_errors)
    global_std_error = np.std(prediction_errors)

    Model.set_global_mean_error(global_mean_error)
    Model.set_global_std_error(global_std_error)
    Model.set_global_errors(prediction_errors)
    y_trues = target_class[:, 0]
    confidences = target_class[:, 1]
    predictions_arr = (confidences > 0.5).astype(int)
    predictions_mapped = np.where(predictions_arr == 1, positive_class, negative_class)
    hard_errors = (y_trues != predictions_mapped).astype(float)
    soft_errors = prediction_errors
    global_hard_error = hard_errors.mean()
    Model.set_hard_errors(hard_errors)
    Model.set_soft_errors(soft_errors)
    Model.set_global_hard_error(global_hard_error)
    print(f"\n=== Precomputed Metrics ===")
    print(f"Global accuracy: {accuracy:.4f}")
    print(f"Global hard error rate: {global_hard_error:.4f}")
    print(f"Global soft mean error: {global_mean_error:.4f}")

    base_path, ext = os.path.splitext(path)
    validation_data_path = base_path + "_test" + ext

    base_target_path, ext = os.path.splitext(target_path)
    validation_target_path = base_target_path + "_test" + ext

    if not os.path.isfile(validation_target_path):
        validation_target_path = target_path
        validation_data_path = path

    noise = None
    seq_lenght = None
    if synth_patterns_path:
        _expected_patterns = parse_expected_patterns(synth_patterns_path)
        _expected_patterns = encode_expected_patterns(_expected_patterns, items_to_encoding)
        noise = filename.split("__")[2].split('_')[1]
        seq_lenght = filename.split("__")[1][2:]

    extra = {
        'validation_data_path': validation_data_path,
        'validation_target_path': validation_target_path,
        'train_data_path': path,
        'train_target_path': target_path,
        'items_to_encoding': items_to_encoding,
        'global_accuracy': accuracy,
        'avg_sequence_lenght': None,
        'noise': noise,
        'dataset_name': filename,
        'avg_sequence_lenght': seq_lenght,
        'max_gap': max_gap or -1,
        'support_penalty': support_penalty,
        'sigmoid_offset': sigmoid_offset
    }

    global current_encoding_to_items
    current_encoding_to_items = encoding_to_items
    Model.set_log_losses(log_losses)
    return data, target_class, log_losses, extra, encoding_to_items


def get_patterns(filename='', top_k=5, time_budget=10, theta=0.1, iterations_limit=2 ** 30, synth_patterns_path=None, max_length=3, max_gap=conf.MAX_GAP, support_penalty=conf.SUPPORT_PENALTY, sigmoid_offset=conf.SIGMOID_OFFSET):
    data, target_class, log_losses, extra, encoding_to_items = prepare_mcts_from_files(
        filename, max_gap=max_gap, support_penalty=support_penalty, sigmoid_offset=sigmoid_offset,
        synth_patterns_path=synth_patterns_path)

    results = launch_mcts(data, target_class, log_losses, top_k=top_k, time_budget=time_budget, theta=theta,
                         iterations_limit=iterations_limit,
                         extra=extra, max_length=max_length)

    print_results_decode(results, encoding_to_items)

    return decode_sequences(results, encoding_to_items)

# Global tracking for dynamic pruning relaxation
_min_support_override = None  # Override MIN_SUPPORT when search space exhausted

def set_dynamic_min_support(override_value):
    """Override MIN_SUPPORT if search space is exhausted."""
    global _min_support_override
    _min_support_override = override_value

def extend_cover_minsup_abs(extend, node_hashmap_size=0, total_nodes=1):
    """Check if extend meets minimum support threshold.
    
    Dynamically relaxes minimum support if search space becomes exhausted (>80% dead-ends).
    This prevents premature termination on small datasets.
    """
    global _min_support_override
    
    # Use override if set
    if _min_support_override is not None:
        return len(extend) >= _min_support_override
    
    return len(extend) >= conf.MIN_SUPPORT


def init_mcts_tree(data, target_class, log_losses, top_k, theta):
    data = filter_empty_sequences(data)
    Model.set_target_class(target_class)
    Model.set_data(data)
    if len(log_losses) != len(data):
        raise Exception("Log losses and data differ in length")
    item_log_losses = calculate_item_log_losses(data, log_losses)
    print(f"Calculated log losses for {len(item_log_losses)} items")
    node_hashmap = {}
    root_node = Node(None, None, node_hashmap)
    node_hashmap[('.')] = root_node
    print(f"Root node candidates after filtering: {len(root_node.candidate_sequences_expand)}/{len(data)}")
    sorted_patterns = PrioritySet(k=top_k, theta=theta)
    stats = {
        'iteration_count': 0,
        'max_depth_reached': 0,
        'successful_expansions': 0,
        'valid_from_exploration': 0,
        'valid_from_exploitation': 0,
        'highest_error': 0,
        'rollout_count': 0,
        'rollout_success_count': 0,
        'max_quality_seen': 0.0,
        'last_gain_iteration': 0,
    }
    return data, root_node, sorted_patterns, node_hashmap, item_log_losses, stats


def mcts_one_iteration(root_node, sorted_patterns, node_hashmap, item_log_losses, stats, min_per_class=10,
                       phase_hook=None, should_abort=None, node_weights=None):
    """Single MCTS iteration; mutates stats and search structures."""
    if should_abort and should_abort():
        return 'aborted'

    # Initialize new stats keys if they are missing (e.g. after loading state)
    if 'rollout_count' not in stats:
        stats['rollout_count'] = 0
        stats['rollout_success_count'] = 0
        stats['max_quality_seen'] = 0.0
        stats['last_gain_iteration'] = 0

    # Track search space health
    dead_end_count = sum(1 for node in node_hashmap.values() if node.is_dead_end())
    total_nodes = len(node_hashmap)
    dead_end_ratio = dead_end_count / max(1, total_nodes)
    
    # Warn if we're reaching deadlock (>80% dead ends)
    if dead_end_ratio > 0.80 and stats.get('iteration_count', 0) % 100 == 0:
        print(f"[WARNING] Search space getting exhausted: {dead_end_ratio*100:.1f}% dead ends ({dead_end_count}/{total_nodes})")
    
    # If we have too many dead ends, dynamically relax MIN_SUPPORT
    if dead_end_ratio > 0.75:  # Relax when >75% dead ends
        base_min_support = conf.MIN_SUPPORT
        # Gradually reduce from base down to 1
        relaxation_factor = min(0.9, (dead_end_ratio - 0.75) / 0.25)  # 0 to 0.9 factor
        relaxed_min_support = max(1, int(base_min_support * (1.0 - relaxation_factor)))
        if relaxed_min_support < base_min_support:
            set_dynamic_min_support(relaxed_min_support)
            if stats.get('iteration_count', 0) % 100 == 0:
                print(f"[INFO] Relaxed MIN_SUPPORT to {relaxed_min_support} (from {base_min_support})")
        stats['search_space_exhaustion_warnings'] = stats.get('search_space_exhaustion_warnings', 0) + 1
    else:
        # Reset to normal when search space recovers
        if _min_support_override is not None:
            set_dynamic_min_support(None)

    if phase_hook:
        phase_hook('MAIN')
    node_sel, is_exploration = select(root_node, node_weights=node_weights)
    if node_sel == 'finished':
        return 'finished'

    node_expand, _ = node_sel.expand(node_hashmap)

    stats['max_depth_reached'] = max(stats['max_depth_reached'], node_expand.depth)
    if len(node_expand.intent) > 0 and len(node_expand.extend) > 0:
        stats['successful_expansions'] += 1

    if (node_expand.quality > 0 and node_expand.accuracy > 0 and len(node_expand.intent)
            and extend_cover_minsup_abs(node_expand.extend)
            and node_expand.size_class_0 >= min_per_class and node_expand.size_class_1 >= min_per_class):
        if is_exploration:
            stats['valid_from_exploration'] += 1
        else:
            stats['valid_from_exploitation'] += 1
        sorted_patterns.add(sequence_mutable_to_immutable(node_expand.intent), node_expand.quality,
                            node_expand.extend, node_expand.accuracy)
        if node_expand.accuracy > stats['highest_error']:
            stats['highest_error'] = node_expand.accuracy
            
        # Track quality gain
        if node_expand.quality > stats['max_quality_seen']:
            stats['max_quality_seen'] = node_expand.quality
            stats['last_gain_iteration'] = stats['iteration_count']

    if should_abort and should_abort():
        return 'aborted'

    if phase_hook:
        phase_hook('ROLLOUT')
    sequence_reward, reward = roll_out(node_expand, item_log_losses=item_log_losses)
    stats['rollout_count'] += 1

    if should_abort and should_abort():
        return 'aborted'

    if phase_hook:
        phase_hook('BACKPROP')
    reward_node = Node(sequence_mutable_to_immutable(sequence_reward), node_sel, node_hashmap)
    stats['max_depth_reached'] = max(stats['max_depth_reached'], reward_node.depth)
    if (reward_node.quality > 0 and reward_node.accuracy > 0 and len(sequence_reward)
            and extend_cover_minsup_abs(reward_node.extend)
            and reward_node.size_class_0 >= min_per_class and reward_node.size_class_1 >= min_per_class):
        if is_exploration:
            stats['valid_from_exploration'] += 1
        else:
            stats['valid_from_exploitation'] += 1
        sorted_patterns.add(reward_node.intent, reward, reward_node.extend, reward_node.accuracy)
        if reward_node.accuracy > stats['highest_error']:
            stats['highest_error'] = reward_node.accuracy
            
        stats['rollout_success_count'] += 1
        # Track quality gain from rollout
        if reward_node.quality > stats['max_quality_seen']:
            stats['max_quality_seen'] = reward_node.quality
            stats['last_gain_iteration'] = stats['iteration_count']

    update(node_expand, reward)
    stats['iteration_count'] += 1
    
    # Track exhaustion metric for telemetry
    if 'search_space_health' not in stats:
        stats['search_space_health'] = []
    stats['search_space_health'].append(dead_end_ratio)
    
    return 'continue'


def build_iteration_metrics(node_hashmap, iteration_count, runtime_seconds, max_depth_reached,
                            successful_expansions, valid_from_exploration, valid_from_exploitation,
                            sorted_patterns):
    visit_dist = sorted_patterns.get_visit_count_distribution()
    metrics = {
        'nodes_visited': len(node_hashmap),
        'iterations': iteration_count,
        'runtime_seconds': runtime_seconds,
        'tree_depth_reached': max_depth_reached,
        'successful_expansions': successful_expansions,
        'expansion_success_rate': (successful_expansions / iteration_count) if iteration_count else 0.0,
        'valid_from_exploration': valid_from_exploration,
        'valid_from_exploitation': valid_from_exploitation,
        'unique_patterns_in_queue': len(sorted_patterns.set),
        'redundant_add_attempts': sorted_patterns.redundant_add_count,
    }
    for k in range(2, 11):
        metrics[f'patterns_visited_{k}_times'] = visit_dist.get(k, 0)
    metrics['patterns_visited_11_plus_times'] = sum(n for c, n in visit_dist.items() if c >= 11)
    return metrics


def launch_mcts(data, target_class, log_losses, time_budget=conf.TIME_BUDGET, top_k=conf.TOP_K, theta=conf.THETA,
                iterations_limit=conf.ITERATIONS_NUMBER, extra={}, max_length=6,
                pause_event=None, stop_event=None, **_kwargs):
    begin = datetime.datetime.now(timezone.utc)
    time_budget = datetime.timedelta(seconds=time_budget)

    data, root_node, sorted_patterns, node_hashmap, item_log_losses, stats = init_mcts_tree(
        data, target_class, log_losses, top_k, theta)

    while (datetime.datetime.now(timezone.utc) - begin <= time_budget
           and stats['iteration_count'] < iterations_limit):
        if stop_event is not None and stop_event.is_set():
            break
        if pause_event is not None:
            pause_event.wait()
        if stop_event is not None and stop_event.is_set():
            break

        status = mcts_one_iteration(root_node, sorted_patterns, node_hashmap, item_log_losses, stats)
        if status == 'finished':
            print('Finished')
            break
        if status == 'aborted':
            break

    iteration_count = stats['iteration_count']
    print('Number iteration mcts: {}'.format(iteration_count))
    extra['iteration_count'] = iteration_count
    runtime_seconds = (datetime.datetime.now(timezone.utc) - begin).total_seconds()
    extra['iteration_metrics'] = build_iteration_metrics(
        node_hashmap, iteration_count, runtime_seconds, stats['max_depth_reached'],
        stats['successful_expansions'], stats['valid_from_exploration'], stats['valid_from_exploitation'],
        sorted_patterns,
    )
    return sorted_patterns.get_top_k_non_redundant(data, top_k, pattern_max_len=max_length, extra=extra)
