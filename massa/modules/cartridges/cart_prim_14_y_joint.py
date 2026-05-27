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



    def build_shape(self, bm: bmesh.types.BMesh):
        seg = self.segments
        if seg % 2 != 0:
            seg += 1  # Ensure even segments for perfect planar symmetry
            
        rad = self.radius
        alpha = math.radians(self.angle)
        
        # ----------------------------------------------------------------------
        # 1. PREPARE PLANES & NORMALS
        # ----------------------------------------------------------------------
        # Plane normals for perfect CSG-free intersection
        n_R = Vector((math.tan(alpha / 2.0), 0, 1)).normalized()
        n_L = Vector((-math.tan(alpha / 2.0), 0, 1)).normalized()
        n_X = Vector((1, 0, 0))
        
        def tag_caps(bm_part, axis_vec):
            for f in bm_part.faces:
                if abs(f.normal.dot(axis_vec)) > 0.9:
                    f.material_index = 1
                    f.smooth = False
                else:
                    f.material_index = 0
                    f.smooth = True

        # ----------------------------------------------------------------------
        # 2. CREATE RIGHT BRANCH
        # ----------------------------------------------------------------------
        bm_right = bmesh.new()
        b_len_gen = self.branch_len + rad
        b_center_z = (-rad + self.branch_len) / 2.0
        
        mat_rot_r = Matrix.Rotation(alpha, 4, "Y")
        mat_trans_gen = Matrix.Translation((0, 0, b_center_z))
        
        bmesh.ops.create_cone(
            bm_right, cap_ends=True, segments=seg, radius1=rad, radius2=rad,
            depth=b_len_gen, matrix=mat_rot_r @ mat_trans_gen
        )
        tag_caps(bm_right, mat_rot_r @ Vector((0, 0, 1)))
        
        # Cut with Trunk intersection (Keep Z > -X tan(a/2))
        bmesh.ops.bisect_plane(
            bm_right, geom=bm_right.verts[:] + bm_right.edges[:] + bm_right.faces[:],
            plane_co=(0, 0, 0), plane_no=n_R, clear_inner=True
        )
        # Cut with Symmetry plane X=0 (Keep X > 0)
        bmesh.ops.bisect_plane(
            bm_right, geom=bm_right.verts[:] + bm_right.edges[:] + bm_right.faces[:],
            plane_co=(0, 0, 0), plane_no=n_X, clear_inner=True
        )

        # ----------------------------------------------------------------------
        # 3. CREATE LEFT BRANCH
        # ----------------------------------------------------------------------
        bm_left = bmesh.new()
        mat_rot_l = Matrix.Rotation(-alpha, 4, "Y")
        
        bmesh.ops.create_cone(
            bm_left, cap_ends=True, segments=seg, radius1=rad, radius2=rad,
            depth=b_len_gen, matrix=mat_rot_l @ mat_trans_gen
        )
        tag_caps(bm_left, mat_rot_l @ Vector((0, 0, 1)))
        
        # Cut with Trunk intersection (Keep Z > X tan(a/2))
        bmesh.ops.bisect_plane(
            bm_left, geom=bm_left.verts[:] + bm_left.edges[:] + bm_left.faces[:],
            plane_co=(0, 0, 0), plane_no=n_L, clear_inner=True
        )
        # Cut with Symmetry plane X=0 (Keep X < 0)
        bmesh.ops.bisect_plane(
            bm_left, geom=bm_left.verts[:] + bm_left.edges[:] + bm_left.faces[:],
            plane_co=(0, 0, 0), plane_no=n_X, clear_outer=True
        )

        # ----------------------------------------------------------------------
        # 4. CREATE TRUNK
        # ----------------------------------------------------------------------
        bm_trunk = bmesh.new()
        t_len_gen = self.trunk_len + rad
        t_center_z = (-self.trunk_len + rad) / 2.0
        
        bmesh.ops.create_cone(
            bm_trunk, cap_ends=True, segments=seg, radius1=rad, radius2=rad,
            depth=t_len_gen, matrix=Matrix.Translation((0, 0, t_center_z))
        )
        tag_caps(bm_trunk, Vector((0, 0, 1)))
        
        # Cut with Right Branch intersection (Keep Z < -X tan(a/2))
        bmesh.ops.bisect_plane(
            bm_trunk, geom=bm_trunk.verts[:] + bm_trunk.edges[:] + bm_trunk.faces[:],
            plane_co=(0, 0, 0), plane_no=n_R, clear_outer=True
        )
        # Cut with Left Branch intersection (Keep Z < X tan(a/2))
        bmesh.ops.bisect_plane(
            bm_trunk, geom=bm_trunk.verts[:] + bm_trunk.edges[:] + bm_trunk.faces[:],
            plane_co=(0, 0, 0), plane_no=n_L, clear_outer=True
        )

        # ----------------------------------------------------------------------
        # 5. MERGE PARTS
        # ----------------------------------------------------------------------
        def merge_bm(target_bm, source_bm):
            source_bm.verts.ensure_lookup_table()
            me_temp = bpy.data.meshes.new("temp_merge")
            source_bm.to_mesh(me_temp)
            source_bm.free()
            target_bm.from_mesh(me_temp)
            bpy.data.meshes.remove(me_temp)

        merge_bm(bm, bm_right)
        merge_bm(bm, bm_left)
        merge_bm(bm, bm_trunk)

        # Stitch seams
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # ----------------------------------------------------------------------
        # 6. EDGES & SEAMS
        # ----------------------------------------------------------------------
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        n_R = Vector((math.tan(alpha / 2.0), 0, 1)).normalized()
        n_L = Vector((-math.tan(alpha / 2.0), 0, 1)).normalized()

        # Pass 1: Boundaries, Intersections (Yellow lines), and Contours
        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1 # PERIMETER
                e.seam = True
            else:
                v1, v2 = e.verts[0].co, e.verts[1].co
                is_intersect = False
                if abs(v1.x) < 0.001 and abs(v2.x) < 0.001:
                    is_intersect = True
                elif abs(v1.dot(n_R)) < 0.001 and abs(v2.dot(n_R)) < 0.001:
                    is_intersect = True
                elif abs(v1.dot(n_L)) < 0.001 and abs(v2.dot(n_L)) < 0.001:
                    is_intersect = True
                
                if is_intersect:
                    e[edge_slots] = 2 # CONTOUR
                    e.seam = True
                    continue
                
                if len(e.link_faces) >= 2:
                    mats = {f.material_index for f in e.link_faces}
                    if len(mats) > 1:
                        e[edge_slots] = 2 # CONTOUR
                        e.seam = True
                        continue
                    # Sharp edges
                    f1, f2 = e.link_faces[0], e.link_faces[1]
                    if f1.smooth and f2.smooth:
                        if f1.normal.dot(f2.normal) < 0.5:
                            e[edge_slots] = 2 # CONTOUR
                            e.seam = True

        # Pass 2: Guide Zippers (Slot 3) along the back (min Y)
        axes = [
            Vector((0, 0, 1)), # Trunk
            Vector((math.sin(alpha), 0, math.cos(alpha))), # Right Branch
            Vector((-math.sin(alpha), 0, math.cos(alpha))) # Left Branch
        ]
        
        for axis in axes:
            long_edges = []
            for e in bm.edges:
                if e[edge_slots] in (1, 2): continue # Skip boundaries/contours
                if len(e.verts) == 2:
                    dir_vec = (e.verts[1].co - e.verts[0].co).normalized()
                    if abs(dir_vec.dot(axis)) > 0.8:
                        long_edges.append(e)
            
            if long_edges:
                min_y = min(((e.verts[0].co + e.verts[1].co) * 0.5).y for e in long_edges)
                for e in long_edges:
                    if abs(((e.verts[0].co + e.verts[1].co) * 0.5).y - min_y) < 0.001:
                        e[edge_slots] = 3 # GUIDE
                        e.seam = True

        # ----------------------------------------------------------------------
        # 7. UV MAPPING
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
