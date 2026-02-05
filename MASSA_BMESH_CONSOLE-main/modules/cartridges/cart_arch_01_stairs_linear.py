import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    FloatVectorProperty,
    EnumProperty,
)
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "Linear Stairs",
    "id": "arch_01_stairs_linear",
    "icon": "MESH_STAIRS",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_ArchStairsLinear(Massa_OT_Base):
    bl_idname = "massa.gen_arch_01_stairs_linear"
    bl_label = "Linear Stairs"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Bounds (XYZ)", default=(2.0, 4.0, 3.0), min=0.1)

    # --- 2. TOPOLOGY ---
    step_count: IntProperty(name="Step Count", default=12, min=2)

    # Detail Props
    tread_thick: FloatProperty(
        name="Thick",
        default=0.05,
        min=0.005,
        step=0.001,
        precision=3,
        description="Tread Thickness",
    )
    nosing: FloatProperty(
        name="Nosing",
        default=0.03,
        min=0.0,
        step=0.001,
        precision=3,
        description="Nosing Depth",
    )
    closed_riser: BoolProperty(name="Closed Risers", default=True)

    # Structure
    has_stringer: BoolProperty(name="Side Stringers", default=True)
    stringer_width: FloatProperty(
        name="Width",
        default=0.1,
        min=0.01,
        step=0.001,
        precision=3,
        description="Stringer Width",
    )
    stringer_depth: FloatProperty(
        name="Height",
        default=0.35,
        min=0.1,
        step=0.01,
        precision=3,
        description="Vertical height of the side beam",
    )

    # Railing
    has_rail: BoolProperty(name="Add Railing", default=True)

    rail_profile: EnumProperty(
        name="Rail Profile",
        items=[
            ("ROUND", "Round", "Cylindrical tubing"),
            ("SQUARE", "Square", "Box section tubing"),
        ],
        default="ROUND",
    )

    rail_height: FloatProperty(
        name="Height", default=0.9, min=0.1, description="Rail Height from Tread"
    )
    rail_radius: FloatProperty(
        name="Radius",
        default=0.04,
        min=0.005,
        step=0.001,
        precision=3,
        description="Rail Thickness/Radius",
    )
    post_density: IntProperty(
        name="Step Gap", default=4, min=2, description="How many steps between posts"
    )

    # --- 3. UV PROTOCOLS (Properties kept for UVS Tab) ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Treads", "uv": "BOX", "phys": "WOOD_OAK"},
            1: {"name": "Risers", "uv": "BOX", "phys": "WOOD_PINE"},
            2: {"name": "Stringers", "uv": "BOX", "phys": "METAL_STEEL"},
            3: {"name": "Railing", "uv": "BOX", "phys": "METAL_CHROME"},
            4: {"name": "Anchors", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        # 1. DIMENSIONS
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "size", index=0, text="W")
        row.prop(self, "size", index=1, text="L")
        row.prop(self, "size", index=2, text="H")

        # Info Readout
        run = self.size[1] / max(1, self.step_count)
        rise = self.size[2] / max(1, self.step_count)
        col.label(text=f"Rise: {rise:.2f}m | Run: {run:.2f}m", icon="INFO")

        layout.separator()

        # 2. TOPOLOGY
        # Main Steps
        box = layout.box()
        box.label(text="Steps Configuration", icon="MESH_GRID")

        row = box.row()
        row.prop(self, "step_count")
        row.prop(self, "closed_riser", text="Risers")

        # Details compacted
        row = box.row(align=True)
        row.prop(self, "tread_thick")
        row.prop(self, "nosing")

        # 3. STRUCTURE
        box = layout.box()
        row = box.row()
        row.prop(self, "has_stringer", icon="MOD_BUILD")

        if self.has_stringer:
            row = box.row(align=True)
            row.prop(self, "stringer_width")
            row.prop(self, "stringer_depth")

        # 4. RAILING
        box = layout.box()
        row = box.row()
        row.prop(self, "has_rail", icon="MOD_PHYSICS")

        if self.has_rail:
            # Profile Select
            box.row().prop(self, "rail_profile", expand=True)

            # Dimensions Compacted
            row = box.row(align=True)
            row.prop(self, "rail_height")
            row.prop(self, "rail_radius")

            # Density
            box.prop(self, "post_density")

        # [REMOVED] UV UI - Moved to Central UVS Tab

    def build_shape(self, bm: bmesh.types.BMesh):
        total_w, total_l, total_h = self.size
        count = max(1, self.step_count)

        rise = total_h / count
        run = total_l / count

        tread_w = total_w
        if self.has_stringer:
            tread_w -= self.stringer_width * 2

        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        # 1. GENERATE STEPS
        for i in range(count):
            t_depth = run + self.nosing
            y_center = -(total_l / 2) + (i * run) + (t_depth / 2) - self.nosing
            z_center = (i * rise) + (self.tread_thick / 2)

            # TREAD
            t_center_vec = Vector((0, y_center, z_center))
            res_t = bmesh.ops.create_cube(bm, size=1.0)
            verts_t = res_t["verts"]
            bmesh.ops.scale(bm, vec=(tread_w, t_depth, self.tread_thick), verts=verts_t)
            bmesh.ops.translate(bm, vec=t_center_vec, verts=verts_t)

            for f in list({f for v in verts_t for f in v.link_faces}):
                f.material_index = 0
                f.smooth = False
                self.apply_box_map(f, uv_layer, s)

            # RISER
            if self.closed_riser:
                r_thick = 0.02
                z_riser = (i * rise) - (rise / 2)
                y_riser = -(total_l / 2) + (i * run) + (r_thick / 2)
                r_center_vec = Vector((0, y_riser, z_riser))

                res_r = bmesh.ops.create_cube(bm, size=1.0)
                verts_r = res_r["verts"]
                bmesh.ops.scale(bm, vec=(tread_w, r_thick, rise), verts=verts_r)
                bmesh.ops.translate(bm, vec=r_center_vec, verts=verts_r)

                for f in list({f for v in verts_r for f in v.link_faces}):
                    f.material_index = 1
                    f.smooth = False
                    self.apply_box_map(f, uv_layer, s)

        # 2. GENERATE STRINGERS
        if self.has_stringer:
            angle = math.atan2(total_h, total_l)
            min_structural_depth = rise * math.cos(angle)
            beam_depth = self.stringer_depth + min_structural_depth

            diag_len = math.sqrt(total_l**2 + total_h**2)
            over_len = diag_len + 2.0
            beam_dims = Vector((self.stringer_width, over_len, beam_depth))

            for side in [-1, 1]:
                bm_st = bmesh.new()
                st_uv = bm_st.loops.layers.uv.verify()

                bmesh.ops.create_cube(bm_st, size=1.0)
                bmesh.ops.scale(bm_st, vec=beam_dims, verts=bm_st.verts)
                bmesh.ops.rotate(
                    bm_st,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(angle, 4, "X"),
                    verts=bm_st.verts,
                )

                x_pos = side * ((total_w / 2) - (self.stringer_width / 2))
                z_mid = total_h / 2
                bmesh.ops.translate(bm_st, vec=(x_pos, 0, z_mid), verts=bm_st.verts)

                # Cuts
                bmesh.ops.bisect_plane(
                    bm_st,
                    geom=bm_st.verts[:] + bm_st.edges[:] + bm_st.faces[:],
                    plane_co=(0, 0, 0),
                    plane_no=(0, 0, -1),
                    clear_outer=True,
                )
                bmesh.ops.contextual_create(
                    bm_st, geom=[e for e in bm_st.edges if e.is_boundary]
                )
                bmesh.ops.bisect_plane(
                    bm_st,
                    geom=bm_st.verts[:] + bm_st.edges[:] + bm_st.faces[:],
                    plane_co=(0, total_l / 2, 0),
                    plane_no=(0, 1, 0),
                    clear_outer=True,
                )
                bmesh.ops.contextual_create(
                    bm_st, geom=[e for e in bm_st.edges if e.is_boundary]
                )
                bmesh.ops.bisect_plane(
                    bm_st,
                    geom=bm_st.verts[:] + bm_st.edges[:] + bm_st.faces[:],
                    plane_co=(0, -total_l / 2, 0),
                    plane_no=(0, -1, 0),
                    clear_outer=True,
                )
                bmesh.ops.contextual_create(
                    bm_st, geom=[e for e in bm_st.edges if e.is_boundary]
                )

                for f in bm_st.faces:
                    f.material_index = 2
                    f.smooth = False
                    self.apply_box_map(f, st_uv, s)

                temp_me = bpy.data.meshes.new("temp_st")
                bm_st.to_mesh(temp_me)
                bm.from_mesh(temp_me)
                bpy.data.meshes.remove(temp_me)
                bm_st.free()

        # 3. GENERATE RAILING
        if self.has_rail:
            n_posts = max(2, int(count / max(1, self.post_density)) + 1)
            float_indices = [i * (count - 1) / (n_posts - 1) for i in range(n_posts)]
            post_indices = sorted(list(set([round(x) for x in float_indices])))

            post_h = self.rail_height
            post_rad = self.rail_radius

            rail_path_l = []
            rail_path_r = []

            embed_depth = 0.25

            margin = 0.02
            inset_dist = self.rail_radius + margin
            if self.has_stringer:
                inset_dist += self.stringer_width

            for i in post_indices:
                i = int(i)
                y_local = -(total_l / 2) + (i * run) + (run / 2.0)
                z_surface = (i * rise) + self.tread_thick

                for side in [-1, 1]:
                    edge_x = side * (total_w / 2)
                    x_pos = edge_x - (side * inset_dist)

                    z_base = z_surface - embed_depth
                    z_visual_top = z_surface + post_h
                    z_phys_top = z_visual_top + (post_rad * 0.5)

                    total_cyl_h = z_phys_top - z_base
                    z_center = z_base + (total_cyl_h / 2)

                    # POST
                    target_pos = Vector((x_pos, y_local, z_center))

                    if self.rail_profile == "ROUND":
                        res_p = bmesh.ops.create_cone(
                            bm,
                            cap_ends=True,
                            radius1=post_rad,
                            radius2=post_rad,
                            depth=total_cyl_h,
                            segments=12,
                        )
                    else:  # SQUARE
                        res_p = bmesh.ops.create_cube(bm, size=1.0)
                        bmesh.ops.scale(
                            bm,
                            vec=(post_rad * 2, post_rad * 2, total_cyl_h),
                            verts=res_p["verts"],
                        )

                    verts_p = res_p["verts"]
                    bmesh.ops.translate(bm, vec=target_pos, verts=verts_p)

                    for f in list({f for v in verts_p for f in v.link_faces}):
                        f.material_index = 3
                        f.smooth = self.rail_profile == "ROUND"

                    # FLANGE
                    z_flange = z_surface + 0.005
                    flange_pos = Vector((x_pos, y_local, z_flange))

                    if self.rail_profile == "ROUND":
                        res_f = bmesh.ops.create_cone(
                            bm,
                            cap_ends=True,
                            radius1=post_rad * 1.8,
                            radius2=post_rad * 1.6,
                            depth=0.02,
                            segments=12,
                        )
                    else:  # SQUARE
                        res_f = bmesh.ops.create_cube(bm, size=1.0)
                        bmesh.ops.scale(
                            bm,
                            vec=(post_rad * 3.6, post_rad * 3.6, 0.02),
                            verts=res_f["verts"],
                        )

                    verts_f = res_f["verts"]
                    bmesh.ops.translate(bm, vec=flange_pos, verts=verts_f)

                    for f in list({f for v in verts_f for f in v.link_faces}):
                        f.material_index = 3
                        f.smooth = False

                    pt = Vector((x_pos, y_local, z_visual_top))
                    if side == -1:
                        rail_path_l.append(pt)
                    else:
                        rail_path_r.append(pt)

            # Continuous Handrail
            for path in [rail_path_l, rail_path_r]:
                if len(path) < 2:
                    continue

                vec_s = (path[1] - path[0]).normalized()
                ext = 0.01
                path_ext = [path[0] - vec_s * ext] + path + [path[-1] + vec_s * ext]

                p0, p1 = path_ext[0], path_ext[1]
                v_dir = (p1 - p0).normalized()

                rot = Vector((0, 0, 1)).rotation_difference(v_dir)
                mat_s = Matrix.Translation(p0) @ rot.to_matrix().to_4x4()

                f_cap = None

                if self.rail_profile == "ROUND":
                    res_c = bmesh.ops.create_circle(
                        bm, radius=self.rail_radius * 1.2, segments=12, matrix=mat_s
                    )
                    try:
                        f_cap = bm.faces.new(res_c["verts"])
                    except ValueError:
                        continue
                else:  # SQUARE
                    r = self.rail_radius * 1.2
                    local_coords = [(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)]
                    world_coords = [mat_s @ Vector(c) for c in local_coords]
                    verts_sq = [bm.verts.new(c) for c in world_coords]
                    try:
                        f_cap = bm.faces.new(verts_sq)
                    except ValueError:
                        continue

                if f_cap:
                    f_cap.material_index = 3
                    f_cap.smooth = self.rail_profile == "ROUND"

                # Extrude
                for k in range(len(path_ext) - 1):
                    seg_vec = path_ext[k + 1] - path_ext[k]
                    res_ex = bmesh.ops.extrude_face_region(bm, geom=[f_cap])
                    verts_ex = [
                        v for v in res_ex["geom"] if isinstance(v, bmesh.types.BMVert)
                    ]
                    faces_ex = [
                        f for f in res_ex["geom"] if isinstance(f, bmesh.types.BMFace)
                    ]

                    bmesh.ops.translate(bm, vec=seg_vec, verts=verts_ex)

                    for f in faces_ex:
                        f.material_index = 3
                        f.smooth = self.rail_profile == "ROUND"
                        if f.normal.dot(seg_vec.normalized()) > 0.5:
                            f_cap = f
                            break

                # Knuckles
                for pt in path:
                    mat_k = Matrix.Translation(pt) @ rot.to_matrix().to_4x4()

                    if self.rail_profile == "ROUND":
                        res_k = bmesh.ops.create_cone(
                            bm,
                            cap_ends=True,
                            radius1=self.rail_radius * 1.5,
                            radius2=self.rail_radius * 1.5,
                            depth=self.rail_radius * 3.5,
                            matrix=mat_k,
                            segments=12,
                        )
                        verts_k = res_k["verts"]
                    else:  # SQUARE
                        res_k = bmesh.ops.create_cube(bm, size=1.0)
                        bmesh.ops.scale(
                            bm,
                            vec=(
                                self.rail_radius * 2.8,
                                self.rail_radius * 2.8,
                                self.rail_radius * 3.5,
                            ),
                            verts=res_k["verts"],
                        )
                        bmesh.ops.transform(bm, matrix=mat_k, verts=res_k["verts"])
                        verts_k = res_k["verts"]

                    for f in list({f for v in verts_k for f in v.link_faces}):
                        f.material_index = 3
                        f.smooth = self.rail_profile == "ROUND"

        # 4. CLEANUP & SOCKETS
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self.create_socket_face(
            bm, Vector((0, total_l / 2, total_h)), Vector((0, 1, 0)), 4
        )
        self.create_socket_face(bm, Vector((0, -total_l / 2, 0)), Vector((0, -1, 0)), 4)

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

    def create_socket_face(self, bm, loc, normal, slot_idx):
        r = 0.05
        t1 = Vector((0, 0, 1)) if abs(normal.z) < 0.9 else Vector((1, 0, 0))
        t2 = normal.cross(t1).normalized() * r
        t1 = normal.cross(t2).normalized() * r
        verts = [
            bm.verts.new(loc + t1),
            bm.verts.new(loc - t1 + t2),
            bm.verts.new(loc - t1 - t2),
        ]
        f = bm.faces.new(verts)
        f.material_index = slot_idx
        f.normal_update()
        if f.normal.dot(normal) < 0:
            f.normal_flip()
