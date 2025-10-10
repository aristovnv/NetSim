# Routes - the set of Route Legs to get from point A to Point B. Could be several sets for one A-B 
from dataclasses import dataclass
import random

@dataclass
class Route:
    def __init__(self, id, **kwargs):
        self.id = id
        
        # Route composition
        self.nodes = kwargs.get('nodes', [])
        self.typical_transit_time = kwargs.get('typical_transit_time', 0.0)  # days
        self.cost_factor = kwargs.get('cost_factor', 1.0)
        self.risk_level = kwargs.get('risk_level', 'medium')  # low, medium, high
        
        # Operational characteristics
        self.seasonal_availability = kwargs.get('seasonal_availability', {
            'jan': True, 'feb': True, 'mar': True, 'apr': True,
            'may': True, 'jun': True, 'jul': True, 'aug': True,
            'sep': True, 'oct': True, 'nov': True, 'dec': True
        })
        self.weather_limitations = kwargs.get('weather_limitations', {
            'max_wind_speed': 50,
            'max_wave_height': 4.0,
            'min_visibility': 1.0  # nautical miles
        })
        
        # Economic factors
        self.toll_costs = kwargs.get('toll_costs', 0.0)  # USD
        self.pilotage_costs = kwargs.get('pilotage_costs', 0.0)  # USD
        self.port_dues = kwargs.get('port_dues', 0.0)  # USD
        self.insurance_multiplier = kwargs.get('insurance_multiplier', 1.0)
        
        # Regulatory constraints
        self.required_certifications = kwargs.get('required_certifications', set())
        self.emission_control_areas = kwargs.get('emission_control_areas', [])
        self.special_areas = kwargs.get('special_areas', [])  # MARPOL special areas
        
        # Alternative routing
        self.alternate_route_ids = kwargs.get('alternate_route_ids', [])
        self.emergency_ports = kwargs.get('emergency_ports', [])
        
        # Performance metrics
        self.reliability_score = kwargs.get('reliability_score', 0.95)  # 0-1
        self.congestion_index = kwargs.get('congestion_index', 0.0)  # 0-1
        self.fuel_efficiency = kwargs.get('fuel_efficiency', 1.0)  # multiplier
        
        # Additional metadata
        self.description = kwargs.get('description', '')
        self.last_updated = kwargs.get('last_updated', '')
        self.data_source = kwargs.get('data_source', '')
        
        # Store any additional attributes
        self.additional_attributes = kwargs

    def __str__(self):
        return f"Route({self.id}: {self.get_origin().id} -> {self.get_destination().id})"

    def __repr__(self):
        return f"Route(id='{self.id}', legs={len(self.legs)}, nodes={len(self.nodes)})"

    def get_origin(self):
        """Get the origin node of the route"""
        return self.legs[0].origin if self.legs else None

    def get_destination(self):
        """Get the destination node of the route"""
        return self.legs[-1].destination if self.legs else None

    def get_total_distance(self):
        """Calculate total distance of the route"""
        return sum(leg.distance for leg in self.legs)

    def get_total_travel_time(self, vessel = None) -> float:
        """Calculate total travel time for the route"""
        total_time = 0.0
        for leg in self.legs:
            vessel_speed = vessel.eco_speed if vessel else None
            total_time += leg.travel_time(vessel_speed)
        return total_time / 24  # Convert to days

    def get_total_fuel_consumption(self, vessel) -> float:
        """Calculate total fuel consumption for the route"""
        total_fuel = 0.0
        for leg in self.legs:
            total_fuel += leg.get_fuel_consumption(vessel)
        return total_fuel * self.fuel_efficiency

    def get_total_cost(self, vessel, fuel_price):
        """Calculate total cost for the route"""
        fuel_consumption = self.get_total_fuel_consumption(vessel)
        fuel_cost = fuel_consumption * fuel_price * self.cost_factor
        
        total_cost = {
            'fuel_cost': fuel_cost,
            'toll_costs': self.toll_costs,
            'pilotage_costs': self.pilotage_costs,
            'port_dues': self.port_dues,
            'insurance_cost': fuel_cost * (self.insurance_multiplier - 1.0),
            'total': fuel_cost + self.toll_costs + self.pilotage_costs + self.port_dues
        }
        
        return total_cost

    def can_accommodate_vessel(self, vessel):
        """Check if vessel can traverse the entire route"""
        for leg in self.legs:
            if not leg.can_accommodate_vessel(vessel):
                return False
        
        # Check route-specific constraints
        if vessel.type in self.required_certifications:
            if not self._has_required_certifications(vessel):
                return False
        
        return True

    def _has_required_certifications(self, vessel):
        """Check if vessel has required certifications for this route"""
        vessel_certs = getattr(vessel, 'certifications', set())
        return all(cert in vessel_certs for cert in self.required_certifications)

    def get_risk_score(self) -> float:
        """Calculate overall risk score for the route"""
        risk_map = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
        base_risk = risk_map.get(self.risk_level, 0.5)
        
        # Add leg-specific risks
        leg_risks = sum(leg.get_risk_factor() for leg in self.legs) / len(self.legs) if self.legs else 0
        
        return (base_risk + leg_risks) / 2

    def is_available_in_season(self, month: str):
        """Check if route is available in given month"""
        return self.seasonal_availability.get(month.lower(), True)

    def get_route_summary(self):
        """Return comprehensive route summary"""
        return {
            'route_id': self.id,
            'origin': self.get_origin().id if self.get_origin() else None,
            'destination': self.get_destination().id if self.get_destination() else None,
            'total_distance_nm': self.get_total_distance(),
            'typical_transit_time_days': self.typical_transit_time,
            'calculated_transit_time_days': self.get_total_travel_time(),
            'number_of_legs': len(self.legs),
            'nodes': self.nodes,
            'risk_level': self.risk_level,
            'risk_score': self.get_risk_score(),
            'cost_factor': self.cost_factor,
            'reliability': self.reliability_score,
            'congestion_index': self.congestion_index,
            'canal_costs': {
                'tolls': self.toll_costs,
                'pilotage': self.pilotage_costs,
                'port_dues': self.port_dues
            }
        }

    def get_leg_by_nodes(self, origin_id, destination_id):
        """Find specific leg by origin and destination nodes"""
        for leg in self.legs:
            if (leg.origin.id == origin_id and 
                leg.destination.id == destination_id):
                return leg
        return None

    def add_leg(self, leg):
        """Add a leg to the route"""
        self.legs.append(leg)
        # Update nodes list if needed
        if leg.origin.id not in self.nodes:
            self.nodes.append(leg.origin.id)
        if leg.destination.id not in self.nodes:
            self.nodes.append(leg.destination.id)