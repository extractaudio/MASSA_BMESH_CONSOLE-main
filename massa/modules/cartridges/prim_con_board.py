import bpy
import bmesh
import math
from bpy.props import FloatProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector

# ==============================================================================
# MASSA CARTRIDGE: CONSTRUCTION BOARD (QUAD CAPS)
# ID: prim_con_board
# ==============================================================================

CARTRIDGE_META = {
    "name": "Con: Board",
    "id": "prim_con_board",
    "icon": "MESH_CUBE",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_board(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_board"
    bl_label = "Construction Board"
    bl_description = "Lumber profile with Full Quad Grid Topology"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMENSIONS ---
    length: FloatProperty(name="Length", default=2.4, min=0.1, unit="LENGTH")
    width: FloatProperty(name="Width", default=0.14, min=0.01, unit="LENGTH")
    thickness: FloatProperty(name="Thickness", default=0.038, min=0.002, unit="LENGTH")

    # --- DETAILING ---
    chamfer: FloatProperty(name="Chamfer", default=0.003, min=0.0, unit="LENGTH")
    cup_warp: FloatProperty(
        name="Cupping",
        default=0.002,
        min=0.0,
        max=0.05,
        description="Moisture warp factor",
    )

    # --- TOPOLOGY ---
    open_caps: BoolProperty(
        name="Open Caps", default=False, description="Remove end faces"
    )

    # Grid Segmentation
    seg_x: IntProperty(
        name="Seg X", default=1, min=1, description="Width Cuts (Quality)"
    )
    seg_y: IntProperty(name="Seg Y", default=4, min=1, description="Length Cuts")
    seg_z: IntProperty(name="Seg Z", default=1, min=1, description="Thickness Cuts")

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon="DRIVER_DISTANCE")
        box.prop(self, "length")
        box.prop(self, "width")
        box.prop(self, "thickness")

        box = layout.box()
        box.label(text="Detailing", icon="MOD_BEVEL")
        box.prop(self, "chamfer")
        box.prop(self, "cup_warp")

        row = box.row()
        row.prop(self, "open_caps")

        box = layout.box()
        box.label(text="Grid Topology", icon="MESH_GRID")
        row = box.row(align=True)
        row.prop(self, "seg_x", text="X")
        row.prop(self, "seg_y", text="Y")
        row.prop(self, "seg_z", text="Z")

    def get_slot_meta(self):
        #
        return {
            0: {"name": "Wood_Face", "uv": "TUBE_Y", "phys": "WOOD_PINE"},
            1: {"name": "Wood_End", "uv": "BOX", "phys": "WOOD_ROUGH"},
            3: {"name": "Socket_Face", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def build_shape(self, bm):
        # 1. PARAMETER SETUP
        w = self.width / 2
        t = self.thickness / 2
        c = min(self.chamfer, min(w, t) * 0.95)

        # 2. GRID GENERATION (Volumetric Grid)
        # We build a 2D array of vertices: grid[x_index][z_index]
        grid_verts = []

        res_x = self.seg_x
        res_z = self.seg_z

        for ix in range(res_x + 1):
            col_verts = []
            factor_x = ix / res_x

            # X Math (Width)
            raw_x = -w + (self.width * factor_x)
            final_x = raw_x

            # Chamfer Logic: Retract X only at the very edges of the board
            # Note: We apply this to the whole column so the side wall remains straight
            if ix == 0:
                final_x += c
            if ix == res_x:
                final_x -= c

            # Cupping Math (Z-Offset based on X)
            norm_x = (factor_x * 2.0) - 1.0  # -1.0 to 1.0
            z_warp = (norm_x * norm_x) * self.cup_warp

            for iz in range(res_z + 1):
                factor_z = iz / res_z

                # Z Math (Thickness)
                # Linear interpolate from bottom (-t) to top (t)
                base_z = -t + (self.thickness * factor_z)

                # Apply Warp to ALL vertices (Volumetric deformation)
                final_z = base_z + z_warp

                v = bm.verts.new((final_x, 0, final_z))
                col_verts.append(v)

            grid_verts.append(col_verts)

        # 3. SKINNING (Create Quad Faces for Start Cap)
        # These faces form the "End Grain" at Y=0
        start_cap_faces = []

        for ix in range(res_x):
            for iz in range(res_z):
                # 4 corners of the quad
                v1 = grid_verts[ix][iz]
                v2 = grid_verts[ix + 1][iz]
                v3 = grid_verts[ix + 1][iz + 1]
                v4 = grid_verts[ix][iz + 1]

                f = bm.faces.new((v1, v2, v3, v4))
                f.material_index = 1  # Wood_End
                start_cap_faces.append(f)

        # 4. EXTRUDE (Solidify along Length)
        # We extrude the entire grid of faces we just made
        ret = bmesh.ops.extrude_face_region(bm, geom=start_cap_faces)

        geom_generated = ret["geom"]
        verts_extruded = [
            v for v in geom_generated if isinstance(v, bmesh.types.BMVert)
        ]

        # Extrude Y+
        bmesh.ops.translate(bm, verts=verts_extruded, vec=(0, self.length, 0))

        # 5. Y-SEGMENTATION (Length Cuts)
        # Since we generated X and Z topology natively, we only need to slice Y.
        if self.seg_y > 1:
            seg_len = self.length / self.seg_y
            for i in range(1, self.seg_y):
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(0, i * seg_len, 0),
                    plane_no=(0, 1, 0),
                )

        # 6. RECALCULATE NORMALS
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 7. MATERIAL & SOCKET ASSIGNMENT
        faces_to_delete = []

        for f in bm.faces:
            # A. END CAPS (Y-Aligned)
            if abs(f.normal.y) > 0.8:
                if self.open_caps:
                    faces_to_delete.append(f)
                else:
                    f.material_index = 1  # Wood_End

            # B. SOCKET (Bottom Face)
            # Strict check: Z- facing AND essentially flat (X/Y normals are low)
            elif f.normal.z < -0.5:
                f.material_index = 3  # Socket_Face

            # C. EVERYTHING ELSE (Top/Sides)
            else:
                f.material_index = 0  # Wood_Face

        if faces_to_delete:
            bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")

        # 8. EDGE ROLE PROTOCOL
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            # A. PERIMETER/SEAM CHECK
            is_seam = False
            if e.is_boundary:
                is_seam = True
            elif len(e.link_faces) == 2:
                m1 = e.link_faces[0].material_index
                m2 = e.link_faces[1].material_index
                # Seam if material boundary (Caps are already material 1)
                if m1 != m2:
                    is_seam = True
            
            # B. LONGITUDINAL EDGES (1 Seam, 3 Sharp)
            vec = e.verts[1].co - e.verts[0].co
            vec.normalize()
            if abs(vec.y) > 0.9: # Y-Aligned
                mid_x = (e.verts[0].co.x + e.verts[1].co.x) * 0.5
                mid_z = (e.verts[0].co.z + e.verts[1].co.z) * 0.5
                
                # Check for Outer Corners
                # If we are near the bounding box extent
                is_corner = False
                if abs(mid_x) > (self.width/2 * 0.9) and abs(mid_z) > (self.thickness/2 * 0.9):
                     is_corner = True
                     
                if is_corner:
                    # TOP-RIGHT (+X, +Z) -> SEAM
                    if mid_x > 0 and mid_z > 0:
                        is_seam = True
                    # OTHERS -> SHARP
                    else:
                        e[edge_slots] = 2 # Sharp

            if is_seam:
                e.seam = True
                e[edge_slots] = 1  # Slot 1: Perimeter

            # C. CONTOUR/SHARP CHECK
            elif e.calc_face_angle() > math.radians(40):
                e[edge_slots] = 2  # Slot 2: Sharp

        # 9. REALTIME UNWRAP (Roundtrip)
        headless_classic_unwrap(bm)


def headless_classic_unwrap(bm):
    try:
        me = bpy.data.meshes.new("_temp_unwrap_mesh")
        bm.to_mesh(me)
        obj = bpy.data.objects.new("_temp_unwrap_obj", me)
        col = bpy.data.collections.get("Collection")
        if not col:
            col = bpy.data.collections.new("Collection")
            bpy.context.scene.collection.children.link(col)
        col.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
        bpy.ops.object.mode_set(mode='OBJECT')
        bm.clear()
        bm.from_mesh(me)
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(me, do_unlink=True)
    except Exception as e:
        print(f"UNWRAP ERROR: {e}")
