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
    
    angled_supports: BoolProperty(
        name="Angled Supports",
        default=False,
        description="Splay column bases outward for an angled/leaning support look"
    )
    
    structural_supports: BoolProperty(
        name="Structural Supports",
        default=False,
        description="Add diagonal support beams around the outside"
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
            0: {"name": "Deck Surface", "uv": "BOX", "phys": "METAL_IRON"},
            1: {"name": "Structure", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Railings", "uv": "BOX", "phys": "METAL_STEEL"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "GENERIC"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")
        layout.prop(self, "angled_supports")
        layout.prop(self, "structural_supports")

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
        # Ensure MASSA_SOCKETS layer exists up front to prevent face pointer invalidation on reallocation
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
            
        builder = MassaBuilder(bm)

        l, w, h = self.length, self.width, self.height
        dt = self.deck_thick
        bd = self.beam_depth
        cw = self.col_width
        cs = self.col_spacing
        oh = self.overhang

        # ── Z levels ──────────────────────────────────────────────────────
        z_beam_bot = h
        z_beam_top = h + bd
        z_deck_top = h + bd + dt

        # ── Column positions: perimeter-only (corners + edge intermediates) ──
        # Columns sit at the 4 deck corners and at col_spacing intervals along
        # each of the 4 edges.  No interior columns.
        def _edge_pos(start, end, spacing):
            """Evenly-spaced positions from start to end at ≤spacing intervals."""
            span = abs(end - start)
            n = max(1, round(span / spacing))
            return [start + i * span / n for i in range(n + 1)]

        x_cols = _edge_pos(-w/2, w/2, cs)   # positions along bottom/top edges
        y_cols = _edge_pos(-l/2, l/2, cs)   # positions along left/right edges

        # Deduplicated perimeter list: bottom, top, left side, right side.
        _seen = set()
        col_positions = []
        for px in x_cols:
            for py in (-l/2, l/2):
                key = (round(px, 4), round(py, 4))
                if key not in _seen:
                    _seen.add(key)
                    col_positions.append((px, py))
        for py in y_cols:
            for px in (-w/2, w/2):
                key = (round(px, 4), round(py, 4))
                if key not in _seen:
                    _seen.add(key)
                    col_positions.append((px, py))

        # ── 1. Columns ────────────────────────────────────────────────────
        for (px, py) in col_positions:
            # Angled splay: base slides outward from centre.
            px_bot, py_bot = px, py
            if self.angled_supports:
                splay_dist = h * 0.2
                vec2d = Vector((px, py))
                if vec2d.length > 0.01:
                    dir_out = vec2d.normalized()
                    px_bot += dir_out.x * splay_dist
                    py_bot += dir_out.y * splay_dist

            # Vertical box, then shear bottom verts outward if angled.
            builder.create_box(cw, cw, h, center=Vector((px, py, h/2)))
            if self.angled_supports:
                splay_dx = px_bot - px
                splay_dy = py_bot - py
                if abs(splay_dx) > 0.001 or abs(splay_dy) > 0.001:
                    bot_verts = [v for v in builder.active_verts if v.co.z < 0.01]
                    if bot_verts:
                        bmesh.ops.translate(bm, verts=bot_verts,
                                            vec=(splay_dx, splay_dy, 0.0))

            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Base plate (STEEL_BEAM only).
            if self.style == "STEEL_BEAM":
                builder.create_box(cw*1.5, cw*1.5, 0.02,
                                   center=Vector((px_bot, py_bot, 0.01)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Diagonal brace toward nearest platform edge.
            if self.structural_supports:
                vec2d = Vector((px, py))
                if vec2d.length > 0.01:
                    dir_out  = vec2d.normalized()
                    brace_end = Vector((px + dir_out.x * cw * 3,
                                        py + dir_out.y * cw * 3, h))
                    start_p  = Vector((px, py, h * 0.5))
                    brace_vec = brace_end - start_p
                    if brace_vec.length > 0.1:
                        builder.create_grid(x_segments=1, y_segments=1,
                                            size=cw*0.5, center=start_p)
                        builder.tag_slot(1)
                        builder.align_normal_to_vector(brace_vec)
                        builder.extrude(brace_vec.length)
                        builder.grow_selection(1)
                        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # ── 2. Beams ──────────────────────────────────────────────────────
        # X-direction beams (full width) at every column Y row.
        for py in y_cols:
            builder.create_box(w + cw, cw * 0.8, bd,
                               center=Vector((0, py, h + bd / 2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Y-direction edge girders at the two column X edges only.
        for px in (-w/2, w/2):
            builder.create_box(cw * 0.8, l + cw, bd,
                               center=Vector((px, 0, h + bd / 2)))
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
            cx    = self.cutout_x
            cut_w = self.cutout_w  # separate name — avoids shadowing col_width (cw)
            cut_l = self.cutout_l

            # Bisect X bounds
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(cx - cut_w/2, 0, 0), plane_no=(1,0,0))
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(cx + cut_w/2, 0, 0), plane_no=(1,0,0))

            # Bisect Y bounds — cutout centred at Y=0
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(0, -cut_l/2, 0), plane_no=(0,1,0))
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(0,  cut_l/2, 0), plane_no=(0,1,0))

            # Select faces inside the cutout bounds and delete them
            to_delete = []
            bm.faces.ensure_lookup_table()
            for f in bm.faces:
                cen = f.calc_center_median()
                if abs(cen.z - z_deck_base) < 0.01: # Only deck faces
                    if (cx - cut_w/2) <= cen.x <= (cx + cut_w/2) and (-cut_l/2) <= cen.y <= (cut_l/2):
                        to_delete.append(f)

            bmesh.ops.delete(bm, geom=to_delete, context='FACES')

        # Extrude Deck Thickness
        # Select all deck faces (approx Z = z_deck_base)
        bm.faces.ensure_lookup_table()
        deck_faces = [f for f in bm.faces if abs(f.calc_center_median().z - z_deck_base) < 0.01]

        if deck_faces:
            builder.active_faces = deck_faces
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.extrude(dt)
            builder.grow_selection(1)
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

                vec = p2 - p1
                angle = math.atan2(vec.y, vec.x)

                builder.create_box(dist, 0.05, 0.05, center=Vector((0,0,0)))
                builder.rotate(math.degrees(angle), axis='Z')
                builder.translate(mid.x, mid.y, mid.z)
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Mid Rail
                mid.z -= rh/2
                builder.create_box(dist, 0.03, 0.03, center=Vector((0,0,0)))
                builder.rotate(math.degrees(angle), axis='Z')
                builder.translate(mid.x, mid.y, mid.z)
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            z_rail = h + bd + dt

            # Corners sit exactly on the deck rim so posts straddle the outer edge.
            c1 = Vector((-w/2, -l/2, z_rail))
            c2 = Vector(( w/2, -l/2, z_rail))
            c3 = Vector(( w/2,  l/2, z_rail))
            c4 = Vector((-w/2,  l/2, z_rail))

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
        
        # Ensure lookup table is valid after boolean deletions
        builder.bm.faces.ensure_lookup_table()
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1)
        # Filter Z ~ 0 and ensure faces are still valid
        bases = [f for f in builder.active_faces if f.is_valid and abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = bases
        builder.tag_socket(9)

        builder.clean()

    def execute(self, context):
        return super().execute(context)
