import numpy as np
import gymnasium as gym
from gymnasium import spaces
from vars import Port, Cargo, Vessel
from typing import Optional
from gymnasium.utils.env_checker import check_env
import random
from copy import deepcopy

SEED = 123
random.seed(SEED)
np.random.seed(SEED)

class NetSim(gym.Env):
    def __init__(self, vessel: Vessel, ports: list[Port], cargos: list[Cargo]):
        super(NetSim, self).__init__()
        self.vessel = vessel
        self._vessel = deepcopy(vessel)
        self.ports = ports
        self._ports = deepcopy(ports)
        self.ports_index = {port.name: i for i, port in enumerate(ports)}
        self.num_ports = len(ports)
        self.cargos = cargos
        self._cargos = deepcopy(cargos)
        self.num_cargos = len(cargos)
        self.action_space: spaces.Discrete = spaces.Discrete(self.num_cargos + 1)
        self.observation_space = spaces.Box(shape=(self.num_cargos, 5), dtype=np.float32, low=0, high=1000)
        self.get_distance_matrix()
    
    def get_distance_matrix(self):
        self.distance_matrix = np.zeros((self.num_ports, self.num_ports))
        for i, port_a in enumerate(self.ports):
            for j, port_b in enumerate(self.ports):
                dist = np.sqrt((port_a.x - port_b.x) ** 2 + (port_a.y - port_b.y) ** 2)
                self.distance_matrix[i, j] = dist
    
    def _get_obs(self):
        observation = np.zeros((self.num_cargos, 5), dtype=np.float32)
        for i, cargo in enumerate(self.cargos):
            observation[i][0] = cargo.volume
            observation[i][1] = min(cargo.volume, self.vessel.current_load)
            observation[i][2] = max(cargo.max_time - self.time, 0)
            observation[i][3] = abs(cargo.port.x - self.vessel.current_port.x)
            observation[i][4] = abs(cargo.port.y - self.vessel.current_port.y)
        return observation
    
    def _get_info(self):
        action_mask = self.action_masks()
        return {'action_mask': action_mask}
    
    def action_masks(self):
        vessel = self.vessel
        action_mask = np.ones(self.num_cargos + 1)
        for i, cargo in enumerate(self.cargos):
            if cargo.volume <= 0 or vessel.current_port == cargo.port:
                action_mask[i] = 0
        if vessel.current_port == self.ports[0]:
            action_mask[-1] = 0
        return action_mask
    
    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)
        self.time = 0
        self.vessel = deepcopy(self._vessel)
        self.ports = deepcopy(self._ports)
        self.cargos = deepcopy(self._cargos)
        observation = self._get_obs()
        info = self._get_info()
        return observation, info
    
    def step(self, action):
        vessel = self.vessel
        current_port = vessel.current_port
        if action < self.num_cargos: # pick a cargo
            cargo: Cargo = self.cargos[action]
            next_port: Port = cargo.port
            distance = self._get_distance(current_port, next_port)
            fuel_cost = vessel.fuel_cost(distance)
            co2_cost = vessel.co2_cost(distance)
            time = int(round(vessel.time(distance), 0))
            amount_offload = min(vessel.current_load, cargo.volume)
            cargo.volume -= amount_offload
            vessel.current_load -= amount_offload
            demurrage_days = max(0, self.time + time - cargo.max_time)
            demurrage_cost = next_port.demurrage_cost(demurrage_days)
            cargo_revenue = amount_offload * cargo.price
        else: #back to load port
            next_port = self.ports[0]
            vessel.current_load = vessel.max_load
            distance = self._get_distance(current_port, next_port)
            time = int(round(vessel.time(distance), 0))
            fuel_cost = vessel.fuel_cost(distance)
            co2_cost = vessel.co2_cost(distance)
            cargo_revenue = 0
            demurrage_cost = 0
        observation = self._get_obs()
        reward = cargo_revenue - demurrage_cost - fuel_cost - co2_cost
        vessel.current_port = next_port
        self.time += time
        terminated = self._check_no_cargos_remaining()
        truncated = False
        info = self._get_info()
        return observation, reward, terminated, truncated, info

    def _check_no_cargos_remaining(self):
        return all(cargo.volume <= 0 for cargo in self.cargos)

    def _get_distance(self, current_port: Port, next_port: Port):
        return self.distance_matrix[self.ports_index[current_port.name], self.ports_index[next_port.name]]
    
    def render(self, mode='human'):
        if mode == 'human':
            print(f"Time: {self.time}, Vessel at {self.vessel.current_port.name} with load {self.vessel.current_load}")
        else:
            raise NotImplementedError(f"Render mode {mode} not implemented.")
        

def get_base_environment():

        LOAD_PORT = Port("Exxon", 0.0, 0.0)

        PORTS = [
            LOAD_PORT,
            Port("Houston", 30.0, 40.0),
            Port("Miami", 80.0, 20.0),
            Port("New York", 150.0, 0.0),
            Port("New Jersey", 60.0, -60.0),
            Port("Seattle", 140.0, -80.0),
        ]
        
        VESSEL = Vessel("Aframax", current_port = LOAD_PORT, current_load=100, max_load=100)

        CARGOS = []
        for i in range(5):
            port = PORTS[i + 1]
            volume = random.randint(11, 300)
            time_window = 5 + random.randint(5,20)
            price = random.randint(50,55)
            CARGOS.append(Cargo(i, volume, volume, port, time_window, price))
        env = NetSim(vessel=VESSEL, ports=PORTS, cargos=CARGOS)
        check_env(env)
        
        return env