# Products
from dataclasses import dataclass

@dataclass
class Product:
    def __init__(self, id, density):
        self.id = id
        self.density = density 

    def get_weight(self, volume):
        return volume * self.density 

