from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

from agents import ScoutDrone, MiningDrone, ProcessingStation, Asteroid, Beacon, SolarRadiation

import random
import numpy as np
from collections import defaultdict, deque

class CustomActivation(RandomActivation):
    def __init__(self, model):
        super().__init__(model)
        self.steps_stats = defaultdict(int)

    def step(self):
        self.steps_stats = defaultdict(int)
        super().step()

class AsteroidMiningColony(Model):
    def __init__(self, width=50, height=50,
                 num_scouts=5, num_miners=10,
                 num_asteroids=80, radiation_probability=0.01,
                 resource_richness=1.0, scout_sensor_range=3):
        super().__init__()
        self.width = width
        self.height = height
        self.num_scouts = num_scouts
        self.num_miners = num_miners
        self.num_asteroids = num_asteroids
        self.radiation_probability = radiation_probability
        self.resource_richness = resource_richness  # Multiplier for resource values
        self.scout_sensor_range = scout_sensor_range

        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = CustomActivation(self)

        self.base_pos = (width // 2, height // 2)

        self.active_beacons = []
        self.active_radiations = []
        self.scouts = []
        self.miners = []
        self.asteroids = []

        self.events = deque(maxlen=15)  

        self.total_resources_collected = 0
        self.step_counter = 0
        self.total_asteroids_depleted = 0
        self.operational_cost = 0 

        self.resource_values = {
            "iron": 1,
            "gold": 5,
            "platinum": 10,
            "water": 2,
            "helium": 20
        }

        station = ProcessingStation(self.next_id(), self)
        self.grid.place_agent(station, self.base_pos)
        self.schedule.add(station)
        self.station = station

        self.create_asteroids()

        for i in range(self.num_scouts):
            scout = ScoutDrone(self.next_id(), self, self.base_pos, sensor_range=scout_sensor_range)
            self.grid.place_agent(scout, self.base_pos)
            self.schedule.add(scout)
            self.scouts.append(scout)

            if i % 3 == 0:
                scout.exploration_pattern = "spiral"
            elif i % 3 == 1:
                scout.exploration_pattern = "sector"
            else:
                scout.exploration_pattern = "quadrant"

        for i in range(self.num_miners):
            miner = MiningDrone(self.next_id(), self, self.base_pos)
            self.grid.place_agent(miner, self.base_pos)
            self.schedule.add(miner)
            self.miners.append(miner)

        self.events.append(f"Colony initialized with {num_scouts} scouts, {num_miners} miners, and {num_asteroids} asteroids")

        self.datacollector = DataCollector(
            model_reporters={
                "Total Resources": lambda m: m.total_resources_collected,
                "Iron Collected": lambda m: m.station.processed_resources["iron"],
                "Gold Collected": lambda m: m.station.processed_resources["gold"],
                "Platinum Collected": lambda m: m.station.processed_resources["platinum"],
                "Water Collected": lambda m: m.station.processed_resources["water"],
                "Helium Collected": lambda m: m.station.processed_resources["helium"],
                "Active Beacons": lambda m: len(m.active_beacons),
                "Radiation Events": lambda m: len(m.active_radiations),
                "Scout Energy": lambda m: sum(s.energy for s in m.scouts) / max(1, len(m.scouts)),
                "Miner Energy": lambda m: sum(m.energy for m in m.miners) / max(1, len(m.miners)),
                "Asteroids Depleted": lambda m: m.total_asteroids_depleted,
                "Emergency Returns": lambda m: m.schedule.steps_stats["emergency_returns"],
                "Mining Efficiency": lambda m: self.calculate_mining_efficiency(),
                "Total Value": lambda m: self.calculate_total_value()
            },
            agent_reporters={
                "Energy": lambda a: getattr(a, "energy", 0) if hasattr(a, "type") and (a.type == "scout" or a.type == "miner") else 0,
                "Capacity": lambda a: getattr(a, "capacity", 0) if hasattr(a, "type") and a.type == "miner" else 0,
                "State": lambda a: getattr(a, "state", "") if hasattr(a, "type") and (a.type == "scout" or a.type == "miner") else "",
                "Resource_Value": lambda a: getattr(a, "resource_value", 0) if hasattr(a, "type") and a.type == "asteroid" else 0,
                "Is_Depleted": lambda a: getattr(a, "is_depleted", False) if hasattr(a, "type") and a.type == "asteroid" else False
            }
        )

        self.datacollector.collect(self)

    def calculate_mining_efficiency(self):
        total_energy_used = sum((scout.max_energy - scout.energy) for scout in self.scouts)
        total_energy_used += sum((miner.max_energy - miner.energy) for miner in self.miners)

        if total_energy_used == 0:
            return 0

        return self.total_resources_collected / max(1, total_energy_used)

    def calculate_total_value(self):
        total_value = 0
        for resource_type, amount in self.station.processed_resources.items():
            value_per_unit = self.resource_values.get(resource_type, 1)
            total_value += amount * value_per_unit
        return total_value

    def get_resource_distribution(self):
        total = sum(self.station.processed_resources.values())
        if total == 0:
            return {r: 0 for r in self.station.processed_resources}

        return {r: (amount / total) * 100 for r, amount in self.station.processed_resources.items()}

    def count_depleted_asteroids(self):
        return sum(1 for asteroid in self.asteroids if asteroid.is_depleted)

    def count_undiscovered_asteroids(self):
        all_beacons = [beacon.asteroid for beacon in self.active_beacons if beacon.asteroid is not None]
        return sum(1 for asteroid in self.asteroids
                   if not asteroid.is_depleted and asteroid not in all_beacons)

    def create_asteroids(self):
        resource_types = ["iron", "gold", "platinum", "water", "helium"]
        resource_weights = [0.5, 0.25, 0.1, 0.1, 0.05]  # Probabilities

        num_clusters = min(10, self.num_asteroids // 5)
        clusters = []

        for _ in range(num_clusters):
            while True:
                x = random.randrange(self.width)
                y = random.randrange(self.height)
                if abs(x - self.base_pos[0]) > 5 or abs(y - self.base_pos[1]) > 5:
                    break

            primary_resource = random.choices(resource_types, weights=resource_weights, k=1)[0]
            cluster_size = random.randint(3, 10)

            clusters.append((x, y, primary_resource, cluster_size))

        asteroids_created = 0
        for cluster_x, cluster_y, primary_resource, cluster_size in clusters:
            self.events.append(f"Created {primary_resource} asteroid cluster")
            for _ in range(cluster_size):
                if asteroids_created >= self.num_asteroids:
                    break

                radius = random.randint(1, 5)
                angle = random.uniform(0, 2 * np.pi)
                x = int(cluster_x + radius * np.cos(angle))
                y = int(cluster_y + radius * np.sin(angle))

                x = max(0, min(x, self.width - 1))
                y = max(0, min(y, self.height - 1))

                if random.random() < 0.8:
                    resource_type = primary_resource
                else:
                    resource_type = random.choices(resource_types, weights=resource_weights, k=1)[0]

                base_values = {
                    "iron": 30,  
                    "gold": 25,  
                    "platinum": 20, 
                    "water": 25,  
                    "helium": 10  
                }

                variation = random.uniform(0.7, 1.3) 
                resource_value = int(base_values[resource_type] * variation * self.resource_richness)

                asteroid = Asteroid(self.next_id(), self, resource_type, resource_value)
                self.grid.place_agent(asteroid, (x, y))
                self.schedule.add(asteroid)
                self.asteroids.append(asteroid)

                asteroids_created += 1

        while asteroids_created < self.num_asteroids:
            while True:
                x = random.randrange(self.width)
                y = random.randrange(self.height)
                if abs(x - self.base_pos[0]) > 3 or abs(y - self.base_pos[1]) > 3:
                    break

            resource_type = random.choices(resource_types, weights=resource_weights, k=1)[0]

            base_values = {
                "iron": 30,  
                "gold": 25,  
                "platinum": 20,  
                "water": 25,  
                "helium": 10   
            }

            variation = random.uniform(0.7, 1.3)
            resource_value = int(base_values[resource_type] * variation * self.resource_richness)

            asteroid = Asteroid(self.next_id(), self, resource_type, resource_value)
            self.grid.place_agent(asteroid, (x, y))
            self.schedule.add(asteroid)
            self.asteroids.append(asteroid)

            asteroids_created += 1

        self.events.append(f"Created {asteroids_created} asteroids total")

    def generate_solar_radiation(self):
        if random.random() < self.radiation_probability:
            radiation = SolarRadiation(self.next_id(), self)

            center_x = random.randrange(self.width)
            center_y = random.randrange(self.height)
            radius = random.randint(4, 8)

            radiation.center = (center_x, center_y)
            radiation.radius = radius

            affected_area = []
            for x in range(max(0, center_x - radius), min(self.width, center_x + radius + 1)):
                for y in range(max(0, center_y - radius), min(self.height, center_y + radius + 1)):
                    if ((x - center_x) ** 2 + (y - center_y) ** 2) <= radius ** 2:
                        affected_area.append((x, y))

            radiation.affected_area = affected_area
            self.schedule.add(radiation)
            self.active_radiations.append(radiation)

    def step(self):
        self.generate_solar_radiation()
        self.schedule.step()

        # operational cost (energy used)
        energy_cost = sum((scout.max_energy - scout.energy) for scout in self.scouts)
        energy_cost += sum((miner.max_energy - miner.energy) for miner in self.miners)
        self.operational_cost += energy_cost

        self.datacollector.collect(self)

        self.step_counter += 1

        if self.step_counter % 50 == 0:
            self.events.append(f"Step {self.step_counter}: {self.total_resources_collected} resources collected, value: {self.calculate_total_value()}")

        depleted_count = self.count_depleted_asteroids()
        depleted_pct = (depleted_count / len(self.asteroids)) * 100 if len(self.asteroids) > 0 else 0

        if (int(depleted_pct) % 10 == 0 and
                int(depleted_pct) > 0 and
                int(depleted_pct / 10) > int(((depleted_count - 1) / len(self.asteroids) * 100) / 10)):
            self.events.append(f"{depleted_pct:.1f}% of asteroids depleted ({depleted_count}/{len(self.asteroids)})")