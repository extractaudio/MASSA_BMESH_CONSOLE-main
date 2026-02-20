import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_17: Iris / Gear Blast Door",
    "id": "asm_17_iris_door",
    "icon": "MOD_BUILD",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_AsmIrisDoor(Massa_OT_Base):
    bl_idname = "massa.gen_asm_17_iris_door"
    bl_label = "ASM_17 Iris Door"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    radius: FloatProperty(name="Radius", default=2.0, min=1.0, unit="LENGTH")
    depth: FloatProperty(name="Frame Depth", default=0.5, min=0.1, unit="LENGTH")
    frame_width: FloatProperty(name="Frame Width", default=0.5, min=0.1, unit="LENGTH")

    # --- 2. IRIS ---
    segment_count: IntProperty(name="Segments", default=8, min=3, max=16)
    aperture_open: FloatProperty(name="Aperture", default=0.0, min=0.0, max=1.0, description="0=Closed, 1=Open")
    wedge_thick: FloatProperty(name="Wedge Thick", default=0.2, min=0.05, unit="LENGTH")

    # --- 3. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Wedges", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Details", "uv": "BOX", "phys": "METAL_DARK"},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "radius")
        col.prop(self, "depth")
        col.prop(self, "frame_width")

        col.separator()
        col.label(text="Iris Mechanism")
        col.prop(self, "segment_count")
        col.prop(self, "aperture_open")
        col.prop(self, "wedge_thick")

        col.separator()
        col.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        r = self.radius
        d = self.depth
        fw = self.frame_width
        segs = self.segment_count
        open_fac = self.aperture_open
        wt = self.wedge_thick

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale

        # Edge Slot layer
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 1. OCTAGONAL FRAME
        # Create a tube/ring.
        # Outer radius = r + fw. Inner radius = r.
        # Height = d.
        # Octagonal means 8 segments for the circle, but let's use segs if it's 8, or just 8.
        # Mandate says "Octagonal outer frame". So 8 sides.

        frame_segs = 8

        # Outer ring
        res_out = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=frame_segs, radius1=r+fw, radius2=r+fw, depth=d)
        verts_out = res_out['verts']
        # Inner ring (hole)
        res_in = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=frame_segs, radius1=r, radius2=r, depth=d+0.1) # Slightly longer for boolean
        verts_in = res_in['verts']

        # Boolean difference is expensive/unstable in bmesh usually.
        # Better to bridge edge loops.

        # Let's delete both and build manually using create_circle and bridge.
        bmesh.ops.delete(bm, geom=verts_out, context='VERTS')
        bmesh.ops.delete(bm, geom=verts_in, context='VERTS')

        # Create 4 circles: Outer Front, Outer Back, Inner Front, Inner Back.
        # Front at -Y? Usually Z is up. Wait, door usually faces Y or X?
        # Let's assume door is flat on XY plane (Z up is thickness) OR standing up on XZ plane.
        # Most architectural cartridges (walls, doors) stand up.
        # Let's assume it stands on XY plane like a silo? No, a door stands vertical.
        # Let's build it flat on XY first (Z is thickness) and then rotate it up?
        # Or just build with Z as thickness (depth).

        # Z is depth.
        z_front = -d/2
        z_back = d/2

        # Verts calculation
        # Octagon angles
        angles = [i * 2 * math.pi / frame_segs for i in range(frame_segs)]

        v_out_f = []
        v_out_b = []
        v_in_f = []
        v_in_b = []

        for ang in angles:
            co = (math.cos(ang), math.sin(ang))
            # Outer
            v_out_f.append(bm.verts.new((co[0]*(r+fw), co[1]*(r+fw), z_front)))
            v_out_b.append(bm.verts.new((co[0]*(r+fw), co[1]*(r+fw), z_back)))
            # Inner
            v_in_f.append(bm.verts.new((co[0]*r, co[1]*r, z_front)))
            v_in_b.append(bm.verts.new((co[0]*r, co[1]*r, z_back)))

        bm.verts.ensure_lookup_table()

        # Faces
        for i in range(frame_segs):
            i_next = (i + 1) % frame_segs

            # Outer Rim
            f = bm.faces.new((v_out_f[i], v_out_f[i_next], v_out_b[i_next], v_out_b[i]))
            f.material_index = 0

            # Inner Rim
            f = bm.faces.new((v_in_b[i], v_in_b[i_next], v_in_f[i_next], v_in_f[i]))
            f.material_index = 0

            # Front Face
            f = bm.faces.new((v_out_f[i], v_in_f[i], v_in_f[i_next], v_out_f[i_next]))
            f.material_index = 0

            # Back Face
            f = bm.faces.new((v_in_b[i], v_out_b[i], v_out_b[i_next], v_in_b[i_next]))
            f.material_index = 0

        # Rotate frame to stand up?
        # Standard wall/door cartridges usually align with X axis and stand in Z.
        # Or align with Y.
        # Let's keep it flat on Z for now (floor door/silo hatch) or rotate at end.
        # "Blast Door" usually implies vertical.
        # Let's rotate 90 deg around X at the end.

        # 2. WEDGES (Iris)
        # Interlocking triangles.
        # To interlock perfectly, they need to be slightly larger than segment angle or offset.
        # Simple iris:
        # Each wedge is a triangle pivot at (R, phi).
        # Or sliding wedges. Mandate: "slides the wedge vertices outward along their local axes".

        # Let's make wedges that meet at center (0,0) when closed.
        # Wedge shape:
        # Base at radius r. Tip at center.
        # But for "Gear" look, maybe trapezoidal teeth.

        # Let's simulate the sliding.
        # Open distance = open_fac * r.

        wedge_angle = 2 * math.pi / segs
        # Make wedge slightly wider to overlap?
        # overlap_factor = 1.2

        for i in range(segs):
            angle_center = i * wedge_angle

            # Local coordinate system for the wedge
            # Direction vector (radial)
            dir_vec = Vector((math.cos(angle_center), math.sin(angle_center), 0))

            # Sliding displacement
            disp = dir_vec * (open_fac * r * 0.9) # Max open almost clears the hole

            # Build wedge at origin, then rotate and translate.
            # Wedge shape in local space (X is radial out, Y is tangential)
            # Tip at (0,0) -> moves to (r, 0)
            # Base width at r.
            # Width = 2 * r * tan(wedge_angle/2).

            # Let's create a simple prism wedge.
            # Vertices:
            # Tip: (0, 0)
            # Base Right: (r, width/2)
            # Base Left: (r, -width/2)

            w_h = r
            w_w_half = r * math.tan(wedge_angle/2) * 1.05 # Overlap slightly

            # Z thickness centered at 0
            z_top = wt/2
            z_bot = -wt/2

            # Define vertices in local space
            local_verts = [
                Vector((0, 0, z_top)), # Tip Top
                Vector((0, 0, z_bot)), # Tip Bot
                Vector((w_h, w_w_half, z_top)), # Base R Top
                Vector((w_h, w_w_half, z_bot)), # Base R Bot
                Vector((w_h, -w_w_half, z_top)), # Base L Top
                Vector((w_h, -w_w_half, z_bot)), # Base L Bot
            ]

            # Create verts in bmesh
            bm_verts = []

            # Rotation matrix for this segment
            rot_mat = Matrix.Rotation(angle_center, 3, 'Z')

            for v_local in local_verts:
                # Apply rotation
                v_world = rot_mat @ v_local
                # Apply sliding displacement
                v_world += disp
                bm_verts.append(bm.verts.new(v_world))

            bm.verts.ensure_lookup_table()

            # Faces
            # Top (0, 2, 4)
            f1 = bm.faces.new((bm_verts[0], bm_verts[4], bm_verts[2]))
            f1.material_index = 1
            # Bottom (1, 3, 5)
            f2 = bm.faces.new((bm_verts[1], bm_verts[3], bm_verts[5]))
            f2.material_index = 1
            # Base (2, 4, 5, 3)
            f3 = bm.faces.new((bm_verts[2], bm_verts[4], bm_verts[5], bm_verts[3]))
            f3.material_index = 1
            # Side R (0, 2, 3, 1)
            f4 = bm.faces.new((bm_verts[0], bm_verts[2], bm_verts[3], bm_verts[1]))
            f4.material_index = 1
            # Side L (0, 1, 5, 4)
            f5 = bm.faces.new((bm_verts[0], bm_verts[1], bm_verts[5], bm_verts[4]))
            f5.material_index = 1

            # Edges for MANDATE: Edge Slot 2 (Contour) on wedge teeth
            # The "Teeth" are the sides (Side R, Side L) that interlock.
            # Edges: (0,2), (2,3), (3,1), (1,0) -> Side R
            # Edges: (0,1), (1,5), (5,4), (4,0) -> Side L

            for f in [f4, f5]:
                for e in f.edges:
                    e[edge_slots] = 2 # Contour

            # Also apply UVs
            for f in [f1, f2, f3, f4, f5]:
                self.apply_box_map(f, uv_layer, scale)

        # 3. ROTATE UPRIGHT
        # Rotate 90 degrees around X to make it a vertical door/hatch.
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=bm.verts)

        # Position so bottom of frame is at Z=0?
        # Current center is at (0,0,0).
        # Radius is r+fw.
        # So bottom is at -(r+fw).
        # Shift up by r+fw.
        bmesh.ops.translate(bm, vec=(0, 0, r+fw), verts=bm.verts)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def apply_box_map(self, face, uv_layer, scale):
        n = face.normal
        nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
        for l in face.loops:
            co = l.vert.co
            if nz > nx and nz > ny:
                u, v = co.x, co.y
            elif nx > ny and nx > nz:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            l[uv_layer].uv = (u * scale, v * scale)
