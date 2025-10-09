from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

@dataclass
class Port:
    name: str
    x: float
    y: float

@dataclass
class Vessel:
    name: str
    capacity: float
    current_port: Optional[Port] = None
    fuel_max_capacity: float = 100.0
    fuel_level: float = 100.0
    cargo_onboard: float = 0.0

@dataclass
class Cargo:
    id: int
    weight: float
    origin_port: Port
    destination_port: Port
    is_loaded: bool = False