from dataclasses import dataclass

@dataclass
class Port:
    name: str
    x: float
    y: float
    
    def demurrage_cost(self, days):
        return 20 * days

@dataclass
class Vessel:
    name: str
    current_port: Port
    current_load: float
    max_load: float
    
    def speed(self):
        base_speed = 20
        load_factor = max(0.5, 1 - (self.current_load / self.max_load) * 0.5)
        return base_speed * load_factor
    
    def fuel_cost(self, distance):
        class_fuel_cost = 2
        return class_fuel_cost * distance
    
    def time(self, distance):
        vessel_speed = self.speed()
        return distance / vessel_speed
    
    def co2_cost(self, distance):
        return 3.0 * distance

@dataclass
class Cargo:
    id: int
    volume: float
    tmp_volume: float
    port: Port
    max_time: int
    price: int