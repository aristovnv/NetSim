# Different types of Fuel with properties
from dataclasses import dataclass

@dataclass
class Fuel:
    def __init__(self, id, **kwargs):
        self.id = id 
        self.co2 = kwargs.get('co2', 1.0)
        self.kwt = kwargs.get('kwt', 1.0)