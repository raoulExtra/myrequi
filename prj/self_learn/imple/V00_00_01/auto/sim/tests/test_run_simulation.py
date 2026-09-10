"""Tests for Mesa simulation runner with -sim JSON argument."""

import json
import sys
import tempfile
import unittest
from pathlib import Path


# Add the project root to sys.path so we can import the simulation module
sys.path.insert(0, str(Path(__file__).resolve().parents[7]))


class TestRunSimulationImport(unittest.TestCase):
    """Test that the run_simulation module can be imported."""

    def test_module_importable(self):
        """Test that run_simulation module can be imported."""
        from prj.self_learn.imple.V00_00_01.auto.sim.run_simulation import run_simulation
        self.assertTrue(callable(run_simulation))


class TestJSONVariantLoading(unittest.TestCase):
    """Test JSON variant loading from project directory."""

    def setUp(self):
        """Set up test fixture."""
        self.test_dir = tempfile.mkdtemp()
        self.JSON_DIR = Path(self.test_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_load_valid_json_variant(self):
        """Test loading a valid JSON variant file."""
        # Create a valid Mesa-compatible JSON variant
        variant = {
            "__class__": "prj.self_learn.auto.sim.models.PhasedProjectModel",
            "phases": [],
            "subprojects": [],
        }
        variant_file = self.JSON_DIR / "test_model.json"
        with open(variant_file, "w") as f:
            json.dump(variant, f)

        # Test loading
        from prj.self_learn.imple.V00_00_01.auto.sim.run_simulation import load_json_variant
        result = load_json_variant(str(variant_file))
        self.assertIsNotNone(result)
        self.assertEqual(result["__class__"], "prj.self_learn.auto.sim.models.PhasedProjectModel")

    def test_load_invalid_json(self):
        """Test loading invalid JSON file."""
        # Create invalid JSON file
        variant_file = self.JSON_DIR / "invalid.json"
        with open(variant_file, "w") as f:
            f.write("{invalid json}")

        # Test loading should fail gracefully
        from prj.self_learn.imple.V00_00_01.auto.sim.run_simulation import load_json_variant
        with self.assertRaises((json.JSONDecodeError, FileNotFoundError)):
            load_json_variant(str(variant_file))

    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        from prj.self_learn.imple.V00_00_01.auto.sim.run_simulation import load_json_variant
        with self.assertRaises(FileNotFoundError):
            load_json_variant("/nonexistent/path.json")


class TestSimulationExecution(unittest.TestCase):
    """Test simulation execution with -sim argument."""

    def setUp(self):
        """Set up test fixture."""
        self.test_dir = tempfile.mkdtemp()
        self.JSON_DIR = Path(self.test_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_create_minimal_variant(self):
        """Test creating a minimal valid Mesa variant."""
        variant = {
            "__class__": "prj.self_learn.auto.sim.models.PhasedProjectModel",
            "phases": [],
            "subprojects": [],
            "name": "test_simulation",
        }
        variant_file = self.JSON_DIR / "test_model.json"
        with open(variant_file, "w") as f:
            json.dump(variant, f)

        # Test that variant can be loaded and has required keys
        from prj.self_learn.imple.V00_00_01.auto.sim.run_simulation import load_json_variant, validate_variant
        loaded = load_json_variant(str(variant_file))
        self.assertTrue(validate_variant(loaded))


if __name__ == "__main__":
    unittest.main()