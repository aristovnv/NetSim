from dataclasses import dataclass
from .ScoreMapper import ScoreMapper

@dataclass
class RentManager:
    def __init__(self, score_fn, min_val=0, max_val=1):
        """
        score_fn: function(entity) -> raw numeric score
        min_val / max_val: used to scale score into [0,1] range
        """
        self.score_fn = score_fn
        self.min_val = min_val
        self.max_val = max_val    
        self.rent_mappers = {}

    def build_for_nodes(self, node_rent_dict):
        """
        node_rent_dict: { node_id: [vessels available at node] }
        Each vessel should have .id, .cost_per_day, .capacity, etc.
        """
        for node_id, rent in node_rent_dict.items():
            mapper = ScoreMapper(f"rent_node_{node_id}")
            def score_fn(v):
                # Example scoring function — customize freely
                return v.capacity / v.cost_per_day
            mapper.build(rent, self.min_val, self.max_val, self.score_fn)
            self.rent_mappers[node_id] = mapper

    def decode(self, node_id, score, remove_if = True):
        return self.rent_mappers[node_id].decode(score, remove_if)
