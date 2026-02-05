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
            0: {"name": "Treads", "uv": "SKIP", "phys": "WOOD_OAK"},
            1: {"name": "Risers", "uv": "SKIP", "phys": "WOOD_PINE"},
            2: {"name": "Structure", "uv": "SKIP", "phys": "METAL_STEEL"},
            3: {"name": "Railing", "uv": "SKIP", "phys": "METAL_CHROME"},
            4: {"name": "Anchors", "uv": "BOX", "phys": "GENERIC", "sock": True},
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

        # [REMOVED] UV UI - Moved to Central UVS Tab

    def build_shape(self, bm: bmesh.types.BMesh):
        h = self.height
        rad = self.radius
        turns = self.turns
        count = max(3, self.step_count)

        angle_total = turns * 2 * math.pi
        angle_step = angle_total / count
        rise_step = h / count

        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        # 1. CENTER POST
        if self.has_center_post:
            res_post = bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                radius1=self.post_radius,
                radius2=self.post_radius,
                depth=h,
                segments=16,
            )
            bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=res_post["verts"])

            post_faces = list({f for v in res_post["verts"] for f in v.link_faces})
            for f in post_faces:
                if f.normal.z > 0.9:  # TOP CAP
                    f.material_index = 4
                    self.apply_box_map(f, uv_layer, s)
                elif f.normal.z < -0.9:  # BOTTOM CAP
                    f.material_index = 4
                    self.apply_box_map(f, uv_layer, s)
                else:  # SIDE WALLS
                    f.material_index = 2
                    f.smooth = True
                    self.apply_polar_map(f, uv_layer, s, self.post_radius)

        # 2. STEPS
        inner_r = self.post_radius if self.has_center_post else 0.1
        tread_len = rad - inner_r
        if self.has_stringer:
            tread_len -= self.stringer_width

        for i in range(count):
            theta = i * angle_step
            z = i * rise_step

            # Tread
            res_t = bmesh.ops.create_cube(bm, size=1.0)
            verts_t = res_t["verts"]

            mid_circ = 2 * math.pi * (inner_r + tread_len / 2)
            step_width_approx = (mid_circ / count) * 1.1

            bmesh.ops.scale(
                bm, vec=(tread_len, step_width_approx, self.tread_thick), verts=verts_t
            )
            dist_from_center = inner_r + (tread_len / 2)
            bmesh.ops.translate(
                bm, vec=(dist_from_center, 0, self.tread_thick / 2), verts=verts_t
            )
            bmesh.ops.rotate(
                bm, cent=(0, 0, 0), matrix=Matrix.Rotation(theta, 4, "Z"), verts=verts_t
            )
            bmesh.ops.translate(bm, vec=(0, 0, z), verts=verts_t)

            for f in list({f for v in verts_t for f in v.link_faces}):
                f.material_index = 0
                f.smooth = False
                self.apply_box_map(f, uv_layer, s)

            # Riser
            if self.closed_riser:
                res_r = bmesh.ops.create_cube(bm, size=1.0)
                verts_r = res_r["verts"]
                r_thick = 0.02
                bmesh.ops.scale(bm, vec=(tread_len, r_thick, rise_step), verts=verts_r)
                bmesh.ops.translate(
                    bm,
                    vec=(dist_from_center, -step_width_approx / 2, -rise_step / 2),
                    verts=verts_r,
                )
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(theta, 4, "Z"),
                    verts=verts_r,
                )
                bmesh.ops.translate(bm, vec=(0, 0, z), verts=verts_r)

                for f in list({f for v in verts_r for f in v.link_faces}):
                    f.material_index = 1
                    f.smooth = False
                    self.apply_box_map(f, uv_layer, s)

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
                is_round=False,
                uv_layer=uv_layer,
                uv_scale=s,
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

                mat_p = Matrix.Translation(Vector((x, y, z_floor + h_post_phys / 2)))

                if self.rail_profile == "ROUND":
                    res_p = bmesh.ops.create_cone(
                        bm,
                        cap_ends=True,
                        radius1=self.rail_radius,
                        radius2=self.rail_radius,
                        depth=h_post_phys,
                        matrix=mat_p,
                        segments=12,
                    )
                else:
                    res_p = bmesh.ops.create_cube(bm, size=1.0)
                    bmesh.ops.scale(
                        bm,
                        vec=(self.rail_radius * 2, self.rail_radius * 2, h_post_phys),
                        verts=res_p["verts"],
                    )
                    bmesh.ops.transform(bm, matrix=mat_p, verts=res_p["verts"])

                for f in list({f for v in res_p["verts"] for f in v.link_faces}):
                    f.material_index = 3
                    f.smooth = self.rail_profile == "ROUND"
                    radius_val = (
                        self.rail_radius
                        if self.rail_profile == "ROUND"
                        else self.rail_radius * 2
                    )
                    self.apply_polar_map(f, uv_layer, s, radius_val)

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
                z_offset=rail_z_offset,
                uv_layer=uv_layer,
                uv_scale=s,
            )

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

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
        z_offset=0.0,
        uv_layer=None,
        uv_scale=1.0,
    ):
        total_angle = turns * 2 * math.pi
        d_theta = total_angle / segs
        d_z = height / segs
        arc_len_segment = math.sqrt((radius * d_theta) ** 2 + d_z**2)

        if is_round:
            perimeter = math.pi * profile_w
        else:
            perimeter = 2 * (profile_w + profile_h)

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

        # 2. EXTRUSION LOOP
        current_v_coord = 0.0

        for k in range(segs):
            current_v_coord += arc_len_segment * uv_scale

            res_ex = bmesh.ops.extrude_edge_only(bm, edges=edges_ring)
            verts_new = [v for v in res_ex["geom"] if isinstance(v, bmesh.types.BMVert)]
            faces_side = [
                f for f in res_ex["geom"] if isinstance(f, bmesh.types.BMFace)
            ]

            bmesh.ops.translate(bm, vec=Vector((0, 0, d_z)), verts=verts_new)
            bmesh.ops.rotate(
                bm,
                cent=(0, 0, 0),
                matrix=Matrix.Rotation(d_theta, 4, "Z"),
                verts=verts_new,
            )

            if uv_layer and faces_side:
                for j, edge_old in enumerate(edges_ring):
                    target_face = None
                    for f in faces_side:
                        if edge_old in f.edges:
                            target_face = f
                            break

                    if target_face:
                        target_face.material_index = slot_idx
                        target_face.smooth = is_round

                        u_start = (j / len(edges_ring)) * perimeter * uv_scale
                        u_end = ((j + 1) / len(edges_ring)) * perimeter * uv_scale

                        v_prev = current_v_coord - (arc_len_segment * uv_scale)
                        v_curr = current_v_coord

                        loops = list(target_face.loops)
                        for l in loops:
                            if l.vert in edge_old.verts:
                                if l.vert == edge_old.verts[0]:
                                    l[uv_layer].uv = (u_start, v_prev)
                                else:
                                    l[uv_layer].uv = (u_end, v_prev)
                            else:
                                connected_to_start = False
                                for e in l.vert.link_edges:
                                    if e.other_vert(l.vert) == edge_old.verts[0]:
                                        connected_to_start = True
                                        break

                                if connected_to_start:
                                    l[uv_layer].uv = (u_start, v_curr)
                                else:
                                    l[uv_layer].uv = (u_end, v_curr)

            new_verts_set = set(verts_new)
            next_verts_ring = [None] * len(verts_ring)
            for i, v_old in enumerate(verts_ring):
                for e in v_old.link_edges:
                    other = e.other_vert(v_old)
                    if other in new_verts_set:
                        next_verts_ring[i] = other
                        break

            verts_ring = next_verts_ring
            edges_ring = []
            for i in range(len(verts_ring)):
                v1 = verts_ring[i]
                v2 = verts_ring[(i + 1) % len(verts_ring)]
                found_edge = bm.edges.get((v1, v2))
                if found_edge:
                    edges_ring.append(found_edge)

        # 3. CAP ENDS
        try:
            bmesh.ops.contextual_create(bm, geom=start_verts)
            for f in bm.faces:
                if all(v in start_verts for v in f.verts):
                    f.material_index = slot_idx
                    f.normal_flip()
                    self.apply_box_map(f, uv_layer, s)
        except:
            pass

        try:
            bmesh.ops.contextual_create(bm, geom=verts_ring)
            for f in bm.faces:
                if all(v in verts_ring for v in f.verts):
                    f.material_index = slot_idx
                    self.apply_box_map(f, uv_layer, s)
        except:
            pass

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

    def apply_polar_map(self, face, uv_layer, scale, radius=1.0):
        circumference = 2 * math.pi * radius
        for l in face.loops:
            co = l.vert.co
            theta = math.atan2(co.y, co.x)
            u = ((theta + math.pi) / (2 * math.pi)) * circumference
            v = co.z
            l[uv_layer].uv = (u * scale, v * scale)
