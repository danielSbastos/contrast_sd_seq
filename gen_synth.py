import argparse
import pandas as pd
import numpy as np
import re
from scipy.stats import norm
from scipy.special import expit
from sklearn.metrics import roc_auc_score
from src.file_handler import load_signal_rules, load_vocabulary


def parse_pattern_itemsets(pattern_str):
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


def format_itemsets_for_sequence(itemsets):
    """
    Convert a list of itemsets (tuples of tokens) into the textual format used
    by the Kosarak-like generator (items separated by spaces).
    """
    return [' '.join(itemset) for itemset in itemsets]


def sequence_string_to_itemsets(sequence_str):
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


def sequence_contains_pattern(sequence_str, pattern_itemsets):
    """
    Check whether the sequence string contains the given pattern (as a list of
    itemsets represented by tuples).
    """
    if not pattern_itemsets:
        return False

    parsed_sequence = sequence_string_to_itemsets(sequence_str)
    pattern_len = len(pattern_itemsets)

    if pattern_len == 0 or pattern_len > len(parsed_sequence):
        return False

    for start_idx in range(len(parsed_sequence) - pattern_len + 1):
        window = parsed_sequence[start_idx:start_idx + pattern_len]
        if window == pattern_itemsets:
            return True

    return False

def to_kosarak_format(class_label, sequence_data):
    """
    Converte uma sequência de itemsets para uma string no formato Kosarak-like (SPMF).
    """
    parts = [str(class_label)]
    for itemset_str in sequence_data:
        parts.append(itemset_str)
        parts.append("-1")
    parts.append("-2")
    return " ".join(parts)

def generate_sequences_with_scores_iterative(
    n_samples, 
    target_auc, 
    base_element=None, 
    vocabulary=None, 
    max_iter=50, 
    tolerance=0.001
):
    """
    Gera um subconjunto de dados com uma ROC AUC alvo específica.
    Modificado para lidar com itemsets (strings com espaços) como elementos.
    """
    if n_samples == 0:
        return pd.DataFrame({'sequence': [], 'y_true': [], 'confidence': []})
    mu_neg = 0.0
    sigma = 1.0
    delta_mu = norm.ppf(target_auc) * np.sqrt(2 * sigma**2)
    n_pos = n_samples // 2
    n_neg = n_samples - n_pos
    targets = np.array([1] * n_pos + [0] * n_neg)
    for i in range(max_iter):
        mu_pos = mu_neg + delta_mu
        scores_pos = np.random.normal(loc=mu_pos, scale=sigma, size=n_pos)
        scores_neg = np.random.normal(loc=mu_neg, scale=sigma, size=n_neg)
        confidence_scores = np.concatenate([scores_pos, scores_neg])
        current_auc = roc_auc_score(targets, confidence_scores)
        error = target_auc - current_auc
        if abs(error) < tolerance:
            break
        delta_mu += error * 1.5
    scaled_scores = expit(confidence_scores)
    # --- Fim da lógica de AUC ---

    sequences = []
    INTERNAL_DELIMITER = "|" 

    base_itemsets = format_itemsets_for_sequence(parse_pattern_itemsets(base_element)) if base_element else []

    for _ in range(n_samples):
        seq_length = np.random.randint(8, 15)
        
        current_vocab = [v for v in vocabulary if v != base_element]
        
        seq = np.random.choice(current_vocab, seq_length, replace=True).tolist()
        
        if base_itemsets:
            insert_pos = np.random.randint(0, len(seq) + 1)
            seq[insert_pos:insert_pos] = base_itemsets
            
        sequences.append(INTERNAL_DELIMITER.join(seq))

    kosarak_formatted_sequences = [to_kosarak_format("9", s.split(INTERNAL_DELIMITER)) for s in sequences]

    df = pd.DataFrame({
        'sequence': kosarak_formatted_sequences,
        'y_true': targets,
        'confidence': scaled_scores,
    })
    
    return df.sample(frac=1).reset_index(drop=True)

def find_optimal_auc_for_remainder(
    global_target_auc_X,
    df_subsets,
    n_remainder,
    vocabulary,
    tolerance=0.005,
    max_iter=100
):
    """
    Usa busca binária para encontrar a AUC do conjunto restante (Z) que resulta
    na AUC global X quando combinado com o subconjunto A.
    """
    print(f"Buscando AUC para o conjunto restante para atingir AUC global de {global_target_auc_X}...")
    
    low_auc_Z = 0.5
    high_auc_Z = 1.0
    df_final = pd.DataFrame()
    
    for i in range(max_iter):
        current_auc_Z = (low_auc_Z + high_auc_Z) / 2
        
        # Gera o conjunto restante com a AUC_Z atual
        df_remainder = generate_sequences_with_scores_iterative(
            n_samples=n_remainder,
            target_auc=current_auc_Z,
            base_element=None,
            vocabulary=vocabulary
        )
        
        # Combina os dataframes
        df_final = pd.concat([df_subsets, df_remainder], ignore_index=True)
        
        # Calcula a AUC global
        current_global_auc = roc_auc_score(df_final['y_true'], df_final['confidence'])
        
        print(f"Iter {i+1}: Testando AUC_Z={current_auc_Z:.4f} -> AUC Global={current_global_auc:.4f}")

        if abs(current_global_auc - global_target_auc_X) < tolerance:
            print("Solução encontrada!")
            return df_final, current_auc_Z
        
        if current_global_auc < global_target_auc_X:
            # Precisamos de um conjunto restante com maior poder de separação
            low_auc_Z = current_auc_Z
        else:
            # Precisamos de um conjunto restante com menor poder de separação
            high_auc_Z = current_auc_Z
            
    print("Máximo de iterações atingido. Retornando a melhor solução encontrada.")
    return df_final, current_auc_Z

# --- Parâmetros ---
parser = argparse.ArgumentParser(description="Gerador de sequências com AUC alvo")
parser.add_argument("--gauc", type=float, required=True, help="Target AUC para o conjunto final")
parser.add_argument("--voc", type=str, required=True, help="Caminho para o vocabulário")
parser.add_argument("--sig", type=str, required=True, help="Caminho para o arquivo de regras")
parser.add_argument("--maxseq", type=int, default=1000, help="Número máximo de sequências permitido")
parser.add_argument("--filename", type=str, default="synth_temp", help="Arquivo output")

args = parser.parse_args()

GLOBAL_AUC_X = args.gauc
VOCABULARY = load_vocabulary(args.voc)
signal_rules = load_signal_rules(args.sig)
total_sequences = sum(rule['quantity'] for rule in signal_rules) if signal_rules else 0
N_REMAINDER = max(args.maxseq - total_sequences, total_sequences or 800)

# --- Geração dos Dados ---

df_list = []
CLEANED_VOCABULARY = [v for v in VOCABULARY if v not in [rule['element'] for rule in signal_rules]]

# Gera os subconjuntos conforme as regras carregadas
for rule in signal_rules:
    element = rule['element']
    quantity = rule['quantity']
    target_auc = rule['target_auc']
    
    print(f"Gerando subconjunto com elemento '{element}' e AUC alvo de {target_auc}...")
    df_rule = generate_sequences_with_scores_iterative(
        n_samples=quantity,
        target_auc=target_auc,
        base_element=element,
        vocabulary=CLEANED_VOCABULARY
    )
    
    # Verifica a AUC do subconjunto gerado
    auc_actual = roc_auc_score(df_rule['y_true'], df_rule['confidence'])
    print(f"AUC real do subconjunto com '{element}': {auc_actual:.4f}\n")
    
    df_list.append(df_rule)

df_list_concatenated = pd.concat(df_list, ignore_index=True)

# 2. Encontrar a melhor AUC para o conjunto restante e gerar o dataframe final
df_final, final_auc_Z = find_optimal_auc_for_remainder(
    global_target_auc_X=GLOBAL_AUC_X,
    df_subsets=df_list_concatenated,
    n_remainder=N_REMAINDER,
    vocabulary=CLEANED_VOCABULARY,
)

print("\n--- Verificação Final ---")
final_global_auc = roc_auc_score(df_final['y_true'], df_final['confidence'])
print(f"AUC Global Alvo (X): {GLOBAL_AUC_X}")
print(f"AUC Global Final: {final_global_auc:.4f}")

for rule in signal_rules:
    element = rule['element']
    target_auc = rule['target_auc']

    pattern_itemsets = [tuple(sorted(itemset)) for itemset in parse_pattern_itemsets(element)]

    df_subsets_final = df_final[
        df_final['sequence'].apply(lambda seq: sequence_contains_pattern(seq, pattern_itemsets))
    ]
    
    if not df_subsets_final.empty:
        final_subset_auc = roc_auc_score(df_subsets_final['y_true'], df_subsets_final['confidence'])
        print(f"\nAUC do Subconjunto Alvo com '{element}': {target_auc}")
        print(f"AUC Final Verificada do Subconjunto: {final_subset_auc:.4f}")
        print(f"Número de sequências no subconjunto com '{element}': {len(df_subsets_final)}")
    else:
        print(f"\nAVISO: Nenhum subconjunto encontrado para o elemento '{element}' na verificação final.")

# Salvando os dados em um arquivo CSV
sequences = df_final['sequence']
np.savetxt(f"data/{args.filename}.dat", sequences, fmt="%s")
print("\nSequências salvas em 'data/synth.dat'")
df_final.to_csv(f"data/{args.filename}.csv", index=False)
print("Dataset final salvo em 'data/synth.csv'")
