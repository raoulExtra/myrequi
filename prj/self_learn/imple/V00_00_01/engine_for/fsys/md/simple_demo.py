#!/usr/bin/env python3
"""
Simple demo script for Filesystem Extraction functionality
"""

import tempfile
import os
import sys

# Add the current directory to Python path so we can import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filesystem_extraction import extract_sections

def main():
    # Create a temporary configuration file for demo
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        config_content = """
# Database Configuration
[database]
host = localhost
port = 5432
username = admin
password = secret

# Logging Configuration  
[logging]
level = INFO
file = /var/log/app.log

# Cache Configuration
[cache]
enabled = true
ttl = 3600
"""
        f.write(config_content)
        temp_file_path = f.name
    
    try:
        print("=== Filesystem Extraction Demo ===\n")
        
        print("Original configuration file content:")
        print("=" * 40)
        with open(temp_file_path, 'r') as f:
            print(f.read())
        
        print("\n" + "=" * 50)
        print("1. Extracting only database section:")
        print("=" * 50)
        result = extract_sections(temp_file_path, include_patterns=['database'], exclude_patterns=[])
        print(result)
        
        print("\n" + "=" * 50)
        print("2. Extracting all sections except cache:")
        print("=" * 50)
        result = extract_sections(temp_file_path, include_patterns=[], exclude_patterns=['cache'])
        print(result)
        
        print("\n" + "=" * 50)
        print("3. Extracting database and logging sections (excluding cache):")
        print("=" * 50)
        result = extract_sections(temp_file_path, include_patterns=['database', 'logging'], exclude_patterns=['cache'])
        print(result)
        
        print("\n" + "=" * 50)
        print("4. Extracting all sections (no patterns):")
        print("=" * 50)
        result = extract_sections(temp_file_path, include_patterns=[], exclude_patterns=[])
        print(result)
        
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

if __name__ == "__main__":
    main()