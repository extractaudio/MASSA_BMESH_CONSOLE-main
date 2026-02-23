import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_05: Arch Column",
    "id": "arc_05_column",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcColumn(Massa_OT_Base):
    bl_idname = "massa.gen_arc_05_column"
    bl_label = "ARC Column"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    total_height: FloatProperty(name="Height", default=4.0, min=0.1)
    radius_base: FloatProperty(name="Base Radius", default=0.4, min=0.1)
    radius_top: FloatProperty(name="Top Radius", default=0.3, min=0.1)
    segments: IntProperty(name="Segments", default=16, min=4)

    # Details
    plinth_height: FloatProperty(name="Plinth H", default=0.3, min=0.0)
    capital_height: FloatProperty(name="Capital H", default=0.4, min=0.0)

    # Styles
    column_style: EnumProperty(
        name="Style",
        items=[
            ("ROUND", "Round", "Classic Column"),
            ("SQUARE", "Square", "Modern Pillar"),
            ("H_BEAM", "H-Beam", "Industrial Beam"),
        ],
        default="ROUND"
    )

    fluted: BoolProperty(name="Fluted Shaft", default=False)
    flute_depth: FloatProperty(name="Flute Depth", default=0.02, min=0.001)

    def get_slot_meta(self):
        return {
            0: {"name": "Column Shaft", "uv": "UNWRAP", "phys": "DEBUG_1"},
            1: {"name": "Cap/Base", "uv": "UNWRAP", "phys": "DEBUG_2"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        th = self.total_height
        ph = self.plinth_height
        ch = self.capital_height
        r_base = self.radius_base

        if self.column_style == 'SQUARE':
            w = r_base * 2
            # Base
            builder.create_box(w*1.2, w*1.2, ph).translate(0, 0, ph/2).tag_slot(1) \
                   .select_boundary().tag_edge_role(1)
            # Shaft
            shaft_h = th - ph - ch
            if shaft_h > 0:
                builder.create_box(w, w, shaft_h).translate(0, 0, ph + shaft_h/2).tag_slot(0) \
                       .select_boundary().tag_edge_role(2) # Sharp corners (will zipper later)
            # Cap
            builder.create_box(w*1.2, w*1.2, ch).translate(0, 0, th - ch/2).tag_slot(1) \
                   .select_boundary().tag_edge_role(1)

        elif self.column_style == 'H_BEAM':
            # Industrial H-Beam
            w = r_base * 2
            d = w
            flange_t = w * 0.1
            web_t = w * 0.1

            # Web
            builder.create_box(web_t, d - 2*flange_t, th).translate(0, 0, th/2).tag_slot(0).select_boundary().tag_edge_role(1)
            # Flanges
            builder.create_box(w, flange_t, th).translate(0, d/2 - flange_t/2, th/2).tag_slot(0).select_boundary().tag_edge_role(1)
            builder.create_box(w, flange_t, th).translate(0, -d/2 + flange_t/2, th/2).tag_slot(0).select_boundary().tag_edge_role(1)

            # Base Plate
            builder.create_box(w*1.4, d*1.4, ph).translate(0, 0, ph/2).tag_slot(1).select_boundary().tag_edge_role(1)

        else: # ROUND
            # Even segments for grid fill
            segs = self.segments if self.segments % 2 == 0 else self.segments + 1
            shaft_top_z = max(ph, th - ch)
            r_top = self.radius_top
            r_cap = r_base * 1.2

            # Plinth
            if ph > 0.001:
                builder.create_cylinder(radius=r_base*1.1, depth=ph, segments=segs, center=Vector((0,0,ph/2))) \
                       .tag_slot(1).select_boundary().tag_edge_role(1)

            # Shaft
            shaft_h = shaft_top_z - ph
            if shaft_h > 0.001:
                builder.create_cone(radius_bottom=r_base, radius_top=r_top, depth=shaft_h, segments=segs, center=Vector((0,0,ph + shaft_h/2))) \
                       .tag_slot(0)

                # Fluting logic
                if self.fluted:
                     flute_candidates = []
                     for f in builder.active_faces:
                         if abs(f.normal.z) < 0.1:
                             flute_candidates.append(f)

                     if flute_candidates:
                         builder.active_faces = flute_candidates
                         try:
                             builder.inset(0.02 * r_base, depth=-self.flute_depth, relative=False) \
                                    .tag_edge_role(2) # Sharp flutes
                         except:
                             pass

                # Mark Shaft Caps as 1 (Seam)
                # Select top/bottom faces
                builder.select_all_faces().select_faces_by_slot(0) \
                       .select_faces_by_normal(Vector((0,0,1)), tolerance=0.1).select_boundary().tag_edge_role(1)

                builder.select_all_faces().select_faces_by_slot(0) \
                       .select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1).select_boundary().tag_edge_role(1)

            # Capital
            cap_h = th - shaft_top_z
            if cap_h > 0.001:
                builder.create_cone(radius_bottom=r_top, radius_top=r_cap, depth=cap_h, segments=segs, center=Vector((0,0,shaft_top_z + cap_h/2))) \
                       .tag_slot(1).select_boundary().tag_edge_role(1)

        # Zipper Logic (Vertical Seam for Shaft)
        builder.clean()

        # Only needed for Shaft (Slot 0)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # Find vertical edges of Slot 0 faces
        candidates = []
        for e in bm.edges:
            # Check if edge belongs to Slot 0
            is_slot_0 = any(f.material_index == 0 for f in e.link_faces)
            if not is_slot_0: continue

            # Check verticality
            dz = abs(e.verts[0].co.z - e.verts[1].co.z)
            dxy = ((e.verts[0].co.x - e.verts[1].co.x)**2 + (e.verts[0].co.y - e.verts[1].co.y)**2)**0.5
            if dz > 0.001 and dxy < 0.001:
                candidates.append(e)

        if candidates:
            # Pick the "Back" edge (Max Y)
            zipper = max(candidates, key=lambda e: (e.verts[0].co.y + e.verts[1].co.y))

            if self.column_style == 'ROUND':
                zipper[edge_slots] = 3 # Guide (Seam only)
            elif self.column_style == 'SQUARE':
                zipper[edge_slots] = 1 # Perimeter (Seam + Sharp)
            # H_BEAM is complex, unwrap usually handles it by island if we marked boundaries.

        # Sockets (Tag Existing Faces)
        builder.clean()

        # Bottom Socket (Z=0, Normal -Z)
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1).tag_socket(1)

        # Top Socket (Z=H, Normal +Z)
        builder.select_faces_by_normal(Vector((0, 0, 1)), tolerance=0.1).tag_socket(2)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "column_style")
        col.prop(self, "total_height")
        col.prop(self, "radius_base")
        if self.column_style == 'ROUND':
            col.prop(self, "radius_top")
            col.prop(self, "segments")
            layout.separator()
            col.prop(self, "fluted")
            if self.fluted:
                col.prop(self, "flute_depth")

        layout.separator()
        col.prop(self, "plinth_height")
        col.prop(self, "capital_height")
