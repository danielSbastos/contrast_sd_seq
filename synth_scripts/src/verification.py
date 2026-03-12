# src/verification.py
import os
import re
import pandas as pd
from sklearn.metrics import roc_auc_score

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
                itemsets.append(tuple(sorted(tokens)))
    else:
        tokens = [token for token in pattern_str.strip().split() if token]
        if tokens:
            itemsets.append(tuple(tokens))

    return itemsets

def _sequence_string_to_itemsets(sequence_str):
    """
    Convert a generated Kosarak-like string into a list of itemsets (tuples of
    sorted tokens) for pattern matching.
    """
    tokens = sequence_str.split()
    itemsets = []
    current_itemset = []

    # Skip the first token which corresponds to the class label
    for token in tokens[1:]:
        if token == "-1":
            if current_itemset:
                itemsets.append(tuple(sorted(current_itemset)))
                current_itemset = []
        elif token == "-2":
            if current_itemset:
                itemsets.append(tuple(sorted(current_itemset)))
            break
        else:
            current_itemset.append(token)

    return itemsets

def _sequence_contains_pattern(sequence_str, pattern_itemsets):
    """
    Check whether the sequence string contains the given pattern (as a list of
    itemsets represented by tuples) in order.
    """
    if not pattern_itemsets:
        return False

    parsed_sequence = _sequence_string_to_itemsets(sequence_str)
    pattern_len = len(pattern_itemsets)

    if pattern_len == 0 or pattern_len > len(parsed_sequence):
        return False

    for start_idx in range(len(parsed_sequence) - pattern_len + 1):
        window = parsed_sequence[start_idx:start_idx + pattern_len]
        if window == pattern_itemsets:
            return True

    return False

def verify_and_print_results(df_final, signal_rules, global_target_auc):
    """
    Calcula e imprime a AUC global e a AUC de cada subconjunto definido nas regras.
    """
    print("\n--- Verificação Final ---")
    final_global_auc = roc_auc_score(df_final['y_true'], df_final['confidence'])
    print(f"AUC Global Alvo: {global_target_auc}")
    print(f"AUC Global Final: {final_global_auc:.4f}")

    for rule in signal_rules:
        element = rule['element']
        target_auc = rule['target_auc']
        df_subset = pd.DataFrame()

        # Check if it's a sequence of itemsets pattern like "{A B} {C} {E}"
        pattern_itemsets = _parse_pattern_itemsets(element)
        if len(pattern_itemsets) > 1:
            # Sequence of itemsets pattern - verify exact sequence match
            df_subset = df_final[
                df_final['sequence'].apply(lambda seq: _sequence_contains_pattern(seq, pattern_itemsets))
            ]
        # Check if it's a single itemset pattern like "{A B C}"
        elif element.startswith('{') and element.endswith('}'):
            # --- NOVA LÓGICA: Verificação de Itemset ---
            content = element.strip('{}') # Remove chaves -> "A B C"
            pattern = f" {re.escape(content)} -1"
            label_pattern = f"^{re.escape(df_final['sequence'].iloc[0].split()[0])} {re.escape(content)} -1"
            df_subset = df_final[
                df_final['sequence'].str.contains(pattern) | df_final['sequence'].str.contains(label_pattern)
            ]
        elif ' ' in element:
            # --- LÓGICA EXISTENTE: Verificação de Sequência Ordenada ---
            pattern = '.*'.join([re.escape(item) for item in element.split(' ')])
            df_subset = df_final[df_final['sequence'].str.contains(pattern, regex=True)]
        else:
            # --- LÓGICA EXISTENTE: Verificação de Item Único ---
            pattern = f" {re.escape(element)} -1"
            label_pattern = f"^{re.escape(df_final['sequence'].iloc[0].split()[0])} {re.escape(element)} -1"
            df_subset = df_final[
                df_final['sequence'].str.contains(pattern) | df_final['sequence'].str.contains(label_pattern)
            ]

        if not df_subset.empty:
            final_subset_auc = roc_auc_score(df_subset['y_true'], df_subset['confidence'])
            print(f"\n> Subconjunto '{element}' (Alvo AUC: {target_auc})")
            print(f"  - AUC Final Verificada: {final_subset_auc:.4f}")
            print(f"  - Número de sequências: {len(df_subset)}")
        else:
            print(f"\nAVISO: Nenhum subconjunto encontrado para o elemento '{element}' na verificação final.")