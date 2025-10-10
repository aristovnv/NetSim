# Vessels

from dataclasses import dataclass

@dataclass
class Vessel:
    def __init__(self, id, **kwargs):
        # Basic Identification (with defaults)
        self.id = id
        self.type = kwargs.get('type', 'Unknown')
        self.imo_number = kwargs.get('imo_number', 0)
        self.build_year = kwargs.get('build_year', 0)
        self.flag = kwargs.get('flag', 'Unknown')
        
        # Capacity & Dimensions (with defaults)
        self.deadweight_tonnage = kwargs.get('deadweight_tonnage', 0)
        self.cargo_capacity = kwargs.get('cargo_capacity', 0)
        self.length_overall = kwargs.get('length_overall', 0)
        self.draft = kwargs.get('draft', 0)
        self.beam = kwargs.get('beam', 0)
        
        # Performance (with defaults)
        self.max_speed = kwargs.get('max_speed', 0)
        self.eco_speed = kwargs.get('eco_speed', 0)
        self.fuel_consumption_at_eco = kwargs.get('fuel_consumption_at_eco', 0)
        self.fuel_type = kwargs.get('fuel_type', 'Unknown')
        self.fuel_capacity = kwargs.get('fuel_capacity', 0)
        
        # Cargo Specifications (with defaults)
        self.cargo_types = kwargs.get('cargo_types', [])
        self.tank_configuration = kwargs.get('tank_configuration', 'Unknown')
        self.pump_capacity = kwargs.get('pump_capacity', 0)
        
        # Store any additional attributes
        self.additional_attributes = kwargs

    def __str__(self):
        return f"{self.type} (IMO: {self.imo_number}) - {self.flag} Flag"

    def __repr__(self):
        return f"Vessel(type='{self.type}', imo={self.imo_number}, dwt={self.deadweight_tonnage})"

    def calculate_fuel_range(self):
        """Calculate maximum range at eco speed"""
        if self.fuel_consumption_at_eco > 0:
            days = self.fuel_capacity / self.fuel_consumption_at_eco
            range_nm = days * 24 * self.eco_speed
            return range_nm
        return 0

    def calculate_loading_time(self, cargo_volume):
        """Calculate time to load given cargo volume"""
        if self.pump_capacity > 0:
            return cargo_volume / self.pump_capacity
        return 0

    def calculate_unloading_time(self, cargo_volume):
        """Calculate time to load given cargo volume"""
        if self.pump_capacity > 0:
            return cargo_volume / self.pump_capacity
        return 0

    def can_carry_cargo_type(self, cargo_type):
        """Check if vessel can carry specific cargo type"""
        return cargo_type in self.cargo_types

    def get_vessel_info(self):
        """Return comprehensive vessel information"""
        return {
            'id': id,
            'type': self.type,
            'imo_number': self.imo_number,
            'build_year': self.build_year,
            'flag': self.flag,
            'deadweight_tonnage': self.deadweight_tonnage,
            'cargo_capacity': self.cargo_capacity,
            'dimensions': {
                'length': self.length_overall,
                'draft': self.draft,
                'beam': self.beam
            },
            'performance': {
                'max_speed': self.max_speed,
                'eco_speed': self.eco_speed,
                'fuel_consumption': self.fuel_consumption_at_eco,
                'fuel_type': self.fuel_type,
                'fuel_capacity': self.fuel_capacity
            },
            'cargo_specs': {
                'cargo_types': self.cargo_types,
                'tank_configuration': self.tank_configuration,
                'pump_capacity': self.pump_capacity
            }
        }
