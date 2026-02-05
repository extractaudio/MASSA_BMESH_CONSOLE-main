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
    "name": "Canopy / Gazebo",
    "id": "struct_canopy",
    "icon": "OUTLINER_OB_LATTICE",
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


class MASSA_OT_Canopy(Massa_OT_Base):
    bl_idname = "massa.gen_struct_canopy"
    bl_label = "Canopy"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    width: FloatProperty(name="Width (X)", default=3.0, min=1.0, unit="LENGTH")
    depth: FloatProperty(name="Depth (Y)", default=3.0, min=1.0, unit="LENGTH")
    height: FloatProperty(name="Post Height", default=2.5, min=1.5, unit="LENGTH")

    # --- 2. ROOF SPECS ---
    roof_style: EnumProperty(
        name="Style",
        items=[
            ("PYRAMID", "Pyramid", "Center Peak"),
            ("GABLE", "Gable", "Ridge Line along Y"),
            ("SLANT", "Slanted", "Slope back-to-front"),
        ],
        default="PYRAMID",
    )
    roof_height: FloatProperty(name="Roof Rise", default=0.8, min=0.0, unit="LENGTH")
    roof_thickness: FloatProperty(
        name="Thickness", default=0.05, min=0.01, unit="LENGTH"
    )
    roof_z_offset: FloatProperty(name="Vertical Offset", default=0.0, unit="LENGTH")
    overhang: FloatProperty(name="Overhang", default=0.2, min=0.0, unit="LENGTH")

    # --- 3. FRAME ---
    add_frame: BoolProperty(name="Add Top Frame", default=True)
    frame_h: FloatProperty(name="Beam Height", default=0.15, min=0.05, unit="LENGTH")
    frame_w: FloatProperty(name="Beam Width", default=0.10, min=0.05, unit="LENGTH")

    # Cross Beams
    add_cross_beams: BoolProperty(name="Add Cross Beams", default=True)
    cross_beam_offset: FloatProperty(
        name="Cross Offset",
        default=0.4,
        min=0.1,
        unit="LENGTH",
        description="Distance below main frame",
    )

    # --- 4. POSTS ---
    post_size: FloatProperty(name="Post Size", default=0.15, min=0.05, unit="LENGTH")
    post_inset_x: FloatProperty(name="Inset X", default=0.2, min=0.0, unit="LENGTH")
    post_inset_y: FloatProperty(name="Inset Y", default=0.2, min=0.0, unit="LENGTH")

    # --- 5. EXTRAS ---
    has_floor: BoolProperty(name="Add Floor", default=False)

    # --- 6. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Posts", "uv": "BOX", "phys": "WOOD_OLD"},
            1: {"name": "Frame Beams", "uv": "BOX", "phys": "WOOD_PINE"},
            2: {"name": "Roof", "uv": "BOX", "phys": "METAL_RUST"},
            3: {"name": "Floor", "uv": "BOX", "phys": "CONCRETE_RAW"},
            4: {"name": "Cross Beams", "uv": "BOX", "phys": "WOOD_PINE"},
            9: {"name": "Anchors", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        row = col.row(align=True)
        row.prop(self, "width", text="W")
        row.prop(self, "depth", text="D")
        row.prop(self, "height", text="H")

        col.separator()
        box = col.box()
        box.label(text="Roofing", icon="MOD_BUILD")
        box.prop(self, "roof_style", text="")

        row = box.row(align=True)
        row.prop(self, "roof_height", text="Rise")
        row.prop(self, "overhang", text="Over")

        row = box.row(align=True)
        row.prop(self, "roof_thickness", text="Thick")
        row.prop(self, "roof_z_offset", text="Z-Off")

        col.separator()
        box = col.box()
        box.label(text="Structure", icon="MESH_GRID")

        row = box.row(align=True)
        row.prop(self, "post_size", text="Post Sz")
        row.prop(self, "post_inset_x", text="Ins X")
        row.prop(self, "post_inset_y", text="Ins Y")

        box.prop(self, "add_frame", toggle=True)
        if self.add_frame:
            row = box.row(align=True)
            row.prop(self, "frame_w", text="Beam W")
            row.prop(self, "frame_h", text="Beam H")

            row = box.row(align=True)
            row.prop(self, "add_cross_beams", text="Cross Beams", toggle=True)
            if self.add_cross_beams:
                row.prop(self, "cross_beam_offset", text="Down")

        box.prop(self, "has_floor", toggle=True)

    def build_shape(self, bm: bmesh.types.BMesh):
        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        # --- HELPERS ---
        def create_box(center, size, slot):
            res = bmesh.ops.create_cube(bm, size=1.0)
            verts = res["verts"]
            bmesh.ops.scale(bm, vec=size, verts=verts)
            bmesh.ops.translate(bm, vec=center, verts=verts)
            for f in list({f for v in verts for f in v.link_faces}):
                f.material_index = slot
                self.apply_box_map(f, uv_layer, s)
            return verts

        p_width = max(0.1, self.width - (self.post_inset_x * 2))
        p_depth = max(0.1, self.depth - (self.post_inset_y * 2))

        # Elevations
        z_front = self.height
        z_back = self.height
        if self.roof_style == "SLANT":
            z_back += self.roof_height

        # 1. POSTS
        h_post_front = z_front
        h_post_back = z_back

        if self.add_frame:
            h_post_front -= self.frame_h
            h_post_back -= self.frame_h

        # Define base footprint for reuse (Anchors)
        post_bases = [
            (p_width / 2, p_depth / 2),
            (-p_width / 2, p_depth / 2),
            (-p_width / 2, -p_depth / 2),
            (p_width / 2, -p_depth / 2),
        ]

        if h_post_front > 0:
            # Reconstruct locs with heights
            post_locs = [
                (post_bases[0][0], post_bases[0][1], h_post_back),
                (post_bases[1][0], post_bases[1][1], h_post_back),
                (post_bases[2][0], post_bases[2][1], h_post_front),
                (post_bases[3][0], post_bases[3][1], h_post_front),
            ]
            for x, y, h_val in post_locs:
                create_box(
                    Vector((x, y, h_val / 2)),
                    Vector((self.post_size, self.post_size, h_val)),
                    0,
                )

        # 2. FRAME
        if self.add_frame:
            bz_front = z_front - (self.frame_h / 2)
            bz_back = z_back - (self.frame_h / 2)
            beam_len_x = p_width + self.post_size

            # A. Front/Back Beams
            create_box(
                Vector((0, -p_depth / 2, bz_front)),
                Vector((beam_len_x, self.frame_w, self.frame_h)),
                1,
            )
            create_box(
                Vector((0, p_depth / 2, bz_back)),
                Vector((beam_len_x, self.frame_w, self.frame_h)),
                1,
            )

            # B. Side Beams (Angled)
            for x_dir in [1, -1]:
                x_pos = x_dir * (p_width / 2)
                p_start = Vector((x_pos, -p_depth / 2, bz_front))
                p_end = Vector((x_pos, p_depth / 2, bz_back))
                mid = (p_start + p_end) / 2
                vec = p_end - p_start
                length = vec.length

                angle = math.atan2(vec.z, vec.y)

                b_side = bmesh.ops.create_cube(bm, size=1.0)
                verts_b = b_side["verts"]
                bmesh.ops.scale(
                    bm, vec=Vector((self.frame_w, length, self.frame_h)), verts=verts_b
                )
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(angle, 4, "X"),
                    verts=verts_b,
                )
                bmesh.ops.translate(bm, vec=mid, verts=verts_b)

                for f in list({f for v in verts_b for f in v.link_faces}):
                    f.material_index = 1
                    self.apply_box_map(f, uv_layer, s)

            # CROSS BEAMS
            if self.add_cross_beams:
                cb_off = self.cross_beam_offset
                cb_size = self.frame_w * 0.8

                # Front/Back
                create_box(
                    Vector((0, -p_depth / 2, bz_front - cb_off)),
                    Vector((p_width - self.post_size, cb_size, cb_size)),
                    4,
                )
                create_box(
                    Vector((0, p_depth / 2, bz_back - cb_off)),
                    Vector((p_width - self.post_size, cb_size, cb_size)),
                    4,
                )

                # Sides (Angled)
                for x_dir in [1, -1]:
                    x_pos = x_dir * (p_width / 2)
                    p_start = Vector((x_pos, -p_depth / 2, bz_front - cb_off))
                    p_end = Vector((x_pos, p_depth / 2, bz_back - cb_off))
                    mid = (p_start + p_end) / 2
                    vec = p_end - p_start

                    # [FIX] Extend length to embed slightly
                    # Original logic was: vec.length - (post_size * 2) -> Gap
                    # New logic: vec.length - (post_size * 0.1) -> Overlap
                    length = vec.length - (self.post_size * 0.1)

                    if length > 0:
                        angle = math.atan2(vec.z, vec.y)
                        b_cross = bmesh.ops.create_cube(bm, size=1.0)
                        verts_c = b_cross["verts"]
                        bmesh.ops.scale(
                            bm, vec=Vector((cb_size, length, cb_size)), verts=verts_c
                        )
                        bmesh.ops.rotate(
                            bm,
                            cent=(0, 0, 0),
                            matrix=Matrix.Rotation(angle, 4, "X"),
                            verts=verts_c,
                        )
                        bmesh.ops.translate(bm, vec=mid, verts=verts_c)
                        for f in list({f for v in verts_c for f in v.link_faces}):
                            f.material_index = 4
                            self.apply_box_map(f, uv_layer, s)

        # 3. ROOF
        r_w = self.width + (self.overhang * 2)
        r_d = self.depth + (self.overhang * 2)
        base_z = self.height + self.roof_z_offset

        v1 = Vector((-r_w / 2, -r_d / 2, base_z))
        v2 = Vector((-r_w / 2, r_d / 2, base_z))
        v3 = Vector((r_w / 2, r_d / 2, base_z))
        v4 = Vector((r_w / 2, -r_d / 2, base_z))

        roof_faces = []

        if self.roof_style == "PYRAMID":
            peak = Vector((0, 0, base_z + self.roof_height))
            b_v1, b_v2, b_v3, b_v4 = [bm.verts.new(v) for v in [v1, v2, v3, v4]]
            b_peak = bm.verts.new(peak)
            roof_faces.append(bm.faces.new((b_v1, b_v2, b_peak)))
            roof_faces.append(bm.faces.new((b_v2, b_v3, b_peak)))
            roof_faces.append(bm.faces.new((b_v3, b_v4, b_peak)))
            roof_faces.append(bm.faces.new((b_v4, b_v1, b_peak)))

        elif self.roof_style == "GABLE":
            ridge_h = base_z + self.roof_height
            v_front = Vector((0, -r_d / 2, ridge_h))
            v_back = Vector((0, r_d / 2, ridge_h))
            b_v1, b_v2, b_v3, b_v4 = [bm.verts.new(v) for v in [v1, v2, v3, v4]]
            b_vf, b_vb = bm.verts.new(v_front), bm.verts.new(v_back)
            roof_faces.append(bm.faces.new((b_v1, b_v2, b_vb, b_vf)))
            roof_faces.append(bm.faces.new((b_v4, b_vf, b_vb, b_v3)))
            roof_faces.append(bm.faces.new((b_v1, b_vf, b_v4)))
            roof_faces.append(bm.faces.new((b_v2, b_v3, b_vb)))

        elif self.roof_style == "SLANT":
            v2.z += self.roof_height
            v3.z += self.roof_height
            b_v1, b_v2, b_v3, b_v4 = [bm.verts.new(v) for v in [v1, v2, v3, v4]]
            roof_faces.append(bm.faces.new((b_v1, b_v2, b_v3, b_v4)))

        # Solidify Roof
        bmesh.ops.recalc_face_normals(bm, faces=roof_faces)
        if roof_faces:
            res = bmesh.ops.solidify(bm, geom=roof_faces, thickness=self.roof_thickness)
            for elem in res["geom"]:
                if isinstance(elem, bmesh.types.BMFace):
                    elem.material_index = 2
                    self.apply_box_map(elem, uv_layer, s)
            for f in roof_faces:
                if f.is_valid:
                    f.material_index = 2
                    self.apply_box_map(f, uv_layer, s)

        # 4. FLOOR
        if self.has_floor:
            create_box(
                Vector((0, 0, 0.1)),
                Vector((self.width + 0.5, self.depth + 0.5, 0.2)),
                3,
            )

        # 5. ANCHORS (Updated)
        # Place sockets at the base of each post, pointing UP
        for x, y in post_bases:
            self.create_socket_face(bm, Vector((x, y, 0)), Vector((0, 0, 1)), 9)

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
        r = 0.1
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
