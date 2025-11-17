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
    parser.add_argument("--from-file", type=str, default=None, help="Usar dataset normal existente (.dat) para extrair tokens e gerar apenas _validation")
    
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
    df_final = None
    if args.from_file:
        existing_path = args.from_file
        if not existing_path.endswith(".dat"):
            candidate = os.path.join("data", f"{existing_path}.dat")
            if os.path.exists(candidate):
                existing_path = candidate
        if not os.path.exists(existing_path):
            raise FileNotFoundError(f"Arquivo normal existente não encontrado: {existing_path}")
        print(f"Carregando tokens do dataset existente: {existing_path}")
        print("Pulando geração do dataset normal - usando arquivo existente")
        with open(existing_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                for tok in parts[1:]:
                    if tok in ("-1", "-2"):
                        if tok == "-2":
                            break
                        continue
                    token_counts[tok] += 1
                    used_tokens.add(tok)
        print(f"Total de tokens únicos carregados do dataset existente: {len(used_tokens)}")
    else:
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

    try:
        os.makedirs("config", exist_ok=True)
        with open("config/vocabulary_noise.txt", "w", encoding="utf-8") as vf_noise:
            for tok in noise_tokens:
                vf_noise.write(f"{tok}\n")
        print("Vocabulário com ruído salvo em config/vocabulary_noise.txt")
    except Exception as e:
        print(f"Aviso: falha ao salvar config/vocabulary_noise.txt: {e}")

    print("\n--- Gerando Dataset de Validação ---")
    print(f"Usando distribuição de tokens do dataset normal (proporções preservadas)")
    df_list_val = []
    for rule in signal_rules:
        element, quantity, target_auc = rule['element'], rule['quantity'], rule['target_auc']
        df_rule_v = generate_sequences_with_scores(
            n_samples=quantity,
            target_auc=target_auc,
            base_element=element,
            vocabulary=CLEANED_VOCABULARY,
            allow_itemsets=args.gen_itemsets,
            noise_density=args.noise_density,
            frozen_vocabulary=list(noise_tokens),
            frozen_vocabulary_probs=noise_token_probs
        )
        df_list_val.append(df_rule_v)
    df_rules_val = pd.concat(df_list_val, ignore_index=True)
    
    df_final_val = find_optimal_auc_for_remainder(
        global_target_auc=GLOBAL_AUC_X,
        df_subsets=df_rules_val,
        n_remainder=N_REMAINDER,
        vocabulary=CLEANED_VOCABULARY,
        allow_itemsets=args.gen_itemsets,
        noise_density=args.noise_density,
        frozen_vocabulary=list(noise_tokens),
        frozen_vocabulary_probs=noise_token_probs,
        tolerance=0.01,
        max_iter=30 
    )
    verify_and_print_results(df_final_val, signal_rules, GLOBAL_AUC_X)
    sequences_val = df_final_val['sequence']
    np.savetxt(f"data/{args.filename}_validation.dat", sequences_val, fmt="%s")
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