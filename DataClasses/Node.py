# Node is any node, including terminal, middle point or anything
from dataclasses import dataclass

@dataclass
class Node:
    vessels_at_node = None
    vessels_at_berth = None    
    demand_at_node = None
    supply_at_node = None
    def __init__(self, id, **kwargs):
        self.id = id
        self.type = kwargs.get('node_type', 'intermediate')
        self.capacity = kwargs.get('capacity', 1)
        self.queue = 0
        
        # Berth & Physical Characteristics
        self.berth_length = kwargs.get('berth_length', 0)
        self.max_capacity = kwargs.get('max_capacity', 1)
        
        # Operational Speeds
        self.load_speed = kwargs.get('load_speed', {})
        self.unload_speed = kwargs.get('unload_speed', {})
        
        # Capacity & Inventory
        self.capacity_per_product = kwargs.get('Capacity', {})
        self.total_capacity = kwargs.get('Total_Capacity', 0)
        self.initial_inventory = kwargs.get('initial_inventory', {})
        self.current_inventory = self.initial_inventory.copy()
        
        # Initial State
        self.initial_berth_occupation_length = kwargs.get('initial_berth_occupation_length', set())
        self.initial_berth_occupation_ships = kwargs.get('initial_berth_occupation_ships', set())
        
        # Fuel & Product Support
        self.fuel_supported = kwargs.get('fuel_supported', set())
        
        # Navigation Constraints
        self.min_draft = kwargs.get('min_draft', set())
        self.max_draft = kwargs.get('max_draft', set())
        self.channel_depth = kwargs.get('channel_depth', set())
        
        # Operations Configuration
        self.allowed_operations = kwargs.get('allowed_operations', {
            'simultaneous_load_unload': False,
            'load_only': False, 
            'unload_only': False
        })
    
        # Facilities & Environmental
        self.cleaning_facility = kwargs.get('cleaning_facility', False)
        self.emission_control_area = kwargs.get('emission_control_area', False)
        self.weather_limits = kwargs.get('weather_limits', {
            'max_wind_speed': float('inf'),
            'max_wave_height': float('inf')
        })
        # part for generators and getting data
        self.demand_product = kwargs.get('demand_product', None)
        self.supply_product = kwargs.get('supply_product', None)

        # Store any additional attributes
        self.additional_attributes = kwargs

        #processing pops
        self.vessel_map = {vessel.id: vessel for vessel in self.vessels}

        self.vessels_at_node_map = {vessel.id: vessel for vessel in self.vessels_at_node_map}
        self.vessels_at_berth_map = {vessel.id: vessel for vessel in self.vessels_at_berth_map}
        self.demand_at_node_map = {demand.id: demand for demand in self.demand_at_node_map}
        self.supply_at_node_map = {supply.id: supply for supply in self.supply_at_node_map}


    def __str__(self):
        return f"Node({self.id}) - {self.type}"

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Node({attrs})"
        #return f"Node(id='{self.id}', type='{self.type}', capacity={self.capacity})"

    def can_handle_product(self, product_type):
        """Check if node can handle specific product type"""
        return product_type in self.capacity_per_product

    def can_handle_fuel(self, fuel_type):
        """Check if node supports specific fuel type"""
        return fuel_type in self.fuel_supported

    def get_load_speed(self, product_type):
        """Get loading speed for specific product type"""
        return self.load_speed.get(product_type, 0)

    def get_unload_speed(self, product_type):
        """Get unloading speed for specific product type"""
        return self.unload_speed.get(product_type, 0)

    def get_product_capacity(self, product_type):
        """Get capacity for specific product type"""
        return self.capacity_per_product.get(product_type, 0)

    def get_available_capacity(self, product_type):
        """Get available capacity for specific product type"""
        current_level = self.current_inventory.get(product_type, 0)
        total_capacity = self.get_product_capacity(product_type)
        return total_capacity - current_level

    def can_operate_in_weather(self, wind_speed, wave_height):
        """Check if operations are allowed in current weather conditions"""
        return (wind_speed <= self.weather_limits['max_wind_speed'] and 
                wave_height <= self.weather_limits['max_wave_height'])

    def can_accommodate_ship(self, ship_draft, ship_length):
        """Check if node can accommodate ship based on draft and length"""
        draft_ok = (any(ship_draft >= min_d for min_d in self.min_draft) and 
                   any(ship_draft <= max_d for max_d in self.max_draft))
        length_ok = ship_length <= self.berth_length
        return draft_ok and length_ok

    def update_inventory(self, product_type, quantity):
        """Update inventory for specific product type"""
        if product_type not in self.current_inventory:
            self.current_inventory[product_type] = 0
        
        new_quantity = self.current_inventory[product_type] + quantity
        capacity = self.get_product_capacity(product_type)
        
        if new_quantity < 0 or new_quantity > capacity:
            return False  # Operation would exceed capacity
        
        self.current_inventory[product_type] = new_quantity
        return True

    def get_operational_info(self):
        """Return comprehensive operational information"""
        return {
            'id': self.id,
            'type': self.type,
            'berth_length': self.berth_length,
            'max_capacity': self.max_capacity,
            'load_speeds': self.load_speed,
            'unload_speeds': self.unload_speed,
            'product_capacities': self.capacity_per_product,
            'total_capacity': self.total_capacity,
            'current_inventory': self.current_inventory,
            'fuel_supported': list(self.fuel_supported),
            'draft_limits': {
                'min': list(self.min_draft),
                'max': list(self.max_draft)
            },
            'allowed_operations': self.allowed_operations,
            'facilities': {
                'cleaning': self.cleaning_facility,
                'emission_control': self.emission_control_area
            },
            'weather_limits': self.weather_limits
        }
    
    def add_vessel_to_node(self, vessel):
        self.vessels_at_node.append(vessel)
        self.vessels_at_node_map[vessel.id] = vessel

    def remove_vessel_from_node(self, vessel):        
        vessel_obj = self.vessels_at_node_map.pop(vessel.id, None)
        if vessel_obj:
            self.vessels_at_node.remove(vessel) 

    def add_vessel_to_berth(self, vessel):
        self.vessels_at_berth.append(vessel)
        self.vessels_at_berth_map[vessel.id] = vessel

    def remove_vessel_from_berth(self, vessel):
        vessel_obj = self.vessels_at_berth_map.pop(vessel.id, None)
        if vessel_obj:
            self.vessels_at_berth.remove(vessel) 

    def add_supply_to_node(self, supply):
        self.supply_at_node.append(supply)
        self.supply_at_node_map[supply.id] = supply

    def remove_supply_from_node(self, supply):
        supply_obj = self.supply_at_node_map.pop(supply.id, None)
        if supply_obj:
            self.supply_at_node.remove(supply) 

    def add_demand_to_node(self, demand):
        self.demand_at_node.append(demand)
        self.demand_at_node_map[demand.id] = demand

    def remove_demand_from_node(self, demand):
        demand_obj = self.demand_at_node_map.pop(demand.id, None)
        if demand_obj:
            self.demand_at_node.remove(demand) 
