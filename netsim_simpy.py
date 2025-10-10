import simpy
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import random
from constants_target import *
from DataClasses import *
#import DataClasses.Node
from tools.utils import sample_distribution
# ---------------------------
# Gymnasium + SimPy environment
# ---------------------------

class MaritimeSimEnv(gym.Env):
    """
    Simple SimPy + Gymnasium environment.
    Each step corresponds to 1 day (default), vessel actions: idle or take route.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, time_step=1.0, seed=None, **kwarg):
        
        super().__init__()
        self.time_step = time_step
        self.rng = random.Random(seed)
        np.random.seed(seed or 0)

        # core data
        self.nodes = kwarg.get('node_list', {})
        self.routes = kwarg.get('route_list', {})
        self.route_legs = kwarg.get('route_legs_list', {})
        self.vessels = kwarg.get('vessel_list', {})
        self.products = kwarg.get('product_list', {})
        self.fuel = kwarg.get('fuel_list', {})

        # simpy environment
        self.simenv = simpy.Environment()
        self.current_time = 0.0
        self.episode_step = 0

        # inventory and demand
        self.node_inventory = {}
        self.demand_specs = {}

        self.delivered = 0.0
        self.costs = 0.0

        # ------------------
        # Define Gym spaces
        # ------------------
        self.num_vessels = len(self.vessels)
        self.num_routes = len(self.routes)
        # discrete action per vessel: 0=idle, 1..num_routes = route choice
        # NEED TO CHANGE IT 
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
        obs = self._get_obs()
        info = {}
        return obs, info

    def step(self, action):
        # interpret multi-vessel discrete actions
        #route_ids = list(self.routes.keys())
        '''
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
        '''
        terminated = True
        truncated = False
        reward = 100
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
    params = {}
    params['node_list'] = [Node(id = node_id, **node_data) for node_id, node_data in NODES.items()]
    params['route_legs_list'] = [RouteLeg(origin = origin_id, destination = destination_id, **route_legs_data) for (origin_id, destination_id), route_legs_data in ROUTE_LEGS.items()]
    #RouteLeg(nA, nB, distance=100, base_travel_time=2, congestion_factor=0.5)
    params['route_list'] = [Route(id = route_id, **route_data) for route_id, route_data in ROUTES.items()]
    #Route("A->B", [legAB])
    params['vessel_list'] = [Vessel(id = vessel_id, **vessel_data) for vessel_id, vessel_data in OWN_VESSELS.items()] 
    #Vessel("V1", 100, 500)
    params['fuel_list'] = [Fuel(id = fuel_id, **fuel_data) for fuel_id, fuel_data in FUELS.items()]
    #Fuel(1.0)    
    params['product_list'] = [Product(id = product_id, **product_data) for product_id, product_data in PRODUCTS.items()]
    
    #Product("oil")
    env = MaritimeSimEnv(time_step=1.0, seed=seed, **params)
    #env.set_node_inventory("A", "oil", 1000)
    #env.set_node_inventory("B", "oil", 0)
    #env.set_demand_spec("B", "oil", {"dist": "normal", "mu": 10, "sigma": 2})
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


