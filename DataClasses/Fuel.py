# Different types of Fuel with properties
from dataclasses import dataclass

@dataclass
class Fuel:
    def __init__(self, id, co2):
        self.id = id 
        self.co2 = co2