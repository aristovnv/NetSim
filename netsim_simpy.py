from ast import Raise
from opt_einsum import contract
import simpy
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import random
from constants_target import *
from DataClasses import *
from tools.utils import sample_distribution
import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
from tools import StepDataGenerator
from datetime import date, timedelta
#remove for running
#from .DataClasses import Vessel, Node, Fuel, Product, Route, RouteLeg, RentManager,ContractManager,ProductManager, NextNodeManager
#from .DataClasses import Day
# ---------------------------
# Gymnasium + SimPy environment
# ---------------------------


TRANSHIPMENT_ALLOWANCE_DAY = 5
TRANSHIPMENT_PENALTY_LAMP = 10000
TRANSHIPMENT_PENALTY_PER_DAY = 5000
CONTRACT_SCORE_MIN_VAL = -200 
CONTRACT_SCORE_MAX_VAL = 200
NODE_SCORE_MIN_VAL = -200 
NODE_SCORE_MAX_VAL = 200
PRODUCT_SCORE_MIN_VAL = -200 
PRODUCT_SCORE_MAX_VAL = 200
RENT_SCORE_MIN_VAL = -200 
RENT_SCORE_MAX_VAL = 200
UNLOAD_NOT_AT_NODE_PENALTY = -100000
LOAD_NOT_AT_NODE_PENALTY = -100000
PENALTY_FOR_EMPTY_EMPTY_SHIP = -100000
PENALTY_FOR_LOAD_ZERO_QTY = -100000

TERMINAL_NODES = [Node("Rotterdam"), Node("Brazil"), Node("Africa"), Node("Houston"), Node("NewYork")]

RANDOM_SIMULATION = True
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
    continuous_actions = ['product', 'product_qty', 'next_node', 'loan_contract']

    node_discrete_actions = ['rent']
    # Continuous actions - random values between 0 and 1
    node_continuous_actions = ['rent_contract', 'product', 'product_qty', 'next_node']
    rent_threshold = 0.8
    available_vessel_types = ["Panamax", "Capesize", "Handysize", "Supramax", "VLCC"]
        
    # Terminal nodes (example)
    terminal_nodes = TERMINAL_NODES
    def __init__(self, time_step=1.0, seed=None, **kwarg):
        
        super().__init__()
        self.time_step = time_step
        self.current_day = Day(day=kwarg.get('day', 17), month=kwarg.get('month', 10), year=kwarg.get('year', 2025))
        self.rng = random.Random(seed)
        np.random.seed(seed or 0)

        # core data
        self.nodes = kwarg.get('node_list', {})
        self.node_map = {node.id: node for node in self.nodes}
        self.routes = kwarg.get('route_list', {})
        self.route_map = {route.id: route for route in self.routes}
        self.route_legs = kwarg.get('route_legs_list', {})
        #self.route_leg_map = {route_leg.id: route_leg for route_leg in self.route_legs}
        self.vessels = kwarg.get('vessel_list', {})
        self.vessel_map = {vessel.id: vessel for vessel in self.vessels}
        self.products = kwarg.get('product_list', {})
        self.product_map = {product.id: product for product in self.products}
        self.fuel = kwarg.get('fuel_list', {})
        self.fuel_map = {fuel.id: fuel for fuel in self.fuel}

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
            'discrete': spaces.Discrete(self.discrete_actions_len),
            'continuous': spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(self.continuous_actions_len,),
                dtype=np.float32
            )
        })
        self.node_action_space = spaces.Dict({
            'discrete': spaces.Discrete(self.discrete_actions_len),
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
        self.demand_mgr = {}
        self.supply_mgr = {}
        self.travel_time_base = self._initialize_base_travel_times()
        self.travel_time_cache = {}
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
        current_travel_times = self.get_travel_time_matrix(self.current_day)
        stepDataGenerator = StepDataGenerator(self.terminal_nodes, self.products, self.vessels, self.current_day)
        self.demand_mgr = stepDataGenerator.update_demand_list(self.demand_mgr, self.current_day)
        self.supply_mgr = stepDataGenerator.update_supply_list(self.supply_mgr, self.current_day)
        # Manager knows how to score vessels
        self.rent_mgr = RentManager(score_fn=lambda v: v.revenue - v.cost_per_day * v.days, min_val=RENT_SCORE_MIN_VAL, max_val=RENT_SCORE_MAX_VAL)
        # Build fresh mapper for this step
        self.rent_mgr.build_for_nodes(stepDataGenerator.get_rental_list())
        # Manager knows how to score vessels
        self.node_mgr = NextNodeManager(score_fn=lambda v: 1000, min_val=NODE_SCORE_MIN_VAL, max_val=NODE_SCORE_MAX_VAL)
        # Build fresh mapper for this step
        self.node_mgr.build_for_nodes(stepDataGenerator.get_next_node_list())
        # Manager knows how to score vessels
        self.product_mgr = ProductManager(score_fn=lambda v: v.demand_revenue, min_val=PRODUCT_SCORE_MIN_VAL, max_val=PRODUCT_SCORE_MAX_VAL)
        # Build fresh mapper for this step
        self.product_mgr.build_for_nodes(stepDataGenerator.get_next_node_list())
        # Manager knows how to score vessels
        self.contract_mgr = ContractManager(score_fn=lambda v: v.revenue - v.cost_per_day * v.days, min_val=CONTRACT_SCORE_MIN_VAL, max_val=CONTRACT_SCORE_MAX_VAL)
        # Build fresh mapper for this step
        self.contract_mgr.build_for_nodes(stepDataGenerator.get_contract_list())
        
        vessels_to_remove = []
        for vessel in self.vessels:
            if self.ship_in_loan(vessel):
                self.change_expected_loan_days(vessel)
                continue
            action_probs = self.get_action_probs(vessel)
            decoded_actions = self.decode_vector_to_action(action_probs)
            print(f" for vessel {vessel} action list is {decoded_actions}")
            
            selected_action_idx = action_probs[:self.discrete_actions_len].index(max(action_probs[:self.discrete_actions_len]))
            picked_action = self.discrete_actions[selected_action_idx - 1]            
            next_node = self.get_next_node(vessel.current_node, decoded_actions['next_node'])
            product= self.get_product(next_node, decoded_actions['product'])
            if picked_action == 'loan':

                contract = self.get_loan_contract(vessel.current_node, decoded_actions['loan_contract'])
                self.ship_to_loan(vessel, contract)

            elif picked_action == 'unload':                
                self.empty_ship(vessel, product, decoded_actions["product_qty"])

            elif picked_action == 'load':
                self.load_product(vessel, product, decoded_actions["product_qty"], next_node)
            elif picked_action == 'go_to':
                self.go_to(vessel, next_node)

            if vessel.is_in_rent:
                #for now rented ship just go from a to b with possible demmurage
                
                if self.change_expected_rent_days(vessel):
                    vessels_to_remove.append(vessel)

        #remove vessels that are not leased        
        for v in vessels_to_remove:
            vessel = self.vessel_map.pop(v.id, None)
            if vessel:
                self.vessels.remove(vessel) 

        for node in self.nodes:
            action_probs = self.get_action_probs(obj = node, isVessel = False)
            decoded_actions = self.decode_vector_to_action(action_probs, False)
            print(f" for vessel {node} action list is {decoded_actions}")
            
            selected_action_idx = action_probs[:self.node_discrete_actions_len].index(max(action_probs[:self.node_discrete_actions_len]))
            picked_action = self.node_discrete_actions[selected_action_idx - 1]
            picked_action = self.discrete_actions[selected_action_idx - 1]
            
            next_node = self.get_next_node(node, decoded_actions['next_node'])
            product= self.get_product(next_node, decoded_actions['product'])
            if picked_action == 'rent' and action_probs[selected_action_idx] > self.rent_threshold:
                #getting rented vessel
                contract = self.get_rent_contract(decoded_actions['rent_contract'])
                self.contract_to_rent(contract, product, decoded_actions['product_qty'], next_node)

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

    def get_action_probs(self, obj, isVessel = True):
        # actions: 
        #   discrete: go_to, load, unload, stay,
        #   continuous: product, product_qty, node  
        if isVessel:
            discrete_actions = self.discrete_actions
            discrete_actions_len = self.discrete_actions_len
            continuous_actions_len = self.continuous_actions_len
        else:
            discrete_actions = self.node_discrete_actions
            discrete_actions_len = self.node_discrete_actions_len
            continuous_actions_len = self.node_continuous_actions_len

        discrete_vector = [0] * len(discrete_actions)
        
        # Randomly select one discrete action to activate
        selected_action_idx = random.randint(0, discrete_actions_len - 1)
        discrete_vector[selected_action_idx] = 1
        
        continuous_vector = [random.random() for _ in range(continuous_actions_len)]
        
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

    def change_expected_rent_days(self, vessel: Vessel):
        # if qty = 1 -> set to random (0, (10 - updated_times) * some probability of late
        if vessel.days_left_in_rent > 1:
            vessel.decrease_rent_days
        else:
            new_days = get_fading_prob(vessel.update_rent_qty_times)
            if new_days == 0:
                vessel.return_from_rent
                return True
            else:
                vessel.update_rent_days(1)
        return False

    def get_loan_contract(self, node, encoded_loan):
        """
            Returns decoded contract from the list        
        """
        return self.contract_mgr.decode(node, encoded_loan, remove_if=True)
        #assert 1==2, "function get_loan_contract is not implemented"

    def ship_to_loan(self, vessel, contract):
        if contract is None:
            print(f"vessel {vessel} can't be loaned - no available contracts")
        else:
            vessel.loaned(contract.days)

    def empty_ship(self, vessel, product, unload_percent):
        
        qty, cost_of_supply = vessel.unload(product, unload_percent)
        total_qty = qty
        if qty > 0.01: 
            # for all demands at current node ordered by max_date, profit decreased:
            if vessel.current_node is None:
                return UNLOAD_NOT_AT_NODE_PENALTY
            node_demand = self.demand_mgr[vessel.current_node.id]
            demand_to_remove = {}
            for demand in node_demand:
                qty_unloaded, profit, remove_demand = self.decrease_demand(demand, qty) 
                # remove demand, continue to the next if there is qty_unloaded < qty
                if remove_demand: 
                    demand_to_remove.append(demand)
                if abs(qty_unloaded - qty) < 0.01:
                    break
                else:
                    qty -= qty_unloaded

            for d in demand_to_remove:
                self.demand_mgr.remove(d) 
            total_cost = cost_of_supply
            cost_of_demand = (total_cost/total_qty) * (total_qty - qty)

            # we also need to add supply
            if qty > 0.01: 
                self.supply_mgr[vessel.current_node].append(
                    Supply(
                        id=f"supply_{vessel.current_node.id}_{self.current_date.strftime('%Y%m%d')}_from_vessel_{vessel.id}",
                        product = product,
                        cost_per_volume = total_cost - cost_of_demand, # need some cost from vessel
                        max_qty = qty * 1.1,  # Using + 10% of quantity as max_qty
                        min_qty = qty * 0.1,  # 10% of quantity as minimum
                        quantity = qty,
                        lump_penalty = TRANSHIPMENT_PENALTY_LAMP,
                        day_penalty = TRANSHIPMENT_PENALTY_PER_DAY,
                        start_date = self.current_day,
                        end_date = self.current_day  + timedelta(days = TRANSHIPMENT_ALLOWANCE_DAY)
                ))
            return profit-cost_of_demand
        else:
            return PENALTY_FOR_EMPTY_EMPTY_SHIP
        
    def decrease_demand(self, demand, qty):
        qty_satisfied, profit, remove_demand = demand.decrease_demand(qty, self.current_day)
        return qty_satisfied, profit, remove_demand
        
    def get_product(self, node, product):        
        idx = self.product_mgr.decode(node, product, remove_if=True)
        if idx is None:
            print(f"for {node} there is no available products")
            return None
        return self.product_map[idx]
        
    def get_next_node(self, node, next_node):
        idx = self.node_mgr.decode(node, next_node, remove_if=True)
        if idx is None:
            print(f"for {node} there is no next_node")
            return None
        return self.node_map[idx]
    
    def load_product(self, vessel, product, load_percent, next_node):
        qty = vessel.load(product, load_percent)
        # we also need to reduce supply at the moment
        # logic to decrease supply - by date of expiration or penalty cost?
        # for all supplies at current node ordered by max_date, penalty decreased:
        if qty > 0.01: 
            # for all demands at current node ordered by max_date, profit decreased:
            if vessel.current_node is None:
                return LOAD_NOT_AT_NODE_PENALTY
        
            node_supply = self.supply_mgr[vessel.current_node.id]
            supply_to_remove = {}
            for supply in node_supply:
                qty_loaded, cost_incured, remove_supply = self.decrease_supply(supply, qty) 
                vessel.update_demand_cost(cost_incured)
                # remove supply, continue to the next if there is qty_loaded < qty
                if remove_supply: 
                    supply_to_remove.append(supply)
                    if abs(qty_loaded - qty) < 0.01:
                        break
                    else:
                        qty -= qty_loaded

            for s in supply_to_remove:
                self.supply_mgr.remove(s) 
            
            vessel.next_node = next_node
            return 0
        else: 
            return PENALTY_FOR_LOAD_ZERO_QTY


    def decrease_supply(self, supply, qty):
        qty_loaded, cost_incured, remove_supply = supply.decrease_supply(qty, self.current_day)
        return qty_loaded, cost_incured, remove_supply

    def go_to(self, vessel, next_node):
        vessel.current_node = vessel.next_node
        vessel.next_node = next_node
            
    def get_rent_contract(self, node, rent_contract):
        return self.rent_mgr.decode(node, rent_contract, remove_if=True)

    def contract_to_rent(self, contract, product, product_qty, next_node, revenue):
        vessel = contract.vessel
        vessel.rented(contract.days, product, product_qty, next_node, contract.cost, revenue, contract.demurrage)
        self.vessels.append(vessel)
        self.vessel_map[vessel.id] = vessel
        
            
    def _initialize_base_travel_times(self):
        """Initialize base travel times between all node pairs (5-25 days)"""
        travel_times = {}
        node_ids = [node.id for node in self.nodes]
        
        for i, node_a in enumerate(node_ids):
            travel_times[node_a] = {}
            for j, node_b in enumerate(node_ids):
                if i == j:
                    travel_times[node_a][node_b] = 0  # Same node
                else:
                    # Random base travel time between 5-25 days
                    travel_times[node_a][node_b] = random.randint(5, 25)
        
        return travel_times


    def get_travel_time_matrix(self, current_date):
        """Get travel time matrix for specific date with 10% variation"""
        date_key = current_date.isoformat()
        
        # Return cached matrix if available
        if date_key in self.travel_time_cache:
            return self.travel_time_cache[date_key]
        
        # Generate new matrix with daily variation
        daily_matrix = {}
        for node_a in self.nodes:
            node_a_id = node_a.id
            daily_matrix[node_a_id] = {}
            
            for node_b in self.nodes:
                node_b_id = node_b.id
                base_time = self.travel_time_base[node_a_id][node_b_id]
                
                # Apply 10% variation (-10% to +10%)
                variation = random.uniform(0.9, 1.1)
                varied_time = max(1, round(base_time * variation))  # At least 1 day
                
                daily_matrix[node_a_id][node_b_id] = varied_time
        
        # Cache for this date
        self.travel_time_cache[date_key] = daily_matrix
        return daily_matrix
    
    def get_travel_time(self, node_a, node_b, current_date):
        """Get travel time between two specific nodes for a given date"""
        matrix = self.get_travel_time_matrix(current_date)
        return matrix[node_a.id][node_b.id]
    
    def clear_old_cache(self, keep_days=1):
        """Optional: Clear cache for old dates to prevent memory issues"""
        cutoff_date = date.today() - timedelta(days=keep_days)
        self.travel_time_cache = {
            k: v for k, v in self.travel_time_cache.items() 
            if date.fromisoformat(k) >= cutoff_date
        }

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
    params['vessel_list'] = [Vessel(id = vessel_id, current_node=random.choice(TERMINAL_NODES), **vessel_data) for vessel_id, vessel_data in OWN_VESSELS.items()] 
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
register_env("MaritimeSimEnv-v0", lambda config: MaritimeSimEnv(config))
if __name__ == "__main__":
    env = build_demo_env()
    obs, info = env.reset()
    print("Initial obs:", obs)
    if RANDOM_SIMULATION: 
        for step in range(5):
            # random action (0 = idle, 1 = route)
            action = env.action_space.sample()
            obs, reward, done, trunc, info = env.step(action)
            print(f"Step {step+1}: action={action}, obs={obs}, reward={reward:.3f}")
            env.render()

        exit()
    
    ray.init(ignore_reinit_error=True)

    algo = (
        PPOConfig()
        .environment(env="MaritimeSimEnv-v0", env_config={"max_steps": 50})
        .env_runners(num_env_runners=2)
        .training(model={"fcnet_hiddens": [64, 64]}, train_batch_size=4000).build()
    )

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


