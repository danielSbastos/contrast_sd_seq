# main.py
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
    # --- 1. Configuração e Carregamento de Dados ---
    parser = argparse.ArgumentParser(description="Gerador de sequências com AUC alvo")
    parser.add_argument("--gauc", type=float, required=True, help="Target AUC para o conjunto final")
    parser.add_argument("--voc", type=str, required=True, help="Caminho para o vocabulário")
    parser.add_argument("--sig", type=str, required=True, help="Caminho para o arquivo de regras")
    parser.add_argument("--maxseq", type=int, default=1000, help="Número máximo de sequências permitido")
    parser.add_argument("--gen-itemsets", action='store_true', help="Se especificado, gera itemsets aleatórios no ruído de fundo.")
    
    # --- ARGUMENTO MODIFICADO ---
    parser.add_argument(
        "--noise-density", 
        type=float, 
        default=1.0, 
        help="Densidade do ruído (0.0 a 1.0). 1.0 = denso (padrões aleatórios se formam). 0.0 = esparso (itens de ruído são únicos)."
    )
    args = parser.parse_args()
    
    # Validação da nova flag
    if not 0.0 <= args.noise_density <= 1.0:
        raise ValueError("--noise-density deve estar entre 0.0 e 1.0")

    GLOBAL_AUC_X = args.gauc
    VOCABULARY = load_vocabulary(args.voc)
    signal_rules = load_signal_rules(args.sig)
    
    total_sequences_rules = sum(rule['quantity'] for rule in signal_rules) if signal_rules else 0
    N_REMAINDER = max(args.maxseq - total_sequences_rules, total_sequences_rules or 800)
    
    CLEANED_VOCABULARY = get_clean_vocabulary(VOCABULARY, signal_rules)

    # --- 2. Geração dos Subconjuntos de "Sinal" ---
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

    # --- 3. Geração do Subconjunto de "Ruído" e Combinação Final ---
    df_final = find_optimal_auc_for_remainder(
        global_target_auc=GLOBAL_AUC_X,
        df_subsets=df_rules_concatenated,
        n_remainder=N_REMAINDER,
        vocabulary=CLEANED_VOCABULARY,
        allow_itemsets=args.gen_itemsets,
        noise_density=args.noise_density  # Passa a nova flag
    )

    # --- 4. Verificação e Salvamento ---
    verify_and_print_results(df_final, signal_rules, GLOBAL_AUC_X)
    sequences = df_final['sequence']
    np.savetxt("data/synth.dat", sequences, fmt="%s")
    print("\nSequências salvas em 'data/synth.dat'")
    df_final.to_csv("data/synth.csv", index=False)
    print("Dataset final salvo em 'data/synth.csv'")

if __name__ == "__main__":
    main()