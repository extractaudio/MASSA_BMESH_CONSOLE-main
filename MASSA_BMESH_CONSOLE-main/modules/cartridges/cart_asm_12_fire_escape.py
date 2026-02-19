import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_12: Fire Escape",
    "id": "asm_12_fire_escape",
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


class MASSA_OT_AsmFireEscape(Massa_OT_Base):
    bl_idname = "massa.gen_asm_12_fire_escape"
    bl_label = "ASM_12 Fire Escape"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    length: FloatProperty(name="Length", default=3.0, min=1.0, unit="LENGTH")
    width: FloatProperty(name="Width", default=1.2, min=0.5, unit="LENGTH")
    height: FloatProperty(name="Floor Height", default=3.0, min=1.0, unit="LENGTH")

    # --- 2. STAIRS ---
    stair_width: FloatProperty(name="Stair Width", default=0.8, min=0.5, unit="LENGTH")
    step_count: IntProperty(name="Step Count", default=12, min=3)

    # --- 3. RAILING ---
    rail_height: FloatProperty(name="Rail Height", default=1.0, min=0.1, unit="LENGTH")

    # --- 4. DETAILS ---
    grating_thick: FloatProperty(name="Platform Thick", default=0.1, min=0.01)

    # --- 5. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Grating", "uv": "BOX", "phys": "METAL_MESH"},
            1: {"name": "Structure", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Railing", "uv": "BOX", "phys": "METAL_STEEL"},
            9: {"name": "Sockets", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")

        col.separator()
        col.label(text="Stairs")
        col.prop(self, "stair_width")
        col.prop(self, "step_count")

        col.separator()
        col.label(text="Details")
        col.prop(self, "rail_height")
        col.prop(self, "grating_thick")

    def build_shape(self, bm: bmesh.types.BMesh):
        l = self.length
        w = self.width
        h = self.height
        sw = min(self.stair_width, w - 0.1)
        sc = self.step_count
        rt = self.rail_height
        gt = self.grating_thick

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale

        # Determine Hole Dimensions
        # Stairs go from Z=0 down to Z=-h
        # Run length depends on slope. Let's fix the hole length to accommodate reasonable slope.
        # Or parameterize hole length? Let's say hole length = length / 2 or calculated.
        # Let's make the hole 40% of length at the end.
        hole_len = l * 0.45

        # 1. PLATFORM (L-Shape or Box with cutout)
        # Vertices for the platform footprint
        # (0,0) -> (l,0) -> (l, w-sw) -> (l-hole_len, w-sw) -> (l-hole_len, w) -> (0, w)
        # Assuming Wall is at Y=0. Stairs are on Outer Edge (Y=w)?
        # "Generate a cutout hole in the corner".

        # Let's say Wall is at Y=0.
        # Platform Y: 0 to w.
        # Hole at far right corner (X=l, Y=w).

        p_verts = [
            (0, 0, 0),
            (l, 0, 0),
            (l, w - sw, 0), # Inner edge of hole
            (l - hole_len, w - sw, 0),
            (l - hole_len, w, 0),
            (0, w, 0)
        ]

        # Create Face
        bm_verts = [bm.verts.new(v) for v in p_verts]
        bm.faces.new(bm_verts)

        # Extrude Thickness (Down)
        # Select all faces (only platform exists)
        for f in bm.faces: f.select = True
        res_ex = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        verts_extruded = [v for v in res_ex['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0,0,-gt), verts=verts_extruded)

        # Assign Material
        for f in bm.faces:
            f.material_index = 0
            self.apply_box_map(f, uv_layer, scale)

        # 2. RAILING
        # Perimeter edges on top
        # Need to find top faces and their outer edges.
        # Top faces are at Z=0.
        top_faces = [f for f in bm.faces if f.calc_center_median().z > -gt/2]

        # Collect perimeter edges
        # Edges that belong to only 1 top face (boundary of top surface)
        # Note: We only have 1 top face (an N-gon) if we did it simply.
        # Yes, we created one face.

        perimeter_edges = []
        for f in top_faces:
            for e in f.edges:
                # Check if it's a boundary of the platform
                # (e.g. not connected to another top face - easy since there is only one)
                perimeter_edges.append(e)

        # Filter out Wall Side (Y=0)
        rail_edges = []
        for e in perimeter_edges:
            # Check vertices. If both have Y approx 0, skip.
            v1, v2 = e.verts
            if v1.co.y < 0.01 and v2.co.y < 0.01:
                continue
            rail_edges.append(e)

        # Extrude Railing
        if rail_edges:
            res_rail = bmesh.ops.extrude_edge_only(bm, edges=rail_edges)
            verts_rail = [v for v in res_rail['geom'] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=(0,0,rt), verts=verts_rail)

            # Assign Material
            rail_faces = [f for f in res_rail['geom'] if isinstance(f, bmesh.types.BMFace)]
            for f in rail_faces:
                f.material_index = 2 # Railing
                self.apply_box_map(f, uv_layer, scale)
                # Double sided?
                # Usually fire escape railings are thin/alpha or bars.
                # Assuming "BOX" logic or alpha.
                # Mandate says "Extrude side faces UP".

        # 3. STAIRS
        # From Top: (l - hole_len, w - sw/2, 0)
        # To Bottom: (l, w - sw/2, -h)
        # This slopes down towards +X.

        start_p = Vector((l - hole_len, w - sw/2, 0))
        end_p = Vector((l, w - sw/2, -h))

        run_vec = end_p - start_p
        step_vec = run_vec / sc

        # Width of step is sw.
        # Create steps.
        for i in range(sc):
            p = start_p + step_vec * i

            # Create Step Box
            # Center p. Dimensions: X=step_len, Y=sw, Z=thick
            # Step Length along X = hole_len / sc
            step_len = hole_len / sc

            res_s = bmesh.ops.create_cube(bm, size=1.0)
            verts_s = res_s['verts']
            bmesh.ops.scale(bm, vec=(step_len, sw, 0.05), verts=verts_s)
            bmesh.ops.translate(bm, vec=(p.x + step_len/2, p.y, p.z - step_vec.z/2), verts=verts_s) # Adjust for center

            for f in list({f for v in verts_s for f in v.link_faces}):
                f.material_index = 0 # Grating
                self.apply_box_map(f, uv_layer, scale)

        # 4. SOCKETS
        # A. Wall Socket (Input/Anchor)
        # At (l/2, 0, 0) facing -Y (into wall)
        # Create a small face
        res_sock1 = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.2)
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 4, 'X'), verts=res_sock1['verts']) # Face -Y
        bmesh.ops.translate(bm, vec=(l/2, 0, 0), verts=res_sock1['verts'])
        for f in res_sock1['faces']:
            f.material_index = 9
            f.normal_flip() # Face -Y

        # B. Bottom Socket (Output/Next Chain)
        # At (l, 0, -h) ? No, stairs end at (l, w-sw/2, -h).
        # But we want to chain the next module.
        # If next module attaches via ITS Wall Socket (at l/2, 0, 0 relative to itself).
        # And we want it to align such that its start matches our end?
        # If we place the next module at (l - hole_len + l_next/2 ??).
        # "Seamlessly chain".
        # If Module 2 starts where Module 1 ends.
        # M1 End X = l.
        # M2 Start X = 0.
        # So shift X = l.
        # Shift Z = -h.
        # Shift Y = 0 (Assuming straight wall).
        # So Bottom Socket should be at (l + l/2 ?? No, relative to what?)

        # If I place a socket at (l - (l/2), 0, -h).
        # Wait, if Wall Socket is at local X=l/2.
        # I want the Next Wall Socket to be at World X = l + l/2.
        # So I need a socket at X = l + l/2 - l/2 = l ?
        # Wait.
        # Module 1 origin: (0,0,0). Wall Socket: (l/2, 0, 0).
        # Module 2 origin: (X2, Y2, Z2). Wall Socket: (X2 + l/2, Y2, Z2).
        # We want Module 2 to start at X=l (relative to M1).
        # So X2 = l.
        # Z2 = -h.
        # Y2 = 0.
        # So M2 Wall Socket is at (l + l/2, 0, -h).
        # So we need a socket at (l + l/2, 0, -h) on M1?
        # No, the socket on M1 is the "Target". M2 snaps "Source" (Wall Socket) to "Target".
        # So we place a socket at (l + l/2, 0, -h).
        # Wait, usually Snap aligns Source to Target.
        # Source: M2 Wall Socket (l/2, 0, 0).
        # Target: M1 Bottom Socket.
        # Result: M2 placed such that Source matches Target.
        # So Target (M1 Bottom Socket) should be where we want M2 Wall Socket to be.
        # We want M2 Origin to be at (l, 0, -h).
        # So M2 Wall Socket will be at (l + l/2, 0, -h).
        # So we place M1 Bottom Socket at (l + l/2, 0, -h).

        # Let's verify overlap.
        # M1 Platform: 0 to l.
        # M2 Platform: l to 2l.
        # Perfect chain.

        res_sock2 = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.2)
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 4, 'X'), verts=res_sock2['verts'])
        bmesh.ops.translate(bm, vec=(l + l/2, 0, -h), verts=res_sock2['verts'])
        for f in res_sock2['faces']:
            f.material_index = 9
            f.normal_flip()

        # 5. Fix Normals
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
