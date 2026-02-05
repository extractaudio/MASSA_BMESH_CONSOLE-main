import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Quaternion
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    FloatVectorProperty,
    EnumProperty,
)
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "Universal Structure",
    "id": "building_assembly_3",
    "icon": "MOD_BUILD",
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


class MASSA_OT_BuildingAssembly3(Massa_OT_Base):
    bl_idname = "massa.gen_building_assembly_3"
    bl_label = "Universal Structure"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. GLOBAL DIMS ---
    length: FloatProperty(name="Length (Y)", default=10.0, min=1.0, unit="LENGTH")
    width: FloatProperty(name="Width (X)", default=6.0, min=1.0, unit="LENGTH")
    height: FloatProperty(name="Height (Z)", default=4.0, min=2.0, unit="LENGTH")

    # --- 2. CATEGORY ---
    category: EnumProperty(
        name="Material System",
        items=[
            ("STEEL", "Steel", "Industrial Frames"),
            ("WOOD", "Wood", "Stick & Timber Framing"),
            ("CONCRETE", "Concrete", "Brutalist & Foundations"),
        ],
        default="STEEL",
    )

    # --- 3. SUB-STYLES ---
    style_steel: EnumProperty(
        name="Steel Style",
        items=[
            ("PORTAL_FRAME", "Portal Frame", "Warehouse Style"),
            ("GRID_FRAME", "Grid Frame", "Multi-story Grid"),
            ("TRUSS_SHED", "Truss Shed", "Lightweight"),
            ("IRON_CLAD", "Iron Clad", "Bunker/Fortress"),
        ],
        default="PORTAL_FRAME",
    )
    style_wood: EnumProperty(
        name="Wood Style",
        items=[
            ("STICK_FRAME", "Stick Frame", "Residential Studs"),
            ("TIMBER_FRAME", "Timber Frame", "Heavy Post & Beam"),
            ("ROOF_TRUSS", "Roof Trusses", "Array of Trusses"),
            ("JAPANESE", "Japanese", "Traditional Joinery"),
        ],
        default="STICK_FRAME",
    )
    style_concrete: EnumProperty(
        name="Concrete Style",
        items=[
            ("COLUMN_SLAB", "Column & Slab", "Modernist Grid"),
            ("TILT_WALL", "Tilt Wall", "Industrial Panels"),
            ("BRUTALIST_A", "Brutalist Block", "Soviet Style A"),
            ("BRUTALIST_B", "Inv. Fortress", "Soviet Style B"),
            ("FOUNDATION", "Foundations", "Pads & Footings"),
        ],
        default="COLUMN_SLAB",
    )

    # --- 4. PARAMETERS ---
    # Common
    bay_spacing: FloatProperty(name="Bay Spacing", default=4.0, min=0.5, unit="LENGTH")
    levels: IntProperty(name="Levels", default=1, min=1)

    # Steel
    roof_pitch: FloatProperty(name="Pitch (Deg)", default=15.0, min=0.0, max=60.0)
    overhang: FloatProperty(name="Overhang", default=0.5, min=0.0, unit="LENGTH")
    purlin_spacing: FloatProperty(
        name="Purlin Gap", default=1.2, min=0.1, unit="LENGTH"
    )

    # Wood
    stud_spacing: FloatProperty(name="Stud Gap", default=0.6, min=0.2, unit="LENGTH")
    has_nogging: BoolProperty(name="Nogging", default=True)
    has_sheathing: BoolProperty(name="Sheathing", default=False)

    # Concrete
    col_size: FloatProperty(name="Col Size", default=0.4, min=0.1, unit="LENGTH")
    slab_thick: FloatProperty(name="Slab Thick", default=0.2, min=0.05, unit="LENGTH")

    # Japanese
    post_dia: FloatProperty(name="Post Dia", default=0.2, min=0.1, unit="LENGTH")
    raised_h: FloatProperty(name="Raised Floor", default=0.6, min=0.0, unit="LENGTH")
    roof_curve: FloatProperty(name="Roof Curve", default=0.5, min=0.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Primary Structure", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Secondary Structure", "uv": "BOX", "phys": "WOOD_PINE"},
            2: {"name": "Cladding / Roof", "uv": "BOX", "phys": "METAL_RUST"},
            3: {"name": "Foundation / Floor", "uv": "BOX", "phys": "CONCRETE_RAW"},
            9: {"name": "Anchors", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="System Configuration")
        col.prop(self, "category", text="")

        # Sub-Style Selector
        if self.category == "STEEL":
            col.prop(self, "style_steel", text="")
        elif self.category == "WOOD":
            col.prop(self, "style_wood", text="")
        elif self.category == "CONCRETE":
            col.prop(self, "style_concrete", text="")

        col.separator()
        col.label(text="Dimensions")
        row = col.row(align=True)
        row.prop(self, "width", text="W")
        row.prop(self, "length", text="L")
        row.prop(self, "height", text="H")

        # Contextual UI
        box = layout.box()
        box.label(text="Parameters", icon="PREFERENCES")

        if self.category == "STEEL":
            box.prop(self, "bay_spacing")
            if self.style_steel == "PORTAL_FRAME":
                row = box.row(align=True)
                row.prop(self, "roof_pitch")
                row.prop(self, "overhang")
                box.prop(self, "purlin_spacing")

        elif self.category == "WOOD":
            if self.style_wood == "STICK_FRAME":
                box.prop(self, "stud_spacing")
                row = box.row(align=True)
                row.prop(self, "has_nogging")
                row.prop(self, "has_sheathing")
            elif self.style_wood == "JAPANESE":
                box.prop(self, "post_dia")
                box.prop(self, "raised_h")
                box.prop(self, "roof_curve")
            elif self.style_wood == "TIMBER_FRAME":
                box.prop(self, "bay_spacing")

        elif self.category == "CONCRETE":
            box.prop(self, "levels")
            if self.style_concrete == "COLUMN_SLAB":
                box.prop(self, "bay_spacing")
                row = box.row(align=True)
                row.prop(self, "col_size")
                row.prop(self, "slab_thick")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, l, h = self.width, self.length, self.height
        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        # --- HELPER: CREATE BOX ---
        def create_box(center, size, slot, rot_euler=None):
            res = bmesh.ops.create_cube(bm, size=1.0)
            verts = res["verts"]
            bmesh.ops.scale(bm, vec=size, verts=verts)
            if rot_euler:
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(rot_euler.x, 4, "X"),
                    verts=verts,
                )
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(rot_euler.y, 4, "Y"),
                    verts=verts,
                )
                bmesh.ops.rotate(
                    bm,
                    cent=(0, 0, 0),
                    matrix=Matrix.Rotation(rot_euler.z, 4, "Z"),
                    verts=verts,
                )
            bmesh.ops.translate(bm, vec=center, verts=verts)
            for f in list({f for v in verts for f in v.link_faces}):
                f.material_index = slot
                self.apply_box_map(f, uv_layer, s)
            return verts

        # =========================
        # LOGIC: STEEL SYSTEMS
        # =========================
        if self.category == "STEEL":
            if self.style_steel == "PORTAL_FRAME":
                bay = self.bay_spacing
                pitch = math.radians(self.roof_pitch)
                num_bays = max(1, int(l / bay))

                # Geometry Calcs
                rise = math.tan(pitch) * (w / 2)
                rafter_len = (w / 2) / math.cos(pitch) + self.overhang

                # Generate Bays
                for i in range(num_bays + 1):
                    y_pos = (-l / 2) + (i * bay)

                    # Columns
                    for x_dir in [-1, 1]:
                        # Column
                        create_box(
                            Vector(((w / 2) * x_dir, y_pos, h / 2)),
                            Vector((0.3, 0.3, h)),
                            0,  # Steel
                        )
                        # Haunch (Knee)
                        create_box(
                            Vector(((w / 2 - 0.4) * x_dir, y_pos, h - 0.2)),
                            Vector((0.8, 0.25, 0.6)),
                            0,
                        )

                    # Rafters
                    for x_dir in [-1, 1]:
                        # Center pos calc
                        c_x = ((w / 2) + (self.overhang * 0.5)) * 0.5 * x_dir
                        c_z = (
                            h + (rise * 0.5) - (math.tan(pitch) * self.overhang * 0.25)
                        )

                        rot_y = pitch * x_dir if x_dir == 1 else -pitch

                        create_box(
                            Vector((c_x, y_pos, c_z)),
                            Vector((rafter_len, 0.2, 0.4)),
                            0,
                            rot_euler=Vector((0, rot_y, 0)),
                        )

                # Purlins
                if self.purlin_spacing > 0.1:
                    p_count = int(rafter_len / self.purlin_spacing)
                    for x_dir in [-1, 1]:
                        for p in range(p_count + 1):
                            d = p * self.purlin_spacing

                            # Trig to place purlins on rafter slope
                            start_x_abs = (w / 2) + self.overhang
                            start_z = h - (math.tan(pitch) * self.overhang)

                            dx = d * math.cos(pitch)
                            dz = d * math.sin(pitch)

                            px = (start_x_abs - dx) * x_dir
                            pz = start_z + dz

                            # Skip if crossing center too much
                            if (x_dir == 1 and px < -0.1) or (x_dir == -1 and px > 0.1):
                                continue

                            rot_y = pitch * x_dir if x_dir == 1 else -pitch

                            create_box(
                                Vector((px, 0, pz + 0.2)),
                                Vector((0.1, l, 0.05)),
                                1,  # Secondary Steel
                                rot_euler=Vector((0, rot_y, 0)),
                            )

            elif self.style_steel == "IRON_CLAD":
                # Bunker Frame logic
                thick = 0.2
                count = int(l / self.bay_spacing) + 1

                # Frames
                for i in range(count):
                    x = -l / 2 + (i * (l / max(1, count - 1)))
                    # Floor/Ceil Beams
                    create_box(
                        Vector((x, 0, thick / 2)), Vector((thick * 2, w, thick)), 0
                    )
                    create_box(
                        Vector((x, 0, h - thick / 2)), Vector((thick * 2, w, thick)), 0
                    )
                    # Walls
                    for y_dir in [-1, 1]:
                        create_box(
                            Vector((x, (w / 2 - thick) * y_dir, h / 2)),
                            Vector((thick * 2, thick * 1.5, h)),
                            0,
                        )
                        # Gusset
                        py = (w / 2 - w * 0.1) * y_dir
                        pz = h - w * 0.1
                        create_box(
                            Vector((x, py, pz)), Vector((thick, w * 0.2, w * 0.2)), 0
                        )

                # Stringers
                s_count = 3
                for s in range(s_count):
                    z_pos = (h * 0.2) + (s * (h * 0.6 / (s_count - 1)))
                    for y_dir in [-1, 1]:
                        create_box(
                            Vector((0, (w / 2 - thick * 1.5) * y_dir, z_pos)),
                            Vector((l, thick / 2, thick)),
                            1,
                        )

        # =========================
        # LOGIC: WOOD SYSTEMS
        # =========================
        elif self.category == "WOOD":
            if self.style_wood == "STICK_FRAME":
                sw = 0.04
                sd = 0.09
                gap = self.stud_spacing

                def build_wall(len_val, ht, axis, offset):
                    # Plates
                    plate_size = (
                        Vector((len_val, sd, sw))
                        if axis == "X"
                        else Vector((sd, len_val, sw))
                    )
                    create_box(offset + Vector((0, 0, sw / 2)), plate_size, 1)  # Bottom
                    create_box(
                        offset + Vector((0, 0, ht - sw * 1.5)), plate_size, 1
                    )  # Top 1
                    create_box(
                        offset + Vector((0, 0, ht - sw * 0.5)), plate_size, 1
                    )  # Top 2

                    # Studs
                    stud_h = ht - (sw * 3)
                    count = int(len_val / gap)
                    start = -len_val / 2 + sw / 2

                    for i in range(count + 1):
                        pos = start + (i * gap)
                        if pos > len_val / 2:
                            pos = len_val / 2 - sw / 2

                        loc = offset.copy()
                        loc.z = ht / 2 - sw / 2
                        if axis == "X":
                            loc.x += pos
                        else:
                            loc.y += pos

                        s_size = (
                            Vector((sw, sd, stud_h))
                            if axis == "X"
                            else Vector((sd, sw, stud_h))
                        )
                        create_box(loc, s_size, 1)

                        # Nogging
                        if self.has_nogging and i < count:
                            nog_x = pos + (gap / 2)
                            if nog_x + gap / 2 <= len_val / 2:
                                n_loc = offset.copy()
                                n_loc.z = ht / 2 + (0.05 if i % 2 == 0 else -0.05)
                                if axis == "X":
                                    n_loc.x += nog_x
                                else:
                                    n_loc.y += nog_x

                                n_size = (
                                    Vector((gap - sw, sd, sw))
                                    if axis == "X"
                                    else Vector((sd, gap - sw, sw))
                                )
                                create_box(n_loc, n_size, 1)

                # Build 4 Walls
                # Front/Back (Length)
                build_wall(l, h, "X", Vector((0, -w / 2 + sd / 2, 0)))
                build_wall(l, h, "X", Vector((0, w / 2 - sd / 2, 0)))
                # Sides (Width - overlap)
                build_wall(w - sd * 2, h, "Y", Vector((-l / 2 + sd / 2, 0, 0)))
                build_wall(w - sd * 2, h, "Y", Vector((l / 2 - sd / 2, 0, 0)))

            elif self.style_wood == "JAPANESE":
                dia = self.post_dia
                bay = 1.82  # Ken
                cols_x = max(2, int(l / bay) + 1)
                cols_y = max(2, int(w / bay) + 1)
                real_bay_x = l / (cols_x - 1)
                real_bay_y = w / (cols_y - 1)

                rh = self.raised_h

                for i in range(cols_x):
                    for j in range(cols_y):
                        cx = -l / 2 + (i * real_bay_x)
                        cy = -w / 2 + (j * real_bay_y)

                        # Perimeter Only
                        if i == 0 or i == cols_x - 1 or j == 0 or j == cols_y - 1:
                            # Stone
                            create_box(
                                Vector((cx, cy, 0.15)),
                                Vector((dia * 1.2, dia * 1.2, 0.3)),
                                3,
                            )
                            # Post
                            ph = h - rh
                            create_box(
                                Vector((cx, cy, rh + ph / 2)), Vector((dia, dia, ph)), 0
                            )
                            # Bracket (Simplification)
                            br_z = h + dia * 0.2
                            create_box(
                                Vector((cx, cy, br_z)),
                                Vector((dia * 1.2, dia * 1.2, dia * 0.4)),
                                0,
                            )

                # Beams
                # X-Runners
                for y_pos in [-w / 2, w / 2]:
                    create_box(
                        Vector((0, y_pos, h + dia * 0.6)),
                        Vector((l + 0.4, dia, dia * 1.2)),
                        1,
                    )
                # Y-Runners
                for x_pos in [-l / 2, l / 2]:
                    create_box(
                        Vector((x_pos, 0, h + dia * 0.6)),
                        Vector((dia, w + 0.4, dia * 1.2)),
                        1,
                    )

        # =========================
        # LOGIC: CONCRETE SYSTEMS
        # =========================
        elif self.category == "CONCRETE":
            if self.style_concrete == "COLUMN_SLAB":
                bay = self.bay_spacing
                cols_x = int(l / bay) + 1
                cols_y = int(w / bay) + 1
                level_h = h / self.levels
                st = self.slab_thick
                cs = self.col_size

                for lvl in range(self.levels):
                    z_floor = lvl * level_h
                    z_ceil = (lvl + 1) * level_h

                    # Slab
                    create_box(Vector((0, 0, z_ceil - st / 2)), Vector((l, w, st)), 3)

                    # Columns
                    start_x = -l / 2
                    start_y = -w / 2

                    for i in range(cols_x):
                        for j in range(cols_y):
                            cx = start_x + (i * (l / max(1, cols_x - 1)))
                            cy = start_y + (j * (w / max(1, cols_y - 1)))
                            col_h = level_h - st
                            create_box(
                                Vector((cx, cy, z_floor + col_h / 2)),
                                Vector((cs, cs, col_h)),
                                3,
                            )

            elif self.style_concrete == "BRUTALIST_A":
                # Soviet Block
                level_h = h / self.levels
                mass = 1.0  # scale factor

                for lvl in range(self.levels + 1):
                    z = lvl * level_h
                    # Heavy Slab
                    create_box(Vector((0, 0, z)), Vector((l + mass, w + mass, 0.4)), 3)

                # Vertical Piers
                rib_count = 6
                bay_x = l / (rib_count - 1)
                for i in range(rib_count):
                    x = -l / 2 + (i * bay_x)
                    pier_d = mass * 1.2
                    # Front
                    create_box(
                        Vector((x, -w / 2 - pier_d / 2, h / 2)),
                        Vector((0.6, pier_d, h)),
                        3,
                    )
                    # Back
                    create_box(
                        Vector((x, w / 2 + pier_d / 2, h / 2)),
                        Vector((0.6, pier_d, h)),
                        3,
                    )

                # Recessed Wall
                create_box(
                    Vector((0, -w / 2 + 0.5, h / 2)), Vector((l, 0.2, h)), 2
                )  # Glass/Infill
                create_box(Vector((0, w / 2 - 0.5, h / 2)), Vector((l, 0.2, h)), 2)

        # Final Cleanup
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
