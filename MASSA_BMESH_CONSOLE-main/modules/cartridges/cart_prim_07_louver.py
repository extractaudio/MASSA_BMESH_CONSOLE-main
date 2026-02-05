import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, FloatVectorProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_07: Louver Vent",
    "id": "prim_07_louver",
    "icon": "MOD_ARRAY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Geometry is already volumetric
        "USE_WELD": True,  # Merge frame/backing vertices
        "FIX_DEGENERATE": True,  # Clean up potential bevel artifacts
        "ALLOW_CHAMFER": True,  # Frame edges need highlights
        "ALLOW_FUSE": False,  # Keep blades distinct for cleanliness
    },
}


class MASSA_OT_PrimLouver(Massa_OT_Base):
    bl_idname = "massa.gen_prim_07_louver"
    bl_label = "PRIM_07: Louver"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Size", default=(1.0, 1.0, 0.1), min=0.01)

    frame_width: FloatProperty(name="Frame Width", default=0.1, min=0.01)
    frame_depth: FloatProperty(name="Frame Depth", default=0.1, min=0.01)

    # --- 2. LOUVERS ---
    blade_count: IntProperty(name="Blade Count", default=8, min=1)
    blade_angle: FloatProperty(name="Blade Angle", default=35.0, min=-90.0, max=90.0)
    blade_overlap: FloatProperty(name="Overlap", default=0.02)
    blade_thick: FloatProperty(name="Blade Thick", default=0.01, min=0.001)

    # --- 3. EXTRAS ---
    add_screen: BoolProperty(name="Add Backing Screen", default=True)

    # --- 4. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            1: {"name": "Blades", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            2: {"name": "Screen", "uv": "BOX", "phys": "METAL_IRON"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)

        # UI UPDATE: Horizontal Sliders for Size
        row = col.row(align=True)
        row.prop(self, "size", index=0, text="X")
        row.prop(self, "size", index=1, text="Y")
        row.prop(self, "size", index=2, text="Z")

        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")

        layout.separator()
        layout.label(text="Louvers", icon="ALIGN_JUSTIFY")
        col = layout.column(align=True)
        col.prop(self, "blade_count")
        col.prop(self, "blade_angle")
        col.prop(self, "blade_overlap")
        col.prop(self, "blade_thick")
        layout.prop(self, "add_screen")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        sx, sy, sz = self.size
        fw = min(self.frame_width, sx / 2.1, sy / 2.1)  # Safety Clamp
        fd = self.frame_depth

        # ----------------------------------------------------------------------
        # 1. BUILD FRAME (Bridge Loops Method)
        # ----------------------------------------------------------------------

        # A. Create Outer Loop (Z=0)
        res_out = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
        verts_out = res_out["verts"]

        # Find and delete faces to create wire loop
        faces_out = list({f for v in verts_out for f in v.link_faces})
        bmesh.ops.delete(bm, geom=faces_out, context="FACES_ONLY")

        bmesh.ops.scale(bm, vec=(sx, sy, 1.0), verts=verts_out)

        # B. Create Inner Loop (Z=0)
        res_in = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
        verts_in = res_in["verts"]

        # Find and delete faces to create wire loop
        faces_in = list({f for v in verts_in for f in v.link_faces})
        bmesh.ops.delete(bm, geom=faces_in, context="FACES_ONLY")

        bmesh.ops.scale(bm, vec=(sx - (fw * 2), sy - (fw * 2), 1.0), verts=verts_in)

        # C. Bridge (Creates the Frame Face)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        edges = bm.edges[:]
        res_bridge = bmesh.ops.bridge_loops(bm, edges=edges, use_pairs=True)
        faces_front = res_bridge["faces"]

        # D. Extrude Frame Backwards (Depth)
        res_ext = bmesh.ops.extrude_face_region(bm, geom=faces_front)
        verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
        faces_side = [f for f in res_ext["geom"] if isinstance(f, bmesh.types.BMFace)]

        # Move extruded verts back
        bmesh.ops.translate(bm, vec=(0, 0, -fd), verts=verts_ext)

        # Assign Frame Material (Slot 0)
        for f in faces_front + faces_side:
            f.material_index = 0

        # Calculate Inner Dimensions for Blades
        inner_w = sx - (fw * 2)
        inner_h = sy - (fw * 2)

        # ----------------------------------------------------------------------
        # 2. BUILD BLADES (Slot 1)
        # ----------------------------------------------------------------------
        if self.blade_count > 0:
            # Spacing Logic
            step_y = inner_h / self.blade_count
            blade_h = step_y + self.blade_overlap

            # Start at top, move down
            start_y = (inner_h / 2) - (step_y / 2)

            for i in range(self.blade_count):
                # Center position for this blade
                y_pos = start_y - (i * step_y)

                # Create Blade Cube
                res_blade = bmesh.ops.create_cube(bm, size=1.0)
                verts_b = res_blade["verts"]
                faces_b = list({f for v in verts_b for f in v.link_faces})

                # Scale (X=Width, Y=Height, Z=Thick)
                bmesh.ops.scale(
                    bm, vec=(inner_w, blade_h, self.blade_thick), verts=verts_b
                )

                # Rotate (Angle)
                rot_mat = Matrix.Rotation(math.radians(self.blade_angle), 4, "X")
                bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_mat, verts=verts_b)

                # Translate (Position in Frame)
                # Z-Pos: Center of frame depth is -fd/2
                bmesh.ops.translate(bm, vec=(0, y_pos, -fd / 2), verts=verts_b)

                # Assign Material
                for f in faces_b:
                    f.material_index = 1

        # ----------------------------------------------------------------------
        # 3. BUILD SCREEN (Slot 2)
        # ----------------------------------------------------------------------
        if self.add_screen:
            res_screen = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
            verts_s = res_screen["verts"]

            # Scale to fit back of frame
            bmesh.ops.scale(bm, vec=(sx, sy, 1.0), verts=verts_s)

            # Move to very back
            bmesh.ops.translate(bm, vec=(0, 0, -fd), verts=verts_s)

            for v in verts_s:
                for f in v.link_faces:
                    f.material_index = 2

        # ----------------------------------------------------------------------
        # 4. CLEANUP & PIVOT
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Pivot Alignment: Z-Min to World Origin
        min_z = min([v.co.z for v in bm.verts])
        bmesh.ops.translate(bm, vec=(0, 0, -min_z), verts=bm.verts)

        # ----------------------------------------------------------------------
        # 5. UV MAPPING (Box Projection)
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            # Box Map Logic
            # Z-Dominant (Front/Back faces) -> Map XY
            if nz > nx and nz > ny:
                for l in f.loops:
                    u = l.vert.co.x
                    v = l.vert.co.y
                    if self.fit_uvs:
                        u = (u + sx / 2) / sx
                        v = (v + sy / 2) / sy
                    else:
                        u *= s
                        v *= s
                    l[uv_layer].uv = (u, v)

            # X-Dominant (Side Walls) -> Map YZ
            elif nx > ny and nx > nz:
                for l in f.loops:
                    u = l.vert.co.y
                    v = l.vert.co.z
                    if self.fit_uvs:
                        u = (u + sy / 2) / sy
                        v = (v - min_z) / fd  # Approx depth fit
                    else:
                        u *= s
                        v *= s
                    l[uv_layer].uv = (u, v)

            # Y-Dominant (Top/Bottom Walls) -> Map XZ
            else:
                for l in f.loops:
                    u = l.vert.co.x
                    v = l.vert.co.z
                    if self.fit_uvs:
                        u = (u + sx / 2) / sx
                        v = (v - min_z) / fd
                    else:
                        u *= s
                        v *= s
                    l[uv_layer].uv = (u, v)
