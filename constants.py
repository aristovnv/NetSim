PORTS_TERMINAL = {
    'Houston': {
        'berth_length': 100,
        'max_capacity': 5,
        'load_speed': {'Oil': 5, 'Petrol': 10},
        'unload_speed': {'Oil': 5, 'Petrol': 10},
        'Capacity': {'Oil': 50, 'Petrol': 100},
        'Total_Capacity': 100,
        'initial_inventory': {'Oil': 40, 'Petrol': 0},
        'initial_berth_occupation_length':{40},
        'initial_berth_occupation_ships':{3},
        'fuel_supported': {'Diesel', 'Hydrogen'},
        'min_draft': {100}, 
        'max_draft': {200},
        'channel_depth': {170},
        'allowed_operations': {'simultaneous_load_unload': False, 'load_only': True, 'unload_only': False},
        'cleaning_facility': True,
        'emission_control_area': True,
        'weather_limits': {'max_wind_speed': 50, 'max_wave_height': 3.0}
    },
    'Rotterdam': {
        'berth_length': 100,
        'max_capacity': 5,
        'load_speed': {'Oil': 5, 'Petrol': 10},
        'unload_speed': {'Oil': 5, 'Petrol': 10},
        'Capacity': {'Oil': 50, 'Petrol': 100},
        'Total_Capacity': 100,
        'initial_inventory': {'Oil': 40, 'Petrol': 0},
        'initial_berth_occupation_length':{40},
        'initial_berth_occupation_ships':{3},
        'fuel_supported': {'Diesel', 'BioDiesel'},
        'min_draft': {100}, 
        'max_draft': {200},
        'channel_depth': {170},
        'allowed_operations': {'simultaneous_load_unload': False, 'load_only': True, 'unload_only': False},
        'cleaning_facility': True,
        'emission_control_area': True,
        'weather_limits': {'max_wind_speed': 50, 'max_wave_height': 3.0}
    },
    'NewYork': {
        'berth_length': 100,
        'max_capacity': 5,
        'load_speed': {'Oil': 5, 'Petrol': 10},
        'unload_speed': {'Oil': 5, 'Petrol': 10},
        'Capacity': {'Oil': 50, 'Petrol': 100},
        'Total_Capacity': 100,
        'initial_inventory': {'Oil': 40, 'Petrol': 0},
        'initial_berth_occupation_length':{40},
        'initial_berth_occupation_ships':{3},
        'fuel_supported': {'Diesel', 'BioDiesel', 'Hydrogen'},
        'min_draft': {100}, 
        'max_draft': {200},
        'channel_depth': {170},
        'allowed_operations': {'simultaneous_load_unload': False, 'load_only': True, 'unload_only': False},
        'cleaning_facility': True,
        'emission_control_area': True,
        'weather_limits': {'max_wind_speed': 50, 'max_wave_height': 3.0}
    },
        'Africa': {
        'berth_length': 100,
        'max_capacity': 5,
        'load_speed': {'Oil': 5, 'Petrol': 10},
        'unload_speed': {'Oil': 5, 'Petrol': 10},
        'Capacity': {'Oil': 50, 'Petrol': 100},
        'Total_Capacity': 100,
        'initial_inventory': {'Oil': 40, 'Petrol': 0},
        'initial_berth_occupation_length':{40},
        'initial_berth_occupation_ships':{3},
        'fuel_supported': {'Diesel'},
        'min_draft': {100}, 
        'max_draft': {200},
        'channel_depth': {170},
        'allowed_operations': {'simultaneous_load_unload': False, 'load_only': True, 'unload_only': False},
        'cleaning_facility': True,
        'emission_control_area': True,
        'weather_limits': {'max_wind_speed': 50, 'max_wave_height': 3.0}
    },
        'Brazil': {
        'berth_length': 100,
        'max_capacity': 5,
        'load_speed': {'Oil': 5, 'Petrol': 10},
        'unload_speed': {'Oil': 5, 'Petrol': 10},
        'Capacity': {'Oil': 50, 'Petrol': 100},
        'Total_Capacity': 100,
        'initial_inventory': {'Oil': 40, 'Petrol': 0},
        'initial_berth_occupation_length':{40},
        'initial_berth_occupation_ships':{3},
        'fuel_supported': {'Diesel', 'Hydrogen'},
        'min_draft': {100}, 
        'max_draft': {200},
        'channel_depth': {170},
        'allowed_operations': {'simultaneous_load_unload': False, 'load_only': True, 'unload_only': False},
        'cleaning_facility': True,
        'emission_control_area': True,
        'weather_limits': {'max_wind_speed': 50, 'max_wave_height': 3.0}
    }
}  

NODES = {
    # Main Terminals (your existing ones)
    'NewYork': {'type': 'terminal', 'region': 'north_atlantic'},
    'Houston': {'type': 'terminal', 'region': 'gulf_of_mexico'},
    'Rotterdam': {'type': 'terminal', 'region': 'europe'},
    'Brazil': {'type': 'terminal', 'region': 'south_atlantic'},
    'Africa': {'type': 'terminal', 'region': 'south_atlantic'},
    
    # Strategic Waypoints
    'Gibraltar': {'type': 'chokepoint', 'region': 'mediterranean_access'},
    'Suez_Canal': {'type': 'chokepoint', 'region': 'red_sea'},
    'Cape_Town': {'type': 'waypoint', 'region': 'south_atlantic'},
    'Azores': {'type': 'waiting_area', 'region': 'mid_atlantic'},
    'Bermuda': {'type': 'waiting_area', 'region': 'west_atlantic'},
    'English_Channel': {'type': 'chokepoint', 'region': 'europe'},
    
    # Floating Storage Areas
    'US_Gulf_Storage': {'type': 'storage_area', 'region': 'gulf_of_mexico'},
    'Rotterdam_Anchorage': {'type': 'storage_area', 'region': 'north_sea'},
    'West_Africa_Storage': {'type': 'storage_area', 'region': 'south_atlantic'}
}

ROUTES = {
    # Brazil to Rotterdam - Multiple Options
    'Brazil_to_Rotterdam_via_Direct': {
        'nodes': ['Brazil', 'Azores', 'Gibraltar', 'Rotterdam'],
        'typical_transit_time': 18,  # days
        'cost_factor': 1.0,
        'risk_level': 'low'
    },
    'Brazil_to_Rotterdam_via_Cape': {
        'nodes': ['Brazil', 'Cape_Town', 'Rotterdam'],
        'typical_transit_time': 25,
        'cost_factor': 1.3,
        'risk_level': 'medium',
        'avoid_suez': True
    },
    
    # Africa to USA - Multiple Options
    'Africa_to_USA_via_Direct': {
        'nodes': ['Africa', 'Bermuda', 'NewYork'],
        'typical_transit_time': 16,
        'cost_factor': 1.0,
        'risk_level': 'medium'
    },
    'Africa_to_USA_via_Gulf': {
        'nodes': ['Africa', 'US_Gulf_Storage', 'Houston'],
        'typical_transit_time': 14,
        'cost_factor': 1.1,
        'risk_level': 'low'
    },
    
    # Houston to Rotterdam with Storage Option
    'Houston_to_Rotterdam_Standard': {
        'nodes': ['Houston', 'Azores', 'English_Channel', 'Rotterdam'],
        'typical_transit_time': 20,
        'cost_factor': 1.0,
        'risk_level': 'low'
    },
    'Houston_to_Rotterdam_with_Storage': {
        'nodes': ['Houston', 'Azores', 'Rotterdam_Anchorage', 'Rotterdam'],
        'typical_transit_time': 'variable',  # Can wait at anchorage
        'cost_factor': 1.2,
        'risk_level': 'low',
        'storage_option': True
    },
    
    # Suez Canal Route (when applicable)
    'Asia_to_Europe_via_Suez': {
        'nodes': ['Asia_Terminal', 'Suez_Canal', 'Gibraltar', 'Rotterdam'],
        'typical_transit_time': 22,
        'cost_factor': 1.4,  # Canal fees
        'risk_level': 'high',  # Geopolitical risk
        'canal_required': True
    }
}


DISTANCES = {
    # Terminal to Terminal (direct, for reference)
    'Brazil': {'Rotterdam': 4700, 'NewYork': 4200, 'Africa': 3200, 'Houston': 4800},
    'Africa': {'Rotterdam': 3500, 'NewYork': 3800, 'Brazil': 3200, 'Houston': 5200},
    
    # Terminal to Waypoints
    'Brazil': {'Azores': 2200, 'Cape_Town': 3800, 'Gibraltar': 3500},
    'Rotterdam': {'Gibraltar': 1200, 'Azores': 1800, 'English_Channel': 200},
    'Africa': {'Cape_Town': 1500, 'Azores': 3200, 'Bermuda': 3800},
    
    # Waypoint to Waypoint
    'Azores': {'Gibraltar': 900, 'Bermuda': 2200, 'English_Channel': 1200},
    'Gibraltar': {'English_Channel': 1100, 'Suez_Canal': 2000},
    'Cape_Town': {'Azores': 4500, 'Suez_Canal': 4800},
    
    # Storage Areas
    'US_Gulf_Storage': {'Houston': 50, 'NewYork': 1200, 'Bermuda': 1400},
    'Rotterdam_Anchorage': {'Rotterdam': 20, 'English_Channel': 150}
}


ROUTE_LEGS = {
    # Terminal to Terminal legs
    ('NewYork', 'Houston'): {
        'distance': 1600, 'typical_speed': 14, 'weather_risk': 'medium', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.0
    },
    ('NewYork', 'Rotterdam'): {
        'distance': 3600, 'typical_speed': 14, 'weather_risk': 'high', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.2
    },
    ('NewYork', 'Brazil'): {
        'distance': 4700, 'typical_speed': 15, 'weather_risk': 'medium', 
        'piracy_risk': 0.02, 'fuel_consumption_factor': 1.0
    },
    ('NewYork', 'Africa'): {
        'distance': 4300, 'typical_speed': 14, 'weather_risk': 'medium', 
        'piracy_risk': 0.03, 'fuel_consumption_factor': 1.1
    },
    
    ('Houston', 'Rotterdam'): {
        'distance': 4800, 'typical_speed': 14, 'weather_risk': 'high', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.3
    },
    ('Houston', 'Brazil'): {
        'distance': 5200, 'typical_speed': 15, 'weather_risk': 'low', 
        'piracy_risk': 0.02, 'fuel_consumption_factor': 0.9
    },
    ('Houston', 'Africa'): {
        'distance': 5800, 'typical_speed': 14, 'weather_risk': 'medium', 
        'piracy_risk': 0.04, 'fuel_consumption_factor': 1.1
    },
    
    ('Rotterdam', 'Brazil'): {
        'distance': 5100, 'typical_speed': 15, 'weather_risk': 'medium', 
        'piracy_risk': 0.02, 'fuel_consumption_factor': 1.0
    },
    ('Rotterdam', 'Africa'): {
        'distance': 4000, 'typical_speed': 15, 'weather_risk': 'low', 
        'piracy_risk': 0.03, 'fuel_consumption_factor': 0.9
    },
    
    ('Brazil', 'Africa'): {
        'distance': 3300, 'typical_speed': 16, 'weather_risk': 'low', 
        'piracy_risk': 0.05, 'fuel_consumption_factor': 0.8
    },
    
    # Terminal to Waypoint legs
    ('NewYork', 'Gibraltar'): {
        'distance': 3200, 'typical_speed': 14, 'weather_risk': 'medium', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.1
    },
    ('NewYork', 'Azores'): {
        'distance': 2400, 'typical_speed': 15, 'weather_risk': 'medium', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.0
    },
    ('NewYork', 'Bermuda'): {
        'distance': 850, 'typical_speed': 16, 'weather_risk': 'low', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 0.9
    },
    
    ('Houston', 'Gibraltar'): {
        'distance': 4500, 'typical_speed': 14, 'weather_risk': 'medium', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.2
    },
    ('Houston', 'Azores'): {
        'distance': 3800, 'typical_speed': 15, 'weather_risk': 'medium', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.1
    },
    ('Houston', 'Bermuda'): {
        'distance': 1600, 'typical_speed': 16, 'weather_risk': 'low', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 0.9
    },
    
    ('Rotterdam', 'Gibraltar'): {
        'distance': 1100, 'typical_speed': 16, 'weather_risk': 'low', 
        'piracy_risk': 0.02, 'fuel_consumption_factor': 0.9
    },
    ('Rotterdam', 'Azores'): {
        'distance': 1900, 'typical_speed': 15, 'weather_risk': 'medium', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.0
    },
    ('Rotterdam', 'English_Channel'): {
        'distance': 250, 'typical_speed': 12, 'weather_risk': 'high', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.5
    },
    
    ('Brazil', 'Gibraltar'): {
        'distance': 3800, 'typical_speed': 15, 'weather_risk': 'low', 
        'piracy_risk': 0.02, 'fuel_consumption_factor': 0.9
    },
    ('Brazil', 'Azores'): {
        'distance': 2400, 'typical_speed': 16, 'weather_risk': 'low', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 0.8
    },
    ('Brazil', 'Cape_Town'): {
        'distance': 2700, 'typical_speed': 16, 'weather_risk': 'low', 
        'piracy_risk': 0.03, 'fuel_consumption_factor': 0.8
    },
    
    ('Africa', 'Gibraltar'): {
        'distance': 2500, 'typical_speed': 16, 'weather_risk': 'low', 
        'piracy_risk': 0.04, 'fuel_consumption_factor': 0.9
    },
    ('Africa', 'Cape_Town'): {
        'distance': 1400, 'typical_speed': 16, 'weather_risk': 'low', 
        'piracy_risk': 0.06, 'fuel_consumption_factor': 0.8
    },
    ('Africa', 'Suez_Canal'): {
        'distance': 3800, 'typical_speed': 15, 'weather_risk': 'medium', 
        'piracy_risk': 0.08, 'fuel_consumption_factor': 1.2
    },
    
    # Waypoint to Waypoint legs
    ('Azores', 'Gibraltar'): {
        'distance': 900, 'typical_speed': 16, 'weather_risk': 'medium', 
        'piracy_risk': 0.02, 'fuel_consumption_factor': 1.1
    },
    ('Azores', 'Bermuda'): {
        'distance': 2300, 'typical_speed': 15, 'weather_risk': 'medium', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.0
    },
    ('Gibraltar', 'Suez_Canal'): {
        'distance': 2100, 'typical_speed': 14, 'weather_risk': 'low', 
        'piracy_risk': 0.05, 'fuel_consumption_factor': 1.3
    },
    ('Gibraltar', 'English_Channel'): {
        'distance': 1200, 'typical_speed': 14, 'weather_risk': 'high', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.4
    },
    ('Cape_Town', 'Suez_Canal'): {
        'distance': 4500, 'typical_speed': 14, 'weather_risk': 'medium', 
        'piracy_risk': 0.10, 'fuel_consumption_factor': 1.2
    },
    ('Bermuda', 'Azores'): {
        'distance': 2300, 'typical_speed': 15, 'weather_risk': 'medium', 
        'piracy_risk': 0.01, 'fuel_consumption_factor': 1.0
    }
}

OWN_VESSELS = {
    'VLCC_Poseidon': {
        # Basic Identification
        'type': 'VLCC',
        'imo_number': 9876543,
        'build_year': 2018,
        'flag': 'Liberia',
        
        # Capacity & Dimensions
        'deadweight_tonnage': 320000,
        'cargo_capacity': 300000,
        'length_overall': 330,
        'draft': 22.5,
        'beam': 60,
        
        # Performance
        'max_speed': 16,
        'eco_speed': 14,
        'fuel_consumption_at_eco': 80,  # tons per day
        'fuel_type': 'VLSFO',
        'fuel_capacity': 6000,
        
        # Cargo Specifications
        'cargo_types': ['Crude_Oil', 'Fuel_Oil'],
        'tank_configuration': 'double_hull',
        'pump_capacity': 10000,  # tons/hour
    },
    
    'Suezmax_Atlas': {
        'type': 'Suezmax',
        'imo_number': 8765432,
        'build_year': 2015,
        'flag': 'Marshall Islands',
        
        'deadweight_tonnage': 160000,
        'cargo_capacity': 150000,
        'length_overall': 274,
        'draft': 17.5,
        'beam': 48,
        
        'max_speed': 15.5,
        'eco_speed': 13.5,
        'fuel_consumption_at_eco': 45,
        'fuel_type': 'VLSFO',
        'fuel_capacity': 3500,
        
        'cargo_types': ['Crude_Oil', 'Diesel', 'Fuel_Oil'],
        'tank_configuration': 'double_hull',
        'pump_capacity': 7000,
    },
    
    'Aframax_Pioneer': {
        'type': 'Aframax',
        'imo_number': 7654321,
        'build_year': 2020,
        'flag': 'Singapore',
        
        'deadweight_tonnage': 115000,
        'cargo_capacity': 110000,
        'length_overall': 250,
        'draft': 14.5,
        'beam': 44,
        
        'max_speed': 15,
        'eco_speed': 13,
        'fuel_consumption_at_eco': 35,
        'fuel_type': 'VLSFO',
        'fuel_capacity': 2500,
        
        'cargo_types': ['Crude_Oil', 'Diesel', 'Petrol', 'Jet_Fuel'],
        'tank_configuration': 'double_hull',
        'pump_capacity': 5000,
    },
    
    'Panamax_Explorer': {
        'type': 'Panamax',
        'imo_number': 6543210,
        'build_year': 2012,
        'flag': 'Greece',
        
        'deadweight_tonnage': 75000,
        'cargo_capacity': 70000,
        'length_overall': 228,
        'draft': 12.5,
        'beam': 32,
        
        'max_speed': 14.5,
        'eco_speed': 12.5,
        'fuel_consumption_at_eco': 25,
        'fuel_type': 'VLSFO',
        'fuel_capacity': 1800,
        
        'cargo_types': ['Crude_Oil', 'Diesel', 'Petrol', 'Jet_Fuel', 'Fuel_Oil'],
        'tank_configuration': 'double_hull',
        'pump_capacity': 4000,
    },
    
    'MR_Challenger': {
        'type': 'MR',
        'imo_number': 5432109,
        'build_year': 2019,
        'flag': 'Norway',
        
        'deadweight_tonnage': 45000,
        'cargo_capacity': 42000,
        'length_overall': 183,
        'draft': 11,
        'beam': 32,
        
        'max_speed': 14,
        'eco_speed': 12,
        'fuel_consumption_at_eco': 18,
        'fuel_type': 'MGO',
        'fuel_capacity': 1200,
        
        'cargo_types': ['Petrol', 'Diesel', 'Jet_Fuel', 'Gasoline', 'Naphtha'],
        'tank_configuration': 'double_hull',
        'pump_capacity': 2500,
    },
    
    'Small_Tanker_Coastal': {
        'type': 'Coastal',
        'imo_number': 4321098,
        'build_year': 2017,
        'flag': 'USA',
        
        'deadweight_tonnage': 25000,
        'cargo_capacity': 23000,
        'length_overall': 150,
        'draft': 9,
        'beam': 24,
        
        'max_speed': 13,
        'eco_speed': 11,
        'fuel_consumption_at_eco': 12,
        'fuel_type': 'MGO',
        'fuel_capacity': 800,
        
        'cargo_types': ['Petrol', 'Diesel', 'Jet_Fuel'],
        'tank_configuration': 'double_hull',
        'pump_capacity': 1500,
    }
}


