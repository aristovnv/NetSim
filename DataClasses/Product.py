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

    def get_weight(self, volume):
        return volume * self.density 

