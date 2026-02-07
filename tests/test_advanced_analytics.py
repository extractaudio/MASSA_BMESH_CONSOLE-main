
import unittest
import sys
from unittest.mock import MagicMock, patch

# --- MOCK BLENDER ENVIRONMENT ---
# We must mock modules before importing advanced_analytics
sys.modules['bpy'] = MagicMock()
sys.modules['bmesh'] = MagicMock()
sys.modules['gpu'] = MagicMock()
sys.modules['gpu_extras'] = MagicMock()
sys.modules['gpu_extras.batch'] = MagicMock()
sys.modules['blf'] = MagicMock()
sys.modules['bpy_extras'] = MagicMock()
# textwrap is NOT mocked, it's standard library

import bpy
import bmesh

# Now we can import the module under test
sys.path.append("./MASSA_BMESH_CONSOLE-main")
from modules import advanced_analytics

class TestAdvancedAnalytics(unittest.TestCase):

    def setUp(self):
        # Reset mocks
        bpy.reset_mock()
        bmesh.reset_mock()

    def test_parse_panel_ast_valid(self):
        """Test parsing a valid Panel class with draw method."""

        # Define a dummy panel class
        class DummyPanel:
            def draw(self, context):
                layout = self.layout
                layout.prop(context.object, "location", text="Position")
                layout.prop(context.scene, "gravity", text="Gravity Force")

        # Mock bpy.types to return this class
        bpy.types.DummyPanel = DummyPanel

        # Run
        result = advanced_analytics.parse_panel_ast("DummyPanel")

        # Verify
        self.assertIsInstance(result, list)
        # Expected: [{"label": "Position", "api_property": "location"}, ...]
        expected = [
            {"label": "Position", "api_property": "location"},
            {"label": "Gravity Force", "api_property": "gravity"}
        ]
        self.assertEqual(result, expected)

    def test_parse_panel_ast_missing(self):
        """Test parsing a non-existent panel."""
        bpy.types.MissingPanel = None
        result = advanced_analytics.parse_panel_ast("MissingPanel")
        self.assertIn("error", result)

    def test_simulate_stack_logic(self):
        """Test the ghost simulation logic flow (creation, modification, cleanup)."""

        # Setup Mocks
        mock_obj = MagicMock()
        mock_obj.name = "TestCube"
        bpy.data.objects.get.return_value = mock_obj

        mock_copy = MagicMock() # The ghost object
        mock_obj.copy.return_value = mock_copy

        # Mock the mesh data object returned by obj.data.copy()
        mock_mesh_data = MagicMock()
        mock_mesh_data.users = 0
        mock_obj.data.copy.return_value = mock_mesh_data

        # Ensure new_obj.data returns this mock_mesh_data
        mock_copy.data = mock_mesh_data

        mock_depsgraph = MagicMock()
        bpy.context.evaluated_depsgraph_get.return_value = mock_depsgraph

        mock_eval_obj = MagicMock()
        mock_copy.evaluated_get.return_value = mock_eval_obj

        # Mock evaluated mesh data
        mock_eval_obj.data.vertices = [1, 2, 3] # len = 3
        mock_eval_obj.data.polygons = [1, 2]    # len = 2

        # Define Modifiers
        mods = [{"type": "REMESH", "props": {"voxel_size": 0.1}}]

        # Run
        stats = advanced_analytics.simulate_stack("TestCube", mods)

        # Assertions
        mock_obj.copy.assert_called_once()
        bpy.context.collection.objects.link.assert_called_with(mock_copy)
        mock_copy.modifiers.new.assert_called_with(name="GhostMod", type="REMESH")
        mock_copy.evaluated_get.assert_called_with(mock_depsgraph)

        # Cleanup Check
        bpy.data.objects.remove.assert_called_with(mock_copy, do_unlink=True)
        # Mesh Cleanup Check
        bpy.data.meshes.remove.assert_called_with(mock_mesh_data)

        self.assertEqual(stats["verts"], 3)
        self.assertEqual(stats["polys"], 2)

    def test_audit_evaluated_mesh(self):
        """Test the mesh audit logic using mocked BMesh."""
        mock_obj = MagicMock()
        bpy.data.objects.get.return_value = mock_obj

        mock_eval_obj = MagicMock()
        mock_obj.evaluated_get.return_value = mock_eval_obj
        mock_eval_obj.type = 'MESH'

        # Mock BMesh behavior
        mock_bm = bmesh.new.return_value

        # Create smart mocks for lists that support len, iter, AND methods
        # Use MagicMock directly but configure __len__ and __iter__
        verts_mock = MagicMock()
        verts_mock.__len__.return_value = 3
        verts_mock.__iter__.return_value = iter([MagicMock(), MagicMock(), MagicMock()])

        faces_mock = MagicMock()
        faces_mock.__len__.return_value = 1
        faces_mock.__iter__.return_value = iter([MagicMock()])

        edges_mock = MagicMock()
        edges_mock.__len__.return_value = 2
        e1, e2 = MagicMock(), MagicMock()
        e1.is_manifold = True
        e2.is_manifold = False
        edges_mock.__iter__.return_value = iter([e1, e2])

        mock_bm.verts = verts_mock
        mock_bm.faces = faces_mock
        mock_bm.edges = edges_mock

        # Run
        stats = advanced_analytics.audit_evaluated("TestCube")

        # Assertions
        # ensure_lookup_table calls
        verts_mock.ensure_lookup_table.assert_called_once()
        edges_mock.ensure_lookup_table.assert_called_once()

        self.assertEqual(stats["verts"], 3)
        self.assertEqual(stats["faces"], 1)
        self.assertEqual(stats["non_manifold"], 1)

        mock_bm.free.assert_called_once()

    def test_overlay_singleton(self):
        """Test that get_overlay returns the same instance."""
        inst1 = advanced_analytics.get_overlay()
        inst2 = advanced_analytics.get_overlay()
        self.assertIs(inst1, inst2)

        inst1.set_highlights([(1,1,1)])
        inst1.set_lines([((0,0,0), (1,1,1))])
        inst1.set_annotations([((0,0,0), "Label")])
        inst1.clear()

        bpy.types.SpaceView3D.draw_handler_add.assert_called_once()

if __name__ == '__main__':
    unittest.main()
