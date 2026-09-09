#!/usr/bin/env python3
"""
Simple demonstration of the filesystem extraction functionality
"""

import sys
import os
import tempfile

# Add the module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filesystem_extraction import extract_sections

def demo_usage():
    # Create a sample config file to test with
    sample_config = """
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
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(sample_config)
        temp_file = f.name
    
    try:
        print("=== Filesystem Extraction Demo ===")
        print()
        
        print("1. Extracting only database section:")
        result = extract_sections(temp_file, include_patterns=['database'], exclude_patterns=[])
        print(result)
        print()
        
        print("2. Extracting all sections except cache:")
        result = extract_sections(temp_file, include_patterns=[], exclude_patterns=['cache'])
        print(result)
        print()
        
        print("3. Extracting with both patterns (database and logging, but exclude cache):")
        result = extract_sections(temp_file, include_patterns=['database', 'logging'], exclude_patterns=['cache'])
        print(result)
        
    finally:
        # Clean up
        os.unlink(temp_file)

if __name__ == "__main__":
    demo_usage()