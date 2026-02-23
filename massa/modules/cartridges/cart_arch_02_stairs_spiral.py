import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
)
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "Spiral Stairs",
    "id": "arch_02_stairs_spiral",
    "icon": "MESH_CONE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_ArchStairsSpiral(Massa_OT_Base):
    bl_idname = "massa.gen_arch_02_stairs_spiral"
    bl_label = "Spiral Stairs"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    radius: FloatProperty(
        name="Radius", default=1.5, min=0.5, unit="LENGTH", description="Outer radius"
    )
    height: FloatProperty(name="Height", default=3.0, min=0.5, unit="LENGTH")
    turns: FloatProperty(
        name="Turns",
        default=0.75,
        min=0.1,
        step=0.05,
        description="Revolutions (1.0 = 360 degrees)",
    )

    # --- 2. TOPOLOGY ---
    step_count: IntProperty(name="Step Count", default=16, min=3)

    tread_thick: FloatProperty(
        name="Thick",
        default=0.05,
        min=0.005,
        step=0.001,
        precision=3,
        unit="LENGTH",
        description="Tread Thickness",
    )
    nosing: FloatProperty(
        name="Nosing",
        default=0.03,
        min=0.0,
        step=0.001,
        precision=3,
        unit="LENGTH",
        description="Nosing overhang",
    )
    closed_riser: BoolProperty(name="Closed Risers", default=False)

    # --- 3. STRUCTURE ---
    has_center_post: BoolProperty(name="Center Post", default=True)
    post_radius: FloatProperty(
        name="Post Rad", default=0.15, min=0.05, step=0.01, precision=3, unit="LENGTH"
    )

    has_stringer: BoolProperty(name="Outer Stringer", default=True)
    stringer_width: FloatProperty(
        name="Str Width", default=0.05, min=0.01, step=0.001, precision=3, unit="LENGTH"
    )
    stringer_depth: FloatProperty(
        name="Str Height", default=0.3, min=0.05, step=0.01, precision=3, unit="LENGTH"
    )

    # --- 4. RAILING ---
    has_rail: BoolProperty(name="Add Railing", default=True)

    rail_profile: EnumProperty(
        name="Rail Profile",
        items=[
            ("ROUND", "Round", "Cylindrical tubing"),
            ("SQUARE", "Square", "Box section tubing"),
        ],
        default="ROUND",
    )

    rail_height: FloatProperty(name="R-Height", default=0.9, min=0.1, unit="LENGTH")
    rail_radius: FloatProperty(
        name="R-Radius", default=0.04, min=0.005, step=0.001, precision=3, unit="LENGTH"
    )
    post_density: IntProperty(
        name="Step Gap", default=4, min=1, description="Steps per post"
    )

    # --- 5. UV PROTOCOLS (Properties kept for UVS Tab) ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Treads", "uv": "UNWRAP", "phys": "WOOD_OAK"},
            1: {"name": "Risers", "uv": "UNWRAP", "phys": "WOOD_PINE"},
            2: {"name": "Structure", "uv": "UNWRAP", "phys": "METAL_STEEL"},
            3: {"name": "Railing", "uv": "UNWRAP", "phys": "METAL_CHROME"},
            4: {"name": "Anchors", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "height")
        col.prop(self, "radius")
        col.prop(self, "turns")

        rise = self.height / max(1, self.step_count)
        row = col.row()
        row.alignment = "LEFT"
        row.label(text=f"Step Rise: {rise:.3f}m", icon="INFO")

        col.separator()

        col.label(text="Configuration")
        col.prop(self, "step_count")
        col.prop(self, "closed_riser")

        row = col.row(align=True)
        row.prop(self, "tread_thick", text="Thickness")
        row.prop(self, "nosing")

        col.separator()

        col.label(text="Structure")

        row = col.row(align=True)
        row.prop(self, "has_center_post", text="Center Post")
        sub = row.row()
        sub.active = self.has_center_post
        sub.prop(self, "post_radius", text="Radius")

        col.prop(self, "has_stringer", text="Outer Stringer")

        if self.has_stringer:
            row = col.row(align=True)
            row.prop(self, "stringer_width", text="Width")
            row.prop(self, "stringer_depth", text="Depth")

        col.separator()

        col.label(text="Railing System")
        col.prop(self, "has_rail", text="Enable Railing")

        if self.has_rail:
            col.prop(self, "rail_profile", text="")
            row = col.row(align=True)
            row.prop(self, "rail_height", text="Height")
            row.prop(self, "rail_radius", text="Radius")
            col.prop(self, "post_density")

    def build_shape(self, bm: bmesh.types.BMesh):
        builder = MassaBuilder(bm)

        h = self.height
        rad = self.radius
        turns = self.turns
        count = max(3, self.step_count)

        angle_total = turns * 2 * math.pi
        angle_step = angle_total / count
        rise_step = h / count

        # 1. CENTER POST
        if self.has_center_post:
            builder.create_cylinder(radius=self.post_radius, depth=h, segments=16, center=Vector((0,0,h/2))) \
                   .tag_slot(2) # Structure

            # Tag Seams: Caps (1), Vertical Zipper (3)
            builder.select_all_faces().select_faces_by_slot(2).select_boundary().tag_edge_role(1)

            # Vertical Zipper for Cylinder
            # Find a vertical edge
            builder.clean() # Ensure topology
            # Helper to find vertical edge on active selection
            # But active selection is last created faces.
            candidates = []
            for f in builder.active_faces:
                for e in f.edges:
                    v1, v2 = e.verts
                    if abs(v1.co.x - v2.co.x) < 0.001 and abs(v1.co.y - v2.co.y) < 0.001:
                        candidates.append(e)
            if candidates:
                # Pick one (e.g. max X)
                zipper = max(candidates, key=lambda e: e.verts[0].co.x)
                builder.active_edges = [zipper]
                builder.tag_edge_role(3)

        # 2. STEPS
        inner_r = self.post_radius if self.has_center_post else 0.1
        tread_len = rad - inner_r
        if self.has_stringer:
            tread_len -= self.stringer_width

        mid_circ = 2 * math.pi * (inner_r + tread_len / 2)
        step_width_approx = (mid_circ / count) * 1.1 # Slightly wider to overlap?

        for i in range(count):
            theta = i * angle_step
            z = i * rise_step

            # Tread
            # Create at origin, scale, translate, rotate
            # Note: create_box creates at center.
            # We need pivot at (0,0,0) for rotation.

            dist_from_center = inner_r + (tread_len / 2)

            # Create Step Tread
            builder.create_box(tread_len, step_width_approx, self.tread_thick) \
                   .translate(dist_from_center, 0, self.tread_thick / 2) \
                   .rotate(math.degrees(theta), 'Z') \
                   .translate(0, 0, z) \
                   .tag_slot(0) \
                   .select_boundary().tag_edge_role(1)

            # Riser
            if self.closed_riser:
                r_thick = 0.02
                builder.create_box(tread_len, r_thick, rise_step) \
                       .translate(dist_from_center, -step_width_approx / 2, -rise_step / 2) \
                       .rotate(math.degrees(theta), 'Z') \
                       .translate(0, 0, z) \
                       .tag_slot(1) \
                       .select_boundary().tag_edge_role(1)

        # 3. HELICAL COMPONENTS
        path_radius_str = rad - (self.stringer_width / 2)
        circ_str = 2 * math.pi * path_radius_str * turns
        pitch_angle = math.atan(h / circ_str)

        # A. Stringer
        if self.has_stringer:
            self.build_helix_extrusion(
                bm,
                radius=path_radius_str,
                height=h,
                turns=turns,
                segs=count * 4,
                profile_w=self.stringer_width,
                profile_h=self.stringer_depth,
                pitch_angle=pitch_angle,
                slot_idx=2,
                is_round=False
            )

        # B. Railing
        if self.has_rail:
            path_radius_rail = path_radius_str if self.has_stringer else (rad - 0.1)

            # Posts
            post_indices = list(range(0, count, self.post_density))
            if (count - 1) not in post_indices:
                post_indices.append(count - 1)

            for i in post_indices:
                theta = i * angle_step
                z_floor = i * rise_step + self.tread_thick

                x = math.cos(theta) * path_radius_rail
                y = math.sin(theta) * path_radius_rail

                h_post_vis = self.rail_height
                h_post_phys = h_post_vis + (self.rail_radius * 0.5)

                center_pos = Vector((x, y, z_floor + h_post_phys / 2))

                if self.rail_profile == "ROUND":
                    builder.create_cylinder(radius=self.rail_radius, depth=h_post_phys, segments=12, center=center_pos)
                else:
                    builder.create_box(self.rail_radius * 2, self.rail_radius * 2, h_post_phys, center=center_pos)

                builder.tag_slot(3).select_boundary().tag_edge_role(1)

            # Handrail
            rail_z_offset = self.rail_height + self.tread_thick
            self.build_helix_extrusion(
                bm,
                radius=path_radius_rail,
                height=h,
                turns=turns,
                segs=count * 6,
                profile_w=self.rail_radius * 2,
                profile_h=self.rail_radius * 2,
                pitch_angle=pitch_angle,
                slot_idx=3,
                is_round=(self.rail_profile == "ROUND"),
                z_offset=rail_z_offset
            )

        # Cleanup & Sockets
        builder.clean()

        # Bottom Socket
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1).tag_socket(4)
        # Top Socket
        builder.select_faces_by_normal(Vector((0, 0, 1)), tolerance=0.1).tag_socket(4)


    def build_helix_extrusion(
        self,
        bm,
        radius,
        height,
        turns,
        segs,
        profile_w,
        profile_h,
        pitch_angle,
        slot_idx,
        is_round,
        z_offset=0.0
    ):
        # Optimized implementation without manual UVs
        # Uses MassaBuilder style tagging

        total_angle = turns * 2 * math.pi
        d_theta = total_angle / segs
        d_z = height / segs

        # 1. INITIAL RING
        mat_setup = Matrix.Translation(Vector((radius, 0, z_offset))) @ Matrix.Rotation(
            pitch_angle, 4, "X"
        )

        verts_ring = []
        if is_round:
            mat_circle = mat_setup @ Matrix.Rotation(math.radians(90), 4, "X")
            seg_circle = 12
            for i in range(seg_circle):
                a = (i / seg_circle) * 2 * math.pi
                v_loc = Vector(
                    (math.cos(a) * profile_w / 2, math.sin(a) * profile_w / 2, 0)
                )
                verts_ring.append(bm.verts.new(mat_circle @ v_loc))
        else:
            hw, hh = profile_w / 2, profile_h / 2
            coords_local = [
                Vector((-hw, 0, -hh)),
                Vector((hw, 0, -hh)),
                Vector((hw, 0, hh)),
                Vector((-hw, 0, hh)),
            ]
            verts_ring = [bm.verts.new(mat_setup @ c) for c in coords_local]

        edges_ring = []
        for i in range(len(verts_ring)):
            v1 = verts_ring[i]
            v2 = verts_ring[(i + 1) % len(verts_ring)]
            edges_ring.append(bm.edges.new((v1, v2)))

        start_verts = list(verts_ring)

        # Track longitudinal edges for tagging
        long_edges = []

        # 2. EXTRUSION LOOP
        for k in range(segs):
            res_ex = bmesh.ops.extrude_edge_only(bm, edges=edges_ring)
            verts_new = [v for v in res_ex["geom"] if isinstance(v, bmesh.types.BMVert)]
            faces_side = [
                f for f in res_ex["geom"] if isinstance(f, bmesh.types.BMFace)
            ]
            edges_side = [e for e in res_ex["geom"] if isinstance(e, bmesh.types.BMEdge) and e not in edges_ring]
            # Note: extrude_edge_only returns edges in 'geom' that are the connecting edges (longitudinal)?
            # Actually it returns faces, and new edges (the ring at other end) and connecting edges?
            # We need to identify connecting edges to tag them as Seam/Guide.

            # The 'geom' contains new verts, edges, faces.
            # Edges perpendicular to ring are the ones connecting old ring to new ring.

            for f in faces_side:
                f.material_index = slot_idx
                f.smooth = is_round

            bmesh.ops.translate(bm, vec=Vector((0, 0, d_z)), verts=verts_new)
            bmesh.ops.rotate(
                bm,
                cent=(0, 0, 0),
                matrix=Matrix.Rotation(d_theta, 4, "Z"),
                verts=verts_new,
            )

            # Tag Longitudinal Edges
            # Find edges connecting verts_ring (old) to verts_new (new)
            # Or just use faces_side edges that are NOT in edges_ring or the new ring.
            # Simpler: All edges of faces_side that align with flow?
            # Let's rely on Edge Slots for seams.
            # For round tube, we need 1 seam.
            # For square, we need sharp edges (Role 2) and 1 seam (Role 1 or 3).

            # Find the edges in faces_side that are not the ring edges
            # ...

            new_verts_set = set(verts_new)
            next_verts_ring = [None] * len(verts_ring)
            for i, v_old in enumerate(verts_ring):
                for e in v_old.link_edges:
                    other = e.other_vert(v_old)
                    if other in new_verts_set:
                        next_verts_ring[i] = other
                        # This 'e' is a longitudinal edge
                        long_edges.append(e)
                        break

            verts_ring = next_verts_ring
            edges_ring = []
            for i in range(len(verts_ring)):
                v1 = verts_ring[i]
                v2 = verts_ring[(i + 1) % len(verts_ring)]
                found_edge = bm.edges.get((v1, v2))
                if found_edge:
                    edges_ring.append(found_edge)

        # 3. CAP ENDS & TAGGING
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # Tag Longitudinal Edges
        # If ROUND: Tag ONE line of edges as Seam (3).
        # If SQUARE: Tag ALL longitudinal edges as Sharp (2), and ONE as Seam (1)?
        # Let's tag all sharp corners.

        # We collected all long_edges.
        # They are ordered by segment.
        # We need to tag them by index in the ring.

        n_profile = len(start_verts)
        # long_edges list structure: [seg0_idx0, seg0_idx1... seg1_idx0...]
        # Actually logic above appends in loop.

        for k in range(segs):
            base_idx = k * n_profile
            if is_round:
                # Tag only index 0 as Seam (3)
                if base_idx < len(long_edges):
                    long_edges[base_idx][edge_slots] = 3
            else:
                # Tag all as Sharp (2)
                for i in range(n_profile):
                    if (base_idx + i) < len(long_edges):
                        long_edges[base_idx + i][edge_slots] = 2

                # Tag index 0 as Seam (1) (override Sharp?)
                # Actually Seam + Sharp = Perimeter (1) or just Seam (3)?
                # If we want unwrap, we need a cut.
                # Let's make one edge Seam (3) (Guide) in addition to sharp?
                # Or make it Perimeter (1) (Sharp+Seam).
                if base_idx < len(long_edges):
                     long_edges[base_idx][edge_slots] = 1

        # Cap Start
        try:
            bmesh.ops.contextual_create(bm, geom=start_verts)
            for f in bm.faces:
                if all(v in start_verts for v in f.verts):
                    f.material_index = slot_idx
                    f.normal_flip()
                    for e in f.edges:
                        e[edge_slots] = 1 # Perimeter Seam
        except:
            pass

        # Cap End
        try:
            bmesh.ops.contextual_create(bm, geom=verts_ring)
            for f in bm.faces:
                if all(v in verts_ring for v in f.verts):
                    f.material_index = slot_idx
                    for e in f.edges:
                        e[edge_slots] = 1 # Perimeter Seam
        except:
            pass
