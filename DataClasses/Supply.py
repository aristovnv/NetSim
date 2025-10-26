# Vessels
from dataclasses import dataclass
PENALTY_FOR_MISSING_SUPPLY = 50000
PENALTY_FOR_MISSING_SUPPLY_PER_DAY = 5000

@dataclass
class Supply:
    def __init__(self, id, **kwargs):
        self.id = id
        self.product = kwargs.get('product', None)
        self.cost_per_volume = kwargs.get('profit_per_volume', 0)
        self.max_qty = kwargs.get('max_qty', 0)
        self.min_qty = kwargs.get('min_qty', 0)
        self.quantity = kwargs.get('quantity', 0)
        self.priority = kwargs.get('priority', 1000)
        self.start_date = kwargs.get('start_date', None)
        self.end_date = kwargs.get('end_date', None)
        self.lump_penalty = kwargs.get('lump_penalty', PENALTY_FOR_MISSING_SUPPLY)
        self.day_penalty = kwargs.get('day_penalty', PENALTY_FOR_MISSING_SUPPLY_PER_DAY)

    def calculate_penalty(self, supply_day, qty):
        if supply_day > self.end_date:
                #penalty
            days = (supply_day - self.end_date)
            return (self.lump_penalty + days * self.day_penalty) * qty
        return 0
    
    def calc_cost(self, qty):
        return self.cost_per_volume * qty
    
    def calc_total_cost(self, load_day, qty):
        return self.calc_cost(qty) + self.calculate_penalty(load_day, qty)
    
    def decrease_supply(self, qty, current_date):
        if qty >= self.min_qty and qty <= self.max_qty:
            self.quantity = 0
            return qty, self.calc_total_cost(current_date, qty), True
        elif qty > self.max_qty:
            self.quantity = 0
            return self.max_qty, self.calc_total_cost(current_date, self.max_qty), True
        return qty, self.calc_total_cost(current_date, qty), False
    
