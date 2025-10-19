from dataclasses import dataclass

import numpy as np
import random

from DataClasses import Contract, Vessel, Node, Product, Route, Fuel

from datetime import timedelta


GENERATE_DATA = True


@dataclass
class StepDataGenerator:
    def __init__(self, nodes, products, vessels, current_day, seed=None):
        """
        nodes: list of node names/IDs
        products: list of product names
        vessels: list of vessel IDs (or objects)
        """
        self.nodes = nodes
        self.products = products
        self.vessels = vessels
        self.current_day = current_day
        self.rng = np.random.default_rng(seed)
        
        # Base parameters (can be tuned later)
        self.params = {
            "contracts_per_node_mean": 4,
            "contracts_per_node_std": 2,
            "rentals_per_node_mean": 3,
            "rentals_per_node_std": 1,
            "demand_per_node_mean": 5,
            "demand_per_node_std": 2,
            
            # Contract attributes
            "revenue_mean": 20000,
            "revenue_std": 5000,
            "days_min_mean": 5,
            "days_min_std": 2,
            "days_max_mean": 15,
            "days_max_std": 3,
            
            # Rental attributes
            "rent_cost_mean": 1000,
            "rent_cost_std": 200,
            "demurrage_mean": 150,
            "demurrage_std": 30,
            
            # Demand attributes
            "qty_mean": 300,
            "qty_std": 80,
            "revenue_demand_mean": 10000,
            "revenue_demand_std": 2000,
        }

    # --- Utility for normal distribution draws ---
    def _randn(self, mean, std, low=None, high=None, dtype=float):
        val = self.rng.normal(mean, std)
        if low is not None:
            val = max(val, low)
        if high is not None:
            val = min(val, high)
        return dtype(val)

    # --- Main methods ---
    def get_next_node_list(self):
        """Generate next-node demand list per node."""
        data = {}
        for node in self.nodes:
            n = max(1, int(self._randn(
                self.params["demand_per_node_mean"],
                self.params["demand_per_node_std"]
            )))
            demands = []
            for i in range(n):
                product = random.choice(self.products)
                qty = max(1, int(self._randn(
                    self.params["qty_mean"], self.params["qty_std"]
                )))
                revenue = max(0, self._randn(
                    self.params["revenue_demand_mean"], self.params["revenue_demand_std"]
                ))
                days_min = max(1, int(self._randn(
                    self.params["days_min_mean"], self.params["days_min_std"]
                )))
                days_max = days_min + int(abs(self._randn(
                    self.params["days_max_mean"], self.params["days_max_std"]
                )))                
                days_ahead = random.randint(1, 14)
                demands.append(Node(
                    id = node.id,
                    demand_product = product,
                    demand_qty = qty,
                    demand_revenue = revenue,
                    demand_start_day = self.current_day.add_days(days_ahead),
                    days_min = days_min,
                    days_max = days_max
                ))
            data[node.id] = demands
        return data

    def get_rental_list(self):
        """Generate rental offers (for renting vessels)."""
        data = {}
        for node in self.nodes:

            n = max(1, int(self._randn(
                self.params["rentals_per_node_mean"],
                self.params["rentals_per_node_std"]
            )))
            rentals = []
            k = 0
            for i in range(n):
                vessel = random.choice(self.vessels)
                rent_cost = max(100, self._randn(
                    self.params["rent_cost_mean"], self.params["rent_cost_std"]
                ))
                demurrage = max(10, self._randn(
                    self.params["demurrage_mean"], self.params["demurrage_std"]
                ))
                rentals.append(Contract(
                    id = f"{node.id}_{k}",
                    vessel = vessel,
                    final_node = node,
                    cost_per_day = rent_cost,
                    demurrage_per_day = demurrage
                ))
                k += 1
            data[node.id] = rentals
        return data

    def get_contract_list(self):
        """Generate contracts where we loan out vessels."""
        data = {}
        for node in self.nodes:
            n = max(1, int(self._randn(
                self.params["contracts_per_node_mean"],
                self.params["contracts_per_node_std"]
            )))
            contracts = []
            k = 0
            for i in range(n):
                vessel = random.choice(self.vessels)
                days = max(1, int(self._randn(
                    self.params["days_min_mean"], self.params["days_min_std"]
                )))
                revenue_per_day = max(0, self._randn(
                    self.params["revenue_mean"], self.params["revenue_std"]
                ))
                demurrage_per_day = max(0, self._randn(
                    self.params["demurrage_mean"], self.params["demurrage_std"]
                ))
                #product = random.choice(self.products)
                contracts.append(Contract(
                    id = f"{node}_{k}",
                    vessel = vessel,
                    final_node = node,
                    revenue_per_day = revenue_per_day,
                    demurrage_per_day = demurrage_per_day,
                    days = days
                ))
                k += 1

            data[node.id] = contracts
        return data
