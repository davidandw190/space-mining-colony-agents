from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter

from model import AsteroidMiningColony
import numpy as np

class ColonyInfoElement(TextElement):

    def render(self, model):
        if model.step_counter == 0:
            return "Simulation starting..."

        total_resources = model.total_resources_collected
        operational_cost = model.operational_cost
        efficiency = total_resources / max(1, operational_cost)

        resources = model.station.processed_resources

        resource_values = model.resource_values

        total_value = sum(resources[r] * resource_values[r] for r in resources.keys())

        scout_states = {state: sum(1 for s in model.scouts if s.state == state) for state in ["exploring", "analyzing", "returning", "recharging", "malfunctioning"]}
        miner_states = {state: sum(1 for m in model.miners if m.state == state) for state in ["idle", "moving_to_beacon", "mining", "returning", "recharging", "malfunctioning"]}

        total_asteroids = len(model.asteroids)
        depleted_asteroids = sum(1 for asteroid in model.asteroids if asteroid.is_depleted)

        info = f"<h3>Colony Stats (Step {model.step_counter})</h3>"
        info += f"<b>Resource Collection:</b> {total_resources} units <br>"
        info += f"<b>Total Value:</b> {total_value} credits <br>"
        info += f"<b>Efficiency:</b> {efficiency:.2f} resources/energy <br>"
        info += f"<b>Asteroids Depleted:</b> {depleted_asteroids}/{total_asteroids} ({(depleted_asteroids/total_asteroids*100) if total_asteroids > 0 else 0:.1f}%) <br>"
        info += f"<b>Active Beacons:</b> {len(model.active_beacons)} <br>"
        info += f"<b>Radiation Events:</b> {len(model.active_radiations)} <br><br>"

        info += "<b>Scout Status:</b> "
        for state, count in scout_states.items():
            if count > 0:
                info += f"{state}: {count} | "

        info += "<br><b>Miner Status:</b> "
        for state, count in miner_states.items():
            if count > 0:
                info += f"{state}: {count} | "

        info += "<br><br><b>Resource Breakdown:</b><br>"
        for resource, amount in resources.items():
            if amount > 0:
                info += f"{resource.capitalize()}: {amount} units (Value: {amount * resource_values[resource]} credits)<br>"

        return info

class EventLogElement(TextElement):
    def render(self, model):
        if not model.events:
            return "No events yet..."

        info = f"<h3>Recent Events</h3>"
        info += "<div style='height: 200px; overflow-y: scroll; border: 1px solid #ccc; padding: 5px;'>"

        for event in reversed(model.events):
            info += f"{event}<br>"

        info += "</div>"

        return info

class LegendElement(TextElement):
    def render(self, model):
        legend = """
        <h3>Legend</h3>
        <div style="display: flex; flex-wrap: wrap;">
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #A52A2A; margin-right: 5px;"></span>Iron Asteroid
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #FFD700; margin-right: 5px;"></span>Gold Asteroid
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #E5E4E2; margin-right: 5px;"></span>Platinum Asteroid
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #1E90FF; margin-right: 5px;"></span>Water Asteroid
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #ADD8E6; margin-right: 5px;"></span>Helium Asteroid
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #D3D3D3; margin-right: 5px;"></span>Depleted Asteroid (X)
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #FFFF00; margin-right: 5px;"></span>Beacon
            </div>
        </div>
        <div style="display: flex; flex-wrap: wrap; margin-top: 5px;">
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #4363d8; margin-right: 5px; border-radius: 50%;"></span>Scout (Exploring)
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #800080; margin-right: 5px; border-radius: 50%;"></span>Scout (Analyzing)
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #3cb44b; margin-right: 5px; border-radius: 50%;"></span>Scout (Returning)
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #4363d8; margin-right: 5px;"></span>Miner (Idle)
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #e6194B; margin-right: 5px;"></span>Miner (Mining)
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #FFA500; margin-right: 5px;"></span>Radiation Warning
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #FF0000; margin-right: 5px;"></span>Active Radiation
            </div>
            <div style="margin-right: 15px; margin-bottom: 5px;">
                <span style="display: inline-block; width: 15px; height: 15px; background-color: #e6beff; margin-right: 5px;"></span>Base Station
            </div>
        </div>
        """
        return legend

def agent_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "Layer": 0, "r": 0.5, "text_color": "black"}

    if hasattr(agent, 'type'):
        if agent.type == "scout":
            portrayal["Shape"] = "circle"
            portrayal["r"] = 0.7
            portrayal["Layer"] = 4 
            
            colors = {
                "exploring": "#4363d8",  # Blue
                "analyzing": "#800080",  # Purple
                "returning": "#3cb44b",  # Green
                "recharging": "#e6194B",  # Red
                "malfunctioning": "#f58231"  # Orange
            }
            portrayal["Color"] = colors.get(agent.state, "#000000")

            energy_pct = agent.energy / agent.max_energy
            if energy_pct > 0.6:
                energy_color = "#00ff00"  # Green
            elif energy_pct > 0.3:
                energy_color = "#ffff00"  # Yellow
            else:
                energy_color = "#ff0000"  # Red

            portrayal["text"] = f"S{agent.unique_id % 100}"
            portrayal["text_color"] = energy_color

            if energy_pct < 0.3:
                portrayal["strokeColor"] = "#ff0000"
                portrayal["strokeWidth"] = 2

        elif agent.type == "miner":
            portrayal["Shape"] = "rect"
            portrayal["w"] = 0.8
            portrayal["h"] = 0.8
            portrayal["Layer"] = 4  

            colors = {
                "idle": "#4363d8",  # Blue
                "moving_to_beacon": "#800080",  # Purple
                "mining": "#e6194B",  # Red
                "returning": "#3cb44b",  # Green
                "recharging": "#42d4f4",  # Cyan
                "malfunctioning": "#f58231"  # Orange
            }
            portrayal["Color"] = colors.get(agent.state, "#000000")

            energy_pct = agent.energy / agent.max_energy
            if energy_pct > 0.6:
                energy_color = "#00ff00"  # Green
            elif energy_pct > 0.3:
                energy_color = "#ffff00"  # Yellow
            else:
                energy_color = "#ff0000"  # Red

            capacity_pct = agent.capacity / agent.max_capacity if agent.max_capacity > 0 else 0

            resource_text = agent.resource_type[0].upper() if agent.resource_type else "-"
            portrayal["text"] = f"M{agent.unique_id % 100}:{resource_text}"
            portrayal["text_color"] = energy_color

            if capacity_pct > 0.8:
                portrayal["strokeColor"] = "#00ff00"
                portrayal["strokeWidth"] = 2

            if energy_pct < 0.3:
                portrayal["strokeColor"] = "#ff0000"
                portrayal["strokeWidth"] = 2

        elif agent.type == "station":
            portrayal["Color"] = "#e6beff"  # Light purple
            portrayal["Shape"] = "rect"
            portrayal["w"] = 1.7
            portrayal["h"] = 1.7
            portrayal["Layer"] = 0
            portrayal["text"] = "BASE"
            portrayal["text_color"] = "#000000"

            # Add processing indicator
            if agent.currently_processing:
                resource_type, amount, time = agent.currently_processing
                portrayal["text"] = f"BASE [{resource_type}: {time}]"
                portrayal["strokeColor"] = "#00ff00"
                portrayal["strokeWidth"] = 2

        elif agent.type == "asteroid":
            portrayal["Layer"] = 1

            if hasattr(agent, 'is_depleted') and agent.is_depleted:
                portrayal["Color"] = "#D3D3D3"  # Light gray
                portrayal["Shape"] = "rect"
                portrayal["w"] = 0.7
                portrayal["h"] = 0.7
                portrayal["text"] = "X"  
                portrayal["text_color"] = "#FF0000"  # Red X
            else:
                colors = {
                    "iron": "#A52A2A",  # Brown
                    "gold": "#FFD700",  # Gold
                    "platinum": "#E5E4E2",  # Silver/Platinum
                    "water": "#1E90FF",  # Blue
                    "helium": "#ADD8E6"   # Light blue
                }
                portrayal["Color"] = colors.get(agent.resource_type, "#000000")

                if agent.resource_value > 20:  
                    portrayal["Shape"] = "rect"
                    portrayal["w"] = 1.0
                    portrayal["h"] = 1.0
                else:
                    portrayal["Shape"] = "rect"
                    portrayal["w"] = 0.7
                    portrayal["h"] = 0.7

                portrayal["text"] = agent.resource_type[0].upper()

                value_percent = agent.resource_value / agent.original_value if agent.original_value > 0 else 0
                if value_percent < 0.3:
                    portrayal["text_color"] = "#ff0000"  # Red for nearly depleted
                else:
                    portrayal["text_color"] = "#000000"

        elif agent.type == "beacon":
            portrayal["Color"] = "#FFFF00"  # Yellow
            portrayal["Layer"] = 2
            portrayal["r"] = 0.3
            portrayal["Shape"] = "circle"

            portrayal["text"] = str(agent.value)
            portrayal["text_color"] = "#000000"

            value_percent = agent.value / agent.original_value if agent.original_value > 0 else 0
            if value_percent < 0.3:
                portrayal["strokeColor"] = "#ff0000"  # Red stroke for nearly depleted
                portrayal["strokeWidth"] = 2
            else:
                portrayal["strokeColor"] = "#ffd700"  # Gold stroke normally
                portrayal["strokeWidth"] = 1

            if agent.model.step_counter % 10 < 5:
                portrayal["r"] = 0.35
            else:
                portrayal["r"] = 0.3

        elif agent.type == "radiation":
            if agent.active:
                portrayal["Color"] = "#FF0000"  
                portrayal["Layer"] = 1

                if agent.center and agent.radius:
                    portrayal["Shape"] = "circle"
                    portrayal["r"] = 0.5
                    portrayal["text"] = "☢"  # Radiation symbol
                    portrayal["text_color"] = "#000000"

                    portrayal["strokeColor"] = "#FF0000"
                    portrayal["strokeWidth"] = 2

                    if agent.model.step_counter % 4 < 2:
                        portrayal["r"] = 0.6
                    else:
                        portrayal["r"] = 0.5
            else:
                portrayal["Color"] = "#FFA500"  # Orange for warning
                portrayal["Layer"] = 1
                portrayal["Shape"] = "circle"
                portrayal["r"] = 0.4
                portrayal["text"] = "!"  # Warning symbol
                portrayal["text_color"] = "#000000"

                portrayal["strokeColor"] = "#FFA500"
                portrayal["strokeWidth"] = 1

                if agent.model.step_counter % 4 < 2:
                    portrayal["r"] = 0.5
                else:
                    portrayal["r"] = 0.4

    return portrayal

canvas_element = CanvasGrid(agent_portrayal, 50, 50, 700, 700)

info_element = ColonyInfoElement()
event_log_element = EventLogElement()
legend_element = LegendElement()

resource_chart = ChartModule([
    {"Label": "Total Resources", "Color": "black"},
    {"Label": "Iron Collected", "Color": "#A52A2A"},
    {"Label": "Gold Collected", "Color": "#FFD700"},
    {"Label": "Platinum Collected", "Color": "#E5E4E2"},
    {"Label": "Water Collected", "Color": "#1E90FF"},
    {"Label": "Helium Collected", "Color": "#ADD8E6"}
], data_collector_name='datacollector')

activity_chart = ChartModule([
    {"Label": "Active Beacons", "Color": "#FFFF00"},
    {"Label": "Radiation Events", "Color": "#FF0000"},
    {"Label": "Asteroids Depleted", "Color": "#D3D3D3"}
], data_collector_name='datacollector')

efficiency_chart = ChartModule([
    {"Label": "Scout Energy", "Color": "#4363d8"},
    {"Label": "Miner Energy", "Color": "#3cb44b"},
    {"Label": "Mining Efficiency", "Color": "#f58231"},
    {"Label": "Total Value", "Color": "#e6194B"}
], data_collector_name='datacollector')

model_params = {
    "width": 50,
    "height": 50,
    "num_scouts": UserSettableParameter("slider", "Number of Scout Drones", 5, 1, 15, 1),
    "num_miners": UserSettableParameter("slider", "Number of Mining Drones", 10, 1, 25, 1),
    "num_asteroids": UserSettableParameter("slider", "Number of Asteroids", 80, 20, 200, 10),
    "radiation_probability": UserSettableParameter("slider", "Radiation Probability", 0.01, 0, 0.1, 0.01),
    "resource_richness": UserSettableParameter("slider", "Resource Richness", 1.0, 0.5, 3.0, 0.1),
    "scout_sensor_range": UserSettableParameter("slider", "Scout Sensor Range", 3, 1, 6, 1)
}

server = ModularServer(
    AsteroidMiningColony,
    [canvas_element, info_element, legend_element, event_log_element, resource_chart, activity_chart, efficiency_chart],
    "Enhanced Asteroid Mining Colony",
    model_params
)