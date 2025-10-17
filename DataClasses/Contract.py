import numpy as np

class Contract:
    def __init__(self, id, revenue, cost, days):
        self.id = id
        self.revenue = revenue
        self.cost = cost
        self.days = days

    def score(self, min_val, max_val):
        raw = self.revenue - self.cost * self.days
        return np.clip((raw - min_val) / (max_val - min_val), 0, 1)
