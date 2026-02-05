"""
Filename: modules/cartridges/prim_con_window.py
Content: Parametric Window Generator (Syntax Fixed)
Status: RESTORED (v14.1)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector

CARTRIDGE_META = {
    "name": "Con: Window",
    "id": "prim_con_window",
    "icon": "WINDOW",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": False,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}

WINDOW_STANDARDS = {
    "S_060_090": (0.6, 0.9),
    "S_100_120": (1.0, 1.2),
    "S_120_150": (1.2, 1.5),
    "P_200_150": (2.0, 1.5),
    "P_240_210": (2.4, 2.1),
}


def update_window_dims(self, context):
    if self.standard_type in WINDOW_STANDARDS:
        w, h = WINDOW_STANDARDS[self.standard_type]
        self.width = w
        self.height = h


class MASSA_OT_prim_con_window(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_window"
    bl_label = "Construction Window"
    bl_description = "Window with 4-Part Frame and Autonomous Slot Setup"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- PRESETS ---
    standard_type: EnumProperty(
        name="Standard",
        items=[
            ("CUSTOM", "Custom", "Manual Dimensions"),
            ("S_060_090", "Small (0.6 x 0.9m)", "Bathroom/Utility"),
            ("S_100_120", "Medium (1.0 x 1.2m)", "Bedroom Standard"),
            ("S_120_150", "Large (1.2 x 1.5m)", "Living Room"),
            ("P_200_150", "Panoramic (2.0 x 1.5m)", "Wide View"),
            ("P_240_210", "Full Height (2.4 x 2.1m)", "Door/Wall"),
        ],
        default="CUSTOM",
        update=update_window_dims,
    )

    # --- FRAME ---
    use_frame: BoolProperty(name="Show Frame", default=True)
    width: FloatProperty(name="Width", default=1.0, min=0.3, unit="LENGTH")
    height: FloatProperty(name="Height", default=1.2, min=0.3, unit="LENGTH")
    depth: FloatProperty(name="Frame Depth", default=0.15, min=0.01, unit="LENGTH")
    frame_width: FloatProperty(
        name="Frame Thickness", default=0.08, min=0.01, unit="LENGTH"
    )

    # --- FILLING ---
    cols: IntProperty(name="Columns", default=2, min=1)
    rows: IntProperty(name="Rows", default=2, min=1)
    muntin_th: FloatProperty(name="Muntin Width", default=0.02, min=0.005)
    glass_inset: FloatProperty(name="Glass Inset", default=0.01, min=0.0, unit="LENGTH")
    glass_pos: FloatProperty(
        name="Glass Position", default=0.0, min=-0.1, max=0.1, unit="LENGTH"
    )

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.prop(self, "standard_type", text="Preset")

        row = box.row()
        row.prop(self, "use_frame", icon="CHECKBOX_HLT")

        col = box.column()
        col.active = self.standard_type == "CUSTOM"
        col.prop(self, "width")
        col.prop(self, "height")

        if self.use_frame:
            col2 = box.column()
            row = col2.row()
            row.prop(self, "depth")
            row.prop(self, "frame_width")

        box = layout.box()
        box.label(text="Grid Layout", icon="GRID")
        row = box.row()
        row.prop(self, "cols")
        row.prop(self, "rows")
        box.prop(self, "muntin_th")
        box.prop(self, "glass_inset")
        box.prop(self, "glass_pos")

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "WOOD_PAINTED"},
            1: {"name": "Muntins", "uv": "BOX", "phys": "METAL_PAINTED"},
            2: {"name": "Glass", "uv": "SKIP", "phys": "SYNTH_GLASS"},
        }

    def build_shape(self, bm):
        # 1. SLOT INIT

        # 2. TAG INIT
        # Persistent layer to track material IDs through destructive ops
        tag_layer = bm.faces.layers.int.new("MAT_TAG")

        # 3. DIMS
        w, h = self.width, self.height
        fd, fw = self.depth, self.frame_width

        if self.use_frame:
            inner_w = w - (2 * fw)
            inner_h = h - (2 * fw)
        else:
            fw = 0.0
            inner_w, inner_h = w, h

        # 4. FRAME GENERATION (Stiles & Rails) - TAG 0
        if self.use_frame:

            def create_bar(size_vec, pos_vec):
                ret = bmesh.ops.create_cube(bm, size=1.0)
                verts = ret["verts"]
                bmesh.ops.scale(bm, vec=size_vec, verts=verts)
                bmesh.ops.translate(bm, verts=verts, vec=pos_vec)

                # Stamp Tag 0
                new_faces = [f for f in bm.faces if f.verts[0] in verts]
                for f in new_faces:
                    f[tag_layer] = 0

            # Stiles (Vertical)
            create_bar((fw, fd, h), (-w / 2 + fw / 2, 0, 0))
            create_bar((fw, fd, h), (w / 2 - fw / 2, 0, 0))
            # Rails (Horizontal)
            if w > 2 * fw:
                create_bar((w - 2 * fw, fd, fw), (0, 0, h / 2 - fw / 2))
            if w > 2 * fw:
                create_bar((w - 2 * fw, fd, fw), (0, 0, -h / 2 + fw / 2))

        # 5. FILLING GENERATION - TAG 1 & 2
        if inner_w > 0.01 and inner_h > 0.01:
            # Base Plane
            v1 = bm.verts.new((-inner_w / 2, 0, -inner_h / 2))
            v2 = bm.verts.new((inner_w / 2, 0, -inner_h / 2))
            v3 = bm.verts.new((inner_w / 2, 0, inner_h / 2))
            v4 = bm.verts.new((-inner_w / 2, 0, inner_h / 2))
            fill_face = bm.faces.new((v1, v2, v3, v4))
            fill_face.normal_update()

            # Stamp Tag 1 (Muntin Base)
            fill_face[tag_layer] = 1

            # Move
            verts_fill = [v1, v2, v3, v4]
            bmesh.ops.translate(bm, verts=verts_fill, vec=(0, self.glass_pos, 0))

            # --- BISECT ---
            def get_geom_by_tag(t):
                # Returns unique geom list for tag t
                fs = [f for f in bm.faces if f[tag_layer] == t]
                return list(
                    set(
                        fs
                        + [e for f in fs for e in f.edges]
                        + [v for f in fs for v in f.verts]
                    )
                )

            if self.cols > 1:
                step = inner_w / self.cols
                start = -inner_w / 2
                for i in range(1, self.cols):
                    # Flattened call to prevent syntax errors
                    bmesh.ops.bisect_plane(
                        bm,
                        geom=get_geom_by_tag(1),
                        plane_co=(start + i * step, 0, 0),
                        plane_no=(1, 0, 0),
                    )

            if self.rows > 1:
                step = inner_h / self.rows
                start = -inner_h / 2
                for i in range(1, self.rows):
                    bmesh.ops.bisect_plane(
                        bm,
                        geom=get_geom_by_tag(1),
                        plane_co=(0, 0, start + i * step),
                        plane_no=(0, 0, 1),
                    )

            # --- INSET (Create Glass) ---
            panes = [f for f in bm.faces if f[tag_layer] == 1]
            if panes:
                ret_munt = bmesh.ops.inset_individual(
                    bm, faces=panes, thickness=self.muntin_th / 2, use_even_offset=True
                )

                # Stamp Tag 2 (Glass) on Inner Faces
                for f in ret_munt["faces"]:
                    f[tag_layer] = 2

                # --- THICKEN MUNTINS (Tag 1) ---
                muntin_faces = [f for f in bm.faces if f[tag_layer] == 1]
                if muntin_faces:
                    ret_ext = bmesh.ops.extrude_face_region(bm, geom=muntin_faces)
                    # Enforce Tag 1 on new side faces
                    for ele in ret_ext["geom"]:
                        if isinstance(ele, bmesh.types.BMFace):
                            ele[tag_layer] = 1
                    # Move
                    verts_ext = [
                        v for v in ret_ext["geom"] if isinstance(v, bmesh.types.BMVert)
                    ]
                    bmesh.ops.translate(bm, verts=verts_ext, vec=(0, self.muntin_th, 0))

                # --- RECESS GLASS (Tag 2) ---
                glass_faces = [f for f in bm.faces if f[tag_layer] == 2]
                if glass_faces and self.glass_inset > 0:
                    bmesh.ops.inset_region(
                        bm,
                        faces=glass_faces,
                        thickness=0.0,
                        depth=-self.glass_inset,
                        use_even_offset=True,
                    )

        # 6. ASSIGNMENT
        # Map Tags to Material Indices
        for f in bm.faces:
            tag = f[tag_layer]
            if tag == 0:
                f.material_index = 0
            elif tag == 1:
                f.material_index = 1
            elif tag == 2:
                f.material_index = 2

        # 7. EDGE ROLES (Consolidated)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1
            elif len(e.link_faces) == 2:
                if e.calc_face_angle() > 0.5:
                    e[edge_slots] = 2
