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
    "name": "Shack Assembly",
    "id": "building_assembly_1",
    "icon": "HOME",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_BuildingAssembly1(Massa_OT_Base):
    bl_idname = "massa.gen_building_assembly_1"
    bl_label = "Shack Assembly"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Bounds (XYZ)", default=(3.0, 4.0, 2.5), min=0.5)

    # --- 2. FOUNDATION & BASE ---
    found_height: FloatProperty(
        name="Slab Height", default=0.2, min=0.01, unit="LENGTH"
    )
    baseboard_height: FloatProperty(
        name="Baseboard H", default=0.15, min=0.01, unit="LENGTH"
    )
    baseboard_thick: FloatProperty(
        name="Baseboard T", default=0.02, min=0.001, unit="LENGTH"
    )

    # --- 3. FRAME & WALLS ---
    post_size: FloatProperty(name="Timber Size", default=0.15, min=0.05, unit="LENGTH")

    # Studs
    has_studs: BoolProperty(name="Studs", default=True)
    stud_spacing: FloatProperty(name="Spacing", default=0.6, min=0.2, unit="LENGTH")

    wall_thick: FloatProperty(name="Wall Thick", default=0.05, min=0.01, unit="LENGTH")
    has_cladding: BoolProperty(name="Cladding", default=True)

    # --- 4. DOORWAY ---
    door_width: FloatProperty(name="Door Width", default=1.0, min=0.5, unit="LENGTH")
    door_height: FloatProperty(name="Door Height", default=2.1, min=1.0, unit="LENGTH")
    door_wall: EnumProperty(
        name="Door Location",
        items=[
            ("FRONT", "Front (+Y)", ""),
            ("BACK", "Back (-Y)", ""),
            ("LEFT", "Left (-X)", ""),
            ("RIGHT", "Right (+X)", ""),
        ],
        default="FRONT",
    )

    # --- 5. ROOF (TRUSS SYSTEM) ---
    has_roof: BoolProperty(name="Enable Roof", default=True)
    roof_height: FloatProperty(name="Gable Height", default=1.2, min=0.1, unit="LENGTH")
    roof_overhang_side: FloatProperty(
        name="Side Eaves", default=0.3, min=0.0, unit="LENGTH"
    )
    roof_overhang_end: FloatProperty(
        name="Gable Eaves", default=0.3, min=0.0, unit="LENGTH"
    )

    # Truss Parameters
    truss_count: IntProperty(name="Truss Count", default=4, min=2)
    truss_size: FloatProperty(
        name="Truss Timber", default=0.12, min=0.05, unit="LENGTH"
    )
    has_ridge_beam: BoolProperty(name="Ridge Beam", default=True)

    # Gutters
    has_gutters: BoolProperty(name="Gutters", default=True)

    # Roof Covering
    roof_type: EnumProperty(
        name="Covering",
        items=[
            ("SHEET", "Sheet Metal", "Flat panels"),
            ("SCALES", "Scales / Shingles", "Overlapping tiles"),
        ],
        default="SCALES",
    )
    scale_size: FloatVectorProperty(
        name="Scale Dims", default=(0.2, 0.3, 0.02), min=0.01, size=3
    )
    scale_overlap: FloatProperty(name="Overlap", default=0.05, min=0.0, unit="LENGTH")

    # --- 6. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Foundation", "uv": "BOX", "phys": "CONCRETE_RAW"},
            1: {"name": "Baseboards", "uv": "BOX", "phys": "WOOD_PAINTED"},
            2: {"name": "Timber Frame", "uv": "BOX", "phys": "WOOD_OLD"},
            3: {"name": "Cladding", "uv": "BOX", "phys": "WOOD_PINE"},
            4: {"name": "Door Frame", "uv": "BOX", "phys": "WOOD_OAK"},
            5: {"name": "Roof Structure", "uv": "BOX", "phys": "WOOD_OLD"},
            6: {"name": "Roof Covering", "uv": "BOX", "phys": "STONE_SLATE"},
            7: {"name": "Door Leaf", "uv": "BOX", "phys": "WOOD_PAINTED"},
            8: {"name": "Gutters", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            9: {"name": "Anchors", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions (W / L / H)")
        row = col.row(align=True)
        row.prop(self, "size", index=0, text="W")
        row.prop(self, "size", index=1, text="L")
        row.prop(self, "size", index=2, text="H")

        col.separator()

        # 2. STRUCTURE
        box = col.box()
        box.label(text="Foundation & Frame", icon="MOD_BUILD")

        row = box.row(align=True)
        row.prop(self, "found_height", text="Slab")
        row.prop(self, "baseboard_height", text="Trim H")
        row.prop(self, "baseboard_thick", text="Trim T")

        row = box.row(align=True)
        row.prop(self, "post_size", text="Post")
        row.prop(self, "wall_thick", text="Wall")

        row = box.row(align=True)
        row.prop(self, "has_studs", toggle=True)
        sub = row.row(align=True)
        sub.active = self.has_studs
        sub.prop(self, "stud_spacing", text="Gap")
        row.separator()
        row.prop(self, "has_cladding", toggle=True)

        # 3. DOORWAY
        box = col.box()
        row = box.row(align=True)
        row.label(text="Door", icon="HOME")
        row.prop(self, "door_wall", text="")
        row = box.row(align=True)
        row.prop(self, "door_width", text="Width")
        row.prop(self, "door_height", text="Height")

        # 4. ROOF SYSTEM
        box = col.box()
        row = box.row()
        row.prop(self, "has_roof", icon="TRIA_DOWN" if self.has_roof else "TRIA_RIGHT")

        if self.has_roof:
            col_r = box.column(align=True)
            row = col_r.row(align=True)
            row.prop(self, "roof_height", text="Rise")
            row.prop(self, "roof_overhang_side", text="Side Eaves")
            row.prop(self, "roof_overhang_end", text="Gable Eaves")

            row = col_r.row(align=True)
            row.prop(self, "truss_count", text="Count")
            row.prop(self, "truss_size", text="Timber")
            row.prop(self, "has_ridge_beam", text="Ridge", toggle=True)

            col_r.prop(self, "has_gutters", toggle=True)
            col_r.separator()

            row = col_r.row(align=True)
            row.prop(self, "roof_type", text="")
            if self.roof_type == "SCALES":
                row.prop(self, "scale_overlap", text="Overlap")
                col_r.prop(self, "scale_size", text="Tile Size")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, l, h = self.size
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

        def create_gutter_u(center, width, length, height, thick, slot):
            # U-Shape Profile along Y
            # Vertices for profile (X/Z plane)
            hw = width / 2
            hh = height

            # Outer U
            v1 = Vector((-hw, 0, hh))  # Top Left
            v2 = Vector((-hw, 0, 0))  # Bottom Left
            v3 = Vector((hw, 0, 0))  # Bottom Right
            v4 = Vector((hw, 0, hh))  # Top Right

            # Inner U
            v1_in = Vector((-hw + thick, 0, hh))
            v2_in = Vector((-hw + thick, 0, thick))
            v3_in = Vector((hw - thick, 0, thick))
            v4_in = Vector((hw - thick, 0, hh))

            # Create Face Profile
            # Since we want a solid U shape, let's create a block and delete top, then solidify?
            # Or manually build the U face and extrude.

            # Let's manually build the U polygon and extrude.
            # Vertices in order: v1 -> v2 -> v3 -> v4 -> v4_in -> v3_in -> v2_in -> v1_in
            profile_verts = [v1, v2, v3, v4, v4_in, v3_in, v2_in, v1_in]
            bm_verts = [
                bm.verts.new(center + v + Vector((0, -length / 2, 0)))
                for v in profile_verts
            ]

            face = bm.faces.new(bm_verts)

            # Extrude
            res = bmesh.ops.extrude_face_region(bm, geom=[face])
            extruded_verts = [
                v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)
            ]
            bmesh.ops.translate(bm, vec=Vector((0, length, 0)), verts=extruded_verts)

            # Assign Material
            all_faces = list(
                {f for v in bm_verts + extruded_verts for f in v.link_faces}
            )
            for f in all_faces:
                f.material_index = slot
                self.apply_box_map(f, uv_layer, s)

        # 1. FOUNDATION
        create_box(
            Vector((0, 0, -self.found_height / 2)), Vector((w, l, self.found_height)), 0
        )

        # 2. TIMBER FRAME
        p_sz = min(self.post_size, w / 2.1, l / 2.1)
        half_w, half_l = w / 2, l / 2
        p_off = p_sz / 2

        corners = [
            (half_w - p_off, half_l - p_off),
            (half_w - p_off, -half_l + p_off),
            (-half_w + p_off, half_l - p_off),
            (-half_w + p_off, -half_l + p_off),
        ]
        for cx, cy in corners:
            create_box(Vector((cx, cy, h / 2)), Vector((p_sz, p_sz, h)), 2)

        beam_thick = p_sz
        create_box(
            Vector((half_w - p_off, 0, h - beam_thick / 2)),
            Vector((p_sz, l, beam_thick)),
            2,
        )
        create_box(
            Vector((-half_w + p_off, 0, h - beam_thick / 2)),
            Vector((p_sz, l, beam_thick)),
            2,
        )
        inner_w = w - (p_sz * 2)
        create_box(
            Vector((0, half_l - p_off, h - beam_thick / 2)),
            Vector((inner_w, p_sz, beam_thick)),
            2,
        )
        create_box(
            Vector((0, -half_l + p_off, h - beam_thick / 2)),
            Vector((inner_w, p_sz, beam_thick)),
            2,
        )

        # Studs
        if self.has_studs:
            stud_w, stud_d = p_sz * 0.35, p_sz * 0.8
            stud_h = h - beam_thick
            stud_z = stud_h / 2
            d_half_w = self.door_width / 2

            def build_stud_row(start_vec, end_vec, axis, check_door):
                vec = end_vec - start_vec
                length = vec.length
                count = int(length / self.stud_spacing)
                if count < 1:
                    return
                step_vec = vec.normalized() * (length / (count + 1))
                for k in range(1, count + 1):
                    pos = start_vec + (step_vec * k)
                    if check_door:
                        dist = abs(pos.x) if axis == "X" else abs(pos.y)
                        if dist < d_half_w + (stud_w / 2):
                            continue
                    s_size = (
                        Vector((stud_w, stud_d, stud_h))
                        if axis == "X"
                        else Vector((stud_d, stud_w, stud_h))
                    )
                    create_box(Vector((pos.x, pos.y, stud_z)), s_size, 2)

            inset = p_sz
            build_stud_row(
                Vector((-half_w + inset, half_l - p_off, 0)),
                Vector((half_w - inset, half_l - p_off, 0)),
                "X",
                self.door_wall == "FRONT",
            )
            build_stud_row(
                Vector((-half_w + inset, -half_l + p_off, 0)),
                Vector((half_w - inset, -half_l + p_off, 0)),
                "X",
                self.door_wall == "BACK",
            )
            build_stud_row(
                Vector((half_w - p_off, -half_l + inset, 0)),
                Vector((half_w - p_off, half_l - inset, 0)),
                "Y",
                self.door_wall == "RIGHT",
            )
            build_stud_row(
                Vector((-half_w + p_off, -half_l + inset, 0)),
                Vector((-half_w + p_off, half_l - inset, 0)),
                "Y",
                self.door_wall == "LEFT",
            )

        # 3. BASEBOARDS
        bb_h, bb_t = self.baseboard_height, self.baseboard_thick
        create_box(
            Vector((0, half_l + bb_t / 2, bb_h / 2)),
            Vector((w + bb_t * 2, bb_t, bb_h)),
            1,
        )
        create_box(
            Vector((0, -half_l - bb_t / 2, bb_h / 2)),
            Vector((w + bb_t * 2, bb_t, bb_h)),
            1,
        )
        create_box(Vector((half_w + bb_t / 2, 0, bb_h / 2)), Vector((bb_t, l, bb_h)), 1)
        create_box(
            Vector((-half_w - bb_t / 2, 0, bb_h / 2)), Vector((bb_t, l, bb_h)), 1
        )

        # 4. WALLS
        if self.has_cladding:
            d_w = min(self.door_width, w - p_sz * 2)
            d_h = min(self.door_height, h - beam_thick)
            wt, inset = self.wall_thick, p_sz * 0.2

            side_wall_h = h
            if self.has_roof:
                rise = self.roof_height
                # [ARCHITECT] Calculate Exact Roof Height at Wall Line
                # Span = w + 2*eaves
                # Slope = rise / (w/2 + eaves)
                # Wall is at x = w/2. Rafter starts at x = w/2 + eaves.
                # Distance from rafter start to wall = eaves.
                # Height rise = slope * eaves.
                # Wall Top Z = h + (rise * (eaves / (w/2 + eaves)))
                total_half_span = (w / 2) + self.roof_overhang_side
                if total_half_span > 0.001:
                    height_at_wall = rise * (self.roof_overhang_side / total_half_span)
                    side_wall_h = h + height_at_wall

            def build_wall_panel(center, size, axis, has_door, override_h=None):
                wall_h = override_h if override_h else size.z
                eff_center = center.copy()
                eff_center.z = wall_h / 2

                if not has_door:
                    create_box(eff_center, Vector((size.x, size.y, wall_h)), 3)
                else:
                    full_w = size.x if axis == "X" else size.y
                    header_h = wall_h - d_h
                    if header_h > 0.01:
                        h_cen = eff_center.copy()
                        h_cen.z = d_h + header_h / 2
                        create_box(h_cen, Vector((size.x, size.y, header_h)), 3)
                    side_w = (full_w - d_w) / 2
                    if side_w > 0.01:
                        off = (d_w + side_w) / 2
                        l_c, r_c = eff_center.copy(), eff_center.copy()
                        l_c.z, r_c.z = d_h / 2, d_h / 2
                        if axis == "X":
                            l_c.x -= off
                            r_c.x += off
                            create_box(l_c, Vector((side_w, size.y, d_h)), 3)
                            create_box(r_c, Vector((side_w, size.y, d_h)), 3)
                        else:
                            l_c.y -= off
                            r_c.y += off
                            create_box(l_c, Vector((size.x, side_w, d_h)), 3)
                            create_box(r_c, Vector((size.x, side_w, d_h)), 3)

                        # Frame & Door
                        fr_t, fr_d = wt * 1.5, self.wall_thick * 2
                        fr_c = eff_center.copy()
                        fr_c.z = d_h
                        if axis == "X":
                            create_box(fr_c, Vector((d_w + fr_t * 2, fr_d, fr_t)), 4)
                        else:
                            create_box(fr_c, Vector((fr_d, d_w + fr_t * 2, fr_t)), 4)
                        sl_c, sr_c = eff_center.copy(), eff_center.copy()
                        sl_c.z, sr_c.z = d_h / 2, d_h / 2
                        off_f = (d_w + fr_t) / 2
                        if axis == "X":
                            sl_c.x -= off_f
                            sr_c.x += off_f
                            create_box(sl_c, Vector((fr_t, fr_d, d_h)), 4)
                            create_box(sr_c, Vector((fr_t, fr_d, d_h)), 4)
                        else:
                            sl_c.y -= off_f
                            sr_c.y += off_f
                            create_box(sl_c, Vector((fr_d, fr_t, d_h)), 4)
                            create_box(sr_c, Vector((fr_d, fr_t, d_h)), 4)
                        leaf_c = eff_center.copy()
                        leaf_c.z = d_h / 2
                        if axis == "X":
                            create_box(leaf_c, Vector((d_w, 0.04, d_h)), 7)
                        else:
                            create_box(leaf_c, Vector((0.04, d_w, d_h)), 7)

            build_wall_panel(
                Vector((0, half_l - inset, 0)),
                Vector((w - p_sz, wt, h)),
                "X",
                self.door_wall == "FRONT",
            )
            build_wall_panel(
                Vector((0, -half_l + inset, 0)),
                Vector((w - p_sz, wt, h)),
                "X",
                self.door_wall == "BACK",
            )
            build_wall_panel(
                Vector((half_w - inset, 0, 0)),
                Vector((wt, l - p_sz, 0)),
                "Y",
                self.door_wall == "RIGHT",
                override_h=side_wall_h,
            )
            build_wall_panel(
                Vector((-half_w + inset, 0, 0)),
                Vector((wt, l - p_sz, 0)),
                "Y",
                self.door_wall == "LEFT",
                override_h=side_wall_h,
            )

            if self.has_roof:
                rise = self.roof_height
                # [ARCHITECT] Gable Triangle Base Width = Total Width + 2*Eaves
                # This ensures the triangle extends to meet the roof line on the sides
                gable_width = w + (self.roof_overhang_side * 2)
                self.create_gable(
                    bm,
                    Vector((0, half_l - inset, h)),
                    gable_width,
                    wt,
                    rise,
                    3,
                    s,
                    uv_layer,
                )
                self.create_gable(
                    bm,
                    Vector((0, -half_l + inset, h)),
                    gable_width,
                    wt,
                    rise,
                    3,
                    s,
                    uv_layer,
                )

        # 5. ROOF SYSTEM
        if self.has_roof:
            t_count = max(2, self.truss_count)
            t_size = self.truss_size
            rise = self.roof_height
            eaves = self.roof_overhang_side

            half_span = (w / 2) + eaves
            rafter_len = math.sqrt(rise**2 + half_span**2)
            pitch_angle = math.atan2(rise, half_span)

            step = l / (t_count - 1) if t_count > 1 else 0
            truss_locs = [-half_l + (i * step) for i in range(t_count)]

            for y_pos in truss_locs:
                create_box(
                    Vector((0, y_pos, h)), Vector((w + (eaves * 2), t_size, t_size)), 5
                )
                kp_h = rise - (t_size)
                if kp_h > 0:
                    create_box(
                        Vector((0, y_pos, h + (t_size / 2) + (kp_h / 2))),
                        Vector((t_size, t_size, kp_h)),
                        5,
                    )
                verts_r = create_box(
                    Vector((0, 0, 0)), Vector((rafter_len, t_size, t_size)), 5
                )
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(pitch_angle, 4, "Y"),
                    verts=verts_r,
                )
                bmesh.ops.translate(
                    bm, vec=Vector((half_span / 2, y_pos, h + rise / 2)), verts=verts_r
                )
                verts_l = create_box(
                    Vector((0, 0, 0)), Vector((rafter_len, t_size, t_size)), 5
                )
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(-pitch_angle, 4, "Y"),
                    verts=verts_l,
                )
                bmesh.ops.translate(
                    bm, vec=Vector((-half_span / 2, y_pos, h + rise / 2)), verts=verts_l
                )

            if self.has_ridge_beam:
                create_box(
                    Vector((0, 0, h + rise - (t_size / 2))),
                    Vector((t_size, l, t_size)),
                    5,
                )

            deck_thick = 0.02
            roof_len = l + (self.roof_overhang_end * 2)

            verts_d1 = create_box(
                Vector((0, 0, 0)), Vector((rafter_len, roof_len, deck_thick)), 5
            )
            bmesh.ops.rotate(
                bm,
                cent=(0, 0, 0),
                matrix=Matrix.Rotation(pitch_angle, 4, "Y"),
                verts=verts_d1,
            )
            bmesh.ops.translate(
                bm,
                vec=Vector(
                    (half_span / 2, 0, h + rise / 2 + (t_size / 2) + (deck_thick / 2))
                ),
                verts=verts_d1,
            )
            verts_d2 = create_box(
                Vector((0, 0, 0)), Vector((rafter_len, roof_len, deck_thick)), 5
            )
            bmesh.ops.rotate(
                bm,
                cent=(0, 0, 0),
                matrix=Matrix.Rotation(-pitch_angle, 4, "Y"),
                verts=verts_d2,
            )
            bmesh.ops.translate(
                bm,
                vec=Vector(
                    (-half_span / 2, 0, h + rise / 2 + (t_size / 2) + (deck_thick / 2))
                ),
                verts=verts_d2,
            )

            cover_lift = (t_size / 2) + deck_thick

            # [NEW] U-SHAPE GUTTERS (Slot 8)
            if self.has_gutters:
                g_w = 0.12
                g_h = 0.08
                g_thick = 0.005
                g_x_off = half_span + (g_w * 0.4)  # Slightly past rafter tip
                g_z = h - (g_h * 0.5)  # Hang below rafter tip

                # Right
                create_gutter_u(
                    Vector((g_x_off, 0, g_z)), g_w, roof_len, g_h, g_thick, 8
                )
                # Left
                create_gutter_u(
                    Vector((-g_x_off, 0, g_z)), g_w, roof_len, g_h, g_thick, 8
                )

            if self.roof_type == "SHEET":
                sheet_thick = 0.01
                verts_s1 = create_box(
                    Vector((0, 0, 0)), Vector((rafter_len, roof_len, sheet_thick)), 6
                )
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(pitch_angle, 4, "Y"),
                    verts=verts_s1,
                )
                bmesh.ops.translate(
                    bm,
                    vec=Vector(
                        (
                            half_span / 2,
                            0,
                            h + rise / 2 + cover_lift + (sheet_thick / 2),
                        )
                    ),
                    verts=verts_s1,
                )
                verts_s2 = create_box(
                    Vector((0, 0, 0)), Vector((rafter_len, roof_len, sheet_thick)), 6
                )
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(-pitch_angle, 4, "Y"),
                    verts=verts_s2,
                )
                bmesh.ops.translate(
                    bm,
                    vec=Vector(
                        (
                            -half_span / 2,
                            0,
                            h + rise / 2 + cover_lift + (sheet_thick / 2),
                        )
                    ),
                    verts=verts_s2,
                )

            elif self.roof_type == "SCALES":
                s_w, s_l, s_t = self.scale_size
                s_ov = self.scale_overlap
                rows_up = int(rafter_len / (s_l - s_ov))
                cols_across = int(roof_len / s_w)

                def build_scale_side(is_right_side):
                    rot_y = pitch_angle if is_right_side else -pitch_angle
                    for r in range(rows_up):
                        row_offset = (s_w / 2) if (r % 2 != 0) else 0.0
                        dist_up = r * (s_l - s_ov)
                        z_stack = r * (s_t * 0.1)
                        for c in range(cols_across + 1):
                            dist_across = (c * s_w) - (roof_len / 2) + row_offset
                            if abs(dist_across) > roof_len / 2:
                                continue
                            verts_t = create_box(
                                Vector((0, 0, 0)), Vector((s_l, s_w, s_t)), 6
                            )
                            bmesh.ops.rotate(
                                bm,
                                cent=(0, 0, 0),
                                matrix=Matrix.Rotation(rot_y, 4, "Y"),
                                verts=verts_t,
                            )
                            start_x = half_span * (1 if is_right_side else -1)
                            slope_vec = (
                                Vector(
                                    (-math.cos(pitch_angle), 0, math.sin(pitch_angle))
                                )
                                if is_right_side
                                else Vector(
                                    (math.cos(pitch_angle), 0, math.sin(pitch_angle))
                                )
                            )
                            base_pos = Vector((start_x, 0, h))
                            final_pos = base_pos + (slope_vec * dist_up)
                            final_pos.y = dist_across
                            final_pos.z += cover_lift + (s_t / 2) + z_stack
                            bmesh.ops.translate(bm, vec=final_pos, verts=verts_t)

                build_scale_side(True)
                build_scale_side(False)

        self.create_socket_face(bm, Vector((0, 0, 0)), Vector((0, 0, 1)), 9)

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

    def create_gable(
        self, bm, base_center, width, thick, height, slot_idx, uv_scale, uv_layer
    ):
        half_w = width / 2
        half_t = thick / 2
        v1 = Vector((-half_w, half_t, 0))
        v2 = Vector((half_w, half_t, 0))
        v3 = Vector((0, half_t, height))
        v4 = Vector((-half_w, -half_t, 0))
        v5 = Vector((half_w, -half_t, 0))
        v6 = Vector((0, -half_t, height))
        verts = [base_center + v for v in [v1, v2, v3, v4, v5, v6]]
        bm_verts = [bm.verts.new(v) for v in verts]
        faces = []
        faces.append(bm.faces.new((bm_verts[0], bm_verts[1], bm_verts[2])))
        faces.append(bm.faces.new((bm_verts[5], bm_verts[4], bm_verts[3])))
        faces.append(bm.faces.new((bm_verts[0], bm_verts[3], bm_verts[4], bm_verts[1])))
        faces.append(bm.faces.new((bm_verts[1], bm_verts[4], bm_verts[5], bm_verts[2])))
        faces.append(bm.faces.new((bm_verts[2], bm_verts[5], bm_verts[3], bm_verts[0])))
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        for f in faces:
            f.material_index = slot_idx
            self.apply_box_map(f, uv_layer, uv_scale)
