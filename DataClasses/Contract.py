import numpy as np

class Contract:
    def __init__(self, id, **kwarg):
        self.id = id
        self.revenue = kwarg.get("revenue", 0)
        self.revenue_per_day = kwarg.get("revenue_per_day", 0)    
        self.demurrage_per_day = kwarg.get("demurrage_per_day", 0)
        self.cost_per_day = kwarg.get("cost_per_day", 0)
        self.days = kwarg.get("days", 0)
        self.final_node = kwarg.get("final_node", None)
        self.vessel = kwarg.get("vessel", None)

        if self.revenue == 0:
            self.revenue = self.revenue_per_day * self.days

    def score(self, min_val, max_val):
        raw = self.revenue - self.cost_per_day * self.days
        return np.clip((raw - min_val) / (max_val - min_val), 0, 1)
