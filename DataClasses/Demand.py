# Vessels
from dataclasses import dataclass
PENALTY_FOR_MISSING_DEMAND = 50000
PENALTY_FOR_MISSING_DEMAND_PER_DAY = 5000

@dataclass
class Demand:
    def __init__(self, id, **kwargs):
        self.id = id
        self.product = kwargs.get('product', None)
        self.profit_per_volume = kwargs.get('profit_per_volume', 0)
        self.max_qty = kwargs.get('max_qty', 0)
        self.min_qty = kwargs.get('min_qty', 0)
        self.quantity = kwargs.get('quantity', 0)
        self.priority = kwargs.get('priority', 1000)
        self.start_date = kwargs.get('start_date', None)
        self.end_date = kwargs.get('end_date', None)
        self.lump_penalty = kwargs.get('lump_penalty', PENALTY_FOR_MISSING_DEMAND)
        self.day_penalty = kwargs.get('day_penalty', PENALTY_FOR_MISSING_DEMAND_PER_DAY)
        self.early_delivering = kwargs.get('early_delivering', False)
        self.early_delivering_penalty_per_day = kwargs.get('early_delivering_penalty_per_day', PENALTY_FOR_MISSING_DEMAND_PER_DAY / 2)

    def calculate_penalty(self, deliver_day, qty):
        if deliver_day > self.end_date:
                #penalty
            days = (deliver_day - self.end_date).days
            return (self.lump_penalty + days * self.day_penalty) * qty
        elif deliver_day < self.start_date:
                #penalty
            days = (self.start_date - deliver_day).days
            return days * self.early_delivering_penalty_per_day * qty
        return 0
    
    def calc_revenue(self, qty):
        return self.profit_per_volume * qty
    
    def calc_profit(self, deliver_day, qty):
        return self.calc_revenue(qty) - self.calculate_penalty(deliver_day, qty)
    
