from dataclasses import dataclass
import random
import DataClasses.Node as Node

@dataclass
class Cargo:
    id: int
    weight: float
    origin_port: Node
    destination_port: Node
    is_loaded: bool = False






