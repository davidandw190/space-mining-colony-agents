from server import server
import argparse

def run_simulation(headless=False, steps=100):
    if headless:
        from model import AsteroidMiningColony
        model = AsteroidMiningColony()

        for i in range(steps):
            model.step()
            if i % 10 == 0:
                print(f"Step {i}, Total Resources: {model.total_resources_collected}")

        print("\n--- Simulation Results ---")
        print(f"Total Resources Collected: {model.total_resources_collected}")
        print(f"Resource Breakdown:")
        for resource, amount in model.station.processed_resources.items():
            if amount > 0:
                value = amount * model.resource_values[resource]
                print(f"  {resource.capitalize()}: {amount} units (Value: {value})")

        total_value = sum(amount * model.resource_values[r] for r, amount in model.station.processed_resources.items())
        print(f"Total Value: {total_value}")

        print(f"Asteroids Depleted: {model.total_asteroids_depleted}")
        print(f"Operational Cost: {model.operational_cost}")
        print(f"Efficiency: {model.total_resources_collected / max(1, model.operational_cost):.2f} resources/energy")
    else:
        server.port = 8521  
        server.launch()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Asteroid Mining Colony Simulation")
    parser.add_argument("--headless", action="store_true", help="Run without visualization")
    parser.add_argument("--steps", type=int, default=100, help="Number of steps for headless simulation")

    args = parser.parse_args()
    run_simulation(args.headless, args.steps)