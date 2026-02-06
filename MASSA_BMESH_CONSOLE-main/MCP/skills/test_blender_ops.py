
import unittest
import json
import sys
import os
from unittest.mock import MagicMock, patch

# Adjust path to import core/skills
mcp_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if mcp_root not in sys.path:
    sys.path.append(mcp_root)

# Mock mcp BEFORE importing skills
sys.modules["core.server"] = MagicMock()
sys.modules["core.server.mcp"] = MagicMock()

from skills import blender_ops

class TestBlenderOps(unittest.TestCase):
    
    def setUp(self):
        # Directly replace the module reference in blender_ops
        self.original_inspector = blender_ops.inspector
        self.mock_inspector = MagicMock()
        blender_ops.inspector = self.mock_inspector
        # The function we want to check is called on this mock
        self.mock_bridge = self.mock_inspector._invoke_bridge
        # Configure return values for successful execution
        self.mock_bridge.return_value = {"status": "success"}

    def tearDown(self):
        blender_ops.inspector = self.original_inspector

    def test_get_scene_info(self):
        # Mock Response
        self.mock_bridge.return_value = {
            "status": "success",
            "scene_info": {"total": 10}
        }
        
        result = blender_ops.get_scene_info(limit=5, offset=2, object_type="MESH")
        
        # Verify Bridge Call
        self.mock_bridge.assert_called_once()
        args, kwargs = self.mock_bridge.call_args
        payload = kwargs['payload']
        
        self.assertEqual(payload['skill'], 'get_scene_info')
        self.assertEqual(payload['params']['limit'], 5)
        self.assertEqual(payload['params']['offset'], 2)
        self.assertEqual(payload['params']['object_type'], "MESH")
        
        # Verify Output
        self.assertIn('"total": 10', result)

    def test_get_object_info(self):
        self.mock_bridge.return_value = {"object_info": {"name": "Cube"}}
        
        result = blender_ops.get_object_info("Cube")
        
        args, kwargs = self.mock_bridge.call_args
        self.assertEqual(kwargs['payload']['skill'], 'get_object_info')
        self.assertEqual(kwargs['payload']['params']['object_name'], "Cube")

    def test_get_viewport_screenshot(self):
        self.mock_bridge.return_value = {"image": "base64data=="}
        
        result = blender_ops.get_viewport_screenshot()
        
        args, kwargs = self.mock_bridge.call_args
        self.assertEqual(kwargs['payload']['skill'], 'get_vision')
        self.assertIn('Screenshot Captured', result)
        
    def test_execute_blender_code(self):
        self.mock_bridge.return_value = {"output": "result", "status": "success"}
        
        result = blender_ops.execute_blender_code("print('hello')")
        
        args, kwargs = self.mock_bridge.call_args
        self.assertEqual(kwargs['payload']['skill'], 'execute_code')
        self.assertEqual(kwargs['payload']['params']['code'], "print('hello')")
        self.assertIn("result", result)

    def test_create_bmesh_object(self):
        self.mock_bridge.return_value = {"msg": "Created Object: NewGrid"}
        
        script = "bmesh.ops.create_grid(bm, x_segments=10, y_segments=10, size=1)"
        result = blender_ops.create_bmesh_object("NewGrid", script)
        
        args, kwargs = self.mock_bridge.call_args
        self.assertEqual(kwargs['payload']['skill'], 'create_bmesh')
        self.assertEqual(kwargs['payload']['params']['name'], "NewGrid")
        self.assertEqual(kwargs['payload']['params']['script_content'], script)

if __name__ == '__main__':
    unittest.main()
