from dataclasses import dataclass
from .ScoreMapper import ScoreMapper

@dataclass
class ProductManager:

    def __init__(self, score_fn, min_val=0, max_val=1):
        """
        score_fn: function(entity) -> raw numeric score
        min_val / max_val: used to scale score into [0,1] range
        """
        self.score_fn = score_fn
        self.min_val = min_val
        self.max_val = max_val    
        self.product_mappers = {}
        

    def build_for_nodes(self, node_products_dict):
        """
        node_products_dict: { node_id: [products] }
        """
        for node_id, products in node_products_dict.items():
            mapper = ScoreMapper()
            def score_fn(p):
                # Example: margin-based
                return p.revenue - p.cost
            mapper.build(products, self.score_fn, self.min_val, self.max_val)
            self.product_mappers[node_id] = mapper

    def decode(self, node_id, score, remove_if = True):
        return self.product_mappers[node_id].decode(score, remove_if)
