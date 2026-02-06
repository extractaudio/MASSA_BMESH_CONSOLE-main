import unittest
import sys
import os
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock

# --- SETUP ENVIRONMENT ---
# Add MCP root to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
mcp_root = os.path.abspath(os.path.join(current_dir, "../")) # Going up one level to MCP root
if mcp_root not in sys.path:
    print(f"Adding {mcp_root} to sys.path")
    sys.path.append(mcp_root)

# MOCK core.server.mcp BEFORE imports
# This is critical because the skills files import 'core.server' at the top level
sys.modules["core"] = MagicMock()
sys.modules["core.server"] = MagicMock()
mock_mcp_instance = MagicMock()
mock_mcp_instance.tool.return_value = lambda func: func 
sys.modules["core.server"].mcp = mock_mcp_instance

# Import Skills (Now safe)
import skills.cartridge_forge as forge
import skills.mechanic as mechanic
import skills.inspector as inspector

class TestMCPComprehensive(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for cartridges
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        
        # Create a dummy bridge script to satisfy os.path.exists checks
        self.dummy_bridge_path = os.path.join(self.test_dir, "runner.py")
        with open(self.dummy_bridge_path, 'w') as f:
            f.write("# Dummy Bridge")
            
        # Patch config constants in modules
        self.patches = [
            patch("skills.cartridge_forge.CARTRIDGE_DIR", self.test_dir),
            patch("skills.mechanic.CARTRIDGE_DIR", self.test_dir),
            patch("skills.inspector.CARTRIDGE_DIR", self.test_dir),
            patch("skills.inspector.OUTPUT_DIR", self.output_dir),
            patch("skills.inspector.BRIDGE_SCRIPT", self.dummy_bridge_path)
        ]
        for p in self.patches:
            p.start()
            
    def tearDown(self):
        for p in self.patches:
            p.stop()
        try:
            shutil.rmtree(self.test_dir)
            shutil.rmtree(self.output_dir)
        except:
            pass

    def create_dummy_cartridge(self, filename, content=""):
        path = os.path.join(self.test_dir, filename)
        with open(path, 'w') as f:
            f.write(content)
        return filename

    # ==========================================
    # 1. CARTRIDGE FORGE TESTS
    # ==========================================
    
    def test_create_primitive_cartridge(self):
        """Forge: Should create a file with correct primitive logic."""
        result = forge.create_primitive_cartridge("TestCube", "CUBE", 5.0)
        self.assertIn("Successfully created", result)
        
        filepath = os.path.join(self.test_dir, "TestCube.py")
        self.assertTrue(os.path.exists(filepath))
        
        with open(filepath, 'r') as f:
            content = f.read()
        self.assertIn("bmesh.ops.create_cube(bm, size=5.0)", content)

    def test_read_write_cartridge(self):
        """Forge: Should write content and read it back."""
        filename = "MyScript.py"
        code = "print('Hello World')"
        
        # Write
        forge.write_cartridge_script(filename, code)
        
        # Read
        read_back = forge.read_cartridge_script(filename)
        self.assertEqual(read_back, code)

    def test_list_cartridges(self):
        """Forge: Should list created files."""
        self.create_dummy_cartridge("A.py")
        self.create_dummy_cartridge("B.py")
        
        listing = forge.list_geometry_cartridges()
        self.assertIn("A.py", listing)
        self.assertIn("B.py", listing)

    def test_duplicate_cartridge(self):
        """Forge: Should copy file."""
        self.create_dummy_cartridge("Original.py", "Original Content")
        result = forge.duplicate_cartridge("Original", "Copy")
        
        self.assertIn("Success", result)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Copy.py")))

    # ==========================================
    # 2. MECHANIC TESTS
    # ==========================================

    def test_repair_topology_logic(self):
        """Mechanic: Should inject Phase 3 cleanup."""
        content = "def generate():\n    bm.to_mesh(mesh)\n    return obj"
        self.create_dummy_cartridge("bad_topo.py", content)
        
        result = mechanic.repair_topology_logic("bad_topo.py")
        self.assertIn("Successfully injected", result)
        
        with open(os.path.join(self.test_dir, "bad_topo.py"), 'r') as f:
            new_content = f.read()
        self.assertIn("bmesh.ops.remove_doubles", new_content)

    def test_fix_uv_pinching(self):
        """Mechanic: Should fix smart_project margin."""
        content = "bpy.ops.uv.smart_project(angle_limit=66)"
        self.create_dummy_cartridge("pinched.py", content)
        
        result = mechanic.fix_uv_pinching("pinched.py")
        self.assertIn("Applied UV margin fix", result)
         
        with open(os.path.join(self.test_dir, "pinched.py"), 'r') as f:
            new_content = f.read()
        self.assertIn("island_margin=0.02", new_content)

    def test_resolve_context_errors(self):
        """Mechanic: Should replace bpy.ops with bmesh.ops."""
        content = "bpy.ops.mesh.primitive_cube_add(size=2)"
        self.create_dummy_cartridge("context_err.py", content)
        
        result = mechanic.resolve_context_errors("context_err.py")
        self.assertIn("Resolved context errors", result)
        
        with open(os.path.join(self.test_dir, "context_err.py"), 'r') as f:
            new_content = f.read()
        self.assertIn("bmesh.ops.create_cube", new_content)

    def test_check_scale_safety(self):
        """Mechanic: Should detect unsafe microscopic values."""
        content = "size = 0.000001"
        self.create_dummy_cartridge("tiny.py", content)
        result = mechanic.check_scale_safety("tiny.py")
        self.assertIn("Unsafe", result)
        
        content_safe = "size = 1.0"
        self.create_dummy_cartridge("norm.py", content_safe)
        result_safe = mechanic.check_scale_safety("norm.py")
        self.assertIn("Safe", result_safe)

    def test_inject_boolean_jitter(self):
        """Mechanic: Should inject jitter before boolean ops."""
        content = "    bmesh.ops.boolean(bm, geom=geom, target=target)"
        self.create_dummy_cartridge("bool_fail.py", content)
        
        result = mechanic.inject_boolean_jitter("bool_fail.py")
        self.assertIn("Injected Jitter Logic", result)
        
        with open(os.path.join(self.test_dir, "bool_fail.py"), 'r') as f:
            new_content = f.read()
        self.assertIn("bmesh.ops.translate", new_content)

    def test_inject_standard_slots(self):
        """Mechanic: Should inject slots dict if missing."""
        content = "bm = bmesh.new()"
        self.create_dummy_cartridge("no_slots.py", content)
        
        result = mechanic.inject_standard_slots("no_slots.py")
        self.assertIn("Injected Standard Slots", result)
        
        with open(os.path.join(self.test_dir, "no_slots.py"), 'r') as f:
            new_content = f.read()
        self.assertIn("slots = {", new_content)

    # ==========================================
    # 3. INSPECTOR TESTS (Mocked Bridge)
    # ==========================================
    
    @patch('subprocess.run')
    def test_audit_cartridge_geometry(self, mock_run):
        """Inspector: Should parse JSON output from bridge."""
        self.create_dummy_cartridge("test.py")
        
        # Mock successful bridge response
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = json.dumps({"status": "PASS", "details": "All good"})
        mock_run.return_value = mock_response
        
        result = inspector.audit_cartridge_geometry("test.py")
        self.assertIn('"status": "PASS"', result)
        
        # Verify args
        args, _ = mock_run.call_args
        self.assertIn("--mode", args[0])
        self.assertIn("AUDIT", args[0])

    @patch('subprocess.run')
    def test_inspect_viewport(self, mock_run):
        """Inspector: Should return image path from bridge."""
        self.create_dummy_cartridge("vis.py")
        
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = json.dumps({"status": "SUCCESS", "image_path": "/tmp/img.png"})
        mock_run.return_value = mock_response
        
        result = inspector.inspect_viewport("vis.py", "TOP")
        self.assertIn("Viewport Captured: /tmp/img.png", result)

    @patch('subprocess.run')
    def test_stress_test_ui(self, mock_run):
        """Inspector: Should handle params and return report."""
        self.create_dummy_cartridge("stress.py")
        
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = json.dumps({"status": "STABLE"})
        mock_run.return_value = mock_response
        
        params = '{"size": 10}'
        result = inspector.stress_test_ui_parameters("stress.py", params)
        self.assertIn("STABLE", result)
        
        # Check if payload was passed
        args, _ = mock_run.call_args
        self.assertIn(json.dumps({"size": 10}), args[0])

    def test_verify_material_logic_static(self):
        """Inspector: Static check for MAT_TAG."""
        # Good case
        self.create_dummy_cartridge("mat_ok.py", 'bm.faces.layers.int.get("MAT_TAG")')
        result_ok = inspector.verify_material_logic("mat_ok.py")
        self.assertIn("PASS", result_ok)
        
        # Bad case
        self.create_dummy_cartridge("mat_bad.py", 'pass')
        result_bad = inspector.verify_material_logic("mat_bad.py")
        self.assertIn("FAIL", result_bad)

    @patch('subprocess.run')
    def test_visualize_edge_slots(self, mock_run):
        """Inspector: Should verify verification tool calls bridge."""
        self.create_dummy_cartridge("slots.py")
        
        mock_response = MagicMock()
        mock_response.returncode = 0
        mock_response.stdout = json.dumps({"status": "SUCCESS", "image_path": "/tmp/slot.png"})
        mock_run.return_value = mock_response
        
        result = inspector.visualize_edge_slots("slots.py", "seam")
        self.assertIn("Visualized: /tmp/slot.png", result)

if __name__ == "__main__":
    unittest.main()
