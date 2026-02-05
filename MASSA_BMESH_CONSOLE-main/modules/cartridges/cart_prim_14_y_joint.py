import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Quaternion
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_14: Hard-Surface Y-Joint",
    "id": "prim_14_y_joint",
    "icon": "BRANCHING_PATH",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "FIX_DEGENERATE": True,
    },
}


class MASSA_OT_PrimYJoint(Massa_OT_Base):
    bl_idname = "massa.gen_prim_14_y_joint"
    bl_label = "PRIM_14: Y-Joint"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    radius: FloatProperty(name="Pipe Radius", default=0.5, min=0.1)
    trunk_len: FloatProperty(name="Trunk Length", default=1.0, min=0.1)
    branch_len: FloatProperty(name="Branch Length", default=1.0, min=0.1)
    angle: FloatProperty(name="Branch Angle", default=45.0, min=15.0, max=85.0)

    # --- 2. TOPOLOGY ---
    segments: IntProperty(name="Radial Segs", default=32, min=8)

    # --- 3. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Pipe Surface", "uv": "SKIP", "phys": "SYNTH_PLASTIC"},
            1: {"name": "Ends", "uv": "SKIP", "phys": "SYNTH_PLASTIC"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        layout.prop(self, "radius")
        layout.prop(self, "trunk_len")
        layout.prop(self, "branch_len")
        layout.prop(self, "angle")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        layout.prop(self, "segments")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        seg = self.segments
        rad = self.radius
        half_rad = math.radians(self.angle)

        # ----------------------------------------------------------------------
        # 1. BUILD RIGHT BRANCH (Base Geometry in Main BM)
        # ----------------------------------------------------------------------
        branch_depth = self.branch_len + (rad * 4.0)

        # Position Cylinder (Right)
        mat_rot_r = Matrix.Rotation(half_rad, 4, "Y")
        mat_trans_r = Matrix.Translation(
            (0, 0, branch_depth / 2 - (rad / math.tan(math.radians(90 - self.angle))))
        )

        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            segments=seg,
            radius1=rad,
            radius2=rad,
            depth=branch_depth,
            matrix=mat_rot_r @ mat_trans_r,
        )

        # Bisect Right Branch at X=0
        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            dist=0.0001,
            plane_co=(0, 0, 0),
            plane_no=(-1, 0, 0),  # Keep X>0
            clear_outer=True,
            clear_inner=False,
        )
        # Close hole
        edges = [e for e in bm.edges if e.is_boundary]
        bmesh.ops.contextual_create(bm, geom=edges)

        # ----------------------------------------------------------------------
        # 2. BUILD LEFT BRANCH (Merge into Main BM)
        # ----------------------------------------------------------------------
        bm_left = bmesh.new()
        mat_rot_l = Matrix.Rotation(-half_rad, 4, "Y")
        mat_trans_l = Matrix.Translation(
            (0, 0, branch_depth / 2 - (rad / math.tan(math.radians(90 - self.angle))))
        )

        bmesh.ops.create_cone(
            bm_left,
            cap_ends=True,
            segments=seg,
            radius1=rad,
            radius2=rad,
            depth=branch_depth,
            matrix=mat_rot_l @ mat_trans_l,
        )

        # Bisect Left
        bmesh.ops.bisect_plane(
            bm_left,
            geom=bm_left.verts[:] + bm_left.edges[:] + bm_left.faces[:],
            dist=0.0001,
            plane_co=(0, 0, 0),
            plane_no=(1, 0, 0),  # Keep X<0
            clear_outer=True,
            clear_inner=False,
        )
        edges = [e for e in bm_left.edges if e.is_boundary]
        bmesh.ops.contextual_create(bm_left, geom=edges)

        # FIXED: Explicit Mesh Data Block for Transfer
        l_mesh = bpy.data.meshes.new("temp_left")
        bm_left.to_mesh(l_mesh)
        bm_left.free()

        bm.from_mesh(l_mesh)
        bpy.data.meshes.remove(l_mesh)

        # Weld V-Joint
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)

        # Snapshot V-Geometry for Boolean Target
        geom_v = bm.verts[:] + bm.edges[:] + bm.faces[:]

        # ----------------------------------------------------------------------
        # 3. BUILD TRUNK (Boolean Intersector)
        # ----------------------------------------------------------------------
        bm_trunk = bmesh.new()

        t_height = self.trunk_len + (rad * 4.0)
        center_z = -self.trunk_len + (t_height / 2)

        bmesh.ops.create_cone(
            bm_trunk,
            cap_ends=True,
            segments=seg,
            radius1=rad,
            radius2=rad,
            depth=t_height,
            matrix=Matrix.Translation((0, 0, center_z)),
        )

        # Transfer Trunk
        t_mesh = bpy.data.meshes.new("temp_t")
        bm_trunk.to_mesh(t_mesh)
        bm_trunk.free()

        bm.from_mesh(t_mesh)
        bpy.data.meshes.remove(t_mesh)

        # Identify Trunk Geometry (Everything newly added)
        set_v = set(geom_v)
        geom_t = (
            [v for v in bm.verts if v not in set_v]
            + [e for e in bm.edges if e not in set_v]
            + [f for f in bm.faces if f not in set_v]
        )

        # 4. BOOLEAN UNION
        # ----------------------------------------------------------------------
        try:
            bmesh.ops.boolean(
                bm,
                geom=geom_v,  # V-Joint (Target)
                intersector=geom_t,  # Trunk (Tool)
                operation="UNION",
                use_swap=True,
            )
        except Exception:
            pass  # Boolean failed, return intersecting meshes

        # 5. FINAL CLEANUP & SLOTS
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Heuristic Slot Assignment
        for f in bm.faces:
            c = f.calc_center_median()
            # Trunk Cap
            if c.z < (-self.trunk_len * 0.95):
                f.material_index = 1
            # Branch Caps (High Z and Far from center)
            elif c.z > 0 and c.length > (self.branch_len * 0.9):
                f.material_index = 1
            else:
                f.material_index = 0
                f.smooth = True

        # 6. UV MAPPING
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        min_v = Vector((float("inf"),) * 3)
        max_v = Vector((float("-inf"),) * 3)
        if self.fit_uvs:
            for v in bm.verts:
                for i in range(3):
                    min_v[i] = min(min_v[i], v.co[i])
                    max_v[i] = max(max_v[i], v.co[i])
            dims = max_v - min_v
            for i in range(3):
                dims[i] = max(0.001, dims[i])

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            for l in f.loops:
                co = l.vert.co
                u, v = 0.0, 0.0

                if nz > nx and nz > ny:
                    u, v = co.x, co.y
                    if self.fit_uvs:
                        u = (u - min_v.x) / dims.x
                        v = (v - min_v.y) / dims.y
                elif nx > ny and nx > nz:
                    u, v = co.y, co.z
                    if self.fit_uvs:
                        u = (u - min_v.y) / dims.y
                        v = (v - min_v.z) / dims.z
                else:
                    u, v = co.x, co.z
                    if self.fit_uvs:
                        u = (u - min_v.x) / dims.x
                        v = (v - min_v.z) / dims.z

                if not self.fit_uvs:
                    u *= s
                    v *= s

                l[uv_layer].uv = (u, v)
