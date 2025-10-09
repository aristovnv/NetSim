import torch
import gymnasium as gym
import numpy as np
import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.env.multi_agent_env import MultiAgentEnv
from typing import Dict as TypingDict, List, Tuple, Any
from gymnasium.spaces import Discrete, Box, Dict, MultiDiscrete
from gymnasium.spaces.utils import flatten_space, flatten
from ray.rllib.algorithms.callbacks import DefaultCallbacks
import networkx as nx
import os
import signal
import pprint
import pickle 
import traceback

BATTERY_CAPACITY = 300.0
LEVEL2_CHARGING_RATE = 20.0
DCFAST_CHARGING_RATE = 200.0

GRAPH_MAPPINGS = {
    "node_to_index": None,
    "index_to_node": None
}


def get_node_to_index():
    if GRAPH_MAPPINGS["node_to_index"] is None:  # Proper None check
        raise RuntimeError("node to index mapping is None")  # Proper exception
    return GRAPH_MAPPINGS["node_to_index"]

def get_index_to_node():
    if GRAPH_MAPPINGS["index_to_node"] is None:  # Proper None check
        raise RuntimeError("index to node mapping is None")  # Proper exception
    return GRAPH_MAPPINGS["index_to_node"]


def get_route_sequence():
    return [
        [5026447875, 65657291, 5433392625],
        [54382864, 90796641],
        [9512913929, 49291774, 90810515],
        [9512913929, 90539746, 90403004],
        [9512913929, 353478871, 9509748626]]

path = os.getcwd()
def read_file(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

edge_distance_file = f"{path}/data/shortest_path_energy_dict.pkl" 
edge_time_file = f"{path}/data/shortest_path_time_dict.pkl" 
chargers_file = f"{path}/data/station_info_dict.pkl" 

isNew = True

checkpoint_dir = f"{path}/checkpoints"

def get_graph():
    if isNew:
        return get_graph_new()
    else:
        return get_graph_old()

def get_truck_configs():
    if isNew:
        return get_truck_configs_new()
    else:
        return get_truck_configs_old()

def fast_charger():
    return DCFAST_CHARGING_RATE

def slow_charger():
    return LEVEL_CHARGING_RATE

charger_function_map = {
        "fast": fast_charger,
        "slow": slow_charger
    }

# =============================================================================
# CONFIGURATION FUNCTIONS (Abstracted as requested)
# =============================================================================
class DebugCallback(DefaultCallbacks):
    def on_episode_end(self, *, episode, **kwargs):
        rewards = episode.get_rewards()
        total_reward = sum(sum(r) if isinstance(r, list) else r for r in rewards.values())

        print("📊 Episode ended.")
        for aid, r in rewards.items():
            total = sum(r) if isinstance(r, list) else r
            print(f"  - {aid}: {total:.2f}")
        print(f"💰 Total reward: {total_reward:.2f}")

        # ✅ This is the only place that works in your RLlib version
        episode.custom_data["total_reward"] = total_reward
def map_charger_type(station_type):
    """Map charger types to internal names."""
    if station_type == 'Level2':
        return 'slow'
    elif station_type == 'DCFC' or station_type == 'DCFast':
        return 'fast'
    return station_type  # Fallback for unknown types

def get_graph_new():
    edge_distance = read_file(edge_distance_file)
    edge_time = read_file(edge_time_file)
    chargers = read_file(chargers_file)

    """Build road network graph using index-based nodes (0,1,2,...)"""
    G = nx.DiGraph()
    all_nodes = set()
    
    # Collect all nodes from edges and chargers
    for (u, v) in edge_distance.keys():
        all_nodes.add(u)
        all_nodes.add(v)
    all_nodes.update(chargers.keys())
    
    # Create sorted list of nodes and mappings
    node_list = sorted(all_nodes)  # Sort for consistent ordering
    node_to_index = {node: idx for idx, node in enumerate(node_list)}
    index_to_node = {idx: node for node, idx in node_to_index.items()}
    
    # Process chargers - handle multiple types per node
    charger_aggregated = {}
    for node, info in chargers.items():
        # Handle single charger type per node
        if 'station_type' in info:
            mapped_type = map_charger_type(info['station_type'])
            count = int(info['total_capacity'])
            idx = node_to_index[node]
            charger_aggregated.setdefault(idx, {})[mapped_type] = count
        
        # Handle multiple charger types per node
        elif 'chargers' in info:
            for charger in info['chargers']:
                mapped_type = map_charger_type(charger['station_type'])
                count = int(charger['total_capacity'])
                idx = node_to_index[node]
                charger_aggregated.setdefault(idx, {})[mapped_type] = charger_aggregated.get(idx, {}).get(mapped_type, 0) + count
    
    # Add nodes with properties using INDEXES
    for idx in range(len(node_list)):
        if idx in charger_aggregated:
            props = {
                "has_charger": True,
                "charger_type": charger_aggregated[idx],
                "original_id": index_to_node[idx]  # Store original ID for reference
            }
        else:
            props = {
                "has_charger": False,
                "charger_type": None,
                "original_id": index_to_node[idx]  # Store original ID for reference
            }
        G.add_node(idx, **props)
    
    # Add edges with attributes using INDEXES
    for (u_orig, v_orig) in edge_distance.keys():
        u_idx = node_to_index[u_orig]
        v_idx = node_to_index[v_orig]
        distance = edge_distance[(u_orig, v_orig)]
        time_val = edge_time.get((u_orig, v_orig), 0)
        G.add_edge(u_idx, v_idx, distance=distance, time=time_val, terrain_factor=1.0)
    GRAPH_MAPPINGS["node_to_index"] = node_to_index
    GRAPH_MAPPINGS["index_to_node"] = index_to_node    
    return G

def get_graph_old():
    """Define the road network graph with charging stations."""
    G = nx.DiGraph()
    
    # Add nodes with properties
    G.add_nodes_from([
        (0, {"has_charger": False, "charger_type": None}),      # Start node
        (1, {"has_charger": True, "charger_type": {"slow":2, "fast":3}}),     # Charging station
        (2, {"has_charger": False, "charger_type": None}),      # Regular node
        (3, {"has_charger": True, "charger_type": {"fast":5}}),     # Charging station  
        (4, {"has_charger": False, "charger_type": None}),      # End node
        (5, {"has_charger": True, "charger_type": {"slow":1}}),     # Charging station
    ])
    
    # Add edges with distance and terrain difficulty
    edges = [
        (0, 1, {"distance": 10, "terrain_factor": 1.0}),
        (1, 2, {"distance": 15, "terrain_factor": 1.2}),
        (2, 3, {"distance": 8, "terrain_factor": 0.8}),
        (3, 4, {"distance": 12, "terrain_factor": 1.1}),
        (1, 3, {"distance": 20, "terrain_factor": 1.3}),
        (0, 2, {"distance": 18, "terrain_factor": 1.0}),
        (2, 5, {"distance": 6, "terrain_factor": 0.9}),
        (5, 4, {"distance": 9, "terrain_factor": 1.0}),
    ]
    G.add_edges_from([(u, v, attr) for u, v, attr in edges])
    
    return G

def get_truck_configs_new():
    """Define individual truck configurations based on route_sequence."""
    route_sequence = get_route_sequence()
    node_to_index = get_node_to_index()
    return [
        {
            "id": idx,
            "start_node": node_to_index[route[0]],   # Convert to index
            "end_node": node_to_index[route[-1]],     # Convert to index
            "initial_battery": BATTERY_CAPACITY,
            "truck_type": "standard"
        }
        for idx, route in enumerate(route_sequence)
    ]

def get_truck_configs_old():
    """Define individual truck configurations with start/end points."""
    return [
        {
            "id": 0,
            "start_node": 0,
            "end_node": 4,
            "initial_battery": 25.0,
            "truck_type": "standard"
        },
        {
            "id": 1, 
            "start_node": 0,
            "end_node": 5,
            "initial_battery": 20.0,
            "truck_type": "heavy"
        }
    ]
def get_charging_nodes(graph):
    """Get only nodes that have charging stations."""
    return [node for node, data in graph.nodes(data=True) if data["has_charger"]]

def get_transit_nodes(graph):
    """Get all nodes (for high-level routing)."""
    return list(graph.nodes())

def charge_standard(current_charge, time = 1):
    return 0.8 * time

def discharge_standard(current_charge, distance = 1):
    return 0.2 * distance

def get_truck_types():
    """Define truck type specifications."""
    return {
        "standard": {
            "battery_capacity": BATTERY_CAPACITY,
            "base_speed": 50.0,  # km/h
            "base_discharge_function": discharge_standard,  # battery per km
            "base_charge_function": charge_standard
        },
        "heavy": {
            "battery_capacity": BATTERY_CAPACITY,
            "base_speed": 40.0,
            "base_discharge_function": discharge_standard,  # battery per km
            "base_charge_function": charge_standard
        }
    }

# def get_charger_configs():
#    """Define charger specifications at each node."""
#    return {
#        1: {"type": "slow", "capacity": 1, "base_charge_rate": 5.0},   # 5 battery/hour
#        3: {"type": "fast", "capacity": 2, "base_charge_rate": 15.0},  # 15 battery/hour  
#        5: {"type": "fast", "capacity": 1, "base_charge_rate": 15.0},
#    }



def get_charger_configs(graph):
    
    """Extract charger capacities from graph nodes."""
    return {
        node: data["charger_type"]
        for node, data in graph.nodes(data=True)
        if data["has_charger"]
    }

def get_charger_occupancy_template(graph):
    """Initialize empty occupancy tracking structure."""
    return {
        node: {ctype: 0 for ctype in data["charger_type"]}
        for node, data in graph.nodes(data=True)
        if data["has_charger"]
    }
# =============================================================================
# CUSTOM DISCHARGE AND CHARGE FUNCTIONS
# =============================================================================

def discharge_function(truck_config: dict, edge_data: dict, travel_time: float, current_time: float) -> float:
    """Custom non-linear discharge function."""
    truck_type = get_truck_types()[truck_config["truck_type"]]
    
    # Base discharge based on distance and truck type
    base_discharge = truck_type["base_discharge_function"](truck_config["current_battery"], edge_data["distance"]) #edge_data["distance"] * truck_type["base_discharge_rate"]
    
    # Terrain factor affects discharge
    terrain_modifier = edge_data.get("terrain_factor", 1.0)
    
    # Time-based modifier (traffic/weather simulation)
    time_modifier = 1.0 #+ 0.1 * np.sin(current_time / 10.0)  # Varies with time
    
    # Non-linear battery efficiency (discharge increases as battery gets low)
    battery_efficiency = 1.0 #if truck_config["current_battery"] > 15 else 1.3
    
    total_discharge = base_discharge * terrain_modifier * time_modifier * battery_efficiency
    
    return max(0, total_discharge)

def charge_function(graph, truck_config: dict, charger_node: int, charge_time: float, current_time: float, charger_type) -> float:
    """Custom non-linear charge function."""
    charger_configs = get_charger_configs(graph)
    truck_types = get_truck_types()
    
    if charger_node not in charger_configs:
        return 0.0
        
    charger = charger_configs[charger_node]
    truck_type = truck_types[truck_config["truck_type"]]

    current_battery = truck_config["current_battery"]

    # Base charge rate
    print(f"truck_type is {truck_type}")
    base_charge = truck_type["base_charge_function"](current_battery, charge_time)# * charger_function_map[charger_type]
    
    # Truck charge efficiency
    efficiency = 1 #truck_type["charge_efficiency"]
    
    # Non-linear charging (slower as battery gets fuller)
    battery_capacity = truck_type["battery_capacity"]
    battery_ratio = current_battery / battery_capacity
    
    if battery_ratio < 0.5:
        charge_efficiency = 1.0
    elif battery_ratio < 0.8:
        charge_efficiency = 0.7
    else:
        charge_efficiency = 0.4
    charge_efficiency = 1
    # Time-based modifier (grid load simulation)
    time_modifier = 1.0 #- 0.2 * np.sin(current_time / 8.0)
    
    total_charge = base_charge * efficiency * charge_efficiency * time_modifier
    
    # Ensure we don't exceed battery capacity
    max_possible_charge = battery_capacity - current_battery
    
    return min(total_charge, max_possible_charge)

# =============================================================================
# ACTION AND OBSERVATION SPACES
# =============================================================================

def get_high_level_action_space(graph):
    """High-level agent chooses next node to route to."""
    return Discrete(graph.number_of_nodes())

def get_low_level_action_space():
    """Low-level agent manages charging decisions."""
    # 0: do nothing, 1: start charging, 2: stop charging, 3: wait for charger
    return Discrete(4)
MAX_CHARGERS = 100
def get_observation_space(graph):#, num_trucks):
    """Observation space for both agent levels."""
    num_nodes = graph.number_of_nodes()
    
    return Dict({
        #"truck_id": Discrete(num_trucks), random trucks
        "id": Box(0.0, 1.0, shape=(), dtype=np.float32),  # for debug
        "current_node": Discrete(num_nodes),
        "destination_node": Discrete(num_nodes),
        "battery_level": Box(0.0, BATTERY_CAPACITY, shape=(), dtype=np.float32),
        "battery_capacity": Box(0.0, BATTERY_CAPACITY, shape=(), dtype=np.float32),
        "is_charging": Discrete(2),
        "charger_available": Discrete(2),
        #"charger_occupancy": Box(0, 5, shape=(), dtype=np.float32),
        #"charger_capacity": Box(0, 5, shape=(), dtype=np.float32),
        "charger_occupancy_fast": Box(0.0, MAX_CHARGERS, (), np.float32),
        "charger_occupancy_slow": Box(0.0, MAX_CHARGERS, (), np.float32),        
        #"charger_capacity_fast": Box(0.0, MAX_CHARGERS, (), np.float32),
        #"charger_capacity_slow": Box(0.0, MAX_CHARGERS, (), np.float32),                
        "time_elapsed": Box(0.0, 1000.0, shape=(), dtype=np.float32),
        "waiting_time": Box(0.0, 800.0, shape=(), dtype=np.float32),
        "can_reach_destination": Discrete(2),
        "nearest_charger_distance": Box(0.0, 900.0, shape=(), dtype=np.float32),
    })

# =============================================================================
# REWARD FUNCTIONS
# =============================================================================

def reward_move_to_next_node():
    """Small reward for moving to next customer node."""
    return 2.0

def reward_finish_charging():
    """Medium reward for completing charging."""
    return 5.0

def reward_arrive_destination():
    """Big reward for reaching destination."""
    return 50.0

def penalty_wait_at_charger(wait_time: float):
    """Small penalty based on waiting time at charging station."""
    return -0.5 * wait_time

def penalty_run_out_of_energy():
    """Big penalty for running out of energy."""
    return -100.0

def penalty_time_elapsed(time_elapsed: float):
    """Penalty to optimize for minimum time."""
    return -0.1 * time_elapsed

def reward_efficient_route(distance_saved: float):
    """Bonus for taking efficient routes."""
    return 0.5 * distance_saved

# =============================================================================
# POLICY CONFIGURATIONS
# =============================================================================

def get_high_level_policy_config():
    """Configuration for route planning policy."""
    return {
        "model": {
            "fcnet_hiddens": [128, 64, 32],
            "fcnet_activation": "relu"
        },
        "lr": 0.0005,
        "entropy_coeff": 0.02,
    }

def get_low_level_policy_config():
    """Configuration for charging management policy."""
    return {
        "model": {
            "fcnet_hiddens": [64, 32, 16],
            "fcnet_activation": "tanh"
        },
        "lr": 0.0003,
        "entropy_coeff": 0.01,
    }             


class HierarchicalTruckRoutingEnv(MultiAgentEnv):
    """Hierarchical environment for truck routing with charging optimization."""
    
    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        
        # Initialize environment components
        self.graph = get_graph()
        self.truck_configs = get_truck_configs()
        self.num_trucks = len(self.truck_configs)
        self.charger_configs = get_charger_configs(self.graph)
        self.charger_occupancy = get_charger_occupancy_template(self.graph)
        self.truck_types = get_truck_types()
        self.done_agents = set()
        # Set up agents
        self.high_level_agents = [f"truck_{i}_route_planner" for i in range(self.num_trucks)]
        self.low_level_agents = [f"truck_{i}_charge_manager" for i in range(self.num_trucks)]
        self.all_agents = self.high_level_agents + self.low_level_agents
        
        self.possible_agents = self.all_agents
        self.agents = self.all_agents.copy()        
        # Define action and observation spaces
        self._action_space_dict = {}
        self._observation_space_dict = {}
        print("I'm Here")
        self._raw_obs_space = get_observation_space(self.graph)#, self.num_trucks)
        flat_obs_space = flatten_space(self._raw_obs_space)        
        for i in range(self.num_trucks):
            high_agent = f"truck_{i}_route_planner"
            low_agent = f"truck_{i}_charge_manager"
            
            self._action_space_dict[high_agent] = get_high_level_action_space(self.graph)
            self._action_space_dict[low_agent] = get_low_level_action_space()
            self._observation_space_dict[high_agent] = flat_obs_space
            self._observation_space_dict[low_agent] = flat_obs_space            
            #self._observation_space_dict[high_agent] = get_observation_space(self.graph, self.num_trucks)
            #self._observation_space_dict[low_agent] = get_observation_space(self.graph, self.num_trucks)
        #self.action_space = self._action_space_dict
        #self.observation_space = self._observation_space_dict
        print("I'm before reset")
        self.reset()
        #self.max_episode_steps = config.get("max_episode_steps", 500) ##
        self.current_step = 0        ##
        print("I'm after reset")

    def reset(self, *, seed=None, options=None):
        """Reset environment to initial state."""
        # Initialize truck states
        self.trucks = []
        num_trucks = len(self.trucks)        
        
        for i, config in enumerate(self.truck_configs):
            if num_trucks > 1:
                normalized_id = i / (num_trucks - 1)
            else:
                normalized_id = 0            
            
            truck_type = self.truck_types[config["truck_type"]]
            truck_state = {
                "id": int(normalized_id),
                "current_node": config["start_node"],
                "destination_node": config["end_node"],
                "current_battery": config["initial_battery"],
                "battery_capacity": truck_type["battery_capacity"],
                "truck_type": config["truck_type"],
                "is_charging": False,
                "waiting_time": 0.0,
                "time_elapsed": 0.0,
                "total_distance": 0.0,
                "charging_sessions": 0,
            }
            self.trucks.append(truck_state)
        
        # Initialize charger occupancy
        #self.charger_occupancy = {node: 0 for node in self.charger_configs.keys()}
        self.charger_occupancy = {
            node: {ctype: 0 for ctype in self.charger_configs[node]}
            for node in self.charger_configs
        }        
        # Global time tracking
        self.global_time = 0.0
         # Maintain proper agent list
        self.agents = self.all_agents.copy()
        
        # Generate observations for all agents
        obs = self._get_observations()
        print("🚀 Reset returned:", {k: v.shape for k, v in obs.items()})
        self.done_agents = set()
        self.current_step = 0  # Reset step counter ##
        return {agent: obs[agent] for agent in self.agents}, {}        

    def step(self, action_dict):
        """Execute one environment step."""
        self.current_step += 1 ##
        observations = {}
        rewards = {}
        terminateds = {}
        truncateds = {}
        infos = {}
        # Process high-level actions (route planning)
        for i, truck in enumerate(self.trucks):
            high_agent = f"truck_{i}_route_planner"
            
            if high_agent in action_dict:
                print(f"🔁 High Agent {high_agent} executing action {action_dict[high_agent]}")
                target_node = action_dict[high_agent]
                self._execute_route_action(truck, target_node, rewards, terminateds)
        
        # Process low-level actions (charging management)
        for i, truck in enumerate(self.trucks):
            low_agent = f"truck_{i}_charge_manager"
            
            if low_agent in action_dict:
                print(f"🔁 Low Agent {low_agent} executing action {action_dict[low_agent]}")
                charge_action = action_dict[low_agent]
                self._execute_charge_action(truck, charge_action, rewards)
            print(f"🔋 Truck {truck['id']} battery: {truck['current_battery']:.2f}")        
        # Update global time
        self.global_time = max(truck["time_elapsed"] for truck in self.trucks)
        
        # Check termination conditions
        # Consider the episode done if either condition is met
        '''
        global_done = all(
            truck["current_node"] == truck["destination_node"] or truck["current_battery"] <= 0
            for truck in self.trucks
        )

        # Also end if max time exceeded
        if self.global_time > 1000 or global_done:
            print("⏹️ Forcing episode end")
            if self.global_time > 1000:
                print("⏱️ Episode ended due to time limit")
            elif global_done:
                print("✅ Episode ended: all trucks done or stuck")            
            terminateds["__all__"] = True
            if terminateds[agent]:
                self.done_agents.add(agent)
        else:
            terminateds["__all__"] = False
            
        #observations = self._get_observations()
        all_obs = self._get_observations()
        observations = {aid: obs for aid, obs in all_obs.items() if aid not in self.done_agents}        
        print("📦 Observations returned:", list(observations.keys()))
        
        # Important: mark each agent done individually!
        for agent in self.agents:
            if agent not in terminateds:
                terminateds[agent] = terminateds["__all__"]
            if terminateds[agent]:
                self.done_agents.add(agent)                
            truncateds[agent] = False
            infos[agent] = {}        
        print("Step called:", action_dict)
        print("Terminateds:", terminateds)        
        active_agents = [agent for agent in self.agents if agent not in self.done_agents]

        observations = {aid: obs for aid, obs in self._get_observations().items() if aid in active_agents}
        rewards = {aid: rewards.get(aid, 0.0) for aid in active_agents}
        terminateds = {aid: terminateds.get(aid, False) for aid in active_agents}
        truncateds = {aid: truncateds.get(aid, False) for aid in active_agents}
        #infos = {aid: infos.get(aid, {}) for aid in active_agents}

        terminateds["__all__"] = terminateds.get("__all__", False)
        truncateds["__all__"] = False  # or your truncation logic        
        '''
        all_done = self.current_step >= 1000
        truck_statuses = []
        
        for truck in self.trucks:
            truck_done = (
                truck["current_node"] == truck["destination_node"]
                or truck["current_battery"] <= 0
            )
            truck_statuses.append(truck_done)
            
            # Set individual agent termination
            high_agent = f"truck_{truck['id']}_route_planner"
            low_agent = f"truck_{truck['id']}_charge_manager"
            
            terminateds[high_agent] = truck_done
            terminateds[low_agent] = truck_done

        terminateds["__all__"] = all(truck_statuses) or all_done
        truncateds["__all__"] = all_done  # Timeout truncation
        if not observations:
            print("🛑 No observations returned — forcing __all__ = True")
            terminateds["__all__"] = True            
        return observations, rewards, terminateds, truncateds, infos
    
    def get_action_space(self, agent_id):
        return self._action_space_dict[agent_id]

    def get_observation_space(self, agent_id):
        return self._observation_space_dict[agent_id]    
    

    def _execute_route_action(self, truck, target_node, rewards, terminateds):
        """Execute high-level routing action."""
        high_agent = f"truck_{truck['id']}_route_planner"
        
        if target_node == truck["current_node"]:
            # Stay at current node
            rewards[high_agent] = 0.0
            return
        
        if not self.graph.has_edge(truck["current_node"], target_node):
            # Invalid move
            rewards[high_agent] = -5.0
            return
        
        # Calculate travel requirements
        edge_data = self.graph[truck["current_node"]][target_node]
        travel_time = edge_data["distance"] / self.truck_types[truck["truck_type"]]["base_speed"]
        
        # Calculate discharge
        discharge = discharge_function(truck, edge_data, travel_time, self.global_time)
        '''
        if truck["current_battery"] < discharge:
            # Not enough battery
            rewards[high_agent] = penalty_run_out_of_energy()
            terminateds[high_agent] = True
            terminateds[f"truck_{truck['id']}_charge_manager"] = True
            return
        '''
        if truck["current_battery"] < discharge:
            # Penalize but don't terminate - let agent recover
            rewards[high_agent] = penalty_run_out_of_energy() / 5  # Smaller penalty
            print(f"⚠️ Truck {truck['id']} insufficient energy "
                  f"({truck['current_battery']:.2f} < {discharge:.2f})")
            return  # Skip movement but continue episode
        # Execute move
        truck["current_battery"] -= discharge
        truck["current_node"] = target_node
        truck["time_elapsed"] += travel_time
        truck["total_distance"] += edge_data["distance"]
        
        # Calculate rewards
        reward = reward_move_to_next_node()
        reward += penalty_time_elapsed(travel_time)  # Encourage efficiency
        
        if truck["current_node"] == truck["destination_node"]:
            reward += reward_arrive_destination()
            terminateds[high_agent] = True
            terminateds[f"truck_{truck['id']}_charge_manager"] = True
        
        rewards[high_agent] = reward

    def _execute_charge_action(self, truck, action, rewards):
        """Execute low-level charging action with support for multiple charger types per node.
        Also handles rewards and penalties as specified.
        """
        low_agent = f"truck_{truck['id']}_charge_manager"
        current_node = truck["current_node"]

        # If not at a charging node, do nothing
        if current_node not in self.charger_configs:
            rewards[low_agent] = 0.0
            return

        charger_types = list(self.charger_configs[current_node].keys())
        if not charger_types:
            rewards[low_agent] = 0.0
            return
        print(f"⚡ Truck {truck['id']} at node {current_node} took charge action: {action}")

        if action == 1:  # Start charging
            if truck["is_charging"]:
                # Already charging
                rewards[low_agent] = 0.0
                return

            # Try to find an available charger type
            for ctype in charger_types:
                if self.charger_occupancy[current_node][ctype] < self.charger_configs[current_node][ctype]:
                    truck["charging_type"] = ctype
                    self.charger_occupancy[current_node][ctype] += 1
                    truck["is_charging"] = True
                    truck["waiting_time"] = 0.0  # Reset waiting time on successful charge start
                    rewards[low_agent] = 1.0  # Small reward for starting to charge
                    return

            # If no charger available, increment waiting time and apply penalty
            truck["waiting_time"] += 1.0
            rewards[low_agent] = penalty_wait_at_charger(1.0)
            return

        elif action == 2:  # Stop charging
            if not truck["is_charging"]:
                # Not charging, do nothing
                rewards[low_agent] = 0.0
                return

            # Calculate charge received
            ctype = truck["charging_type"]
            charge_time = 1.0  # Time unit for charging (adjust as needed)

            charge_amount = charge_function(self.graph,
                truck, current_node, charge_time, self.global_time, charger_type=ctype
            )

            # Update battery, time, and charger occupancy
            truck["current_battery"] = min(
                truck["battery_capacity"],
                truck["current_battery"] + charge_amount
            )
            truck["is_charging"] = False
            truck["charging_sessions"] += 1
            truck["time_elapsed"] += charge_time
            self.charger_occupancy[current_node][ctype] -= 1
            truck["charging_type"] = None

            # Apply reward for finishing charging
            rewards[low_agent] = reward_finish_charging()
            return

        elif action == 3:  # Wait for charger
            # Check if any charger is available
            any_available = any(
                self.charger_occupancy[current_node][ctype] < self.charger_configs[current_node][ctype]
                for ctype in charger_types
            )
            if not any_available:
                # No charger available, wait and apply penalty
                truck["waiting_time"] += 1.0
                rewards[low_agent] = penalty_wait_at_charger(1.0)
            else:
                # Charger available, but chose to wait (unnecessary)
                rewards[low_agent] = -1.0
            return

        else:  # Do nothing (action 0 or invalid)
            rewards[low_agent] = 0.0

    def _can_charge(self, truck):
        """Check if truck can charge at current location."""
        return (truck["current_node"] in self.charger_configs and 
                self.charger_occupancy[truck["current_node"]] < 
                self.charger_configs[truck["current_node"]]["capacity"])

    def _get_observations(self):
        """Get observations for all agents."""
        observations = {}
        num_trucks = len(self.trucks)        
        for i, truck in enumerate(self.trucks):
            high_agent = f"truck_{i}_route_planner"
            low_agent = f"truck_{i}_charge_manager"

            if num_trucks > 1:
                normalized_id = i / (num_trucks - 1)
            else:
                normalized_id = 0            
            # Calculate nearest charger distance
            nearest_charger_dist = self._get_nearest_charger_distance(truck)
            
            # Check if can reach destination with current battery
            can_reach = self._can_reach_destination(truck)
            
            # Get charger info for current node
            current_node = truck["current_node"]
            charger_available = 1 if current_node in self.charger_configs else 0
            #charger_occupancy = self.charger_occupancy.get(current_node, 0)
            #charger_capacity = self.charger_configs.get(current_node, {}).get("capacity", 0)
            charger_occupancy = self.charger_occupancy.get(current_node, {})
            obs = {
                "id": int(normalized_id),
                "current_node": truck["current_node"],
                "destination_node": truck["destination_node"],
                "battery_level": truck["current_battery"],
                "battery_capacity": truck["battery_capacity"],
                "is_charging": int(truck["is_charging"]),
                "charger_available": charger_available,
                #"charger_occupancy": charger_occupancy,
                #"charger_capacity": charger_capacity,
                "time_elapsed": truck["time_elapsed"],
                "waiting_time": truck["waiting_time"],
                "can_reach_destination": int(can_reach),
                "nearest_charger_distance": nearest_charger_dist,
            }
            for ctype in ["fast", "slow"]:  # or use your actual charger types
                obs[f"charger_occupancy_{ctype}"] = charger_occupancy.get(ctype, 0)            
            #pprint.pprint(f"OBS is {obs}")
            #pprint.pprint(f"_raw_obs_space is {self._raw_obs_space}")
            flat_obs = flatten(self._raw_obs_space, obs)
            print(f"Flattened obs shape: {flat_obs.shape}, type: {type(flat_obs)}")
            observations[high_agent] = flat_obs #.copy()
            observations[low_agent] = flat_obs #.copy()
            
        return observations

    def _get_nearest_charger_distance(self, truck):
        """Calculate distance to nearest charger."""
        current_node = truck["current_node"]
        min_distance = float('inf')
        
        for charger_node in self.charger_configs.keys():
            if charger_node != current_node and self.graph.has_node(charger_node):
                try:
                    path_length = nx.shortest_path_length(
                        self.graph, current_node, charger_node, weight='distance'
                    )
                    min_distance = min(min_distance, path_length)
                except nx.NetworkXNoPath:
                    continue
        
        return min_distance if min_distance != float('inf') else 0.0

    def _can_reach_destination(self, truck):
        """Check if truck can reach destination with current battery."""
        try:
            path_length = nx.shortest_path_length(
                self.graph, truck["current_node"], truck["destination_node"], weight='distance'
            )
            estimated_discharge = self.truck_types[truck["truck_type"]]["base_discharge_function"](truck["current_battery"], path_length)
            return truck["current_battery"] >= estimated_discharge
        except nx.NetworkXNoPath:
            return False


# =============================================================================
# MAIN EXECUTION
# =============================================================================
def policy_mapping_fn(agent_id, episode, **kwargs):
    """Map agents to their respective policies."""
    if agent_id.endswith("_route_planner"):
        return "high_level_policy"
    elif agent_id.endswith("_charge_manager"):
        return "low_level_policy"
    else:
        raise ValueError(f"Unknown agent_id: {agent_id}")

def create_hierarchical_truck_config():
    """Create RLlib configuration for hierarchical truck routing."""
    print("creating config")
    tune.register_env("hierarchical_truck_env", 
                     lambda config: HierarchicalTruckRoutingEnv(config))
    raw_obs_space = get_observation_space(get_graph())#, len(get_truck_configs()))
    flat_obs_space = flatten_space(raw_obs_space)
    config = (
        PPOConfig()
        .environment(
            "hierarchical_truck_env",
            env_config={}
        )
        .multi_agent(
            policies={
                "high_level_policy": (
                    None,
                    flat_obs_space,
                    get_high_level_action_space(get_graph()),
                    get_high_level_policy_config()
                ),
                "low_level_policy": (
                    None,
                    flat_obs_space,
                    get_low_level_action_space(),
                    get_low_level_policy_config()
                ),
            },
            policy_mapping_fn=policy_mapping_fn,
            policies_to_train=["high_level_policy", "low_level_policy"],
        )
        .env_runners(
            sample_timeout_s=300,
    
            # Reduce fragment length
            rollout_fragment_length=10,
            num_env_runners=2,
            num_envs_per_env_runner=1,
        )
        .training(
            train_batch_size_per_learner=2000,
            minibatch_size=256,
            num_epochs=10,
            lr=0.0003,
            entropy_coeff=0.01,
        )
        .callbacks(DebugCallback)
        #.rollouts(batch_mode="complete_episodes")
        .framework("torch")
    )
    print("end of creating config")
    return config

def eval(checkpoint_path):
    if not ray.is_initialized():
        ray.init(num_cpus=4, _temp_dir="/tmp/ray1", address=None, object_store_memory=10**9)
    try:
        # Create config
        config = create_hierarchical_truck_config()

        # Build algo object
        algo = config.build()

        # Restore weights
        algo.restore(checkpoint_path)
        print("\nStarting Evaluation...")

        # Create a new environment instance for evaluation
        eval_env = HierarchicalTruckRoutingEnv()

        # Use the trained algorithm for evaluation
        for ep in range(3):
            # Initialize episode
            episode_rewards = {agent: 0 for agent in eval_env.possible_agents}
            obs, _ = eval_env.reset()
            terminated = {"__all__": False}

            print(f"\n=== Evaluation Episode {ep+1} ===")

            # Track routes
            for truck in eval_env.trucks:
                truck['route'] = [truck['current_node']]  # Start route

            # Run episode
            while not terminated["__all__"]:
                actions = {}
                for agent_id in eval_env.agents:
                    policy_id = policy_mapping_fn(agent_id, None)

                    # Get action from trained policy
                    module = algo.get_module(policy_id)
                    obs_tensor = torch.tensor([obs[agent_id]], dtype=torch.float32)

                    action_out = module.forward_inference({
                        "obs": obs_tensor
                    })
                    #print("action_out:", action_out , flush=True)
                    #action = action_out["actions"][0]
                    #action_out = module.forward_inference({
                    #    "obs": np.array([obs[agent_id]])
                    #})
                    logits = action_out["action_dist_inputs"]
                    action = torch.argmax(logits, dim=1)[0].item()
                    actions[agent_id] = action                    
                    #actions[agent_id] = action_out["actions"][0]
                    #actions[agent_id] = algo.compute_single_action(
                    #    obs[agent_id],
                    #    policy_id=policy_id,
                    #    explore=False  # Disable exploration for evaluation
                    #)

                # Execute actions
                obs, rewards, terminated, truncated, info = eval_env.step(actions)

                # Accumulate rewards
                for agent_id, reward in rewards.items():
                    episode_rewards[agent_id] += reward

                # Update routes
                for i, truck in enumerate(eval_env.trucks):
                    if truck['current_node'] != truck['route'][-1]:
                        truck['route'].append(truck['current_node'])

            # Print results
            print(f"\nEpisode {ep+1} Results:")
            for i, truck in enumerate(eval_env.trucks):
                # Convert to OSM IDs if available
                if GRAPH_MAPPINGS["index_to_node"]:
                    route_osn = [GRAPH_MAPPINGS["index_to_node"][idx] for idx in truck['route']]
                else:
                    route_osn = truck['route']

                print(f"  Truck {i}:")
                print(f"    Route: {route_osn}")
                print(f"    Charging sessions: {truck['charging_sessions']}")
                print(f"    Total distance: {truck['total_distance']:.2f} km")
                print(f"    Final battery: {truck['current_battery']:.2f}/{truck['battery_capacity']} kWh")
                print(f"    Time taken: {truck['time_elapsed']:.2f} hours")

            # Print rewards
            print("\nAgent Rewards:")
            for agent_id, reward in episode_rewards.items():
                print(f"  {agent_id}: {reward:.2f}")      
    
        algo.stop()
    except Exception as e:
        print(f"Error occurred: {e}")      
        traceback.print_exc()        
        ray.shutdown()
        # Force termination if needed
        os.kill(os.getpid(), signal.SIGTERM)
    finally:
        if ray.is_initialized():
            ray.shutdown()

def main():
    """Main training loop."""
    if not ray.is_initialized():
        print("I'm in init!!!!")
        ray.init(num_cpus=4, _temp_dir="/tmp/ray1", address=None, object_store_memory=10**9)
    try:
        config = create_hierarchical_truck_config()
        algo = config.build()

        print("Starting hierarchical truck routing training...")
        print("=" * 60)

        for iteration in range(30):
            result = algo.train()
            #pprint.pprint(result)
            print(f"Iteration {iteration + 1}:")
            print(f"  Episode Reward Mean: {result.get('env_runners', 'N/A').get('episode_return_mean', 'N/A')}")
            print(f"  High Level Policy Reward: {result.get('env_runners', 'N/A').get('module_episode_returns_mean', {}).get('high_level_policy', 'N/A')}")
            print(f"  Low Level Policy Reward: {result.get('env_runners', 'N/A').get('module_episode_returns_mean', {}).get('low_level_policy', 'N/A')}")
            print(f"  Time passed Total: {result.get('time_total_s', 'N/A')}")

            print("-" * 40)
        print("Training completed!")
        # Save checkpoint
        

        os.makedirs(checkpoint_dir, exist_ok=True)
        checkpoint_path = algo.save(checkpoint_dir)
        print(f"Saved checkpoint to: {checkpoint_path}")        
        algo.stop()
    except Exception as e:
        print(f"Error occurred: {e}")      
        traceback.print_exc()
        ray.shutdown()
        # Force termination if needed
        os.kill(os.getpid(), signal.SIGTERM)
    finally:
        if ray.is_initialized():
            ray.shutdown()

if __name__ == "__main__":
    main()
    #checkpoint_path = '' 
    #eval(f"{checkpoint_dir}")
