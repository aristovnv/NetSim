# Vessels

from dataclasses import dataclass

@dataclass
class Vessel:
    cargo_capacity = float
    draft = float
    product = None
    product_qty: float = 0.0
    next_node = None
    contract = None
    current_node = None
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
        
        # our ship went to loan
        self.is_in_loan = kwargs.get('is_in_loan', False)
        self.days_left_in_loan = kwargs.get('days_left_in_loan', 0)
        self.product_qty = kwargs.get('product_qty', 0.0)
        self.product = kwargs.get('product', None)
        self.current_node = kwargs.get('current_node', None)
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
    
    # LOAN HANDLING
    def loaned(self, days):
        self.is_in_loan = True
        self.days_left_in_loan = days
        self.update_loan_qty_times = 0

    def return_from_loan(self):
        self.is_in_loan = False
        self.update_loan_qty_times = 0

    def decrease_loan_days(self):
        self.days_left_in_loan -= 1 

    def update_loan_days(self, days):
        self.days_left_in_loan = days    
        self.update_loan_qty_times += 1
    # LOAD HANDLING
    def load(self, product, qty_percent: float):
        """
        Load product onto the vessel.
        
        Args:
            product: Type of product to load
            qty_percent: Percentage of cargo capacity to load (0.0 to 1.0)
            
        Returns:
            Actual quantity loaded
        """
        if qty_percent < 0 or qty_percent > 1:
            raise ValueError("qty_percent must be between 0.0 and 1.0")
        
        # Calculate requested quantity
        requested_qty = qty_percent * self.cargo_capacity
        
        # Check if we can load (different product or same product with space)
        if self.product is not None and self.product.id != product.id:
            return 0.0  # Cannot load different product
        
        # Calculate available space
        available_space = self.cargo_capacity - self.product_qty
        loaded_qty = min(requested_qty, available_space)
        
        if loaded_qty > 0:
            if self.product is None:
                self.product = product
            self.product_qty += loaded_qty
        
        return loaded_qty
    
    def unload(self, product, qty_percent: float):
        """
        Unload product from the vessel.
        
        Args:
            product: Type of product to unload
            qty_percent: Percentage of current quantity to unload (0.0 to 1.0)
            
        Returns:
            Actual quantity unloaded
        """
        if qty_percent < 0 or qty_percent > 1:
            raise ValueError("qty_percent must be between 0.0 and 1.0")
        
        # Check if we have the requested product
        if self.product.id != product.id or self.product_qty == 0:
            return 0.0
        
        # Calculate requested quantity to unload
        requested_qty = qty_percent * self.product_qty
        unloaded_qty = min(requested_qty, self.product_qty)
        
        self.product_qty -= unloaded_qty
        
        # If all product is unloaded, clear the product type
        if self.product_qty == 0:
            self.product = None
        
        return unloaded_qty
    
    def test_load(self, product, qty_percent: float, test_only: bool = True):
        """
        Test if loading is possible, optionally perform the load.
        
        Args:
            product: Type of product to load
            qty_percent: Percentage of cargo capacity to load (0.0 to 1.0)
            test_only: If True, only test without loading
            
        Returns:
            If test_only=True: boolean indicating if load is possible
            If test_only=False: tuple (success, loaded_qty)
        """
        if qty_percent < 0 or qty_percent > 1:
            if test_only:
                return False
            else:
                return False, 0.0
        
        # Check loading constraints
        if self.product is not None and self.product.id != product.id:
            if test_only:
                return False
            else:
                return False, 0.0
        
        requested_qty = qty_percent * self.cargo_capacity
        available_space = self.cargo_capacity - self.product_qty
        can_load = available_space >= requested_qty and (self.product is None or self.product.id == product.id)
        
        if test_only:
            return can_load
        else:
            if can_load:
                loaded_qty = self.load(product, qty_percent)
                return True, loaded_qty
            else:
                return False, 0.0
    
    def test_unload(self, product, qty_percent: float, test_only: bool = True):
        """
        Test if unloading is possible, optionally perform the unload.
        
        Args:
            product: Type of product to unload
            qty_percent: Percentage of current quantity to unload (0.0 to 1.0)
            test_only: If True, only test without unloading
            
        Returns:
            If test_only=True: boolean indicating if unload is possible
            If test_only=False: tuple (success, unloaded_qty)
        """
        if qty_percent < 0 or qty_percent > 1:
            if test_only:
                return False
            else:
                return False, 0.0
        
        # Check unloading constraints
        if self.product.id != product.id or self.product_qty == 0:
            if test_only:
                return False
            else:
                return False, 0.0
        
        requested_qty = qty_percent * self.product_qty
        can_unload = self.product_qty >= requested_qty
        
        if test_only:
            return can_unload
        else:
            if can_unload:
                unloaded_qty = self.unload(product, qty_percent)
                return True, unloaded_qty
            else:
                return False, 0.0
    
    @property
    def capacity_utilization(self) -> float:
        """Get current capacity utilization as percentage (0.0 to 1.0)"""
        return self.product_qty / self.cargo_capacity
    
    @property
    def available_capacity(self) -> float:
        """Get available cargo capacity"""
        return self.cargo_capacity - self.product_qty

    @property
    def available_capacity_percent(self) -> float:
        """Get available cargo capacity"""
        return 1 - self.capacity_utilization

    # RENT HANDLING
    def rented(self, days, product, product_qty, next_node, cost,  revenue, demurrage):
        self.is_in_rent = True
        self.days_left_in_rent = days
        self.days_left_in_rent_original = days
        self.update_rent_qty_times = 0
        self.rent_cost = cost
        self.rent_revenue = revenue
        self.rent_demurrage_rate = demurrage
        self.total_days_in_rent = 0
        self.product = product
        self.product_qty = product_qty
        self.next_node = next_node

    def return_from_rent(self):
        self.is_in_rent = False
        self.update_rent_qty_times = 0
        return self.rent_profit, self.rent_demurrage_rate * (self.days_left_in_rent - self.days_left_in_rent_original)

    def decrease_rent_days(self):
        self.days_left_in_rent -= 1 
        self.total_days_in_rent += 1

    def update_rent_days(self, days): 
        self.days_left_in_rent = days    
        self.update_rent_qty_times += 1



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
