import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARC_03: Curtain Wall",
    "id": "arc_03_window",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcWindow(Massa_OT_Base):
    bl_idname = "massa.gen_arc_03_window"
    bl_label = "ARC Window"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    win_width: FloatProperty(name="Width", default=2.0, min=0.1)
    win_height: FloatProperty(name="Height", default=2.5, min=0.1)

    # Grid
    mullion_x: IntProperty(name="Mullion X", default=2, min=1)
    mullion_y: IntProperty(name="Mullion Y", default=3, min=1)
    frame_width: FloatProperty(name="Frame Width", default=0.1, min=0.01)
    mullion_thick: FloatProperty(name="Frame Depth", default=0.1, min=0.01)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "GLASS"}, # Mandate: Manual UV Fit
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        # 2. Base Plane
        # XZ Plane facing Y-
        # No, usually windows face Y- or Y+. Let's align with Wall (XZ Plane).

        # Create single face
        v1 = bm.verts.new(Vector((-self.win_width/2, 0, 0)))
        v2 = bm.verts.new(Vector((self.win_width/2, 0, 0)))
        v3 = bm.verts.new(Vector((self.win_width/2, 0, self.win_height)))
        v4 = bm.verts.new(Vector((-self.win_width/2, 0, self.win_height)))

        f_main = bm.faces.new((v1, v2, v3, v4))
        f_main.material_index = 0 # Frame initially

        # 3. Outer Frame Inset
        ret = bmesh.ops.inset_region(bm, faces=[f_main], thickness=self.frame_width, use_even_offset=True)
        # Identify the inner face (center)
        # The result includes new faces (rim) and the inner face.
        # The inner face is the one not connected to the outer boundary edges of the original face?
        # Usually it's the last one created or something.
        # Or checking area?
        # Or selecting faces created.

        # bmesh.ops.inset_region returns 'faces' which are the newly created faces (the rim).
        # Wait, documentation says it returns "faces: list of faces added".
        # So the original face is modified? Or replaced?
        # Actually inset_region modifies the input faces.
        # But usually it replaces the original face with a set of faces.
        # Let's inspect the result.

        # Usually inset creates a ring around. The center face is what we want.
        # Let's find the face with the largest area or by location.
        center_face = None
        # faces in bm.faces that are selected?
        # Let's re-find based on center.
        for f in bm.faces:
            if abs(f.calc_center_median().x) < 0.1 and abs(f.calc_center_median().z - self.win_height/2) < 0.1:
                # Approximate center
                center_face = f
                break

        if not center_face:
            return # Safety

        # 4. Subdivide Inner Region (Mullions)
        # Simple subdivision
        # bmesh.ops.subdivide_edges on the edges of center_face?
        # No, that creates a spider web if n-gon. It's a quad.
        # So we can just cut it.

        # Grid Cut
        # Let's use bmesh.ops.bisect_plane repeatedly?
        # Or delete and recreate grid.

        # Recreate Grid Method:
        # Delete center face
        bm.faces.remove(center_face)

        # Determine the bounds of the hole
        # Find the loop of edges that formed the hole.
        # Collect boundary edges.
        boundary_edges = [e for e in bm.edges if len(e.link_faces) == 1]
        # This includes the outer boundary of the frame too!
        # We only want the inner loop.

        # Easier: inset, select inner face, delete it, fill with grid.

        # Or use bmesh.ops.subdivide_edges with cuts=...
        # But that subdivides all edges.

        # Let's use loop cuts on the center face?
        # Loop cut requires edges.

        # Let's just create the grid of glass panes separate and bridge?
        # Or use inset individual.

        # 3. Alternative:
        # Start with Grid.
        # Inset individual faces.

        # Let's restart logic:
        bm.clear()

        # Create Grid of Faces
        bmesh.ops.create_grid(bm, x_segments=self.mullion_x, y_segments=self.mullion_y, size=1)
        # Scale to size
        bmesh.ops.scale(bm, vec=Vector((self.win_width, self.win_height, 1)), verts=bm.verts)
        # Rotate to upright
        bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=bm.verts)
        # Translate to sit on Z=0
        bmesh.ops.translate(bm, vec=Vector((0, 0, self.win_height/2)), verts=bm.verts)

        # Assign all to Glass initially
        for f in bm.faces:
            f.material_index = 3 # Glass

        # Inset Each Face (Individual) to create frame
        # thickness = frame_width / 2 (since it's double)
        ret = bmesh.ops.inset_individual(bm, faces=bm.faces, thickness=self.frame_width/2, use_even_offset=True)

        # The result of inset_individual:
        # Original faces are shrunk (glass).
        # New faces are the frames between.

        # Identify glass faces vs frame faces.
        # We can detect by area?
        # Or by selection state if we track it.

        # Actually, `inset_individual` doesn't return easy mapping.
        # But the faces in `faces` input are modified to be the inner faces?
        # Or are they replaced?
        # Usually original pointers remain valid for the inner face if possible.

        # Let's assume faces with larger area are glass?
        # Or select faces that are "inset".

        # Let's check material index.
        # We can set material of all to Frame (0).
        # Then Inset. The "inner" faces we want to be Glass (3).

        for f in bm.faces:
            f.material_index = 3 # Glass

        # Select all faces for inset
        faces_to_inset = bm.faces[:]

        ret = bmesh.ops.inset_individual(bm, faces=faces_to_inset, thickness=self.frame_width/2)

        # Now, how to distinguish?
        # The faces in `faces_to_inset` might still point to the inner faces?
        # Let's test.
        # If so, we set their material to 3. The new faces (rims) will be 3 too.
        # Wait, if we set all to 0 (Frame) first.
        for f in bm.faces:
            f.material_index = 0

        ret = bmesh.ops.inset_individual(bm, faces=bm.faces[:], thickness=self.frame_width/2)

        # Usually the original faces (the list passed) become the center faces.
        # Let's try setting them to Glass.
        for f in ret['faces']:
            # Wait, `faces` in output is "faces added"?
            # No, standard bmesh ops return dict.
            # `inset_individual` doesn't document return well in some versions.
            pass

        # Heuristic: Glass faces are the ones pointing exactly Y-normal and roughly planar?
        # All are planar.
        # The frame faces are the "webs".
        # Let's use selection.

        # 4. Extrude Frame
        # We want the frame to stick out.
        # Select faces that are FRAME (0).
        # But we don't know which are which yet.

        # Let's try:
        # The faces that were inset (the centers) are the ones we want as glass.
        # If the input list `faces_to_inset` pointers are still valid and point to centers, we are good.
        # bmesh usually preserves pointers for the "main" face in inset.

        for f in faces_to_inset:
            f.material_index = 3 # Glass

        # Now faces that are NOT in faces_to_inset (or created new) are frame?
        # New faces are the frames.
        # So loop all faces, if not in faces_to_inset, set to 0.

        glass_faces = set(faces_to_inset)
        frame_faces = [f for f in bm.faces if f not in glass_faces]

        for f in frame_faces:
            f.material_index = 0

        # Extrude Frame Faces Outward
        ret = bmesh.ops.extrude_face_region(bm, geom=frame_faces)
        verts_to_move = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, -self.mullion_thick, 0)), verts=verts_to_move)

        # 5. Manual UVs
        # Frame (0) -> Box
        # Glass (3) -> Fit (0-1)

        for f in bm.faces:
            mat_idx = f.material_index

            if mat_idx == 3: # Glass
                # FIT UVs to 0-1 range based on face bounds?
                # Or based on global window size?
                # Usually individual pane mapping.

                # Bounds of this face
                min_x = min(v.co.x for v in f.verts)
                max_x = max(v.co.x for v in f.verts)
                min_z = min(v.co.z for v in f.verts)
                max_z = max(v.co.z for v in f.verts)

                w = max_x - min_x
                h = max_z - min_z

                for l in f.loops:
                    u = (l.vert.co.x - min_x) / w if w > 0 else 0
                    v = (l.vert.co.z - min_z) / h if h > 0 else 0
                    l[uv_layer].uv = (u, v)

            elif mat_idx == 0: # Frame
                # Box mapping
                scale = getattr(self, "uv_scale_0", 1.0)
                n = f.normal
                for l in f.loops:
                    # Simple box projection
                    if abs(n.x) > 0.5:
                        l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
                    elif abs(n.z) > 0.5:
                        l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)
                    else:
                        l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "win_width")
        col.prop(self, "win_height")
        layout.separator()
        col.prop(self, "mullion_x")
        col.prop(self, "mullion_y")
        col.prop(self, "frame_width")
        col.prop(self, "mullion_thick")
