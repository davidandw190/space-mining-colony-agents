from mesa import Agent
import numpy as np
import random
import math
from collections import defaultdict

class ScoutDrone(Agent):
    def __init__(self, unique_id, model, base_pos, max_energy=100, sensor_range=3):
        super().__init__(unique_id, model)
        self.type = "scout"
        self.energy = max_energy
        self.max_energy = max_energy
        self.base_pos = base_pos
        self.state = "exploring"  # states: exploring, analyzing, returning, recharging, malfunctioning
        self.exploration_pattern = "sector"  # "spiral", "sector", or "quadrant"
        self.analyzed_asteroids = set()
        self.visited_positions = set()  
        self.sensor_range = sensor_range  
        self.target_position = None
        self.malfunction_chance = 0.001  
        self.repair_time = 0  
        self.quadrant = random.randint(0, 3)  
        self.target_asteroid = None
        self.critical_energy = self.max_energy * 0.15
        self.step_count = 0  

        # for spiral pattern
        self.direction = 0  # 0 = right, 1 = up, 2 = left, 3 = down
        self.steps_in_direction = 1
        self.steps_taken = 0
        self.turns_taken = 0

        # for sector pattern
        self.current_radius = 3
        self.max_radius = max(self.model.grid.width, self.model.grid.height) // 2
        self.angle = random.uniform(0, 2 * math.pi)
        self.angle_increment = math.pi / 8  # 22.5 degrees

    def step(self):
        self.step_count += 1
        if self.state != "malfunctioning" and random.random() < self.malfunction_chance:
            self.state = "malfunctioning"
            self.repair_time = random.randint(3, 8)
            self.model.events.append(f"Scout {self.unique_id} malfunctioned!")
            return

        if self.state == "malfunctioning":
            if self.pos == self.base_pos:
                self.repair_time -= 1
                if self.repair_time <= 0:
                    self.state = "recharging"
                    self.model.events.append(f"Scout {self.unique_id} repaired")
            else:
                self.move_safely_towards(self.base_pos)
            return

        self.energy -= 1

        if self.energy <= self.critical_energy and self.state != "returning" and self.state != "recharging":
            self.state = "returning"
            self.model.schedule.steps_stats["emergency_returns"] += 1

        if self.state == "exploring":
            self.visited_positions.add(self.pos)

            if self.scan_for_asteroids():
                return

            self.move_exploration_pattern()

        elif self.state == "analyzing":
            self.analyze_asteroid()

        elif self.state == "returning":
            if self.pos == self.base_pos:
                self.state = "recharging"
                self.energy = min(self.energy + self.max_energy * 0.3, self.max_energy)  # Initial energy boost
            else:
                self.move_safely_towards(self.base_pos)

        elif self.state == "recharging":
            self.energy = min(self.energy + self.max_energy * 0.2, self.max_energy)
            if self.energy >= self.max_energy:
                self.state = "exploring"
                if random.random() < 0.3:
                    self.reset_exploration_pattern()

    def scan_for_asteroids(self):
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False, radius=self.sensor_range
        )

        unanalyzed_asteroids = [
            neighbor for neighbor in neighbors
            if hasattr(neighbor, 'type') and neighbor.type == "asteroid"
               and neighbor not in self.analyzed_asteroids
               and not (hasattr(neighbor, 'is_depleted') and neighbor.is_depleted)
        ]

        if unanalyzed_asteroids:
            self.target_asteroid = min(
                unanalyzed_asteroids,
                key=lambda a: ((a.pos[0] - self.pos[0])**2 + (a.pos[1] - self.pos[1])**2)
            )
            self.state = "analyzing"
            return True
        return False

    def analyze_asteroid(self):
        if not self.target_asteroid or not hasattr(self.target_asteroid, 'resource_value'):
            self.state = "exploring"
            return

        self.analyzed_asteroids.add(self.target_asteroid)

        if hasattr(self.target_asteroid, 'is_depleted') and self.target_asteroid.is_depleted:
            self.state = "exploring"
            return

        min_value_threshold = {
            "iron": 8,
            "gold": 4,
            "platinum": 2,
            "water": 6,
            "helium": 1
        }.get(self.target_asteroid.resource_type, 5)  # Lower thresholds for faster depletion

        if self.target_asteroid.resource_value >= min_value_threshold:
            cell_contents = self.model.grid.get_cell_list_contents([self.target_asteroid.pos])
            existing_beacon = any(hasattr(a, 'type') and a.type == "beacon" for a in cell_contents)

            if not existing_beacon:
                beacon = Beacon(
                    self.model.next_id(),
                    self.model,
                    self.target_asteroid.pos,
                    self.target_asteroid.resource_type,
                    self.target_asteroid.resource_value,
                    self.target_asteroid
                )
                self.model.grid.place_agent(beacon, self.target_asteroid.pos)
                self.model.schedule.add(beacon)
                self.model.active_beacons.append(beacon)
                self.model.schedule.steps_stats["beacons_placed"] += 1

                self.model.events.append(f"Scout {self.unique_id} placed beacon for {self.target_asteroid.resource_type}")

        self.state = "exploring"

    def reset_exploration_pattern(self):
        if self.exploration_pattern == "spiral":
            # reset spiral parameters
            self.direction = random.randint(0, 3)
            self.steps_in_direction = 1
            self.steps_taken = 0
            self.turns_taken = 0
        elif self.exploration_pattern == "sector":
            # move to a new sector
            self.angle = random.uniform(0, 2 * math.pi)
            self.current_radius = 3
        elif self.exploration_pattern == "quadrant":
            # move to a different quadrant
            self.quadrant = random.randint(0, 3)

    def move_exploration_pattern(self):
        if self.exploration_pattern == "spiral":
            self.move_spiral_pattern()
        elif self.exploration_pattern == "sector":
            self.move_sector_pattern()
        elif self.exploration_pattern == "quadrant":
            self.move_quadrant_pattern()

    def move_spiral_pattern(self):
        next_pos = list(self.pos)

        # Direction: 0 = right, 1 = up, 2 = left, 3 = down
        if self.direction == 0:
            next_pos[0] += 1
        elif self.direction == 1:
            next_pos[1] += 1
        elif self.direction == 2:
            next_pos[0] -= 1
        elif self.direction == 3:
            next_pos[1] -= 1

        if (0 <= next_pos[0] < self.model.grid.width and
                0 <= next_pos[1] < self.model.grid.height):
            self.model.grid.move_agent(self, tuple(next_pos))
        else:
            self.direction = (self.direction + 1) % 4
            return self.move_spiral_pattern()

        self.steps_taken += 1
        if self.steps_taken == self.steps_in_direction:
            self.direction = (self.direction + 1) % 4
            self.steps_taken = 0
            self.turns_taken += 1
            if self.turns_taken == 2:
                self.steps_in_direction += 1
                self.turns_taken = 0

    def move_sector_pattern(self):
        center_x, center_y = self.base_pos
        target_x = center_x + int(self.current_radius * math.cos(self.angle))
        target_y = center_y + int(self.current_radius * math.sin(self.angle))

        if (0 <= target_x < self.model.grid.width and
                0 <= target_y < self.model.grid.height):
            self.move_safely_towards((target_x, target_y))

            if self.pos == (target_x, target_y):
                self.angle += self.angle_increment
                if self.angle >= 2 * math.pi:
                    self.angle = 0
                    self.current_radius += 2
                    if self.current_radius > self.max_radius:
                        self.current_radius = 3
        else:
            self.angle += self.angle_increment
            if self.angle >= 2 * math.pi:
                self.angle = 0
                self.current_radius += 2

    def move_quadrant_pattern(self):
        half_width = self.model.grid.width // 2
        half_height = self.model.grid.height // 2

        if self.quadrant == 0:  # Top-right
            bounds = (half_width, self.model.grid.width, half_height, self.model.grid.height)
        elif self.quadrant == 1:  # Top-left
            bounds = (0, half_width, half_height, self.model.grid.height)
        elif self.quadrant == 2:  # Bottom-left
            bounds = (0, half_width, 0, half_height)
        else:  # Bottom-right
            bounds = (half_width, self.model.grid.width, 0, half_height)

        # choose a random point in the quadrant
        if not self.target_position or self.pos == self.target_position:
            x = random.randint(bounds[0], bounds[1] - 1)
            y = random.randint(bounds[2], bounds[3] - 1)
            self.target_position = (x, y)

        self.move_safely_towards(self.target_position)

    def move_safely_towards(self, target_pos):
        current_x, current_y = self.pos
        target_x, target_y = target_pos

        dx = 0
        if current_x < target_x:
            dx = 1
        elif current_x > target_x:
            dx = -1

        dy = 0
        if current_y < target_y:
            dy = 1
        elif current_y > target_y:
            dy = -1

        possible_moves = []

        if dx != 0 and dy != 0:
            # diagonal movement
            possible_moves.append((current_x + dx, current_y + dy))
            possible_moves.append((current_x + dx, current_y))
            possible_moves.append((current_x, current_y + dy))
        elif dx != 0:
            # horizontal movement
            possible_moves.append((current_x + dx, current_y))
            possible_moves.append((current_x + dx, current_y + 1))
            possible_moves.append((current_x + dx, current_y - 1))
        elif dy != 0:
            # vertical movement
            possible_moves.append((current_x, current_y + dy))
            possible_moves.append((current_x + 1, current_y + dy))
            possible_moves.append((current_x - 1, current_y + dy))

        valid_moves = [
            move for move in possible_moves
            if 0 <= move[0] < self.model.grid.width and 0 <= move[1] < self.model.grid.height
        ]

        if not valid_moves:
            return  # No valid moves

        safe_moves = []
        for move in valid_moves:
            is_safe = True
            for radiation in self.model.active_radiations:
                if move in radiation.affected_area:
                    is_safe = False
                    break
            if is_safe:
                safe_moves.append(move)

        if safe_moves:
            unvisited_moves = [move for move in safe_moves if move not in self.visited_positions]
            if unvisited_moves:
                next_pos = min(unvisited_moves,
                               key=lambda m: abs(m[0] - target_x) + abs(m[1] - target_y))
            else:
                next_pos = min(safe_moves,
                               key=lambda m: abs(m[0] - target_x) + abs(m[1] - target_y))
        else:
            next_pos = min(valid_moves,
                           key=lambda m: abs(m[0] - target_x) + abs(m[1] - target_y))

        self.model.grid.move_agent(self, next_pos)

class MiningDrone(Agent):
    def __init__(self, unique_id, model, base_pos, max_capacity=50, max_energy=150):
        super().__init__(unique_id, model)
        self.type = "miner"
        self.base_pos = base_pos
        self.energy = max_energy
        self.max_energy = max_energy
        self.capacity = 0
        self.max_capacity = max_capacity
        self.state = "idle"  # States: idle, moving_to_beacon, mining, returning, recharging, malfunctioning
        self.target_beacon = None
        self.mining_efficiency = {
            "iron": 8,      
            "gold": 5,      
            "platinum": 4,  
            "water": 6,     
            "helium": 2     
        }
        self.resource_type = None  
        self.malfunction_chance = 0.002 
        self.repair_time = 0 
        self.critical_energy = self.max_energy * 0.2
        self.last_positions = []  
        self.wait_time = 0  
        self.step_count = 0 

    def step(self):
        self.step_count += 1
        
        if self.state != "malfunctioning" and random.random() < self.malfunction_chance:
            self.state = "malfunctioning"
            self.repair_time = random.randint(4, 10)
            self.model.events.append(f"Miner {self.unique_id} malfunctioned!")
            return

        if self.state == "malfunctioning":
            if self.pos == self.base_pos:
                self.repair_time -= 1
                if self.repair_time <= 0:
                    self.state = "recharging"
                    self.model.events.append(f"Miner {self.unique_id} repaired")
            else:
                self.move_safely_towards(self.base_pos)
            return

        self.last_positions.append(self.pos)
        if len(self.last_positions) > 5:
            self.last_positions.pop(0)

        if len(self.last_positions) == 5 and all(p == self.last_positions[0] for p in self.last_positions):
            if self.wait_time > 0:
                self.wait_time -= 1
                return
            else:
                self.random_move()
                self.model.events.append(f"Miner {self.unique_id} was stuck, making random move")
                return

        self.energy -= 1

        if self.energy <= self.critical_energy and self.state not in ["returning", "recharging"]:
            self.state = "returning"
            self.model.schedule.steps_stats["emergency_returns"] += 1
            self.model.events.append(f"Miner {self.unique_id} low energy, returning to base")

        if self.state == "idle":
            if self.find_optimal_beacon():
                self.state = "moving_to_beacon"
            else:
                self.random_move()

        elif self.state == "moving_to_beacon":
            if self.target_beacon not in self.model.active_beacons:
                self.state = "idle"
                self.target_beacon = None
                return

            if self.pos == self.target_beacon.pos:
                self.state = "mining"
                self.model.events.append(f"Miner {self.unique_id} started mining {self.target_beacon.resource_type}")
            else:
                self.move_safely_towards(self.target_beacon.pos)

        elif self.state == "mining":
            if self.target_beacon not in self.model.active_beacons:
                self.state = "idle"
                self.target_beacon = None
                return

            self.mine_resources()

            if self.capacity >= self.max_capacity * 0.8 or (self.target_beacon and self.target_beacon.value <= 0):
                self.state = "returning"
                if self.target_beacon and self.target_beacon.value <= 0:
                    self.clean_up_depleted_beacon()

                self.target_beacon = None

        elif self.state == "returning":
            if self.pos == self.base_pos:
                self.state = "recharging"
                if self.capacity > 0:
                    self.deliver_resources()
            else:
                self.move_safely_towards(self.base_pos)

        elif self.state == "recharging":
            if self.energy < self.max_energy * 0.3:
                self.energy = min(self.energy + self.max_energy * 0.3, self.max_energy)
            else:
                self.energy = min(self.energy + self.max_energy * 0.1, self.max_energy)

            if self.energy >= self.max_energy:
                self.state = "idle"
                if self.capacity > 0:
                    self.model.events.append(f"Miner {self.unique_id} fully recharged but still has {self.capacity} resources!")
                else:
                    self.model.events.append(f"Miner {self.unique_id} fully recharged and ready")

    def deliver_resources(self):
        for agent in self.model.grid.get_cell_list_contents([self.pos]):
            if hasattr(agent, 'type') and agent.type == "station":
                agent.receive_resources(self.capacity, self.resource_type)
                self.model.total_resources_collected += self.capacity
                self.model.schedule.steps_stats["resources_delivered"] += self.capacity

                self.model.events.append(f"Miner {self.unique_id} delivered {self.capacity} {self.resource_type}")

                self.capacity = 0
                self.resource_type = None
                break

    def clean_up_depleted_beacon(self):
        if not self.target_beacon:
            return

        if self.target_beacon.asteroid:
            self.target_beacon.asteroid.resource_value = 0
            self.target_beacon.asteroid.is_depleted = True
            self.model.events.append(f"Asteroid depleted: {self.target_beacon.resource_type}")

        self.model.grid.remove_agent(self.target_beacon)
        self.model.schedule.remove(self.target_beacon)
        if self.target_beacon in self.model.active_beacons:
            self.model.active_beacons.remove(self.target_beacon)

        self.model.schedule.steps_stats["asteroids_depleted"] += 1
        self.model.total_asteroids_depleted += 1 

    def find_optimal_beacon(self):
        if not self.model.active_beacons:
            return False

        available_beacons = []
        beacon_miners_count = {}

        for beacon in self.model.active_beacons:
            miners_targeting = sum(1 for miner in self.model.miners
                                   if miner.target_beacon == beacon and miner.unique_id != self.unique_id)
            beacon_miners_count[beacon] = miners_targeting

            if miners_targeting < 2: 
                available_beacons.append(beacon)

        if not available_beacons:
            return False

        # we calculate score for each beacon based on:
        # 1. resource value
        # 2. distance (closer is better)
        # 3. congestion (fewer miners is better)
        # 4. resource type priority

        resource_priority = {
            "platinum": 5,
            "helium": 4,
            "gold": 3,
            "water": 2,
            "iron": 1
        }

        beacon_scores = {}
        for beacon in available_beacons:
            distance = abs(beacon.pos[0] - self.pos[0]) + abs(beacon.pos[1] - self.pos[1])
            miners_count = beacon_miners_count[beacon]

            if distance > self.energy * 0.4:
                continue

            resource_score = resource_priority.get(beacon.resource_type, 0)

            score = (beacon.value * 0.5) + (resource_score * 10) - (distance * 2) - (miners_count * 10)
            beacon_scores[beacon] = score

        if not beacon_scores:
            return False

        self.target_beacon = max(beacon_scores.keys(), key=lambda b: beacon_scores[b])
        self.resource_type = self.target_beacon.resource_type
        self.model.events.append(f"Miner {self.unique_id} targeting {self.resource_type} beacon")
        return True

    def mine_resources(self):
        if not self.target_beacon:
            return

        mining_speed = self.mining_efficiency.get(self.target_beacon.resource_type, 3)
        actual_mining_speed = max(1, int(mining_speed * random.uniform(0.8, 1.2)))
        amount = min(actual_mining_speed, self.target_beacon.value, self.max_capacity - self.capacity)

        self.target_beacon.value -= amount
        if self.target_beacon.asteroid:
            self.target_beacon.asteroid.resource_value = self.target_beacon.value
        
        self.capacity += amount

        self.model.schedule.steps_stats["resources_mined"] += amount

        if self.step_count % 5 == 0 or self.target_beacon.value <= 0:
            if self.target_beacon.value <= 0:
                self.model.events.append(f"Miner {self.unique_id} depleted asteroid, returning with {self.capacity} {self.resource_type}")
            else:
                self.model.events.append(f"Miner {self.unique_id} mined {amount} {self.resource_type}, remaining: {self.target_beacon.value}")

    def random_move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )

        free_positions = []
        for pos in possible_steps:
            agents_in_cell = self.model.grid.get_cell_list_contents([pos])
            has_drone = any(hasattr(a, 'type') and (a.type == "scout" or a.type == "miner") for a in agents_in_cell)
            if not has_drone:
                free_positions.append(pos)

        if free_positions:
            new_position = random.choice(free_positions)
            self.model.grid.move_agent(self, new_position)
        else:
            self.wait_time = random.randint(1, 3)

    def move_safely_towards(self, target_pos):
        current_x, current_y = self.pos
        target_x, target_y = target_pos

        dx = 0
        if current_x < target_x:
            dx = 1
        elif current_x > target_x:
            dx = -1

        dy = 0
        if current_y < target_y:
            dy = 1
        elif current_y > target_y:
            dy = -1

        possible_moves = []

        if dx != 0 and dy != 0:
            # Diagonal movement
            possible_moves.append((current_x + dx, current_y + dy))
            possible_moves.append((current_x + dx, current_y))
            possible_moves.append((current_x, current_y + dy))
        elif dx != 0:
            # Horizontal movement
            possible_moves.append((current_x + dx, current_y))
            possible_moves.append((current_x + dx, current_y + 1))
            possible_moves.append((current_x + dx, current_y - 1))
        elif dy != 0:
            # Vertical movement
            possible_moves.append((current_x, current_y + dy))
            possible_moves.append((current_x + 1, current_y + dy))
            possible_moves.append((current_x - 1, current_y + dy))

        valid_moves = [
            move for move in possible_moves
            if 0 <= move[0] < self.model.grid.width and 0 <= move[1] < self.model.grid.height
        ]

        if not valid_moves:
            return  

        safe_moves = []
        for move in valid_moves:
            is_safe = True

            for radiation in self.model.active_radiations:
                if move in radiation.affected_area:
                    is_safe = False
                    break

            if is_safe:
                agents_in_cell = self.model.grid.get_cell_list_contents([move])
                for agent in agents_in_cell:
                    if hasattr(agent, 'type') and (agent.type == "scout" or agent.type == "miner"):
                        is_safe = False
                        break

            if is_safe:
                safe_moves.append(move)

        if safe_moves:
            next_pos = min(safe_moves,
                           key=lambda m: abs(m[0] - target_x) + abs(m[1] - target_y))
        elif valid_moves:
            if (target_x, target_y) in valid_moves:
                next_pos = (target_x, target_y)
            else:
                if random.random() < 0.7:  
                    self.wait_time = random.randint(1, 2)
                    return
                next_pos = min(valid_moves,
                               key=lambda m: abs(m[0] - target_x) + abs(m[1] - target_y))
        else:
            return  

        self.model.grid.move_agent(self, next_pos)

class ProcessingStation(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "station"
        self.resources = {"iron": 0, "gold": 0, "platinum": 0, "water": 0, "helium": 0}
        self.processed_resources = {"iron": 0, "gold": 0, "platinum": 0, "water": 0, "helium": 0}
        self.processing_queue = [] 
        self.processing_capacity = 15 
        self.processing_time = {
            "iron": 1,     
            "gold": 2,     
            "platinum": 3, 
            "water": 1,
            "helium": 3    
        }  
        self.currently_processing = None  # (resource_type, amount, remaining_time)
        self.total_processed = 0  

    def step(self):
        self.process_current_batch()

        if self.currently_processing is None and self.processing_queue:
            self.start_new_batch()

    def receive_resources(self, amount, resource_type):
        if resource_type in self.resources:
            self.resources[resource_type] += amount
            self.processing_queue.append((resource_type, amount))

    def process_current_batch(self):
        if self.currently_processing:
            resource_type, amount, remaining_time = self.currently_processing

            remaining_time -= 1

            if remaining_time <= 0:
                self.processed_resources[resource_type] += amount
                self.total_processed += amount

                self.model.events.append(f"Station processed {amount} {resource_type}")

                self.currently_processing = None
            else:
                self.currently_processing = (resource_type, amount, remaining_time)

    def start_new_batch(self):
        if not self.processing_queue:
            return

        resource_type, amount = self.processing_queue.pop(0)

        processing_time = self.processing_time.get(resource_type, 2)

        self.currently_processing = (resource_type, amount, processing_time)

        self.model.events.append(f"Station started processing {amount} {resource_type}")

class Asteroid(Agent):
    def __init__(self, unique_id, model, resource_type, resource_value):
        super().__init__(unique_id, model)
        self.type = "asteroid"
        self.resource_type = resource_type
        self.resource_value = resource_value 
        self.original_value = resource_value 
        self.is_depleted = False

    def step(self):
        if self.resource_value <= 0 and not self.is_depleted:
            self.is_depleted = True
            self.model.events.append(f"Asteroid {self.unique_id} ({self.resource_type}) depleted")

class Beacon(Agent):
    def __init__(self, unique_id, model, pos, resource_type, value, asteroid=None):
        super().__init__(unique_id, model)
        self.type = "beacon"
        self.resource_type = resource_type
        self.value = value 
        self.original_value = value  
        self.asteroid = asteroid  
        self.lifetime = 200  
        self.creation_time = model.schedule.steps

    def step(self):
        self.lifetime -= 1
        if self.asteroid and hasattr(self.asteroid, 'resource_value'):
            self.value = self.asteroid.resource_value

        if self.value <= 0:
            if self.asteroid:
                self.asteroid.is_depleted = True

            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            if self in self.model.active_beacons:
                self.model.active_beacons.remove(self)
            return

        if self.lifetime <= 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            if self in self.model.active_beacons:
                self.model.active_beacons.remove(self)

            self.model.events.append(f"Beacon expired after {self.model.schedule.steps - self.creation_time} steps")

class SolarRadiation(Agent):
    def __init__(self, unique_id, model, duration=10, damage=5, warning_duration=3):
        super().__init__(unique_id, model)
        self.type = "radiation"
        self.duration = duration  
        self.damage = damage  
        self.affected_area = [] 
        self.active = False  
        self.warning_duration = warning_duration 
        self.center = None 
        self.radius = 0 

        model.events.append(f"Radiation warning detected! Will activate in {warning_duration} steps")

    def step(self):
        if self.warning_duration > 0:
            self.warning_duration -= 1
            if self.warning_duration <= 0:
                self.active = True
                self.model.events.append("Radiation activated! Drones in affected area taking damage")
        else:
            self.duration -= 1

            if self.active:
                drones_affected = 0
                for pos in self.affected_area:
                    cell_contents = self.model.grid.get_cell_list_contents([pos])
                    for agent in cell_contents:
                        if hasattr(agent, 'type') and (agent.type == "scout" or agent.type == "miner"):
                            before_energy = agent.energy
                            agent.energy = max(0, agent.energy - self.damage)
                            drones_affected += 1

                            if agent.energy <= agent.critical_energy:
                                agent.state = "returning"
                                self.model.events.append(f"Drone {agent.unique_id} critically damaged by radiation, returning to base")

                if drones_affected > 0 and self.duration % 3 == 0:
                    self.model.events.append(f"Radiation affecting {drones_affected} drones")

            if self.duration <= 0:
                self.model.schedule.remove(self)
                if self in self.model.active_radiations:
                    self.model.active_radiations.remove(self)

                self.model.events.append("Radiation dissipated")