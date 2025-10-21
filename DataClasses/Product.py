# Products
from dataclasses import dataclass

@dataclass
class Product:
    def __init__(self, id, **kwargs):
        self.id = id
        self.density = kwargs.get('density', 1)
        self.type = kwargs.get('type', 'general')
        self.hazard_level = kwargs.get('hazard_level', 'low')
        self.evaporation_rate = kwargs.get('evaporation_rate', 0)
        self.viscosity = kwargs.get('viscosity', None)
        self.flash_point = kwargs.get('flash_point', None)
        self.storage_temp = kwargs.get('storage_temp', None)
        self.storage_pressure = kwargs.get('storage_pressure', None)
        self.demand_qty = kwargs.get('demand_qty', 0)
        self.demand_revenue = kwargs.get('demand_revenue', 0)
        self.demand_start_day = kwargs.get('semand_start_day', 0)
        self.supply_qty = kwargs.get('supply_qty', 0)
        self.supply_cost = kwargs.get('supply_cost', 0)
        self.supply_end_day = kwargs.get('supply_end_day', 0)


    def get_weight(self, volume):
        return volume * self.density 
    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Product({attrs})"