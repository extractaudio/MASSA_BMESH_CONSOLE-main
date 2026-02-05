import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Quaternion
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_12: Wireframe Truss",
    "id": "prim_12_truss",
    "icon": "MOD_WIREFRAME",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
    },
}


class MASSA_OT_PrimTruss(Massa_OT_Base):
    bl_idname = "massa.gen_prim_12_truss"
    bl_label = "PRIM_12: Truss"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. SHAPE ---
    base_shape: EnumProperty(
        name="Base Structure",
        items=[
            ("BOX", "Cube Grid", "Standard cubic truss"),
            ("PYRAMID", "Pyramid / Tower", "Tapered structure"),
            ("ICOS", "Icosphere", "Geodesic style"),
        ],
        default="BOX",
    )
    size: FloatProperty(name="Overall Size", default=2.0, min=0.1)

    # --- 2. COMPONENTS ---
    strut_radius: FloatProperty(name="Strut Radius", default=0.04, min=0.001)
    joint_radius: FloatProperty(name="Joint Radius", default=0.08, min=0.001)

    # --- 3. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 STRICT: UV must be 'SKIP'.
        We calculate UVs manually to handle local orientation correctly.
        """
        return {
            0: {"name": "Struts", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            1: {"name": "Joints", "uv": "SKIP", "phys": "METAL_STEEL"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Structure", icon="MESH_DATA")
        layout.prop(self, "base_shape", text="")
        layout.prop(self, "size")

        layout.separator()
        layout.label(text="Components", icon="CONSTRAINT_BONE")
        col = layout.column(align=True)
        col.prop(self, "strut_radius")
        col.prop(self, "joint_radius")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. CREATE GHOST MESH
        # ----------------------------------------------------------------------
        bm_ghost = bmesh.new()

        if self.base_shape == "BOX":
            bmesh.ops.create_cube(bm_ghost, size=self.size)

        elif self.base_shape == "PYRAMID":
            bmesh.ops.create_cone(
                bm_ghost,
                cap_ends=True,
                radius1=self.size / 2,
                radius2=0,
                depth=self.size,
                segments=4,
            )

        elif self.base_shape == "ICOS":
            bmesh.ops.create_icosphere(
                bm_ghost,
                subdivisions=1,
                radius=self.size / 2,
            )

        bm_ghost.verts.ensure_lookup_table()
        bm_ghost.edges.ensure_lookup_table()

        uv_layer = bm.loops.layers.uv.verify()

        # 2. GENERATE JOINTS (Nodes)
        # ----------------------------------------------------------------------
        create_joints = self.joint_radius >= self.strut_radius

        if create_joints:
            for v in bm_ghost.verts:
                res = bmesh.ops.create_icosphere(
                    bm,
                    subdivisions=2,
                    radius=self.joint_radius,
                    matrix=Matrix.Translation(v.co),
                )

                # Manual Box Mapping for Joints
                # Ensures density matches struts

                # Derive faces safely
                new_verts = res.get("verts", [])
                faces = list({f for v in new_verts for f in v.link_faces})

                for f in faces:
                    f.material_index = 1
                    f.smooth = True

                    # Box Map
                    n = f.normal
                    nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

                    for l in f.loops:
                        co = l.vert.co
                        u, v_coord = 0.0, 0.0

                        if nx > ny and nx > nz:
                            u, v_coord = co.y, co.z
                        elif ny > nx and ny > nz:
                            u, v_coord = co.x, co.z
                        else:
                            u, v_coord = co.x, co.y

                        if not self.fit_uvs:
                            u *= self.uv_scale
                            v_coord *= self.uv_scale

                        l[uv_layer].uv = (u, v_coord)

        # 3. GENERATE STRUTS (Edges)
        # ----------------------------------------------------------------------
        z_vec = Vector((0, 0, 1))

        # UV Scale Factors
        # For struts, we map the circumference to U.
        # Ideally, to match density:
        # U range = Circumference * Scale
        # V range = Length * Scale
        # But standard primitives often map U 0-1.
        # To match visual density of joints (Box Map), we should scale U by perimeter?
        # Actually, simpler is better: U is 0-1 (Radial), V is 0-Length (Linear).
        # We apply uv_scale to V. U usually stays 0-1 or we scale by radius * uv_scale.
        # Let's align V to match the joints.

        s_u = 1.0  # Keep radial 0-1 for standard trim sheets
        if not self.fit_uvs:
            # Option: s_u = (2 * math.pi * self.strut_radius) * self.uv_scale
            # For now, let's keep U 0-1 standard for pipes, but scale V heavily.
            pass

        for e in bm_ghost.edges:
            v1 = e.verts[0].co
            v2 = e.verts[1].co
            vec = v2 - v1
            length = vec.length
            mid = (v1 + v2) / 2

            if length < 0.001:
                continue

            # A. Create Cylinder at Origin (Z-Aligned)
            res = bmesh.ops.create_cone(
                bm,
                cap_ends=False,
                radius1=self.strut_radius,
                radius2=self.strut_radius,
                depth=length,
                segments=8,
            )

            new_verts = res.get("verts", [])
            new_faces = list({f for v in new_verts for f in v.link_faces})

            # B. UV Map in Local Space
            # Cylinder runs from Z = -length/2 to +length/2
            z_offset = length / 2

            s_v = 1.0 if self.fit_uvs else (length * self.uv_scale)

            for f in new_faces:
                f.material_index = 0
                f.smooth = True

                for l in f.loops:
                    co = l.vert.co  # Local coords

                    # U: Radial 0-1
                    phi = math.atan2(co.y, co.x)
                    u = (phi + math.pi) / (2 * math.pi)

                    # V: Linear 0-1 (normalized relative to length)
                    v_norm = (co.z + z_offset) / length

                    # Apply Scale
                    l[uv_layer].uv = (u * s_u, v_norm * s_v)

                # Seam Fix
                us = [l[uv_layer].uv.x for l in f.loops]
                if max(us) - min(us) > 0.5:
                    for l in f.loops:
                        if l[uv_layer].uv.x < 0.5:
                            l[uv_layer].uv.x += 1.0

            # C. Transform to World Position
            rot_quat = z_vec.rotation_difference(vec)
            mat_trans = Matrix.Translation(mid)
            mat_rot = rot_quat.to_matrix().to_4x4()
            mat_final = mat_trans @ mat_rot

            bmesh.ops.transform(bm, matrix=mat_final, verts=new_verts)

        # 4. CLEANUP
        # ----------------------------------------------------------------------
        bm_ghost.free()
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        min_z = min([v.co.z for v in bm.verts]) if bm.verts else 0.0
        if abs(min_z) > 0.001:
            bmesh.ops.translate(bm, vec=(0, 0, -min_z), verts=bm.verts)
