# src/utils.py

import re

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

def get_clean_vocabulary(vocabulary, signal_rules):
    """
    Remove todos os itens presentes nas regras de sinal do vocabulário principal.
    Lida com itens únicos, sequências ordenadas, itemsets ({A B C}) e sequências de itemsets ({A B} {C} {E}).
    """
    items_to_exclude = set()
    for rule in signal_rules:
        element = rule['element']
        
        # Check if it's a sequence of itemsets pattern like "{A B} {C} {E}"
        pattern_itemsets = _parse_pattern_itemsets(element)
        if len(pattern_itemsets) > 1:
            # Extract all items from all itemsets in the sequence
            for itemset in pattern_itemsets:
                items_to_exclude.update(itemset)
        elif element.startswith('{') and element.endswith('}'):
            # É um itemset: remove as chaves e divide
            items = element.strip('{}').split(' ')
            items_to_exclude.update(items)
        else:
            # É um item único ou uma sequência ordenada
            items = element.split(' ')
            items_to_exclude.update(items)
    
    cleaned_vocabulary = [v for v in vocabulary if v not in items_to_exclude]
    return cleaned_vocabulary