import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_06: Transit Shelter",
    "id": "asm_06_transit",
    "icon": "MOD_ARCH",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmTransit(Massa_OT_Base):
    bl_idname = "massa.gen_asm_06_transit"
    bl_label = "ASM_06: Transit Shelter"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=4.0, min=2.0)
    depth: FloatProperty(name="Depth (Y)", default=2.5, min=1.5)
    height: FloatProperty(name="Height (Z)", default=2.8, min=2.0)

    pillar_thickness: FloatProperty(name="Pillar Thickness", default=0.15, min=0.05)
    roof_curve: FloatProperty(name="Roof Curve", default=0.5, min=0.1, max=1.0)
    bench_slats: IntProperty(name="Bench Slats", default=8, min=3)

    ad_board_width: FloatProperty(name="Ad Width", default=1.2, min=0.5)

    def get_slot_meta(self):
        return {
            0: {"name": "Concrete Base", "uv": "SKIP", "phys": "CONCRETE"},
            1: {"name": "Structure (Metal)", "uv": "SKIP", "phys": "METAL_PAINTED"},
            2: {"name": "Bench Wood", "uv": "SKIP", "phys": "WOOD_VARNISHED"},
            3: {"name": "Glass Canopy", "uv": "SKIP", "phys": "GLASS_PANE"},
            4: {"name": "Ad Board (Emission)", "uv": "SKIP", "phys": "GLASS_SCREEN"}, # Mandate: UV FIT
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")

        layout.separator()
        layout.label(text="DETAILS", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "pillar_thickness")
        col.prop(self, "roof_curve")
        col.prop(self, "bench_slats")
        col.prop(self, "ad_board_width")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, d, h = self.width, self.depth, self.height
        pt = self.pillar_thickness

        # 1. Base Concrete Pad
        base_h = 0.2
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w + 0.5, d + 0.5, base_h), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, base_h/2), verts=bm.verts)

        # Assign Slot 0 (Concrete)
        for f in bm.faces:
            f.material_index = 0

        # 2. Pillars (3 Pillars at back)
        pillar_x_positions = [-w/2 + pt, 0, w/2 - pt]
        pillar_y = d/2 - pt*2

        for px in pillar_x_positions:
            ret = bmesh.ops.create_cube(bm, size=1.0)
            verts = ret['verts']
            # Scale to pillar size
            bmesh.ops.scale(bm, vec=(pt, pt, h), verts=verts)
            # Translate to position
            bmesh.ops.translate(bm, vec=(px, pillar_y, h/2), verts=verts)

            # Assign Slot 1 (Structure)
            for v in verts:
                for f in v.link_faces:
                    f.material_index = 1

        # 3. Cantilevered Curved Glass Roof
        # Create a profile curve (arc)
        arc_segments = 8
        arc_verts = []

        # Arc from back (pillar_y) to front (-d/2)
        # We want the curve to go up and forward.
        start_y = pillar_y
        end_y = -d/2 - 0.5
        y_range = start_y - end_y

        # Roof starts at height h, curves up slightly then down? Or simple cantilever.
        # Let's do a simple curve: Z = h + curve * sin(t)

        # Actually, let's make it a simple curved sheet.
        # Create a grid and bend it? Or extrude an edge?

        # Let's create a grid for the roof
        ret = bmesh.ops.create_grid(
            bm,
            x_segments=1,
            y_segments=arc_segments,
            size=1.0 # arbitrary, will scale
        )
        roof_faces = ret['faces']
        roof_verts = ret['verts']

        # Map the grid to the arc shape
        # Grid is initially on XY plane centered at 0
        # X range: -0.5 to 0.5 -> map to -w/2 to w/2
        # Y range: -0.5 to 0.5 -> map to arc from back to front

        for v in roof_verts:
            # Normalized coordinates
            nx = (v.co.x + 0.5) # 0 to 1
            ny = (v.co.y + 0.5) # 0 to 1 (back to front)

            # Map X
            world_x = (nx - 0.5) * (w + 0.5) # Overhang slightly

            # Map Y (Linear from back to front)
            world_y = start_y - ny * (y_range)

            # Map Z (Curve)
            # Parabolic or circular arc
            # Curve factor controls height of arc
            arc_h = self.roof_curve
            # Let's make it highest in the middle of the cantilever
            curve_z = math.sin(ny * math.pi) * arc_h
            # Or maybe just slope up?
            # "Cantilevered curved glass roof" usually implies curvature along the cantilever direction.
            # Let's curve it down towards the front.
            # Start at h, curve up then down.

            world_z = h + math.sin(ny * math.pi/2) * arc_h * 0.5 # Slight rise
            # Wait, bus stops usually slope down to front or back.
            # Let's simple curve:
            world_z = h + (1 - math.cos(ny * 1.0)) * arc_h

            v.co = Vector((world_x, world_y, world_z))

        # Assign Slot 3 (Glass)
        for f in roof_faces:
            f.material_index = 3
            f.smooth = True

        # 4. Slatted Bench
        # Linear array of boxes
        bench_h = 0.5
        bench_d = 0.5
        bench_y = 0 # Center Y
        bench_w = w * 0.6

        slat_w = bench_w / self.bench_slats * 0.8
        gap = (bench_w - (slat_w * self.bench_slats)) / (self.bench_slats - 1) if self.bench_slats > 1 else 0

        start_x = -bench_w/2 + slat_w/2

        for i in range(self.bench_slats):
            bx = start_x + i * (slat_w + gap)

            ret = bmesh.ops.create_cube(bm, size=1.0)
            b_verts = ret['verts']
            bmesh.ops.scale(bm, vec=(slat_w, bench_d, 0.05), verts=b_verts) # Thin slats
            bmesh.ops.translate(bm, vec=(bx, bench_y, bench_h), verts=b_verts)

            for v in b_verts:
                for f in v.link_faces:
                    f.material_index = 2 # Wood

        # Legs for bench
        leg_x_pos = [-bench_w/2 + 0.2, bench_w/2 - 0.2]
        for lx in leg_x_pos:
            ret = bmesh.ops.create_cube(bm, size=1.0)
            l_verts = ret['verts']
            bmesh.ops.scale(bm, vec=(0.1, bench_d*0.8, bench_h), verts=l_verts)
            bmesh.ops.translate(bm, vec=(lx, bench_y, bench_h/2), verts=l_verts)
            for v in l_verts:
                for f in v.link_faces:
                    f.material_index = 1 # Metal

        # 5. Illuminated Ad Board
        # Attached to one side (e.g., right side)
        ad_x = w/2 - 0.1
        ad_y = 0
        ad_w = self.ad_board_width
        ad_h = 2.0
        ad_thickness = 0.2

        ret = bmesh.ops.create_cube(bm, size=1.0)
        ad_verts = ret['verts']
        bmesh.ops.scale(bm, vec=(ad_thickness, ad_w, ad_h), verts=ad_verts)
        bmesh.ops.translate(bm, vec=(ad_x, ad_y, h/2), verts=ad_verts)

        # Assign Slot 1 (Frame)
        # Assign Slot 1 (Frame)
        ad_faces = ret['faces']
        for f in ad_faces:
            f.material_index = 1

        # Inset faces for Ad (Front and Back)
        # Identify faces pointing +/- X (Wait, board is at right side, facing +/- X is the thin side. Facing +/- Y is the main face)
        # Ah, the board should probably be perpendicular to the street, i.e., in YZ plane.
        # So facing +/- X.
        # Wait, if it's on the side wall, it faces the people inside and outside.
        # Yes, +/- X normals are the large faces if scaled (thickness, width, height).
        # Wait, I scaled X by thickness (0.2) and Y by width (1.2). So the large faces are normals +/- X.
        # No, X is thickness. So large faces have normals +/- X?
        # A cube scaled (0.2, 1.2, 2.0).
        # Faces with normal X have size 1.2 x 2.0. Correct.

        bm.faces.ensure_lookup_table()
        ad_display_faces = []
        for f in ad_faces:
            if f.is_valid and abs(f.normal.x) > 0.9:
                ad_display_faces.append(f)

        if ad_display_faces:
            res = bmesh.ops.inset_individual(bm, faces=ad_display_faces, thickness=0.05, depth=-0.02)
            for f in res['faces']:
                f.material_index = 4 # Ad Board (Emission)

                # UV Logic for Ad Board (FIT)
                # We need to ensure the UVs map 0-1 perfectly on this face.
                # Since we do UVs manually at the end, we can tag them or do it now.
                # Let's do it at the end but we need to identify them.
                # Actually, I'll handle UVs in the final pass.

        # 6. UV Mapping
        uv_layer = bm.loops.layers.uv.verify()

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            if f.material_index == 4: # Ad Board
                # Fit UVs
                # Assuming simple quad
                # Find bottom-left, etc.
                # Or simply project based on bounding box of the face

                # Get face verts
                vs = [v.co for v in f.verts]
                # Project to local YZ plane (since normal is X)
                min_y = min(v.y for v in vs)
                max_y = max(v.y for v in vs)
                min_z = min(v.z for v in vs)
                max_z = max(v.z for v in vs)

                dy = max_y - min_y
                dz = max_z - min_z

                for l in f.loops:
                    v = l.vert.co
                    u = (v.y - min_y) / dy if dy > 0 else 0
                    v_coord = (v.z - min_z) / dz if dz > 0 else 0

                    # Flip U if normal is negative X?
                    if f.normal.x < 0:
                        u = 1.0 - u

                    l[uv_layer].uv = (u, v_coord)

            elif f.material_index == 3: # Glass Roof
                # Map based on XY position (top down)
                for l in f.loops:
                    u = (l.vert.co.x + w/2) / w
                    v = (l.vert.co.y + d/2) / d
                    l[uv_layer].uv = (u, v)

            elif f.material_index == 0: # Concrete
                 for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * 0.5, l.vert.co.y * 0.5)

            else: # Metal, Wood
                 for l in f.loops:
                     # Box mapping logic (simplified)
                     nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                     if nz > 0.5:
                         u, v = l.vert.co.x, l.vert.co.y
                     elif ny > 0.5:
                         u, v = l.vert.co.x, l.vert.co.z
                     else:
                         u, v = l.vert.co.y, l.vert.co.z
                     l[uv_layer].uv = (u, v)
