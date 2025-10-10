import simpy
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import random
from constants_target import PORTS_TERMINAL, NODES, ROUTE_LEGS, ROUTES, OWN_VESSELS, DISTANCES, PORTS_TERMINAL
from vars import * 
# ---------------------------
# Core domain objects
# ---------------------------



# ---------------------------
# Demand / supply generator
# ---------------------------

def sample_distribution(spec: Dict[str, Any], rng: random.Random) -> float:
    dist = spec.get("dist", "normal")
    if dist == "normal":
        return max(0.0, rng.gauss(spec.get("mu", 0.0), spec.get("sigma", 1.0)))
    elif dist == "uniform":
        return rng.uniform(spec.get("low", 0.0), spec.get("high", 1.0))
    elif dist == "poisson":
        return float(np.random.poisson(spec.get("lam", 1.0)))
    else:
        return rng.random()


# ---------------------------
# Gymnasium + SimPy environment
# ---------------------------

class MaritimeSimEnv(gym.Env):
    """
    Simple SimPy + Gymnasium environment.
    Each step corresponds to 1 day (default), vessel actions: idle or take route.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, nodes, routes, vessels, products, fuel, time_step=1.0, seed=None):
        super().__init__()
        self.time_step = time_step
        self.rng = random.Random(seed)
        np.random.seed(seed or 0)

        # core data
        self.nodes = {n.id: n for n in nodes}
        self.routes = {r.id: r for r in routes}
        self.vessels = {v.id: v for v in vessels}
        self.products = {p.id: p for p in products}
        self.fuel = fuel

        # simpy environment
        self.simenv = simpy.Environment()
        self.current_time = 0.0
        self.episode_step = 0

        # inventory and demand
        self.node_inventory: Dict[Tuple[str, str], float] = {}
        self.demand_specs: Dict[Tuple[str, str], Dict[str, Any]] = {}

        self.delivered = 0.0
        self.costs = 0.0

        # ------------------
        # Define Gym spaces
        # ------------------
        self.num_vessels = len(vessels)
        self.num_routes = len(routes)
        # discrete action per vessel: 0=idle, 1..num_routes = route choice
        self.action_space = spaces.MultiDiscrete([self.num_routes + 1] * self.num_vessels)
        # observation space is simplified continuous vector (time, delivered, costs)
        self.observation_space = spaces.Box(
            low=0, high=np.inf, shape=(3,), dtype=np.float32
        )

    # ------------------
    # Helpers
    # ------------------

    def set_demand_spec(self, node_id, product_id, spec):
        self.demand_specs[(node_id, product_id)] = spec

    def set_node_inventory(self, node_id, product_id, amount):
        self.node_inventory[(node_id, product_id)] = amount

    # ------------------
    # Core Gym methods
    # ------------------

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.simenv = simpy.Environment()
        self.current_time = 0.0
        self.episode_step = 0
        self.delivered = 0.0
        self.costs = 0.0
        for v in self.vessels.values():
            v.cargo = {}
            v.location = random.choice(list(self.nodes.values()))
        obs = self._get_obs()
        info = {}
        return obs, info

    def step(self, action):
        # interpret multi-vessel discrete actions
        route_ids = list(self.routes.keys())
        for i, v_id in enumerate(self.vessels.keys()):
            a = action[i]
            vessel = self.vessels[v_id]
            if a == 0:
                # idle
                self.costs += vessel.cost_per_day * self.time_step
            else:
                rid = route_ids[a - 1]
                route = self.routes[rid]
                travel_time = sum(leg.travel_time() for leg in route.legs)
                self.simenv.timeout(min(travel_time, self.time_step))
                vessel.location = route.legs[-1].destination
                self.costs += vessel.cost_per_day * travel_time

        # apply random demand
        for (node_id, pid), spec in self.demand_specs.items():
            amt = sample_distribution(spec, self.rng)
            key = (node_id, pid)
            inv = self.node_inventory.get(key, 0.0)
            self.node_inventory[key] = max(0.0, inv - amt)

        self.current_time += self.time_step
        self.episode_step += 1

        reward = self.delivered - 0.001 * self.costs
        obs = self._get_obs()
        terminated = False
        truncated = False
        info = {}
        return obs, reward, terminated, truncated, info

    def _get_obs(self):
        return np.array(
            [self.current_time, self.delivered, self.costs],
            dtype=np.float32
        )

    def render(self):
        print(f"t={self.current_time:.1f}, delivered={self.delivered:.1f}, costs={self.costs:.1f}")

# ---------------------------
# Demo builder
# ---------------------------

def build_demo_env(seed=0):
    nA = Node("A", "port_load")
    nB = Node("B", "port_unload")
    legAB = RouteLeg(nA, nB, distance=100, base_travel_time=2, congestion_factor=0.5)
    route = Route("A->B", [legAB])
    v1 = Vessel("V1", 100, 500)
    fuel = Fuel(1.0)
    prod = Product("oil")
    env = MaritimeSimEnv([nA, nB], [route], [v1], [prod], fuel, time_step=1.0, seed=seed)
    env.set_node_inventory("A", "oil", 1000)
    env.set_node_inventory("B", "oil", 0)
    env.set_demand_spec("B", "oil", {"dist": "normal", "mu": 10, "sigma": 2})
    return env

# ---------------------------
# Run demo
# ---------------------------

if __name__ == "__main__":
    env = build_demo_env()
    obs, info = env.reset()
    print("Initial obs:", obs)
    for step in range(5):
        # random action (0 = idle, 1 = route)
        action = env.action_space.sample()
        obs, reward, done, trunc, info = env.step(action)
        print(f"Step {step+1}: action={action}, obs={obs}, reward={reward:.3f}")
        env.render()
