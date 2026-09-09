import unittest
import tempfile
import os
import sys

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from filesystem_extraction import extract_sections

class TestFilesystemExtraction(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary configuration file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "test_config.conf")
        
        # Sample config content
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
        
        with open(self.config_file, 'w') as f:
            f.write(config_content)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_extract_sections_with_inclusion_pattern(self):
        """Test extracting sections that match inclusion pattern"""
        # Extract sections containing 'database'
        result = extract_sections(
            self.config_file,
            include_patterns=['database'],
            exclude_patterns=[]
        )
        
        # Should contain database section
        self.assertIn('[database]', result)
        self.assertIn('host = localhost', result)
        self.assertIn('port = 5432', result)
        
        # Should not contain other sections
        self.assertNotIn('[logging]', result)
        self.assertNotIn('[cache]', result)
    
    def test_extract_sections_with_exclusion_pattern(self):
        """Test excluding sections that match exclusion pattern"""
        # Extract all sections except those containing 'cache'
        result = extract_sections(
            self.config_file,
            include_patterns=[],
            exclude_patterns=['cache']
        )
        
        # Should contain database and logging sections
        self.assertIn('[database]', result)
        self.assertIn('[logging]', result)
        
        # Should not contain cache section
        self.assertNotIn('[cache]', result)
    
    def test_extract_sections_with_both_patterns(self):
        """Test combining inclusion and exclusion patterns"""
        # Extract sections containing 'database' or 'logging' but exclude 'logging'
        result = extract_sections(
            self.config_file,
            include_patterns=['database', 'logging'],
            exclude_patterns=['logging']
        )
        
        # Should contain database section only
        self.assertIn('[database]', result)
        self.assertNotIn('[logging]', result)
        self.assertNotIn('[cache]', result)
    
    def test_extract_sections_no_matches(self):
        """Test when no patterns match"""
        result = extract_sections(
            self.config_file,
            include_patterns=['nonexistent'],
            exclude_patterns=[]
        )
        
        # Should return empty string
        self.assertEqual(result.strip(), '')
    
    def test_extract_sections_empty_patterns(self):
        """Test with empty patterns (should return all content)"""
        result = extract_sections(
            self.config_file,
            include_patterns=[],
            exclude_patterns=[]
        )
        
        # Should return entire content
        self.assertIn('[database]', result)
        self.assertIn('[logging]', result)
        self.assertIn('[cache]', result)
        self.assertIn('host = localhost', result)

if __name__ == '__main__':
    unittest.main()