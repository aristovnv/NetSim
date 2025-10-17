from dataclasses import dataclass
from .ScoreMapper import ScoreMapper

@dataclass
class NextNodeManager:

    def __init__(self, score_fn, min_val=0, max_val=1):
        """
        score_fn: function(entity) -> raw numeric score
        min_val / max_val: used to scale score into [0,1] range
        """
        self.score_fn = score_fn
        self.min_val = min_val
        self.max_val = max_val    
        self.node_mappers = {}

    def build_for_nodes(self, transition_dict):
        """
        transition_dict: { current_node: [possible_next_nodes] }
        Each 'next node' object could include distance, expected profit, etc.
        """
        for node_id, next_nodes in transition_dict.items():
            mapper = ScoreMapper(f"next_from_{node_id}")
            def score_fn(n):
                # Example: prefer closer + profitable nodes
                return n.expected_profit / (1 + n.distance)
            mapper.build(next_nodes, self.min_val, self.max_val, self.score_fn)
            self.node_mappers[node_id] = mapper

    def decode(self, current_node, score, remove_if = True):
        return self.node_mappers[current_node].decode(score, remove_if)
