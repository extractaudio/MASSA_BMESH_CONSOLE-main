import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_07: Mezzanine Platform",
    "id": "arc_07_mezzanine",
    "icon": "MOD_ARRAY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcMezzanine(Massa_OT_Base):
    bl_idname = "massa.gen_arc_07_mezzanine"
    bl_label = "ARC Mezzanine"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Structure Style",
        items=[
            ("STEEL_BEAM", "Steel I-Beam", "Standard I-Beam construction"),
            ("TRUSS", "Open Web Truss", "Lightweight truss joists"),
            ("CONCRETE", "Concrete", "Heavy concrete slab and columns"),
        ],
        default="STEEL_BEAM"
    )

    # Dimensions
    length: FloatProperty(name="Length", default=6.0, min=1.0)
    width: FloatProperty(name="Width", default=4.0, min=1.0)
    height: FloatProperty(name="Clear Height", default=3.0, min=2.1) # Headroom

    # Structure
    deck_thick: FloatProperty(name="Deck Thickness", default=0.1, min=0.05)
    beam_depth: FloatProperty(name="Beam Depth", default=0.3, min=0.1)
    col_spacing: FloatProperty(name="Column Spacing", default=4.0, min=2.0)
    col_width: FloatProperty(name="Column Width", default=0.2, min=0.1)

    overhang: FloatProperty(name="Cantilever", default=0.0, min=0.0)

    # Features
    railing_h: FloatProperty(name="Railing Height", default=1.1, min=0.0) # 1.1m ~ 42" OSHA
    stair_cutout: BoolProperty(name="Stair Opening", default=False)
    cutout_x: FloatProperty(name="Cutout X", default=0.0)
    cutout_w: FloatProperty(name="Cutout Width", default=1.0)
    cutout_l: FloatProperty(name="Cutout Length", default=3.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Deck Surface", "uv": "BOX", "phys": "METAL_CHECKERPLATE"},
            1: {"name": "Structure", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Railings", "uv": "BOX", "phys": "METAL_PAINTED"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CUBE')
        col = box.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "deck_thick")

        box = layout.box()
        box.label(text="Structure", icon='MOD_ARRAY')
        col = box.column(align=True)
        col.prop(self, "col_spacing")
        col.prop(self, "col_width")
        col.prop(self, "beam_depth")
        col.prop(self, "overhang")

        box = layout.box()
        box.label(text="Features", icon='MOD_BOOLEAN')
        col = box.column(align=True)
        col.prop(self, "railing_h")
        col.prop(self, "stair_cutout")
        if self.stair_cutout:
            col.prop(self, "cutout_x")
            col.prop(self, "cutout_w")
            col.prop(self, "cutout_l")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        l, w, h = self.length, self.width, self.height
        dt = self.deck_thick
        bd = self.beam_depth
        cw = self.col_width
        cs = self.col_spacing
        oh = self.overhang

        # Calculate Grid
        # Structure Area = (w - 2*oh) x (l - 2*oh) ?
        # Or Overhang adds to L/W?
        # Usually params define total deck size, overhang defines how far columns are inset.

        struct_w = max(w - 2*oh, cw)
        struct_l = max(l - 2*oh, cw)

        # Determine number of bays
        nx = max(1, int(struct_w / cs))
        ny = max(1, int(struct_l / cs))

        step_x = struct_w / nx
        step_y = struct_l / ny

        start_x = -struct_w/2
        start_y = -struct_l/2

        # Deck Z level = h + bd (Clear height is below beam usually)
        # So Deck Top = h + bd + dt
        # Or usually Height param is Deck Height?
        # User prompt says "Clear Height (Headroom)".
        # So Columns are H tall. Beams sit ON columns (or framed into).
        # Let's say Clear Height = H.
        # Bottom of Beam = H.
        # Top of Beam = H + BD.
        # Deck sits on top = H + BD + DT.

        z_beam_bot = h
        z_beam_top = h + bd
        z_deck_top = h + bd + dt

        # 1. Structure (Columns)
        for ix in range(nx + 1):
            for iy in range(ny + 1):
                px = start_x + ix*step_x
                py = start_y + iy*step_y

                # Check cutout interference?
                # Usually columns exist even if cutout is nearby, unless inside cutout?
                # Simple check: point inside cutout box?

                # Create Column
                if self.style == "CONCRETE":
                    builder.create_box(cw, cw, h, center=Vector((px, py, h/2)))
                else:
                    # Steel I-Beam Column
                    # Simplified as Box for now, or H profile?
                    # Box is robust.
                    builder.create_box(cw, cw, h, center=Vector((px, py, h/2)))

                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Base Plate?
                if self.style == "STEEL_BEAM":
                    builder.create_box(cw*1.5, cw*1.5, 0.02, center=Vector((px, py, 0.01)))
                    builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 2. Structure (Beams)
        # Main Beams (X Axis?)
        # Secondary Beams (Y Axis?)

        # Frame perimeter of structure
        # And internal grid lines

        # X Beams (along Width)
        # At each Y grid line
        for iy in range(ny + 1):
            py = start_y + iy*step_y

            # Beam from start_x to end_x
            # Center = 0, Length = struct_w
            # Height = bd
            # Z center = h + bd/2

            if self.style == "TRUSS":
                # Truss Logic (Simplified block with cutout texture or geometry?)
                # Geometry is better.
                # Top Chord, Bottom Chord, Web.

                # Create Block for now to be safe on topology
                builder.create_box(struct_w + cw, cw*0.8, bd, center=Vector((0, py, h + bd/2)))
            else:
                # Steel / Concrete
                builder.create_box(struct_w + cw, cw*0.8, bd, center=Vector((0, py, h + bd/2)))

            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Y Beams (Joists / Girders)
        # Between X beams? Or overlapping?
        # Usually Frame: Girders (Y) carry Beams (X).
        # Let's just frame the grid.

        for ix in range(nx + 1):
            px = start_x + ix*step_x

            # Beam along Y
            # Avoid intersecting X beams?
            # Or just boolean/overlap? Overlap is fine for weld.
            builder.create_box(cw*0.8, struct_l + cw, bd, center=Vector((px, 0, h + bd/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Deck (with optional Cutout)
        z_deck_base = h + bd

        # Create base plane
        builder.create_grid(x_segments=1, y_segments=1, size=1.0, center=Vector((0,0,z_deck_base)))
        # Scale to size (create_grid uses size=1)
        builder.scale(w, l, 1.0) # Plane is XY

        # Ensure normals up
        builder.select_faces_by_normal(Vector((0,0,1)))

        # Cutout Logic
        if self.stair_cutout:
            cx = self.cutout_x
            cw = self.cutout_w
            cl = self.cutout_l

            # Bisect X bounds
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(cx - cw/2, 0, 0), plane_no=(1,0,0))
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(cx + cw/2, 0, 0), plane_no=(1,0,0))

            # Bisect Y bounds
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(0, -cl/2, 0), plane_no=(0,1,0)) # Assume centered on Y=0 or parameter?
            # Let's parameterize Y center? User only gave length. Assume centered at Y=0 or start?
            # Usually stair is at edge. Let's assume centered on X, but Y relative to edge?
            # For simplicity, let's assume cutout is centered at (cx, 0).
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(0, cl/2, 0), plane_no=(0,1,0))

            # Select faces inside bounds
            # X between cx +/- cw/2
            # Y between +/- cl/2
            to_delete = []
            bm.faces.ensure_lookup_table()
            for f in bm.faces:
                # Check center
                cen = f.calc_center_median()
                if abs(cen.z - z_deck_base) < 0.01: # Only deck faces
                    if (cx - cw/2) <= cen.x <= (cx + cw/2) and (-cl/2) <= cen.y <= (cl/2):
                        to_delete.append(f)

            bmesh.ops.delete(bm, geom=to_delete, context='FACES')

        # Extrude Deck Thickness
        # Select all deck faces (approx Z = z_deck_base)
        bm.faces.ensure_lookup_table()
        deck_faces = [f for f in bm.faces if abs(f.calc_center_median().z - z_deck_base) < 0.01]

        if deck_faces:
            builder.active_faces = deck_faces
            builder.extrude(dt)
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 4. Railings
        if self.railing_h > 0:
            # Perimeter loop
            # Create fence posts and rails

            # Path: (-w/2, -l/2) -> (w/2, -l/2) -> (w/2, l/2) -> (-w/2, l/2) -> close

            rh = self.railing_h
            post_dist = 1.5 # Max spacing

            # Helper to build rail segment
            def build_rail(p1, p2):
                dist = (p2 - p1).length
                if dist < 0.1: return

                cnt = max(2, int(dist / post_dist) + 1)

                # Posts
                for i in range(cnt):
                    t = i / (cnt - 1)
                    pos = p1.lerp(p2, t)
                    pos.z += rh/2

                    builder.create_box(0.05, 0.05, rh, center=pos)
                    builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Top Rail
                mid = (p1 + p2) / 2
                mid.z += rh

                # Align box to vector
                # Or just create cylinder/box and rotate
                vec = p2 - p1
                # Angle?
                angle = math.atan2(vec.y, vec.x)

                builder.create_box(dist, 0.05, 0.05, center=mid)
                builder.rotate(math.degrees(angle), axis='Z')
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Mid Rail
                mid.z -= rh/2
                builder.create_box(dist, 0.03, 0.03, center=mid)
                builder.rotate(math.degrees(angle), axis='Z')
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            z_rail = h + bd + dt

            # Corners
            c1 = Vector((-w/2, -l/2, z_rail))
            c2 = Vector((w/2, -l/2, z_rail))
            c3 = Vector((w/2, l/2, z_rail))
            c4 = Vector((-w/2, l/2, z_rail))

            build_rail(c1, c2)
            build_rail(c2, c3)
            build_rail(c3, c4)
            build_rail(c4, c1)


        # 6. Sockets
        # Floor Socket (0,0,0)
        builder.active_faces = [] # Clear
        # Create a temp face at 0,0,0?
        # Or rely on column bottoms?

        # Select faces at Z=0?
        # Column bases are at Z=0.
        # But maybe we want a central anchor.
        # Tagging column bottoms is good.
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1)
        # Filter Z ~ 0
        bases = [f for f in builder.active_faces if abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = bases
        builder.tag_socket(9)

        builder.clean()

    def execute(self, context):
        return super().execute(context)
