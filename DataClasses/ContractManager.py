from dataclasses import dataclass
from .ScoreMapper import ScoreMapper

@dataclass
class ContractManager:
    def __init__(self, score_fn, min_val=0, max_val=1):
        """
        score_fn: function(entity) -> raw numeric score
        min_val / max_val: used to scale score into [0,1] range
        """
        self.score_fn = score_fn
        self.min_val = min_val
        self.max_val = max_val    
        self.contract_mappers = {}

    def decode(self, current_node, score, remove_if = True):
        return self.contract_mappers[current_node].decode(score, remove_if)

    def build_for_nodes(self, node_contract_dict):
        """
        node_contract_dict: { node_id: [contracts] }
        """
        for node_id, contracts in node_contract_dict.items():
            mapper = ScoreMapper()
            def score_fn(p):
                # Example: margin-based
                return p.revenue - p.cost
            mapper.build(contracts, self.score_fn, self.min_val, self.max_val)
            self.contract_mappers[node_id] = mapper
