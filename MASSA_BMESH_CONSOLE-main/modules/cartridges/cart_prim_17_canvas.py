import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, FloatVectorProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_17: Sagging Canvas",
    "id": "prim_17_canvas",
    "icon": "PHYSICS",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": True,  # Essential for cloth thickness
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,  # Cloth doesn't need chamfers
        "PROTECT_NORMALS": False,  # Allow smooth shading
    },
}


class MASSA_OT_PrimCanvas(Massa_OT_Base):
    bl_idname = "massa.gen_prim_17_canvas"
    bl_label = "PRIM_17: Canvas"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Size (XY)", default=(2.0, 2.0, 0.0), min=0.1)
    res: IntProperty(name="Grid Density", default=32, min=4, max=128)
    sag_amount: FloatProperty(name="Gravity Sag", default=0.5, min=-5.0, max=5.0)

    # --- 2. CONSTRAINTS ---
    pin_tl: BoolProperty(name="Pin Top-Left", default=True)
    pin_tr: BoolProperty(name="Pin Top-Right", default=True)
    pin_bl: BoolProperty(name="Pin Bot-Left", default=True)
    pin_br: BoolProperty(name="Pin Bot-Right", default=True)

    # --- 3. HARDWARE ---
    grommet_radius: FloatProperty(name="Grommet Size", default=0.03, min=0.001)

    # --- 4. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=True)

    def get_slot_meta(self):
        """
        V2 Standard:
        Slot 0 (Fabric) -> SKIP (Manual Topological Mapping).
        Slot 1 (Hardware) -> BOX (Grommets).
        """
        return {
            0: {"name": "Fabric", "uv": "SKIP", "phys": "FABRIC_CANVAS"},
            1: {"name": "Grommets", "uv": "BOX", "phys": "METAL_BRASS"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "size", index=0, text="X")
        row.prop(self, "size", index=1, text="Y")
        col.prop(self, "res")

        layout.separator()
        layout.label(text="Physics", icon="MOD_PHYSICS")
        layout.prop(self, "sag_amount")

        layout.separator()
        layout.label(text="Pin Constraints", icon="PINNED")
        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "pin_tl", text="TL", toggle=True)
        row.prop(self, "pin_tr", text="TR", toggle=True)
        row = box.row(align=True)
        row.prop(self, "pin_bl", text="BL", toggle=True)
        row.prop(self, "pin_br", text="BR", toggle=True)

        layout.separator()
        layout.label(text="Hardware", icon="MESH_TORUS")
        layout.prop(self, "grommet_radius")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        # FIXED: Unpack directly to avoid bpy_prop_array attribute error
        w, d, _ = self.size
        res_x = self.res
        res_y = self.res

        # 1. CREATE GRID
        # ----------------------------------------------------------------------
        # bmesh.ops.create_grid creates a grid centered at 0,0 ranging -0.5 to 0.5
        ret = bmesh.ops.create_grid(
            bm,
            x_segments=res_x,
            y_segments=res_y,
            size=1.0,  # Base unit size, we scale later
        )
        verts = ret["verts"]

        # Scale to dimensions
        bmesh.ops.scale(bm, vec=(w, d, 1.0), verts=verts)

        # 2. DEFINE PIN LOCATIONS
        # ----------------------------------------------------------------------
        # Coordinates relative to center (0,0)
        hw, hd = w / 2, d / 2

        pins = []
        if self.pin_tl:
            pins.append(Vector((-hw, hd, 0)))  # Top Left
        if self.pin_tr:
            pins.append(Vector((hw, hd, 0)))  # Top Right
        if self.pin_bl:
            pins.append(Vector((-hw, -hd, 0)))  # Bot Left
        if self.pin_br:
            pins.append(Vector((hw, -hd, 0)))  # Bot Right

        # Fallback: if no pins, pin the center (tent pole style) or corners?
        if not pins:
            pins.append(Vector((-hw, hd, 0)))
            pins.append(Vector((hw, hd, 0)))

        # 3. APPLY UVs (Topological)
        # ----------------------------------------------------------------------
        # We calculate UVs *before* deformation so the texture follows the grid logic
        uv_layer = bm.loops.layers.uv.verify()

        s_u = 1.0 if self.fit_uvs else (self.uv_scale * w / 2.0)
        s_v = 1.0 if self.fit_uvs else (self.uv_scale * d / 2.0)

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            f.material_index = 0
            f.smooth = True
            for l in f.loops:
                # Map range -w/2..w/2 to 0..1
                u = (l.vert.co.x + hw) / w
                v = (l.vert.co.y + hd) / d

                # Apply scaling logic
                if not self.fit_uvs:
                    # Center the scaling
                    u = (u - 0.5) * self.uv_scale + 0.5
                    v = (v - 0.5) * self.uv_scale + 0.5

                l[uv_layer].uv = (u, v)

        # 4. APPLY SAG DEFORMATION
        # ----------------------------------------------------------------------
        # Algorithm: Z -= Sag * (min_dist_to_any_pin / max_possible_dist)^Power

        max_dist_ref = math.hypot(w, d)  # Diagonal

        for v in verts:
            min_d = 100000.0

            # Find distance to closest active pin
            for p in pins:
                dist = (v.co - p).length
                if dist < min_d:
                    min_d = dist

            # Normalize influence
            ratio = min_d / max_dist_ref

            # Apply Curve (Power 1.8 gives a nice heavy cloth hang)
            # We offset Z downwards
            drop = self.sag_amount * math.pow(ratio, 1.8) * 5.0
            v.co.z -= drop

        # 5. GENERATE GROMMETS (Hardware)
        # ----------------------------------------------------------------------
        # Create a small torus/tube at each pin location
        if self.grommet_radius > 0.001:
            g_rad = self.grommet_radius
            g_thick = g_rad * 0.2

            for p in pins:
                mat_loc = Matrix.Translation(p)

                # Create Grommet Geometry
                res_g = bmesh.ops.create_cone(
                    bm,
                    cap_ends=False,  # Open tube
                    cap_tris=False,
                    segments=12,
                    radius1=g_rad,
                    radius2=g_rad,
                    depth=g_thick,
                    matrix=mat_loc,
                )

                # Solidify the grommet (Fake it with a second inner shell?
                # Or just let the Solidify modifier handle the whole object?)
                # Since 'ALLOW_SOLIDIFY' is True, the whole canvas gets thickness.
                # The grommet should be slightly thicker to stand out.
                # Let's simple Scale the grommet faces along Z to 'pop' out.

                # Use vertices key from result safely
                g_verts = res_g.get("verts", [])
                # Scale Z by 3.0 to make it thicker than the canvas
                bmesh.ops.scale(bm, vec=(1, 1, 3.0), verts=g_verts, space=mat_loc)

                # Assign Material
                # Derive faces from verts to be safe
                g_faces = list({f for v in g_verts for f in v.link_faces})
                for f in g_faces:
                    f.material_index = 1  # Hardware
                    f.smooth = True

        # 6. CLEANUP
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
