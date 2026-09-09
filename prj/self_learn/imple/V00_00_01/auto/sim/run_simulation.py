#!/usr/bin/env python3
"""
Mesa Simulation Runner with -sim JSON argument.

Allows running Mesa simulations by specifying a JSON variant file
via command-line argument: --sim <path> or -sim <path>.

Supports phased project evolution with subprojects auto and auto/sim.
"""

import argparse
import json
import sys
from pathlib import Path


def load_json_variant(json_path: str) -> dict:
    """
    Load a Mesa-compatible JSON variant file.

    Args:
        json_path: Path to the JSON variant file

    Returns:
        Loaded JSON dictionary

    Raises:
        FileNotFoundError: If the JSON file does not exist
        json.JSONDecodeError: If the JSON is invalid
        ValueError: If the JSON lacks required __class__ key
    """
    json_file = Path(json_path)

    if not json_file.exists():
        raise FileNotFoundError(f"JSON variant file not found: {json_path}")

    with open(json_file, "r") as f:
        data = json.load(f)

    if "__class__" not in data:
        raise ValueError(
            f"JSON variant must contain '__class__' key: {json_path}"
        )

    return data


def validate_variant(data: dict) -> bool:
    """
    Validate that the loaded JSON variant has required structure.

    Args:
        data: Loaded JSON dictionary

    Returns:
        True if valid, False otherwise
    """
    required_keys = ["__class__"]
    return all(key in data for key in required_keys)


def run_simulation(json_path: str, iterations: int = 100) -> dict:
    """
    Run a Mesa simulation using a JSON variant file.

    Args:
        json_path: Path to the JSON variant file
        iterations: Number of simulation iterations (default: 100)

    Returns:
        Dictionary with simulation results including:
        - model: Loaded Mesa Model object
        - iterations: Number of iterations run
        - success: Whether simulation completed successfully
    """
    # Load the JSON variant
    data = load_json_variant(json_path)

    # Import Mesa components
    try:
        from mesa import Model, Agent
    except ImportError:
        print("Error: Mesa not installed. Install with: pip install mesa-py")
        sys.exit(1)

    # Validate the variant has required structure
    if not validate_variant(data):
        print(f"Error: Invalid JSON variant format: {json_path}")
        print("Must contain '__class__' key with fully qualified class name")
        sys.exit(1)

    # Extract class name from __class__ key
    class_name = data.pop("__class__")

    # TODO: Dynamically import and instantiate the model class
    # For now, create a basic Mesa Model
    model = Model()

    # Run simulation loop
    results = []
    for i in range(iterations):
        # Observe
        model.step()

        # Update (placeholder for learning logic)
        # Verify
        # Reuse
        results.append({"iteration": i, "model_state": model})

    return {
        "model": model,
        "iterations": iterations,
        "success": True,
        "results": results,
    }


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Run Mesa simulations with JSON variant argument",
        epilog="""
Examples:
    python -m auto.sim.run_simulation --sim variants/test_model.json
    python -m auto.sim.run_simulation -sim variants/test_model.json --iterations 500
        """,
    )

    parser.add_argument(
        "-sim",
        "--sim",
        dest="json_path",
        help="Path to JSON variant file to run simulation with",
        required=True,
    )

    parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=100,
        help="Number of simulation iterations (default: 100)",
    )

    args = parser.parse_args()

    # Run the simulation
    result = run_simulation(args.json_path, iterations=args.iterations)

    # Output results
    print(f"Mesa Simulation Results")
    print(f"=======================")
    print(f"JSON Variant: {args.json_path}")
    print(f"Iterations: {result['iterations']}")
    print(f"Success: {result['success']}")
    print(f"Final model: {result['model']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())