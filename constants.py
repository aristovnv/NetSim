from vars import Port, Vessel, Cargo
import random

PORTS = (
    Port("Houston", 0.0, 0.0),
    Port("Miami", 80.0, 20.0),
    Port("New York", 150.0, 0.0),
    Port("New Jersey", 60.0, -60.0),
    Port("Seattle", 140.0, -80.0),
)

VESSEL = Vessel("Vessel_A", 100.0, current_port=PORTS[0], fuel_max_capacity=100, fuel_level=100, cargo_onboard=0)

CARGOS = (
    Cargo(i, random.randint(1, 100), random.choice(PORTS), random.choice(PORTS)) for i in range(10)
)