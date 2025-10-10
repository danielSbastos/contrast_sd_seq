# src/file_handler.py

import json
from typing import List, Dict

def load_signal_rules(file_path: str) -> List[Dict]:
    """
    Carrega e valida as regras de sinalização de um arquivo JSON.
    Suporta dois formatos:
    1. Com 'element': para injetar um itemset único
    2. Com 'pattern': para injetar um padrão sequencial (lista de itemsets)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)

        if not isinstance(rules, list):
            print(f"Format Error: The content of '{file_path}' must be a JSON list ([...]).")
            return []

        base_required_keys = {"quantity", "target_auc"}
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                print(f"Format Error: Item {i} in '{file_path}' is not a dictionary.")
                return []
            
            # Verificar se tem as chaves base
            if not base_required_keys.issubset(rule.keys()):
                print(f"Format Error: Item {i} in '{file_path}' does not contain the required keys: {base_required_keys}.")
                return []
            
            # Verificar se tem 'element' OU 'pattern'
            has_element = 'element' in rule
            has_pattern = 'pattern' in rule
            
            if not has_element and not has_pattern:
                print(f"Format Error: Item {i} in '{file_path}' must have either 'element' or 'pattern' key.")
                return []
            
            if has_element and has_pattern:
                print(f"Format Error: Item {i} in '{file_path}' cannot have both 'element' and 'pattern' keys.")
                return []
            
            # Validar formato de 'pattern' se presente
            if has_pattern:
                if not isinstance(rule['pattern'], list):
                    print(f"Format Error: Item {i} in '{file_path}' has 'pattern' that is not a list.")
                    return []
                if len(rule['pattern']) == 0:
                    print(f"Format Error: Item {i} in '{file_path}' has empty 'pattern' list.")
                    return []
                for j, itemset in enumerate(rule['pattern']):
                    if not isinstance(itemset, str):
                        print(f"Format Error: Item {i}, pattern element {j} in '{file_path}' is not a string.")
                        return []
            
        return rules
    
    except Exception as e:
        print(f"An unexpected error occurred while loading '{file_path}': {e}")
        return []
    
def load_vocabulary(file_path):
    """
    Carrega o vocabulário de um arquivo de texto.
    """
    try:
        with open(file_path, 'r') as f:
            vocab = [line.strip() for line in f if line.strip()]
        return vocab
    except Exception as e:
        print(f"Erro ao carregar o vocabulário: {e}")
        return ['T', 'U', 'V', 'W', 'X', 'Y', 'Z']  # Default vocabulary