# Edge properties
import Node
import random
from dataclasses import dataclass

@dataclass
class RouteLeg:
    def __init__(self, origin: Node, destination: Node, distance=1.0, base_travel_time=1.0, congestion_factor=0.0):
        self.origin = origin
        self.destination = destination
        self.distance = distance
        self.base_travel_time = base_travel_time
        self.congestion_factor = congestion_factor

    def travel_time(self):
        return self.base_travel_time + random.random() * self.congestion_factor

@dataclass
class RouteLeg:
    def __init__(self, origin, destination, **kwargs):
        self.origin = origin
        self.destination = destination
        
        # Basic route properties
        self.distance = kwargs.get('distance', 1.0)
        self.base_travel_time = kwargs.get('base_travel_time', 1.0)
        self.congestion_factor = kwargs.get('congestion_factor', 0.0)
        
        # Navigation & Performance
        self.typical_speed = kwargs.get('typical_speed', 12.0)
        self.weather_risk = kwargs.get('weather_risk', 'low')  # low, medium, high
        self.piracy_risk = kwargs.get('piracy_risk', 0.0)
        self.fuel_consumption_factor = kwargs.get('fuel_consumption_factor', 1.0)
        
        # Physical Constraints
        self.min_draft = kwargs.get('min_draft', 0.0)  # Minimum water depth required
        self.max_draft = kwargs.get('max_draft', float('inf'))  # Maximum draft allowed
        self.min_air_draft = kwargs.get('min_air_draft', 0.0)  # Minimum air clearance
        self.max_air_draft = kwargs.get('max_air_draft', float('inf'))  # Maximum air clearance
        self.min_beam = kwargs.get('min_beam', 0.0)  # Minimum channel width
        self.max_beam = kwargs.get('max_beam', float('inf'))  # Maximum vessel beam allowed
        self.min_length = kwargs.get('min_length', 0.0)  # Minimum vessel length
        self.max_length = kwargs.get('max_length', float('inf'))  # Maximum vessel length
        
        # Channel/Specific waterway constraints
        self.channel_depth = kwargs.get('channel_depth', float('inf'))
        self.channel_width = kwargs.get('channel_width', float('inf'))
        self.bridge_clearance = kwargs.get('bridge_clearance', float('inf'))
        self.lock_dimensions = kwargs.get('lock_dimensions', {  # if route includes locks
            'length': float('inf'),
            'width': float('inf'),
            'depth': float('inf')
        })
        
        # Vessel type restrictions
        self.allowed_vessel_types = kwargs.get('allowed_vessel_types', set())  # {'VLCC', 'Container', 'Bulk'}
        self.restricted_vessel_types = kwargs.get('restricted_vessel_types', set())
        self.hazardous_cargo_allowed = kwargs.get('hazardous_cargo_allowed', True)
        
        # Operational constraints
        self.tidal_dependent = kwargs.get('tidal_dependent', False)
        self.ice_class_required = kwargs.get('ice_class_required', False)
        self.pilot_required = kwargs.get('pilot_required', False)
        self.night_transit_allowed = kwargs.get('night_transit_allowed', True)
        
        # Additional route characteristics
        self.seasonal_restrictions = kwargs.get('seasonal_restrictions', {})  # {'winter': 'ice', 'summer': 'none'}
        self.congestion_zones = kwargs.get('congestion_zones', [])
        self.alternate_routes = kwargs.get('alternate_routes', [])
        
        # Store any additional attributes
        self.additional_attributes = kwargs

    def travel_time(self, vessel_speed = None) -> float:
        """Calculate travel time considering congestion and vessel speed"""
        speed = vessel_speed if vessel_speed else self.typical_speed
        base_time = self.distance / speed if speed > 0 else float('inf')
        congestion_delay = random.random() * self.congestion_factor
        return base_time + congestion_delay

    def can_accommodate_vessel(self, vessel) -> bool:
        """Check if vessel can traverse this route leg"""
        # Draft constraints
        if vessel.draft < self.min_draft or vessel.draft > self.max_draft:
            return False
        
        # Beam constraints
        if vessel.beam < self.min_beam or vessel.beam > self.max_beam:
            return False
        
        # Length constraints
        if vessel.length_overall < self.min_length or vessel.length_overall > self.max_length:
            return False
        
        # Channel constraints
        if vessel.draft > self.channel_depth:
            return False
        
        if vessel.beam > self.channel_width:
            return False
        
        # Vessel type restrictions
        if (self.allowed_vessel_types and 
            vessel.type not in self.allowed_vessel_types):
            return False
        
        if vessel.type in self.restricted_vessel_types:
            return False
        
        # Special requirements
        if self.ice_class_required and not getattr(vessel, 'ice_class', False):
            return False
        
        return True

    def get_fuel_consumption(self, vessel, speed = None) -> float:
        """Calculate fuel consumption for this leg"""
        time = self.travel_time(speed)
        base_consumption = vessel.fuel_consumption_at_eco * time / 24  # Convert tons/day to tons/hour
        return base_consumption * self.fuel_consumption_factor

    def get_risk_factor(self) -> float:
        """Calculate overall risk factor for this leg"""
        weather_risk_map = {'low': 0.1, 'medium': 0.3, 'high': 0.6}
        weather_risk = weather_risk_map.get(self.weather_risk, 0.3)
        
        return weather_risk + self.piracy_risk

    def get_route_info(self):
        """Return comprehensive route information"""
        return {
            'origin': self.origin.id,
            'destination': self.destination.id,
            'distance': self.distance,
            'typical_travel_time': self.travel_time(),
            'physical_constraints': {
                'draft_limits': {'min': self.min_draft, 'max': self.max_draft},
                'beam_limits': {'min': self.min_beam, 'max': self.max_beam},
                'length_limits': {'min': self.min_length, 'max': self.max_length},
                'channel_depth': self.channel_depth,
                'channel_width': self.channel_width
            },
            'risks': {
                'weather': self.weather_risk,
                'piracy': self.piracy_risk,
                'overall_risk': self.get_risk_factor()
            },
            'operational_constraints': {
                'tidal_dependent': self.tidal_dependent,
                'ice_class_required': self.ice_class_required,
                'pilot_required': self.pilot_required
            }
        }

    def __str__(self):
        return f"RouteLeg({self.origin.id} -> {self.destination.id}, {self.distance}nm)"

    def __repr__(self):
        return f"RouteLeg(origin={self.origin.id}, destination={self.destination.id}, distance={self.distance})"