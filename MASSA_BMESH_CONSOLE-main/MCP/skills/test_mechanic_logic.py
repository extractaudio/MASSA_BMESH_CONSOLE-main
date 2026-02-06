import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# --- SETUP ENVIRONMENT ---
# Add MCP root to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
mcp_root = os.path.abspath(os.path.join(current_dir, "../MCP"))
if mcp_root not in sys.path:
    sys.path.append(mcp_root)

# Mock core.server.mcp to avoid server initialization side effects during testing
# This must be done BEFORE importing skills.mechanic
sys.modules["core"] = MagicMock()
sys.modules["core.server"] = MagicMock()
mock_mcp = MagicMock()
# The decorator needs to return the function itself so the tool remains callable
mock_mcp.tool.return_value = lambda func: func 
sys.modules["core.server"].mcp = mock_mcp

# Import the tool to be tested
from skills.mechanic import inject_standard_slots

class TestMechanicLogic(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory to act as the 'geometry_cartridges' folder
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Cleanup the temporary directory
        shutil.rmtree(self.test_dir)

    def create_dummy_cartridge(self, filename, content):
        path = os.path.join(self.test_dir, filename)
        with open(path, 'w') as f:
            f.write(content)
        return filename

    def test_inject_slots_success(self):
        """Test that slots are injected correctly when missing."""
        content = """
import bmesh
def generate_geometry():
    bm = bmesh.new()
    # Logic missing slots
    bmesh.ops.create_cube(bm, size=1)
    bm.free()
"""
        filename = self.create_dummy_cartridge("missing_slots.py", content)
        
        # Patch CARTRIDGE_DIR to point to our temp directory
        with patch("skills.mechanic.CARTRIDGE_DIR", self.test_dir):
            result = inject_standard_slots(filename)
            
        self.assertIn("Injected Standard Slots dictionary", result)
        
        # Verify file content
        with open(os.path.join(self.test_dir, filename), 'r') as f:
            new_content = f.read()
            
        self.assertIn("slots = {", new_content)
        self.assertIn("'bevel': []", new_content)

    def test_slots_already_present(self):
        """Test that the tool does nothing if slots exist."""
        content = """
import bmesh
def generate_geometry():
    bm = bmesh.new()
    slots = {'bevel': []}
    bm.free()
"""
        filename = self.create_dummy_cartridge("has_slots.py", content)
        
        with patch("skills.mechanic.CARTRIDGE_DIR", self.test_dir):
            result = inject_standard_slots(filename)
            
        self.assertIn("Slots dictionary already present", result)

    def test_no_anchor_point(self):
        """Test failure when bmesh.new() cannot be found."""
        content = """def generate(): pass"""
        filename = self.create_dummy_cartridge("empty.py", content)
        
        with patch("skills.mechanic.CARTRIDGE_DIR", self.test_dir):
            result = inject_standard_slots(filename)
            
        self.assertIn("Could not find 'bm = bmesh.new()' to inject slots", result)

if __name__ == "__main__":
    unittest.main()