from ast import Raise
from opt_einsum import contract
import simpy
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import random
from constants_target import *
from DataClasses import *
#import DataClasses.Node
from tools.utils import sample_distribution
import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
#remove for running - just to 
from .DataClasses import Vessel, Node, Fuel, Product, Route, RouteLeg, RentManager,ContractManager,ProductManager, NextNodeManager
from .DataClasses import Day
# ---------------------------
# Gymnasium + SimPy environment
# ---------------------------

CONTRACT_SCORE_MIN_VAL = -200 
CONTRACT_SCORE_MAX_VAL = 200
NODE_SCORE_MIN_VAL = -200 
NODE_SCORE_MAX_VAL = 200
PRODUCT_SCORE_MIN_VAL = -200 
PRODUCT_SCORE_MAX_VAL = 200
RENT_SCORE_MIN_VAL = -200 
RENT_SCORE_MAX_VAL = 200


def get_fading_prob(update_num):
    # Define probability for each update step 
    prob_map = {
        0: 0.30,  # 30%
        1: 0.10,  # 10% 
        2: 0.05,  # 5%
        3: 0.03,  # 3%
        4: 0.02,  # 2%
        5: 0.01,  # 1%
        6: 0.005, # 0.5%
        7: 0.0    # 0%
    }
    
    current_prob = prob_map.get(update_num, 0.0)
    return 1 if random.random() < current_prob else 0


class MaritimeSimEnv(gym.Env):
    """
    Simple SimPy + Gymnasium environment.
    Each step corresponds to 1 day (default), vessel actions: idle or take route.
    """
    metadata = {"render_modes": ["human"]}
    # Discrete actions - one-hot encoding
    discrete_actions = ['go_to', 'load', 'unload', 'stay', 'loan']
    # Continuous actions - random values between 0 and 1
    continuous_actions = ['product', 'product_qty', 'node', 'loan_contract']

    node_discrete_actions = ['rent']
    # Continuous actions - random values between 0 and 1
    node_continuous_actions = ['rent_contract', 'product', 'product_qty', 'node']
    rent_threshold = 0.8

    def __init__(self, time_step=1.0, seed=None, **kwarg):
        
        super().__init__()
        self.time_step = time_step
        self.current_day = Day(day=kwarg.get('day', 17), month=kwarg.get('month', 10), year=kwarg.get('year', 2025))
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
        #self.action_space = spaces.MultiDiscrete([self.num_routes + 1] * self.num_vessels)
        self.discrete_actions_len = len(self.discrete_actions)
        self.continuous_actions_len = len(self.continuous_actions)
        self.actions_len = self.discrete_actions_len + self.continuous_actions_len

        self.node_discrete_actions_len = len(self.node_discrete_actions)
        self.node_continuous_actions_len = len(self.node_continuous_actions)
        self.node_actions_len = self.node_discrete_actions_len + self.node_continuous_actions_len

        self.action_space = spaces.Dict({
            'discrete': spaces.MultiBinary(self.discrete_actions_len),
            'continuous': spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(self.continuous_actions_len,),
                dtype=np.float32
            )
        })
        self.node_action_space = spaces.Dict({
            'discrete': spaces.MultiBinary(self.node_discrete_actions_len),
            'continuous': spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(self.node_continuous_actions_len,),
                dtype=np.float32
            )
        })

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
        # so, at every step we have to do net things:
        # 2. for every ship:
        #     check if previous action has ended and it is time to pick new one
        #     pick new action from the list and start changing the state
        # 3. Control that physics works (?)    
        # interpret multi-vessel discrete actions
        #route_ids = list(self.routes.keys())
        self.current_day.add_day()
        # Manager knows how to score vessels
        self.rent_mgr = RentManager(score_fn=lambda v: v.capacity / v.cost_per_day, min_val=RENT_SCORE_MIN_VAL, max_val=RENT_SCORE_MAX_VAL)
        # Build fresh mapper for this step
        self.rent_mgr.build_for_nodes(self.get_rents())
        # Manager knows how to score vessels
        self.node_mgr = NextNodeManager(score_fn=lambda v: v.capacity / v.cost_per_day, min_val=NODE_SCORE_MIN_VAL, max_val=NODE_SCORE_MAX_VAL)
        # Build fresh mapper for this step
        self.rent_mgr.build_for_nodes(self.get_nodes())
        # Manager knows how to score vessels
        self.product_mgr = ProductManager(score_fn=lambda v: v.capacity / v.cost_per_day, min_val=PRODUCT_SCORE_MIN_VAL, max_val=PRODUCT_SCORE_MAX_VAL)
        # Build fresh mapper for this step
        self.product_mgr.build_for_nodes(self.get_products())
        # Manager knows how to score vessels
        self.contract_mgr = ContractManager(score_fn=lambda v: v.capacity / v.cost_per_day, min_val=CONTRACT_SCORE_MIN_VAL, max_val=CONTRACT_SCORE_MAX_VAL)
        # Build fresh mapper for this step
        self.contract_mgr.build_for_nodes(self.get_contracts())
        

        for vessel in self.vessels:
            if self.ship_in_loan(vessel):
                self.change_expected_loan_days(vessel)
                continue
            action_probs = self.get_action_probs(vessel)
            decoded_actions = self.decode_vector_to_action(action_probs)
            print(f" for vessel {vessel} action list is {decoded_actions}")
            
            selected_action_idx = action_probs[:self.discrete_actions_len].index(max(action_probs[:self.discrete_actions_len]))
            picked_action = self.discrete_actions[selected_action_idx - 1]
            product, product_qty = self.get_product(decoded_actions['product'], decoded_actions['product_qty'])
            next_node = self.get_next_node(decoded_actions['next_node'])
            if picked_action == 'loan':
                self.get_loan_contract(vessel, decoded_actions['loan_contract'])
                self.ship_to_loan(vessel)
            elif picked_action == 'unload':
                self.empty_ship(vessel, product, product_qty)
                k = 1
            elif picked_action == 'load':
                self.load_product(vessel, product, product_qty, next_node)
            elif picked_action == 'go_to':
                self.go_to(vessel, next_node)
            #should be stay, but we don't do anything now
                

        for node in self.nodes:
            action_probs = self.get_node_action_probs(node)
            decoded_actions = self.decode_vector_to_action(action_probs, False)
            print(f" for vessel {node} action list is {decoded_actions}")
            
            selected_action_idx = action_probs[:self.node_discrete_actions_len].index(max(action_probs[:self.node_discrete_actions_len]))
            picked_action = self.node_discrete_actions[selected_action_idx - 1]
            picked_action = self.discrete_actions[selected_action_idx - 1]
            product, product_qty = self.get_product(decoded_actions['product'], decoded_actions['product_qty'])
            next_node = self.get_next_node(decoded_actions['next_node'])
            if picked_action == 'rent' and action_probs[selected_action_idx] > self.rent_threshold:
                contract = self.get_rent_contract(decoded_actions['rent_contract'])
                self.contract_to_rent(contract, product, product_qty, next_node)

            #see no other actions atm
        '''
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
        print(f"my meaningful status is ")

    def get_action_probs(self, Vessel: Vessel):
        # actions: 
        #   discrete: go_to, load, unload, stay,
        #   continuous: product, product_qty, node  
        discrete_vector = [0] * len(self.discrete_actions)
        
        # Randomly select one discrete action to activate
        selected_action_idx = random.randint(0, len(self.discrete_actions) - 1)
        discrete_vector[selected_action_idx] = 1
        
        continuous_vector = [random.random() for _ in range(len(self.continuous_actions))]
        
        # Combine discrete and continuous actions
        action_vector = discrete_vector + continuous_vector
        
        return action_vector
    
    def encode_action_to_vector(self, action_dict, isVessel = True):
        """
        Encodes a dictionary action to vector format with ALL discrete and continuous values.
        
        Args:
            action_dict: Dictionary with keys for ALL actions:
                Discrete: from self.discrete_actions or self.node_discrete_actions
                Continuous: from self.continuous_actions or self.node_continuous_actions
            isVessel: True (default):
                True - takes vessels actions
                False - takes nodes actions        
        Returns:
            List of values: [discrete_actions, continuous_actions]
        """
        if isVessel:
            discrete_actions = self.discrete_actions
            continuous_actions = self.continuous_actions
        else:
            discrete_actions = self.node_discrete_actions
            continuous_actions = self.node_continuous_actions

        # Get ALL discrete values
        discrete_vector = [action_dict.get(action, 0) for action in discrete_actions]
        
        # Get ALL continuous values
        continuous_vector = [action_dict.get(action, 0.0) for action in continuous_actions]
        
        return discrete_vector + continuous_vector
    
    def decode_vector_to_action(self, action_vector, isVessel = True):
        """
        Decodes a vector to dictionary format with ALL discrete and continuous values.
        
        Args:
            action_vector: List of values: [discrete+continuous]
            isVessel: True (default):
                True - takes vessels actions
                False - takes nodes actions        
        Returns:
            Dictionary with ALL keys: discrete_actions + continuous_actions
        """
        if isVessel:
            discrete_actions = self.discrete_actions
            continuous_actions = self.continuous_actions
            actions_len = self.actions_len
            discrete_actions_len = self.discrete_actions_len
        else:
            discrete_actions = self.node_discrete_actions
            continuous_actions = self.node_continuous_actions
            actions_len = self.node_actions_len
            discrete_actions_len = self.node_discrete_actions_len

        if len(action_vector) != actions_len:
            raise ValueError(f"Action vector must have {actions_len} elements, got {len(action_vector)}")
        
        
        # Split vector into discrete and continuous parts
        discrete_part = action_vector[:discrete_actions_len]
        continuous_part = action_vector[discrete_actions_len:]
        
        # Create dictionary with ALL values
        action_dict = {}
        
        # Add ALL discrete actions
        for i, action in enumerate(discrete_actions):
            action_dict[action] = discrete_part[i]
        
        # Add ALL continuous actions
        for i, action in enumerate(continuous_actions):
            action_dict[action] = continuous_part[i]
        
        return action_dict
    
    # loan ships routine
    def ship_in_loan(self, vessel: Vessel):
        return vessel.is_in_loan
                
    def change_expected_loan_days(self, vessel: Vessel):
        # if qty = 1 -> set to random (0, (10 - updated_times) * some probability of late
        if vessel.days_left_in_loan > 1:
            vessel.decrease_loan_days
        else:
            new_days = get_fading_prob(vessel.update_loan_qty_times)
            if new_days == 0:
                vessel.return_from_loan
            else:
                vessel.update_loan_days(1)

    def get_loan_contract(self, encoded_loan, node):
        """
            Returns decoded contract from the list        
        """
        self.contract_mgr.decode(encoded_loan, node, remove_if=True)        
        assert 1==2, "function get_loan_contract is not implemented"
    def ship_to_loan(self, vessel):
        assert 1==2, "function ship_to_loan is not implemented"
    def empty_ship(self, vessel, product, product_volume):
        assert 1==2, "function empty_ship is not implemented"
    def get_product(self, product, product_qty):
        assert 1==2, "function get_product is not implemented"
        return product, product_qty
    def get_next_node(self, next_node):
        assert 1==2, "function get_next_node is not implemented"
        return next_node
    def load_product(self, vessel, product, product_volume, next_node):
        assert 1==2, "function load_product is not implemented"
    def go_to(self, vessel, next_node):
        assert 1==2, "function go_to is not implemented"
            

    # Node Parts
    def get_node_action_probs(self, node):
        assert 1==2, "function get_node_action_probs is not implemented"
    def get_rent_contract(self, rent_contract):
        assert 1==2, "function get_rent_contract is not implemented"
    def contract_to_rent(self, contract, product, product_qty, next_node):
        assert 1==2, "function contract_to_rent is not implemented"
    '''
    def get_node_product(self, product, product_qty):
        assert 1==2, "function get_product is not implemented"
        return product, product_qty
    def get_node_next_node(self, next_node):
        assert 1==2, "function get_next_node is not implemented"
        return next_node
    '''
    def get_rents(self):
        assert 1==2, "function get_rents is not implemented"
        rents = {}
        return rents
    
    def get_nodes(self):
        assert 1==2, "function get_nodes is not implemented"
        nodes = {}
        return nodes
    
    def get_products():
        assert 1==2, "function get_products is not implemented"
        products = {}
        return products
    
    def get_contracts(self):
        assert 1==2, "function get_contracts is not implemented"
        contracts = {}
        return contracts
        



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

    ray.init(ignore_reinit_error=True)

    config = (
        PPOConfig()
        .environment(env=build_demo_env(), env_config={"max_steps": 50})
        .rollouts(num_rollout_workers=2)
        .training(model={"fcnet_hiddens": [64, 64]}, train_batch_size=4000)
    )

    algo = config.build()

    for i in range(5):
        result = algo.train()
        print(f"Iteration {i}: reward_mean={result['episode_reward_mean']:.3f}")

    # Save checkpoint
    checkpoint = algo.save("rllib_checkpoints")
    print("Checkpoint saved:", checkpoint)
    '''
    # ---------- INFERENCE ----------
    env = build_demo_env()
    obs, _ = env.reset()
    terminated = False
    while not terminated:
        action = algo.compute_single_action(obs)
        obs, reward, terminated, truncated, _ = env.step(action)
        env.render()
    '''


