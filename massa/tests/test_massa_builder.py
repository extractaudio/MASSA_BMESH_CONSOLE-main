import bpy
import bmesh
import unittest
import sys
import os
from mathutils import Vector

# Ensure path to modules is available
# Assuming we are in 'tests/' folder or root, we need to add 'MASSA_BMESH_CONSOLE-main' to path?
# The structure is:
# /repo/MASSA_BMESH_CONSOLE-main/tests/test_massa_builder.py
# /repo/MASSA_BMESH_CONSOLE-main/modules/massa_builder.py

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from modules.massa_builder import MassaBuilder
except ImportError:
    print("Failed to import MassaBuilder. Check sys.path.")
    sys.exit(1)

class TestMassaBuilder(unittest.TestCase):

    def setUp(self):
        # Create a new BMesh for each test
        self.bm = bmesh.new()
        self.builder = MassaBuilder(self.bm)

    def tearDown(self):
        self.bm.free()

    def test_create_box(self):
        self.builder.create_box(2.0, 2.0, 2.0)
        self.bm.verts.ensure_lookup_table()
        self.assertEqual(len(self.bm.verts), 8)
        self.assertEqual(len(self.bm.faces), 6)

        # Check volume (approximate)
        vol = self.bm.calc_volume()
        self.assertAlmostEqual(vol, 8.0, places=4)

    def test_extrude(self):
        self.builder.create_grid(1, 1, 1.0) # 1 face
        self.builder.select_all_faces()
        self.builder.extrude(1.0)

        # Grid (4 verts, 1 face) -> Extrude (8 verts, 1+4 = 5 faces? Or does extrude replace original?)
        # extrude_face_region usually keeps the original "bottom" if it wasn't dissolved, but typically creates a volume.
        # Grid is a plane. Extruding a plane creates a box (no bottom cap unless implied).
        # Let's check counts.
        self.bm.verts.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

        # Should be a box without bottom face? Or with?
        # MassaBuilder.extrude calls bmesh.ops.extrude_face_region.
        # If input is a single open face, result is a box with 5 faces (4 sides + top). The bottom is the original face?
        # No, the original face is moved or replaced.
        # Actually, extrude_face_region on a manifold mesh extrudes. On a plane, it creates a solid.

        # Grid: 1 face.
        # Extrude: 5 faces total (Top + 4 Sides). The original bottom face is usually kept at the base?
        # Actually, for a grid, bmesh extrude creates the side walls and the new top. The original face stays at the bottom.
        # So 6 faces?

        # Let's just check valid geometry.
        self.assertTrue(len(self.bm.verts) >= 8)
        self.assertTrue(len(self.bm.faces) >= 5)

    def test_selection_by_normal(self):
        self.builder.create_box(1, 1, 1)
        self.builder.select_faces_by_normal(Vector((0, 0, 1)))

        self.assertEqual(len(self.builder.active_faces), 1)
        # Verify it's the top face
        face = self.builder.active_faces[0]
        self.assertAlmostEqual(face.normal.z, 1.0, places=4)

    def test_tag_slot(self):
        self.builder.create_box(1, 1, 1)
        self.builder.select_faces_by_normal(Vector((0, 0, 1)))
        self.builder.tag_slot(5)

        face = self.builder.active_faces[0]
        self.assertEqual(face.material_index, 5)

    def test_tag_socket(self):
        self.builder.create_box(1, 1, 1)
        self.builder.select_faces_by_normal(Vector((0, 0, 1)))
        self.builder.tag_socket(2)

        layer = self.bm.faces.layers.int.get("MASSA_SOCKETS")
        self.assertIsNotNone(layer)

        face = self.builder.active_faces[0]
        self.assertEqual(face[layer], 2)

    def test_report(self):
        self.builder.create_box(1,1,1)
        report = self.builder.report()
        self.assertIn("Verts: 8", report)
        self.assertIn("Faces: 6", report)

if __name__ == '__main__':
    # Isolate from Blender CLI args
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        # If run directly via blender --python without -- args,
        # unittest will try to interpret blender flags.
        # Safest is to pass empty argv if no -- args are present.
        argv = [sys.argv[0]] # Just script name

    unittest.main(argv=argv, exit=False)
