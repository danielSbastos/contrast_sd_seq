"""
AuditLens weights integration: apply user-defined weights to MCTS tree exploration.
Weights can be provided as:
- Per-pattern: weight certain discovered patterns for deeper exploration
- Per-subtree: emphasize exploration of specific branches
- Per-attribute: focus on patterns with certain attributes (support, quality, etc.)
"""

import mctsextent.main as mcts_main
from typing import Dict, List, Optional, Tuple

class WeightManager:
    """Manage node weights for MCTS exploration focusing."""
    
    def __init__(self):
        self.node_weights: Dict[int, float] = {}  # id(node) -> weight multiplier
        self.pattern_weights: Dict[str, float] = {}  # pattern_str -> weight
        self.attribute_weights: Dict[str, float] = {}  # "support>100" -> weight
        self.parsed_attribute_weights: List[Tuple[str, str, float, float]] = []
    
    def compile_attribute_weights(self):
        """Pre-parse and compile attribute weight conditions to avoid string parsing in UCB loops."""
        self.parsed_attribute_weights = []
        for condition, weight in self.attribute_weights.items():
            try:
                if '>' in condition:
                    parts = condition.split('>')
                    attr = parts[0].strip()
                    threshold = float(parts[1].strip())
                    self.parsed_attribute_weights.append((attr, '>', threshold, weight))
                elif '<' in condition:
                    parts = condition.split('<')
                    attr = parts[0].strip()
                    threshold = float(parts[1].strip())
                    self.parsed_attribute_weights.append((attr, '<', threshold, weight))
                elif '=' in condition:
                    parts = condition.split('=')
                    attr = parts[0].strip()
                    threshold = float(parts[1].strip())
                    self.parsed_attribute_weights.append((attr, '=', threshold, weight))
            except Exception:
                pass

    def set_node_weight(self, node_id: int, weight: float):
        """Set weight for a specific node (by id)."""
        self.node_weights[node_id] = max(0.1, min(2.0, weight))  # Clamp to [0.1, 2.0]
    
    def clear_node_weights(self):
        """Reset all node weights."""
        self.node_weights.clear()
    
    def apply_weights_to_mcts(self):
        """Apply current weights to MCTS global state."""
        mcts_main.current_node_weights = dict(self.node_weights)
    
    def set_pattern_weight(self, pattern_descriptor: str, weight: float):
        """Mark a pattern for exploration (heavier = explore children more)."""
        self.pattern_weights[pattern_descriptor] = max(0.1, min(2.0, weight))
    
    def set_attribute_weight(self, condition: str, weight: float):
        """
        Set weights based on pattern attributes.
        Examples:
            "support>100" -> weight=1.5 (explore patterns with high support)
            "quality>0.8" -> weight=2.0 (explore high-quality patterns)
            "class_balance>0.7" -> weight=1.2 (explore balanced patterns)
        """
        self.attribute_weights[condition] = max(0.1, min(2.0, weight))
        self.compile_attribute_weights()
    
    def apply_attribute_filters(self, patterns: List) -> Dict[str, float]:
        """
        Evaluate attribute conditions on patterns and return weights.
        Returns: Dict[pattern_id, computed_weight]
        """
        result = {}
        
        if not self.attribute_weights:
            return result
        
        for pattern in patterns:
            weight_mult = 1.0
            
            for attr, op, threshold, attr_weight in self.parsed_attribute_weights:
                val = self._get_attribute_value(pattern, attr)
                if op == '>':
                    if val > threshold:
                        weight_mult *= attr_weight
                elif op == '<':
                    if val < threshold:
                        weight_mult *= attr_weight
                elif op == '=':
                    if abs(val - threshold) < 1e-5:
                        weight_mult *= attr_weight
            
            if weight_mult > 1.0:
                pattern_id = str(pattern.descriptor if hasattr(pattern, 'descriptor') else pattern)
                result[pattern_id] = weight_mult
        
        return result
    
    @staticmethod
    def _get_attribute_value(pattern, attr: str) -> float:
        """Helper to extract attribute value from either a search Node or PatternInfo/dict object."""
        try:
            # Check if it is a Node from mctsextent
            if hasattr(pattern, 'extend'):
                if attr == "support":
                    return float(len(pattern.extend)) if pattern.extend is not None else 0.0
                elif attr in ("quality", "quality_score"):
                    return float(pattern.quality) if pattern.quality is not None else 0.0
                elif attr in ("class_balance", "separation", "deviation"):
                    if pattern.extend is None:
                        return 0.0
                    # Cache subgroup error stats on Node instance to avoid heavy recomputations
                    if not hasattr(pattern, '_subgroup_error_stats'):
                        from general.utils import compute_subgroup_error_stats
                        pattern._subgroup_error_stats = compute_subgroup_error_stats(pattern.extend)
                    sg = pattern._subgroup_error_stats
                    if sg is None:
                        return 0.0
                    if attr == "class_balance":
                        sup = sg["size_class_0"] + sg["size_class_1"]
                        return float(sg["size_class_0"] / sup) if sup > 0 else 0.5
                    elif attr == "separation":
                        delta_g = abs(sg["error_class_0"] - sg["error_class_1"])
                        max_std = max(sg["std_class_0"], sg["std_class_1"])
                        return float(delta_g / (1.0 + max_std**2))
                    elif attr == "deviation":
                        return float(max(abs(sg["error_class_0"] - 0.3), abs(sg["error_class_1"] - 0.32)))
            
            # If it's a dictionary
            if isinstance(pattern, dict):
                if attr in pattern:
                    return float(pattern[attr])
                elif "attributes" in pattern and attr in pattern["attributes"]:
                    return float(pattern["attributes"][attr])
                return 0.0

            # If it has attributes dict (like PatternInfo or similar)
            if hasattr(pattern, "attributes") and isinstance(pattern.attributes, dict):
                if attr in pattern.attributes:
                    return float(pattern.attributes[attr])

            # Direct attribute fallback
            val = getattr(pattern, attr, None)
            if val is not None:
                return float(val)
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _eval_condition(condition: str, pattern) -> bool:
        """Evaluate a simple condition against a pattern or node."""
        try:
            parts = condition.split('>')
            if len(parts) == 2:
                attr, threshold = parts[0].strip(), float(parts[1].strip())
                val = WeightManager._get_attribute_value(pattern, attr)
                return val > threshold
            
            parts = condition.split('<')
            if len(parts) == 2:
                attr, threshold = parts[0].strip(), float(parts[1].strip())
                val = WeightManager._get_attribute_value(pattern, attr)
                return val < threshold

            parts = condition.split('=')
            if len(parts) == 2:
                attr, threshold = parts[0].strip(), float(parts[1].strip())
                val = WeightManager._get_attribute_value(pattern, attr)
                return abs(val - threshold) < 1e-5
        except Exception:
            pass
        
        return False
    
    def get_weights_dict(self) -> Dict[int, float]:
        """Get current weights as dict for MCTS."""
        return dict(self.node_weights)


# Global instance
_weight_manager = WeightManager()

def get_weight_manager() -> WeightManager:
    """Get the global weight manager instance."""
    return _weight_manager

def apply_auditlens_weights(weights_config: Dict) -> None:
    """
    Apply weights from AuditLens config.
    """
    mgr = get_weight_manager()
    
    if "nodes" in weights_config:
        mgr.node_weights = weights_config["nodes"]
    else:
        mgr.node_weights = {}
    
    if "patterns" in weights_config:
        mgr.pattern_weights = weights_config["patterns"]
    else:
        mgr.pattern_weights = {}
    
    if "attributes" in weights_config:
        mgr.attribute_weights = weights_config["attributes"]
    else:
        mgr.attribute_weights = {}
    
    mgr.compile_attribute_weights()
    mgr.apply_weights_to_mcts()

def focus_on_region(node_descriptor: str, intensity: float = 1.5) -> None:
    """
    High-level API: focus exploration on a specific tree region.
    """
    mgr = get_weight_manager()
    mgr.set_pattern_weight(node_descriptor, intensity)
    mgr.apply_weights_to_mcts()

def focus_on_attributes(attribute_filters: Dict[str, float]) -> None:
    """
    High-level API: focus on patterns matching certain attributes.
    """
    mgr = get_weight_manager()
    for attr, weight in attribute_filters.items():
        mgr.set_attribute_weight(attr, weight)
    mgr.compile_attribute_weights()
    mgr.apply_weights_to_mcts()

def reset_weights() -> None:
    """Clear all weights to uniform exploration."""
    mgr = get_weight_manager()
    mgr.clear_node_weights()
    mgr.pattern_weights.clear()
    mgr.attribute_weights.clear()
    mgr.compile_attribute_weights()
    mcts_main.current_node_weights = {}
