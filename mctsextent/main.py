import pandas as pd
import math
import datetime
import sys
import random
import copy
import math

from sklearn.metrics import roc_auc_score

import general.conf as conf

from general.reader import read_data_kosarak
from general.utils import parse_expected_patterns, sequence_mutable_to_immutable, compute_quality, \
    sequence_immutable_to_mutable, calculate_log_losses, filter_empty_sequences, encode_items, \
    encode_data, print_results_decode, extract_items, decode_sequences, get_idx_from_cumulative_prop, \
    compute_cumulative_probs, compute_sequence_expand, encode_expected_patterns, decode_expected_patterns 

from general.priorityset import PrioritySet
from mctsextent.node import Node
from seqscout.global_var import Model

sys.setrecursionlimit(15000)


def best_child(node):
    """
    Returns the best child node of node w.r.t UCB
    :param node:
    :return:
    """
    if node.is_dead_end() and len(node.parents) == 0:
        return 'finished'

    best_node = None
    max_score = -float("inf")

    for child in node.children:
        current_ucb = child.get_normalized_quality() / child.number_visits + 0.5 * math.sqrt(
            2 * math.log(node.number_visits) / child.number_visits)
        
        if current_ucb > max_score and not child.is_dead_end():
            max_score = current_ucb
            best_node = child

    if best_node == None:
        return node.parents[0]

    return best_node


def select(node):
    while node != 'finished':
        if len(node.children) == 0:
            return node
        else:
            if (random.random() < 0.5) and (not node.is_fully_expanded()):
                return node
            else:
                node = best_child(node)
    return 'finished'


computed_rollouts = {}


def roll_out(node, item_log_losses=None):
    """
    Generalize a sequence by deleting items (weighted by log loss or random)
    :param node: the node corresponding to the sequence to generalize
    :param data:
    :param target_class:
    :return: the new sequence and its quality
    """
    sequence = copy.deepcopy(node.intent)
    sequence = sequence_immutable_to_mutable(sequence)

    if not sequence: return sequence, 1

    seq_items_nb = len([i for j_set in sequence for i in j_set])
    z = random.randint(0, seq_items_nb - 1 if seq_items_nb else seq_items_nb)

    item_candidates = []
    for itemset_i, itemset in enumerate(sequence):
        for item in itemset:
            log_loss = item_log_losses[item]
            removal_prob = 1.0 / (1.0 + log_loss)
            item_candidates.append((itemset_i, item, removal_prob))

    probs = [prob for _, _, prob in item_candidates]
    min_prob = min(probs)
    max_prob = max(probs)
    prob_range = max_prob - min_prob

    if prob_range > 0:
        n_probs = [(p - min_prob) / prob_range for p in probs]
    else:
        n_probs = probs

    n_item_candidates = []
    for (itemset_idx, item, _), n_prob in zip(item_candidates, n_probs):
        n_item_candidates.append((itemset_idx, item, n_prob))

    items_to_remove = []
    available_candidates = n_item_candidates.copy()

    for _ in range(min(z, len(available_candidates))):
        probs = [prob for _, _, prob in available_candidates]
        chosen_idx = get_idx_from_cumulative_prop(probs) or 0

        itemset_i, item, _ = available_candidates.pop(chosen_idx)
        items_to_remove.append((itemset_i, item))

    # remove selected items from sequence
    items_by_itemset = {}
    for itemset_i, item in items_to_remove:
        if itemset_i not in items_by_itemset:
            items_by_itemset[itemset_i] = []
        items_by_itemset[itemset_i].append(item)

    # remove items and track which itemsets become empty
    itemsets_to_remove = []
    for itemset_i, items in items_by_itemset.items():
        for item in items:
            sequence[itemset_i].discard(item)

        # append empty itemsets to be later removed
        if len(sequence[itemset_i]) == 0:
            itemsets_to_remove.append(itemset_i)

    # remove empty itemsets
    for itemset_i in sorted(itemsets_to_remove, reverse=True):
        sequence.pop(itemset_i)

    immutable_sequence = tuple(sequence_mutable_to_immutable(sequence))
    if computed_rollouts.get(immutable_sequence, 0) > 5 and z > 0:
        return roll_out(node, item_log_losses)
    else:
        computed_rollouts[immutable_sequence] = computed_rollouts.get(immutable_sequence, 0) + 1

    reward, _, _ = compute_quality(immutable_sequence)
    return sequence, reward


def update(node, reward):
    """
    Backtrack: update the node and recursively update all parent nodes until the extent root
    :param node: the node we want to update
    :param reward: the reward we got
    :return: None
    """

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

def get_patterns(path='', target_path='', top_k=5, time_budget=10, theta=0.1, iterations_limit=2 ** 30, synth_patterns_path=None):
    '''
    :param path: path to the file containing data, in kosarak format
    :param target_class: the target class we want to find pattern of: string
    :param top_k: the number of patterns we want to get
    :param time_budget: the time we give to the algorithm
    :return: the top-k best pattern w.r.t WRAcc, and display them
    '''
    data = read_data_kosarak(path)
    items = extract_items(data)
    items, items_to_encoding, encoding_to_items = encode_items(items)
    data = encode_data(data, items_to_encoding)

    target_file = pd.read_csv(target_path)[['y_true', 'confidence']]
    target_class = target_file.values

    Model.set_labels(list(target_file['y_true'].unique()))

    if Model.is_multiclass():
        target_file['confidence'] = target_file['confidence'].map(eval)
        rocauc = roc_auc_score(target_file['y_true'].tolist(), target_file['confidence'].tolist(), multi_class='ovo')
    else:
        positive_class_scores = target_file['confidence']
        rocauc = roc_auc_score(target_file['y_true'].tolist(), positive_class_scores)

    Model.set_rocauc(rocauc)

    expected_patterns = []
    if synth_patterns_path:
        expected_patterns = parse_expected_patterns(synth_patterns_path)
        expected_patterns = encode_expected_patterns(expected_patterns, items_to_encoding)
    
    results = launch_mcts(data, target_class, top_k=top_k, time_budget=time_budget, theta=theta, iterations_limit=iterations_limit, expected_patterns=expected_patterns)
    
    print(f"Model ROC AUC: {rocauc}")
    print_results_decode(results, encoding_to_items)

    return decode_sequences(results, encoding_to_items)

def extend_cover_minsup_abs(extend):
    return len(extend) >= conf.MIN_SUPPORT

def calculate_item_log_losses(data, log_losses):
    item_loss_sums = {}
    item_counts = {}

    for i, sequence in enumerate(data):
        loss = log_losses[i]
        for itemset in sequence:
            for item in itemset:
                if item not in item_loss_sums:
                    item_loss_sums[item] = 0
                    item_counts[item] = 0
                item_loss_sums[item] += loss
                item_counts[item] += 1

    item_log_losses = {}
    for item in item_loss_sums:
        item_log_losses[item] = item_loss_sums[item] / item_counts[item]

    return item_log_losses

def launch_mcts(data, target_class, time_budget=conf.TIME_BUDGET, top_k=conf.TOP_K, theta=conf.THETA,
                iterations_limit=conf.ITERATIONS_NUMBER, expected_patterns=[]):

    begin = datetime.datetime.utcnow()
    time_budget = datetime.timedelta(seconds=time_budget)

    log_losses = calculate_log_losses(target_class)
    data = filter_empty_sequences(data)

    Model.set_target_class(target_class)
    Model.set_log_losses(log_losses)
    Model.set_data(data)

    if (len(log_losses) != len(data)): raise Exception("Log losses and data differ in length")

    item_log_losses = calculate_item_log_losses(data, log_losses)
    print(f"Calculated log losses for {len(item_log_losses)} items")
    print(f"JACCARD SIMILARITY: ", conf.USE_JACCARD_PRIORITY)

    node_hashmap = {}
    root_node = Node(None, None, node_hashmap)
    node_hashmap[('.')] = root_node
    
    print(f"Root node candidates after filtering: {len(root_node.candidate_sequences_expand)}/{len(data)}")

    sorted_patterns = PrioritySet(k=top_k, theta=theta)
    iteration_count = 0

    found_expected_patterns = 0

    while datetime.datetime.utcnow() - begin <= time_budget and iteration_count < iterations_limit:
        node_sel = select(root_node)

        if node_sel == 'finished':
            print('Finished')
            break

        node_expand, _ = node_sel.expand()

        if node_expand.quality > 0 and node_expand.rocauc > 0 and len(node_expand.intent) and extend_cover_minsup_abs(node_expand.extend):
            quality = node_expand.quality - math.log(len(node_expand.intent) + 2, 10)
            quality += 1
            sorted_patterns.add(sequence_mutable_to_immutable(node_expand.intent), quality, node_expand.extend, node_expand.rocauc)

        sequence_reward, reward = roll_out(node_expand, item_log_losses=item_log_losses)

        reward_node = Node(sequence_mutable_to_immutable(sequence_reward), node_sel, node_hashmap)
        if reward_node.quality > 0 and reward_node.rocauc > 0 and len(sequence_reward) and extend_cover_minsup_abs(reward_node.extend):
            reward -= math.log(len(sequence_reward) + 2, 10)
            reward += 1
            sorted_patterns.add(reward_node.intent, reward, reward_node.extend, reward_node.rocauc)

        update(node_expand, reward)

        iteration_count += 1

        for expected_pattern in expected_patterns:
            if (node_expand.intent == expected_pattern) or (reward_node.intent == expected_pattern):
                print(f"Found expected pattern: {expected_pattern} at iteration {iteration_count}")
                found_expected_patterns += 1

        if len(expected_pattern) > 0 and found_expected_patterns == len(expected_pattern):
            print(f"Found all patterns at iteration {iteration_count}")
            found_expected_patterns = float('inf')
            #break

        if iteration_count % 100 == 0:
            print(iteration_count)


    print('Number iteration mcts: {}'.format(iteration_count))
#    print("compute_quality: ", compute_quality.cache_info())
#    print("compute_cumulative_probs: ", compute_cumulative_probs.cache_info())
#    print("compute_sequence_expand: ", compute_sequence_expand.cache_info())

    return sorted_patterns.get_top_k_non_redundant(data, top_k)
