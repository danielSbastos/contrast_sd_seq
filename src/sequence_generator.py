import pandas as pd
import numpy as np
import re
from scipy.stats import norm
from scipy.special import expit
from sklearn.metrics import roc_auc_score
from src.utils import to_kosarak_format

def _parse_pattern_itemsets(pattern_str):
    """
    Convert a pattern definition string (e.g. "{A B} {C} {E}") into a list of
    itemsets where each itemset is represented as a tuple of tokens.
    """
    if not pattern_str:
        return []

    matches = re.findall(r'\{([^}]*)\}', pattern_str)
    itemsets = []

    if matches:
        for match in matches:
            tokens = [token for token in match.strip().split() if token]
            if tokens:
                itemsets.append(tuple(tokens))
    else:
        tokens = [token for token in pattern_str.strip().split() if token]
        if tokens:
            itemsets.append(tuple(tokens))

    return itemsets

def _generate_random_element(vocabulary, allow_itemsets=False, prob_itemset=0.15, max_itemset_size=3, noise_density=1.0, frozen_vocabulary=None, frozen_vocabulary_probs=None):
    """Gera um elemento aleatório, controlando a densidade do ruído."""
    if not vocabulary:
        return "NULL_VOCAB_ITEM"

    # If a frozen vocabulary is provided, sample from it (with weights if provided)
    if frozen_vocabulary:
        if frozen_vocabulary_probs is not None:
            return np.random.choice(frozen_vocabulary, p=frozen_vocabulary_probs)
        else:
            return np.random.choice(frozen_vocabulary)

    # 1. Determina o elemento base (item ou itemset)
    is_itemset = allow_itemsets and np.random.rand() <= prob_itemset and len(vocabulary) >= 2
    
    if not is_itemset:
        base_element = np.random.choice(vocabulary)
    else:
        size = min(np.random.randint(2, max_itemset_size + 1), len(vocabulary))
        items = np.random.choice(vocabulary, size=size, replace=False)
        base_element = " ".join(items)

    # 2. Aplica a lógica de densidade do ruído
    if np.random.rand() < noise_density:
        # Comportamento DENSO (ex: "ItemA" ou "ItemA ItemB")
        return base_element
    else:
        # Comportamento ESPARSO (ex: "ItemA_s12345" ou "ItemA_s12345 ItemB_s67890")
        if not is_itemset:
            return f"{base_element}_s{np.random.randint(10000, 99999)}"
        else:
            items = base_element.split(' ')
            sparse_items = [f"{item}_s{np.random.randint(10000, 99999)}" for item in items]
            return " ".join(sparse_items)


def _calculate_auc_scores(n_samples, target_auc, max_iter=50, tolerance=0.001):
    if n_samples == 0:
        return np.array([]), np.array([])
    
    mu_neg, sigma = 0.0, 1.0
    delta_mu = norm.ppf(target_auc) * np.sqrt(2 * sigma**2)
    n_pos = n_samples // 2
    n_neg = n_samples - n_pos
    targets = np.array([1] * n_pos + [0] * n_neg)

    for _ in range(max_iter):
        mu_pos = mu_neg + delta_mu
        scores_pos = np.random.normal(loc=mu_pos, scale=sigma, size=n_pos)
        scores_neg = np.random.normal(loc=mu_neg, scale=sigma, size=n_neg)
        confidence_scores = np.concatenate([scores_pos, scores_neg])
        error = target_auc - roc_auc_score(targets, confidence_scores)
        if abs(error) < tolerance:
            break
        delta_mu += error * 1.5
        
    return targets, expit(confidence_scores)

def _create_single_sequence(base_element, vocabulary, allow_itemsets, noise_density, frozen_vocabulary=None, frozen_vocabulary_probs=None):
    seq_length = np.random.randint(15, 30)
    
    def gen_noise(n_items):
        return [
            _generate_random_element(
                vocabulary,
                allow_itemsets,
                noise_density=noise_density,
                frozen_vocabulary=frozen_vocabulary,
                frozen_vocabulary_probs=frozen_vocabulary_probs
            )
            for _ in range(n_items)
        ]

    if not base_element:
        return gen_noise(seq_length)

    # Check if it's a sequence of itemsets pattern like "{A B} {C} {E}"
    pattern_itemsets = _parse_pattern_itemsets(base_element)
    if len(pattern_itemsets) > 1:
        # Sequence of itemsets: insert them consecutively as a block, then add noise around
        signal_itemsets = [" ".join(itemset) for itemset in pattern_itemsets]
        
        # Collect all signal items to exclude from vocabulary
        all_signal_items = set()
        for itemset in pattern_itemsets:
            all_signal_items.update(itemset)
        
        # Ensure minimum sequence length
        n_signal_itemsets = len(signal_itemsets)
        seq_length = max(seq_length, n_signal_itemsets)
        
        # Generate background noise
        background_seq = gen_noise(seq_length - n_signal_itemsets)
        
        # Insert the complete pattern as a consecutive block, then insert noise before/after it
        # This ensures the pattern itemsets remain consecutive for verification
        insert_pos = np.random.randint(0, len(background_seq) + 1)
        final_seq = background_seq.copy()
        for itemset in reversed(signal_itemsets):  # Insert in reverse to maintain order
            final_seq.insert(insert_pos, itemset)
        
        return final_seq

    # Check if it's a single itemset pattern like "{A B C}"
    if base_element.startswith('{') and base_element.endswith('}'):
        content = base_element.strip('{}')
        signal_items = content.split(' ')
        current_vocab = [v for v in vocabulary if v not in signal_items]
        background_seq = gen_noise(seq_length - 1)
        insert_pos = np.random.randint(0, len(background_seq) + 1)
        background_seq.insert(insert_pos, " ".join(signal_items))
        return background_seq

    # Check if it's an ordered sequence of items like "A B C"
    if ' ' in base_element:
        signal_items = base_element.split(' ')
        n_signal = len(signal_items)
        seq_length = max(seq_length, n_signal)
        current_vocab = [v for v in vocabulary if v not in signal_items]
        background_seq = gen_noise(seq_length - n_signal)
        
        final_seq = signal_items.copy()
        for item in background_seq:
            insert_pos = np.random.randint(0, len(final_seq) + 1)
            final_seq.insert(insert_pos, item)
        return final_seq

    # Single item pattern
    signal_items = [base_element] if base_element else []
    current_vocab = [v for v in vocabulary if v not in signal_items]
    seq_len = seq_length - len(signal_items)
    seq = gen_noise(seq_len)
    
    if base_element:
        insert_pos = np.random.randint(0, len(seq) + 1)
        seq.insert(insert_pos, base_element)
    return seq

def generate_sequences_with_scores(n_samples, target_auc, base_element=None, vocabulary=None, allow_itemsets=False, noise_density=1.0, frozen_vocabulary=None, frozen_vocabulary_probs=None):
    """Gera um subconjunto de dados com uma AUC alvo, controlando a densidade do ruído."""
    if n_samples == 0:
        return pd.DataFrame({'sequence': [], 'y_true': [], 'confidence': []})

    targets, scaled_scores = _calculate_auc_scores(n_samples, target_auc)
    
    sequences = [
        _create_single_sequence(base_element, vocabulary, allow_itemsets, noise_density, frozen_vocabulary, frozen_vocabulary_probs) for _ in range(n_samples)
    ]
    
    INTERNAL_DELIMITER = "|"
    sequences_as_str = [INTERNAL_DELIMITER.join(seq) for seq in sequences]
    kosarak_sequences = [to_kosarak_format("9", s.split(INTERNAL_DELIMITER)) for s in sequences_as_str]

    df = pd.DataFrame({
        'sequence': kosarak_sequences, 
        'y_true': targets, 
        'confidence': scaled_scores
    })
    return df.sample(frac=1).reset_index(drop=True)

def find_optimal_auc_for_remainder(global_target_auc, df_subsets, n_remainder, vocabulary, allow_itemsets=False, noise_density=1.0, tolerance=0.005, max_iter=100, frozen_vocabulary=None, frozen_vocabulary_probs=None):
    print(f"Buscando AUC para o conjunto restante para atingir AUC global de {global_target_auc}...")
    low_auc, high_auc = 0.5, 1.0
    
    for i in range(max_iter):
        current_auc = (low_auc + high_auc) / 2
        df_remainder = generate_sequences_with_scores(
            n_samples=n_remainder, 
            target_auc=current_auc, 
            vocabulary=vocabulary,
            allow_itemsets=allow_itemsets,
            noise_density=noise_density,
            frozen_vocabulary=frozen_vocabulary,
            frozen_vocabulary_probs=frozen_vocabulary_probs
        )
        df_combined = pd.concat([df_subsets, df_remainder], ignore_index=True)
        current_global_auc = roc_auc_score(df_combined['y_true'], df_combined['confidence'])
        
        print(f"Iter {i+1}: Testando AUC_Restante={current_auc:.4f} -> AUC Global={current_global_auc:.4f}")

        if abs(current_global_auc - global_target_auc) < tolerance:
            print("Solução encontrada!")
            return df_combined
        
        if current_global_auc < global_target_auc:
            low_auc = current_auc
        else:
            high_auc = current_auc
            
    print("Máximo de iterações atingido. Retornando a melhor solução encontrada.")
    return df_combined