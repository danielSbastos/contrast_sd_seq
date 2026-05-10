import re
import numpy as np
import pandas as pd
import os
import math
import datetime
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


def best_child(node):
    if node.is_dead_end() and len(node.parents) == 0:
        return 'finished'

    best_node = None
    max_score = -float("inf")

    for child in node.children:
        if child.is_dead_end():
            continue
        a = child.get_normalized_quality() / child.number_visits
        b = 0.5 * math.sqrt(2 * math.log(node.number_visits) / child.number_visits)
        current_ucb = a + b

        if current_ucb > max_score:
            max_score = current_ucb
            best_node = child

    if best_node is None:
        return node.parents[0]

    return best_node


def select(node):
    while node != 'finished':
        if len(node.children) == 0:
            return (node, False)  # exploitation: descended to leaf via best_child
        if (random.random() < 0.5) and (not node.is_fully_expanded()):
            return (node, True)   # exploration: chose to expand this node
        node = best_child(node)
    return ('finished', None)


computed_rollouts = {}


def roll_out(node, item_log_losses=None):
    """
    Fast rollout: Remove contiguous chunks from start or end only.
    No scoring, no complex logic - just simple boundary removal.
    """
    sequence = copy.deepcopy(node.intent)
    sequence = sequence_immutable_to_mutable(sequence)

    if not sequence or len(sequence) <= 1:
        return sequence, 1

    # How many to remove (20-50% of length)
    num_to_remove = random.randint(
        max(1, int(len(sequence) * 0.2)),
        max(1, int(len(sequence) * 0.5))
    )

    choice = random.randint(0, 2)

    if choice == 0:
        sequence = sequence[num_to_remove:]
    elif choice == 1:
        sequence = sequence[:-num_to_remove]
    else:
        remove_start = num_to_remove // 2
        remove_end = num_to_remove - remove_start
        sequence = sequence[remove_start:-remove_end if remove_end > 0 else None]

    if not sequence:
        return [], 0

    immutable_sequence = tuple(sequence_mutable_to_immutable(sequence))
    reward, _, _, _, _ = compute_quality(immutable_sequence)

    return sequence, reward

def update(node, reward):
    update_nodes = {node}
    parents_seen = set()

    while len(update_nodes) != 0:
        node = random.sample(update_nodes, 1)[0]
        parents_seen.add(node)
        for parent in node.parents:
            if parent not in parents_seen:
                update_nodes.add(parent)

        node.update(reward)
        update_nodes.remove(node)

def prepare_mcts_from_files(filename, max_gap=conf.MAX_GAP, support_penalty=conf.SUPPORT_PENALTY,
                            sigmoid_offset=conf.SIGMOID_OFFSET, synth_patterns_path=None):
    """Load sequences, targets, and model globals needed for MCTS (shared by get_patterns and api.MCTS)."""
    conf.MAX_GAP = max_gap
    conf.SUPPORT_PENALTY = support_penalty
    conf.SIGMOID_OFFSET = sigmoid_offset
    path = f"data/{filename}_train.dat"
    target_path = f"data/{filename}_train.csv"

    if not os.path.isfile(path):
        path = f"data/{filename}.dat"
        target_path = f"data/{filename}.csv"

    data = read_data_kosarak(path)
    items = extract_items(data)
    items, items_to_encoding, encoding_to_items = encode_items(items)
    data = encode_data(data, items_to_encoding)

    target_file = pd.read_csv(target_path)[['y_true', 'confidence']]
    target_class = target_file.values

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

    log_losses_file = f"data/log_losses/log_losses_{filename}.txt"
    try:
        log_losses = np.loadtxt(log_losses_file)
        print("Loaded log losses file")
    except FileNotFoundError:
        log_losses = calculate_log_losses(target_class)
        np.savetxt(log_losses_file, log_losses)
        print("Created log losses file")

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

def extend_cover_minsup_abs(extend):
    return len(extend) >= conf.MIN_SUPPORT


def init_mcts_tree(data, target_class, log_losses, top_k, theta):
    """Build root tree + priority queue state (used by launch_mcts and api.MCTS)."""
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
    }
    return data, root_node, sorted_patterns, node_hashmap, item_log_losses, stats


def mcts_one_iteration(root_node, sorted_patterns, node_hashmap, item_log_losses, stats, min_per_class=10,
                       phase_hook=None, should_abort=None):
    """Single MCTS iteration; mutates stats and search structures."""
    if should_abort and should_abort():
        return 'aborted'

    if phase_hook:
        phase_hook('MAIN')
    node_sel, is_exploration = select(root_node)
    if node_sel == 'finished':
        return 'finished'

    node_expand, _ = node_sel.expand()

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
            print(f"Highest Error: {stats['highest_error']}. Pattern: {node_expand.intent}")

    if should_abort and should_abort():
        return 'aborted'

    if phase_hook:
        phase_hook('ROLLOUT')
    sequence_reward, reward = roll_out(node_expand, item_log_losses=item_log_losses)

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
            print(f"Highest Error: {stats['highest_error']}. Pattern: {reward_node.intent}")

    update(node_expand, reward)
    stats['iteration_count'] += 1
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
    begin = datetime.datetime.utcnow()
    time_budget = datetime.timedelta(seconds=time_budget)

    data, root_node, sorted_patterns, node_hashmap, item_log_losses, stats = init_mcts_tree(
        data, target_class, log_losses, top_k, theta)

    while (datetime.datetime.utcnow() - begin <= time_budget
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
    runtime_seconds = (datetime.datetime.utcnow() - begin).total_seconds()
    extra['iteration_metrics'] = build_iteration_metrics(
        node_hashmap, iteration_count, runtime_seconds, stats['max_depth_reached'],
        stats['successful_expansions'], stats['valid_from_exploration'], stats['valid_from_exploitation'],
        sorted_patterns,
    )
    return sorted_patterns.get_top_k_non_redundant(data, top_k, pattern_max_len=max_length, extra=extra)
