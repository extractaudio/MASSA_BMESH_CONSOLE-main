import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "IND_03: Catwalk Grate",
    "id": "ind_03_catwalk",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndCatwalk(Massa_OT_Base):
    bl_idname = "massa.gen_ind_03_catwalk"
    bl_label = "IND Catwalk"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.0, min=0.1)
    width: FloatProperty(name="Width", default=1.0, min=0.1)
    frame_height: FloatProperty(name="Frame H", default=0.1, min=0.01)
    toe_kick_height: FloatProperty(name="Toe Kick H", default=0.1, min=0.0)
    frame_thick: FloatProperty(name="Frame Thick", default=0.05, min=0.01)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Grate", "uv": "SKIP", "phys": "METAL_GRATE"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        l, w = self.length, self.width
        fh = self.frame_height
        tk = self.toe_kick_height
        ft = self.frame_thick

        # 2. Base Plane (Grate Surface)
        # Create at Z=0 (Walking surface)
        v1 = bm.verts.new(Vector((-l/2, -w/2, 0)))
        v2 = bm.verts.new(Vector((l/2, -w/2, 0)))
        v3 = bm.verts.new(Vector((l/2, w/2, 0)))
        v4 = bm.verts.new(Vector((-l/2, w/2, 0)))

        f_main = bm.faces.new((v1, v2, v3, v4))
        f_main.material_index = 1 # Grate (Center)

        # 3. Inset for Frame
        # Actually, let's extrude perimeter OUT? No, usually inset inward if defining outer bounds.
        # Let's say length/width define outer bounds.
        # Inset main face to create frame border.

        ret = bmesh.ops.inset_region(bm, faces=[f_main], thickness=ft)
        # The center face (newly created or original modified) is now smaller.
        # The rim faces are the frame top.

        # Identify faces
        # Center face is likely the one with area close to (l-2ft)*(w-2ft)
        center_face = None
        max_area = 0
        for f in bm.faces:
            if f.calc_area() > max_area:
                max_area = f.calc_area()
                center_face = f

        if center_face:
            center_face.material_index = 1 # Grate

        # Frame Faces (Rim)
        frame_faces = [f for f in bm.faces if f != center_face]
        for f in frame_faces:
            f.material_index = 0 # Frame

        # 4. Extrude Toe Kick (Up)
        # Select outer edges of the frame?
        # Or extrude the frame faces up?
        # Toe kick is usually a thin plate on the edge.
        # Let's extrude the frame faces UP for toe kick? No, toe kick is thin.
        # Frame is usually a C-channel below.

        # Let's extrude Frame Faces DOWN for support.
        ret = bmesh.ops.extrude_face_region(bm, geom=frame_faces)
        verts_down = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, 0, -fh)), verts=verts_down)

        # Now Side Faces created by extrusion are Frame (0).
        # Bottom faces of frame are Frame (0).

        # 5. Toe Kick (Up)
        if tk > 0:
            # Select top outer edges of the frame.
            # Boundary edges at Z=0.
            outer_edges = [e for e in bm.edges if e.is_boundary and e.calc_face_angle(0) == 0] # Angle check might fail if single face
            # Just check Z=0 and Length/Width bounds.
            toe_edges = []
            for e in bm.edges:
                # Check verts z
                if abs(e.verts[0].co.z) < 0.001 and abs(e.verts[1].co.z) < 0.001:
                    # Check if on outer perimeter
                    # X approx +/- l/2 or Y approx +/- w/2
                    is_outer = False
                    for v in e.verts:
                        if abs(abs(v.co.x) - l/2) < 0.01 or abs(abs(v.co.y) - w/2) < 0.01:
                            is_outer = True
                    if is_outer:
                        toe_edges.append(e)

            # Extrude edges Up
            ret = bmesh.ops.extrude_edge_only(bm, edges=toe_edges)
            verts_up = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=Vector((0, 0, tk)), verts=verts_up)

            # Assign material to new faces (Toe Kick)
            for f in ret['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    f.material_index = 0

        # 6. Sockets
        # Midpoints of short ends (Left/Right)
        # We can add explicit faces or rely on geometry.
        # Let's add socket anchor faces at ends of the frame.
        pass

        # 7. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            mat_idx = f.material_index
            n = f.normal

            if mat_idx == 1: # Grate
                # Planar Z
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)
            else: # Frame
                # Box Mapping
                for l in f.loops:
                    if abs(n.x) > 0.5:
                        l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
                    elif abs(n.y) > 0.5:
                        l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
                    else:
                        l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "frame_height")
        col.prop(self, "toe_kick_height")
        col.prop(self, "frame_thick")
