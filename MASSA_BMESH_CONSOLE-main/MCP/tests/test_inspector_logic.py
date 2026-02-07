import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# --- SETUP ENVIRONMENT ---
# Add MCP root to path to allow imports
# Add MCP root to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is MCP/tests
# mcp_root is MCP
mcp_root = os.path.abspath(os.path.join(current_dir, ".."))
if mcp_root not in sys.path:
    sys.path.append(mcp_root)

# Mock core.server.mcp to avoid server initialization side effects during testing
# This must be done BEFORE importing skills.inspector
sys.modules["core"] = MagicMock()
sys.modules["core.server"] = MagicMock()
mock_mcp = MagicMock()
# The decorator needs to return the function itself so the tool remains callable
mock_mcp.tool.return_value = lambda func: func 
sys.modules["core.server"].mcp = mock_mcp

# Import the tool to be tested
from skills.inspector import verify_material_logic

class TestVerifyMaterialLogic(unittest.TestCase):
    
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

    def test_compliant_cartridge(self):
        """Test that a cartridge with the correct MAT_TAG logic passes."""
        content = """
import bmesh
def generate(bm):
    # This line is required for Phase 4 compliance
    tag_layer = bm.faces.layers.int.new("MAT_TAG")
    edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
    pass
"""
        filename = self.create_dummy_cartridge("valid_cart.py", content)
        
        # Patch CARTRIDGE_DIR to point to our temp directory
        with patch("skills.inspector.CARTRIDGE_DIR", self.test_dir):
            result = verify_material_logic(filename)
            
        self.assertIn("PASS: MAT_TAG layer detected", result)
        self.assertIn("PASS: MASSA_EDGE_SLOTS layer detected", result)

    def test_non_compliant_cartridge(self):
        """Test that a cartridge missing the MAT_TAG logic fails."""
        content = """
import bmesh
def generate(bm):
    # Missing the layer retrieval
    pass
"""
        filename = self.create_dummy_cartridge("invalid_cart.py", content)
        
        with patch("skills.inspector.CARTRIDGE_DIR", self.test_dir):
            result = verify_material_logic(filename)
            
        self.assertIn("FAIL: MAT_TAG layer missing", result)
        self.assertIn("FAIL: MASSA_EDGE_SLOTS layer missing", result)

if __name__ == "__main__":
    unittest.main()