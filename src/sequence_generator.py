import pandas as pd
import numpy as np
from scipy.stats import norm
from scipy.special import expit
from sklearn.metrics import roc_auc_score
from src.utils import to_kosarak_format

def _generate_random_element(vocabulary, allow_itemsets=False, prob_itemset=0.15, max_itemset_size=3):
    """Gera um elemento aleatório, que pode ser um item único ou um itemset."""
    if not allow_itemsets or np.random.rand() > prob_itemset or len(vocabulary) < 2:
        return np.random.choice(vocabulary)
    
    size = min(np.random.randint(2, max_itemset_size + 1), len(vocabulary))
    items = np.random.choice(vocabulary, size=size, replace=False)
    return " ".join(items)

def _calculate_auc_scores(n_samples, target_auc, max_iter=50, tolerance=0.001):
    """Calcula scores de confiança para atingir uma AUC alvo."""
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

def _create_single_sequence(base_element, vocabulary, allow_itemsets):
    """Cria uma única sequência com base em uma regra de sinal (ou sem ela)."""
    seq_length = np.random.randint(5, 8)
    
    # Regra de Itemset: {A B}
    if base_element and base_element.startswith('{') and base_element.endswith('}'):
        content = base_element.strip('{}')
        signal_items = content.split(' ')
        current_vocab = [v for v in vocabulary if v not in signal_items]
        background_seq = [_generate_random_element(current_vocab, allow_itemsets) for _ in range(seq_length - 1)]
        insert_pos = np.random.randint(0, len(background_seq) + 1)
        background_seq.insert(insert_pos, " ".join(signal_items))
        return background_seq

    # Regra de Sequência Ordenada: A B
    if base_element and ' ' in base_element:
        signal_items = base_element.split(' ')
        n_signal = len(signal_items)
        seq_length = max(seq_length, n_signal)
        current_vocab = [v for v in vocabulary if v not in signal_items]
        background_seq = [_generate_random_element(current_vocab, allow_itemsets) for _ in range(seq_length - n_signal)]
        
        final_seq = signal_items.copy()
        for item in background_seq:
            insert_pos = np.random.randint(0, len(final_seq) + 1)
            final_seq.insert(insert_pos, item)
        return final_seq

    # Regra de Item Único ou Sem Regra
    signal_items = [base_element] if base_element else []
    current_vocab = [v for v in vocabulary if v not in signal_items]
    seq_len = seq_length - len(signal_items)
    seq = [_generate_random_element(current_vocab, allow_itemsets) for _ in range(seq_len)]
    
    if base_element:
        insert_pos = np.random.randint(0, len(seq) + 1)
        seq.insert(insert_pos, base_element)
    return seq

def generate_sequences_with_scores(n_samples, target_auc, base_element=None, vocabulary=None, allow_itemsets=False):
    """Gera um subconjunto de dados com uma AUC alvo, suportando regras de item único, itemset e sequência ordenada."""
    if n_samples == 0:
        return pd.DataFrame({'sequence': [], 'y_true': [], 'confidence': []})

    targets, scaled_scores = _calculate_auc_scores(n_samples, target_auc)
    
    sequences = [
        _create_single_sequence(base_element, vocabulary, allow_itemsets) for _ in range(n_samples)
    ]
    
    # Formatação final
    INTERNAL_DELIMITER = "|"
    sequences_as_str = [INTERNAL_DELIMITER.join(seq) for seq in sequences]
    kosarak_sequences = [to_kosarak_format("9", s.split(INTERNAL_DELIMITER)) for s in sequences_as_str]

    df = pd.DataFrame({
        'sequence': kosarak_sequences, 
        'y_true': targets, 
        'confidence': scaled_scores
    })
    return df.sample(frac=1).reset_index(drop=True)

def find_optimal_auc_for_remainder(global_target_auc, df_subsets, n_remainder, vocabulary, allow_itemsets=False, tolerance=0.005, max_iter=100):
    """Usa busca binária para encontrar a AUC do conjunto restante que atinge a AUC global desejada."""
    print(f"Buscando AUC para o conjunto restante para atingir AUC global de {global_target_auc}...")
    low_auc, high_auc = 0.5, 1.0
    
    for i in range(max_iter):
        current_auc = (low_auc + high_auc) / 2
        df_remainder = generate_sequences_with_scores(
            n_samples=n_remainder, 
            target_auc=current_auc, 
            vocabulary=vocabulary,
            allow_itemsets=allow_itemsets
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