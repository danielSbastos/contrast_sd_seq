# src/file_handler.py

import json
from typing import List, Dict

def load_signal_rules(file_path: str) -> List[Dict]:
    """
    Carrega e valida as regras de sinalização de um arquivo JSON.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)

        if not isinstance(rules, list):
            print(f"Format Error: The content of '{file_path}' must be a JSON list ([...]).")
            return []

        required_keys = {"element", "quantity", "target_auc"}
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict) or not required_keys.issubset(rule.keys()):
                print(f"Format Error: Item {i} in '{file_path}' does not contain the required keys: {required_keys}.")
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