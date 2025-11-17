# main.py
import re
import os
from collections import Counter

import argparse
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

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

    with open("config/vocabulary_noise.txt", "w", encoding="utf-8") as vf_noise:
        for tok in noise_tokens:
            vf_noise.write(f"{tok}\n")

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
    
    def is_itemset_pattern(itemset_str, pattern_element):
        """Check if an itemset contains a pattern element (for itemset patterns like {A B C})."""
        if pattern_element.startswith('{') and pattern_element.endswith('}'):
            pattern_items = set(pattern_element.strip('{}').split())
            itemset_items = set(itemset_str.split())
            return pattern_items.issubset(itemset_items)
        return False
    
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
        if element.startswith('{') and element.endswith('}'):
            # Itemset pattern
            pattern_items = set(element.strip('{}').split())
            pattern_itemsets_by_rule.append(('itemset', pattern_items))
        elif ' ' in element:
            # Ordered sequence pattern
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
            
            if pattern_type == 'itemset':
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

    try:
        import os
        os.makedirs("config", exist_ok=True)
        with open("config/vocabulary_validation.txt", "w", encoding="utf-8") as vf:
            for token in VOCABULARY:
                vf.write(f"{token}\n")
        print("Vocabulário de validação salvo em config/vocabulary_validation.txt")
    except Exception as e:
        print(f"Aviso: falha ao salvar config/vocabulary_validation.txt: {e}")


if __name__ == "__main__":
    main()