#!/usr/bin/env python3
"""Checker for configuration files.

Usage:
    python checker_for_conf.py -inp <file_or_path> -conf <file_or_path> [-extract]

Arguments:
    -inp <file_or_path>   Path to the input file to process
    -conf <file_or_path>  Path to the configuration file
    -extract              Flag to extract configuration values
"""

import argparse
import json
import os
import sys


def validate_config(config_path: str) -> dict:
    """Validate a configuration file against expected schema.

    Args:
        config_path: Path to the configuration file to validate.

    Returns:
        dict: Validated configuration data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the configuration is invalid.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load configuration file
    with open(config_path, "r") as f:
        if config_path.endswith(".json"):
            config = json.load(f)
        elif config_path.endswith(".yaml") or config_path.endswith(".yml"):
            import yaml
            config = yaml.safe_load(f)
        else:
            config = {}

    # Basic validation: ensure we have a dictionary
    if not isinstance(config, dict):
        raise ValueError(f"Configuration file must contain a JSON object/dictionary, got {type(config)}")

    return config


def process_input(input_path: str) -> dict:
    """Process an input file and extract relevant parameters.

    Args:
        input_path: Path to the input file to process.

    Returns:
        dict: Extracted parameters from the input file.

    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load input file
    with open(input_path, "r") as f:
        content = f.read()

    # Try to parse as JSON
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Return raw content as string if not valid JSON
    return {"content": content, "path": input_path}


def extract_values(config: dict, keys: list) -> dict:
    """Extract specified values from a configuration dictionary.

    Args:
        config: The configuration dictionary to extract from.
        keys: List of key paths to extract (dot-notation for nested keys).

    Returns:
        dict: Extracted values with their keys.
    """
    result = {}
    for key in keys:
        parts = key.split(".")
        value = config
        try:
            for part in parts:
                value = value[part]
            result[key] = value
        except (KeyError, TypeError):
            result[key] = None
    return result


def main():
    """Main entry point for the configuration checker."""
    parser = argparse.ArgumentParser(
        description="Checker for configuration files"
    )
    parser.add_argument(
        "-inp",
        required=True,
        help="Path to the input file to process",
    )
    parser.add_argument(
        "-conf",
        required=True,
        help="Path to the configuration file",
    )
    parser.add_argument(
        "-extract",
        action="store_true",
        help="Flag to extract configuration values",
    )

    args = parser.parse_args()

    # Validate configuration file
    try:
        config = validate_config(args.conf)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error validating configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Process input file
    try:
        input_data = process_input(args.inp)
    except FileNotFoundError as e:
        print(f"Error processing input: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle extraction flag
    if args.extract:
        # Extract common configuration keys
        keys_to_extract = ["input_path", "config_path", "mode", "format"]
        extracted = extract_values(config, keys_to_extract)

        print("=== Extracted Values ===")
        for key, value in extracted.items():
            print(f"{key}: {value}")

    # Report processing results
    print("=== Processing Summary ===")
    print(f"Input file: {args.inp}")
    print(f"Configuration file: {args.conf}")
    print(f"Input data type: {type(input_data).__name__}")
    print(f"Configuration validated: Yes")

    if args.extract:
        print("-extract flag: values extracted and displayed above")


if __name__ == "__main__":
    main()