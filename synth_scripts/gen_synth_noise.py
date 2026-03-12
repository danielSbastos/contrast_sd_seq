# main.py
import re
import os
from collections import Counter

import argparse
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, log_loss

from src.file_handler import load_signal_rules, load_vocabulary
from src.utils import get_clean_vocabulary
from src.sequence_generator import generate_sequences_with_scores, find_optimal_auc_for_remainder
from src.verification import verify_and_print_results

def parse_arguments():
    parser = argparse.ArgumentParser(description="Gerador de sequências com AUC alvo")
    parser.add_argument("--gauc", type=float, required=True, help="Target AUC para o conjunto final")
    parser.add_argument("--voc", type=str, required=True, help="Caminho para o vocabulário")
    parser.add_argument("--sig", type=str, required=True, help="Caminho para o arquivo de regras")
    parser.add_argument("--maxseq", type=int, default=1000, help="Número máximo de sequências permitido")
    parser.add_argument("--gen-itemsets", action='store_true', help="Se especificado, gera itemsets aleatórios no ruído de fundo.")
    return parser.parse_args()

def save_sequences_to_file(sequences, filename="data/synth.dat"):
    np.savetxt(filename, sequences, fmt="%s")
    print(f"Sequências salvas em '{filename}'")

def save_dataframe_to_csv(df, filename="data/synth.csv"):
    df.to_csv(filename, index=False)
    print(f"DataFrame salvo em '{filename}'")

def main():
    parser = argparse.ArgumentParser(description="Gerador de sequências com AUC alvo")
    parser.add_argument("--gauc", type=float, required=True, help="Target AUC para o conjunto final")
    parser.add_argument("--voc", type=str, required=True, help="Caminho para o vocabulário")
    parser.add_argument("--sig", type=str, required=True, help="Caminho para o arquivo de regras")
    parser.add_argument("--maxseq", type=int, default=1000, help="Número máximo de sequências permitido")
    parser.add_argument("--gen-itemsets", action='store_true', help="Se especificado, gera itemsets aleatórios no ruído de fundo.")
    parser.add_argument("--filename", type=str, default="synth_temp", help="Arquivo output")
    parser.add_argument(
        "--noise-density", 
        type=float, 
        default=1.0, 
        help="Densidade do ruído (0.0 a 1.0). 1.0 = denso (padrões aleatórios se formam). 0.0 = esparso (itens de ruído são únicos)."
    )
    args = parser.parse_args()
    
    if not 0.0 <= args.noise_density <= 1.0:
        raise ValueError("--noise-density deve estar entre 0.0 e 1.0")

    GLOBAL_AUC_X = args.gauc
    VOCABULARY = load_vocabulary(args.voc)
    signal_rules = load_signal_rules(args.sig)
    
    total_sequences_rules = sum(rule['quantity'] for rule in signal_rules) if signal_rules else 0
    N_REMAINDER = max(args.maxseq - total_sequences_rules, total_sequences_rules or 800)
    
    CLEANED_VOCABULARY = get_clean_vocabulary(VOCABULARY, signal_rules)

    used_tokens = set()
    token_counts = Counter()
    df_list = []
    for rule in signal_rules:
        element, quantity, target_auc = rule['element'], rule['quantity'], rule['target_auc']
        
        print(f"Gerando subconjunto com elemento '{element}' e AUC alvo de {target_auc}...")
        df_rule = generate_sequences_with_scores(
            n_samples=quantity,
            target_auc=target_auc,
            base_element=element,
            vocabulary=CLEANED_VOCABULARY,
            allow_itemsets=args.gen_itemsets,
            noise_density=args.noise_density
        )
        
        auc_actual = roc_auc_score(df_rule['y_true'], df_rule['confidence'])
        print(f"AUC real do subconjunto com '{element}': {auc_actual:.4f}\n")
        df_list.append(df_rule)

    df_rules_concatenated = pd.concat(df_list, ignore_index=True)

    df_final = find_optimal_auc_for_remainder(
        global_target_auc=GLOBAL_AUC_X,
        df_subsets=df_rules_concatenated,
        n_remainder=N_REMAINDER,
        vocabulary=CLEANED_VOCABULARY,
        allow_itemsets=args.gen_itemsets,
        noise_density=args.noise_density 
    )

    verify_and_print_results(df_final, signal_rules, GLOBAL_AUC_X)
    sequences = df_final['sequence']
    np.savetxt(f"data/{args.filename}.dat", sequences, fmt="%s")
    print(f"\nSequências salvas em data/{args.filename}.dat")
    df_final.to_csv(f"data/{args.filename}.csv", index=False)
    print(f"Dataset final salvo em data/{args.filename}.csv")

    def calculate_log_losses(target_class):
        i = 0
        log_losses = []
        for y_true, confidence in target_class:
            labels = set(target_class[:, 0])
            log_losses.append(log_loss([y_true], [confidence], labels=list(labels)))
            if i % 1000 == 0:
                print(i)
            i+=1

        return log_losses

    log_losses_file = f"data/log_losses/log_losses_{args.filename}.txt"
    log_losses = calculate_log_losses(df_final[['y_true', 'confidence']].values)
    np.savetxt(log_losses_file, log_losses)
    print(f"Log losses salvos em {log_losses_file}")

    for seq_str in df_final['sequence']:
        parts = seq_str.split()
        for tok in parts[1:]:
            if tok in ("-1", "-2"):
                continue
            token_counts[tok] += 1
            used_tokens.add(tok)

    def base_token(t): return re.sub(r"_s\d+$", "", t)
    signal_base_tokens = set()
    for rule in signal_rules:
        elem = rule.get('element', '')
        elem_clean = elem.replace('{', ' ').replace('}', ' ')
        for tok in elem_clean.split():
            if tok.strip():
                signal_base_tokens.add(base_token(tok.strip()))

    noise_token_counts = {t: token_counts[t] for t in used_tokens if base_token(t) not in signal_base_tokens}
    noise_tokens = sorted(noise_token_counts.keys())
    total_noise_count = sum(noise_token_counts.values())
    noise_token_probs = np.array([noise_token_counts[t] / total_noise_count for t in noise_tokens]) if total_noise_count > 0 else None

    print("\n--- Gerando Dataset de Validação ---")
    print("Shuffling itemsets in sequences (preserving expected patterns)")
    
    def parse_kosarak_sequence(seq_str):
        """Parse a kosarak format sequence into itemsets."""
        parts = seq_str.split()
        if not parts:
            return None, []
        class_label = parts[0]
        itemsets = []
        current_itemset = []
        for part in parts[1:]:
            if part == "-1":
                if current_itemset:
                    itemsets.append(" ".join(current_itemset))
                    current_itemset = []
            elif part == "-2":
                break
            else:
                current_itemset.append(part)
        if current_itemset:
            itemsets.append(" ".join(current_itemset))
        return class_label, itemsets
    
    def reconstruct_kosarak_sequence(class_label, itemsets):
        """Reconstruct a kosarak format sequence from itemsets."""
        parts = [class_label]
        for itemset in itemsets:
            parts.append(itemset)
            parts.append("-1")
        parts.append("-2")
        return " ".join(parts)
    
    def parse_pattern_itemsets(pattern_str):
        """Parse a pattern definition string (e.g. "{A B} {C} {E}") into a list of itemsets."""
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
    
    def is_itemset_pattern(itemset_str, pattern_element):
        """Check if an itemset contains a pattern element (for itemset patterns like {A B C})."""
        if pattern_element.startswith('{') and pattern_element.endswith('}'):
            pattern_items = set(pattern_element.strip('{}').split())
            itemset_items = set(itemset_str.split())
            return pattern_items.issubset(itemset_items)
        return False
    
    def contains_itemset_sequence_pattern(sequence_itemsets, pattern_itemsets_list):
        """Check if sequence contains an itemset sequence pattern and return indices of matching itemsets."""
        pattern_len = len(pattern_itemsets_list)
        if pattern_len == 0 or pattern_len > len(sequence_itemsets):
            return []
        
        # Convert sequence itemsets to sorted tuples for comparison
        seq_itemsets_tuples = [tuple(sorted(itemset.split())) for itemset in sequence_itemsets]
        
        # Find consecutive itemsets that match the pattern in order
        for start_idx in range(len(seq_itemsets_tuples) - pattern_len + 1):
            window = seq_itemsets_tuples[start_idx:start_idx + pattern_len]
            if window == pattern_itemsets_list:
                return list(range(start_idx, start_idx + pattern_len))
        
        return []
    
    def contains_ordered_pattern(sequence_itemsets, pattern_element):
        """Check if sequence contains an ordered pattern and return indices of matching itemsets."""
        if ' ' not in pattern_element or pattern_element.startswith('{'):
            return []
        
        pattern_items = pattern_element.split()
        if len(pattern_items) == 1:
            # Single item pattern
            pattern_item = pattern_items[0]
            matching_indices = []
            for i, itemset in enumerate(sequence_itemsets):
                if pattern_item in itemset.split():
                    matching_indices.append(i)
            return matching_indices
        
        # Ordered sequence pattern - find consecutive itemsets that contain the pattern in order
        pattern_indices = []
        pattern_idx = 0
        for i, itemset in enumerate(sequence_itemsets):
            itemset_items = itemset.split()
            if pattern_items[pattern_idx] in itemset_items:
                pattern_indices.append(i)
                pattern_idx += 1
                if pattern_idx >= len(pattern_items):
                    return pattern_indices
        return []
    
    # Extract pattern items for all rules
    pattern_itemsets_by_rule = []
    for rule in signal_rules:
        element = rule['element']
        pattern_itemsets = parse_pattern_itemsets(element)
        
        if len(pattern_itemsets) > 1:
            # Sequence of itemsets pattern like "{A B} {C} {E}"
            pattern_itemsets_by_rule.append(('itemset_sequence', pattern_itemsets))
        elif element.startswith('{') and element.endswith('}'):
            # Single itemset pattern like "{A B C}"
            pattern_items = set(element.strip('{}').split())
            pattern_itemsets_by_rule.append(('itemset', pattern_items))
        elif ' ' in element:
            # Ordered sequence pattern like "A B C"
            pattern_items = element.split()
            pattern_itemsets_by_rule.append(('ordered', pattern_items))
        else:
            # Single item pattern
            pattern_itemsets_by_rule.append(('single', [element]))
    
    # Shuffle sequences
    sequences_val = []
    y_true_val = []
    confidence_val = []
    
    for idx, row in df_final.iterrows():
        seq_str = row['sequence']
        class_label, itemsets = parse_kosarak_sequence(seq_str)
        
        if not itemsets:
            # Empty sequence, keep as is
            sequences_val.append(seq_str)
            y_true_val.append(row['y_true'])
            confidence_val.append(row['confidence'])
            continue
        
        # Identify which itemsets are part of patterns
        protected_indices = set()
        for rule_idx, rule in enumerate(signal_rules):
            element = rule['element']
            pattern_type, pattern_data = pattern_itemsets_by_rule[rule_idx]
            
            if pattern_type == 'itemset_sequence':
                # Find itemsets that form the itemset sequence pattern in order
                matching_indices = contains_itemset_sequence_pattern(itemsets, pattern_data)
                protected_indices.update(matching_indices)
            elif pattern_type == 'itemset':
                # Check each itemset to see if it contains all pattern items
                for i, itemset in enumerate(itemsets):
                    itemset_items = set(itemset.split())
                    if pattern_data.issubset(itemset_items):
                        protected_indices.add(i)
            elif pattern_type == 'ordered':
                # Find itemsets that form the ordered pattern
                matching_indices = contains_ordered_pattern(itemsets, element)
                protected_indices.update(matching_indices)
            else:  # single
                # Find itemsets containing the single item
                pattern_item = pattern_data[0]
                for i, itemset in enumerate(itemsets):
                    if pattern_item in itemset.split():
                        protected_indices.add(i)
        
        # Separate protected and shuffleable itemsets
        protected_itemsets = []
        shuffleable_itemsets = []
        protected_positions = []
        shuffleable_positions = []
        
        for i, itemset in enumerate(itemsets):
            if i in protected_indices:
                protected_itemsets.append((i, itemset))
                protected_positions.append(i)
            else:
                shuffleable_itemsets.append(itemset)
                shuffleable_positions.append(i)
        
        # Shuffle only the shuffleable itemsets
        np.random.shuffle(shuffleable_itemsets)
        
        # Reconstruct the sequence maintaining original positions
        new_itemsets = [None] * len(itemsets)
        shuffleable_idx = 0
        protected_idx = 0
        
        for i in range(len(itemsets)):
            if i in protected_indices:
                new_itemsets[i] = protected_itemsets[protected_idx][1]
                protected_idx += 1
            else:
                new_itemsets[i] = shuffleable_itemsets[shuffleable_idx]
                shuffleable_idx += 1
        
        # Reconstruct the sequence
        new_seq_str = reconstruct_kosarak_sequence(class_label, new_itemsets)
        sequences_val.append(new_seq_str)
        y_true_val.append(row['y_true'])
        confidence_val.append(row['confidence'])
    
    # Create validation dataframe
    df_final_val = pd.DataFrame({
        'sequence': sequences_val,
        'y_true': y_true_val,
        'confidence': confidence_val
    })
    
    verify_and_print_results(df_final_val, signal_rules, GLOBAL_AUC_X)
    sequences_val_str = df_final_val['sequence']
    np.savetxt(f"data/{args.filename}_validation.dat", sequences_val_str, fmt="%s")
    df_final_val.to_csv(f"data/{args.filename}_validation.csv", index=False)
    print(f"Arquivos de validação salvos em data/{args.filename}_validation.dat e data/{args.filename}_validation.csv")

if __name__ == "__main__":
    main()