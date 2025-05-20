# Asteroid Mining Colony Simulation in MESA

An agent-based simulation of an autonomous asteroid mining operation built with MESA framework for my Intelligent Systems and Machine Learning course. The simulation models a space mining colony with scout drones exploring the environment, mining drones collecting resources, and a central processing station.

## Project Overview

This simulation models a resource extraction operation in space with the following key components:

- **Scout Drones**: Explore the environment to locate asteroid resources using different exploration patterns (spiral, sector, quadrant)
- **Mining Drones**: Extract resources from identified asteroids and return them to base
- **Processing Station**: Central base that processes collected resources
- **Asteroids**: Resources of different types (iron, gold, platinum, water, helium) with varying values
- **Beacons**: Markers placed by scouts to indicate valuable asteroid locations
- **Solar Radiation**: Environmental hazard that affects drone operations

The simulation includes emergent behaviors and challenges such as:
- Energy management for drones
- Optimal resource allocation and mining priority
- Dealing with environmental hazards
- Drone malfunctions and repairs

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt

# or install directly with setup.py
pip install -e .
```
## Requirements

- Python 3.11+
- Mesa 1.2.1
- NumPy
- Matplotlib

## Running the Simulation

### With Visualization (Web Interface)

```bash
python run.py
```

### Headless Mode (No Visualization)

```bash
python run.py --headless --steps 200
```

## Simulation Parameters

The following parameters can be adjusted in the web interface or programmatically:

| Parameter | Description | Default |
|-----------|-------------|---------|
| Number of Scout Drones | Quantity of scouts exploring the environment | 5 |
| Number of Mining Drones | Quantity of miners collecting resources | 10 |
| Number of Asteroids | Resource objects distributed in the environment | 80 |
| Radiation Probability | Chance of solar radiation events each step | 0.01 |
| Resource Richness | Multiplier affecting asteroid resource values | 1.0 |
| Scout Sensor Range | Detection range for scout drones | 3 |

## Components and Mechanics

### Agents

1. **ScoutDrone**
   - Explores the environment using different patterns (spiral, sector, quadrant)
   - Detects asteroids within sensor range
   - Analyzes asteroid content and places beacons on valuable resources
   - Manages energy and returns to base when low on power
   - May experience random malfunctions

2. **MiningDrone**
   - Targets beacons placed by scouts
   - Extracts resources from asteroids
   - Returns to base when cargo is full or energy is low
   - Delivers resources to the processing station
   - Has different mining efficiency for different resource types

3. **ProcessingStation**
   - Central base for the colony
   - Receives and processes resources from mining drones
   - Tracks collected resources by type
   - Has a processing queue with different times per resource

4. **Asteroid**
   - Contains a specific resource type (iron, gold, platinum, water, helium)
   - Has a limited resource value that depletes when mined
   - Distributed in clusters throughout the environment

5. **Beacon**
   - Placed by scouts to mark valuable asteroids
   - Contains information about resource type and value
   - Has a limited lifetime
   - Helps miners locate resources

6. **SolarRadiation**
   - Random environmental hazard
   - Affects a circular area for a limited time
   - Damages drones within its area of effect
   - Has a warning period before activation

### Visualization Components

The web interface includes:
- **Main Grid**: Visual representation of the simulation environment
- **Colony Stats**: Real-time statistics on resource collection and drone status
- **Event Log**: Recent events in the simulation
- **Resource Charts**: Graphs showing resource collection over time
- **Activity Charts**: Tracking of beacons, radiation events, and depleted asteroids
- **Efficiency Charts**: Monitoring of drone energy levels and mining efficiency

## Output and Analysis

The simulation tracks various metrics including:
- Total resources collected by type
- Resource values
- Mining efficiency (resources per energy unit)
- Drone states and activities
- Environmental events

In headless mode, a summary of these statistics is printed at the end of the simulation.

