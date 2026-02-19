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
        rad = self.radius
        half_rad = math.radians(self.angle)
        
        # ----------------------------------------------------------------------
        # 1. PREPARE GEOMETRY CONTAINERS
        # ----------------------------------------------------------------------
        # We will build parts in separate BMeshes and combine them to ensure
        # clean booleans.
        
        # ----------------------------------------------------------------------
        # 2. CREATE V-JOINT (Branches)
        # ----------------------------------------------------------------------
        bm_branches = bmesh.new()
        
        # Parameters for branches
        # Make them long enough to be trimmed
        b_len_gen = self.branch_len + rad * 2.0 
        
        # --- Right Branch ---
        mat_rot_r = Matrix.Rotation(half_rad, 4, "Y")
        # Shift so the 'start' of the cylinder (bottom) is near origin after rotation
        # create_cone makes cylinder centered at (0,0,0) with length 'depth'
        # We want the connection point at 0.
        # Shift Z up by half length
        mat_trans_gen = Matrix.Translation((0, 0, b_len_gen / 2))
        
        # We need to offset the pivot so the inner edge meets at X=0
        # Simple trig: offset_x = rad / cos(theta)? 
        # Actually, let's just make them centered at origin and miter them.
        
        # Right Branch Mesh
        bmesh.ops.create_cone(
            bm_branches,
            cap_ends=True,
            segments=seg,
            radius1=rad,
            radius2=rad,
            depth=b_len_gen,
            matrix=mat_rot_r @ mat_trans_gen,
        )
        
        # Bisect Right (Keep X > 0)
        bmesh.ops.bisect_plane(
            bm_branches,
            geom=bm_branches.verts[:] + bm_branches.edges[:] + bm_branches.faces[:],
            dist=0.0001,
            plane_co=(0, 0, 0),
            plane_no=(-1, 0, 0),
            clear_outer=True,
            clear_inner=False,
        )
        # Cap the bisect
        edges_r = [e for e in bm_branches.edges if e.is_boundary]
        bmesh.ops.contextual_create(bm_branches, geom=edges_r)

        # --- Left Branch ---
        bm_left = bmesh.new()
        mat_rot_l = Matrix.Rotation(-half_rad, 4, "Y")
        
        bmesh.ops.create_cone(
            bm_left,
            cap_ends=True,
            segments=seg,
            radius1=rad,
            radius2=rad,
            depth=b_len_gen,
            matrix=mat_rot_l @ mat_trans_gen,
        )
        
        # Bisect Left (Keep X < 0)
        bmesh.ops.bisect_plane(
            bm_left,
            geom=bm_left.verts[:] + bm_left.edges[:] + bm_left.faces[:],
            dist=0.0001,
            plane_co=(0, 0, 0),
            plane_no=(1, 0, 0),
            clear_outer=True,
            clear_inner=False,
        )
        # Cap the bisect
        edges_l = [e for e in bm_left.edges if e.is_boundary]
        bmesh.ops.contextual_create(bm_left, geom=edges_l)
        
        # Merge Left into branches BM
        bm_left.verts.ensure_lookup_table()
        me_temp = bpy.data.meshes.new("temp_left")
        bm_left.to_mesh(me_temp)
        bm_branches.from_mesh(me_temp)
        bm_left.free()
        bpy.data.meshes.remove(me_temp)
        
        # Weld the seam at X=0
        bmesh.ops.remove_doubles(bm_branches, verts=bm_branches.verts, dist=0.001)
        bmesh.ops.recalc_face_normals(bm_branches, faces=bm_branches.faces)

        # Transfer V-Joint to Main BM
        me_v = bpy.data.meshes.new("temp_v")
        bm_branches.to_mesh(me_v)
        bm_branches.free()
        bm.from_mesh(me_v)
        bpy.data.meshes.remove(me_v)
        
        geom_branches = bm.verts[:] + bm.edges[:] + bm.faces[:]

        # ----------------------------------------------------------------------
        # 3. CREATE TRUNK
        # ----------------------------------------------------------------------
        # Trunk goes from -trunk_len to roughly +rad (overlap)
        # Total height = trunk_len + overlap
        overlap = rad * 1.5 
        t_height = self.trunk_len + overlap
        
        # Center Z: Bottom is at -trunk_len. Top is at +overlap.
        # Midpoint = (-trunk_len + overlap) / 2
        center_z = (-self.trunk_len + overlap) / 2
        
        bm_trunk = bmesh.new()
        bmesh.ops.create_cone(
            bm_trunk,
            cap_ends=True,
            segments=seg,
            radius1=rad,
            radius2=rad,
            depth=t_height,
            matrix=Matrix.Translation((0, 0, center_z)),
        )
        
        # Transfer Trunk to Main BM
        me_t = bpy.data.meshes.new("temp_t")
        bm_trunk.to_mesh(me_t)
        bm_trunk.free()
        bm.from_mesh(me_t)
        bpy.data.meshes.remove(me_t)
        
        # Identify Trunk Geometry
        set_b = set(geom_branches)
        geom_trunk = [g for g in (bm.verts[:] + bm.edges[:] + bm.faces[:]) if g not in set_b]

        # ----------------------------------------------------------------------
        # 4. BOOLEAN UNION
        # ----------------------------------------------------------------------
        # Combine Trunk + Branches
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        try:
            bmesh.ops.boolean(
                bm,
                geom=geom_branches,
                intersector=geom_trunk,
                operation="UNION",
                use_swap=True,
                # solver='EXACT' # Not exposed in BMesh ops, uses default
            )
        except Exception as e:
            print(f"Boolean Union Failed: {e}")
            # Fallback: Just leave them intersecting (better than crash)

        # ----------------------------------------------------------------------
        # 5. CLEANUP & SLOTS
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        
        # Slot Assignment
        for f in bm.faces:
            c = f.calc_center_median()
            
            # Simple heuristic based on normals and position
            is_cap = False
            
            # Ends of branches
            # Projects onto branch vectors?
            
            # Trunk Bottom Cap
            if c.z < (-self.trunk_len + 0.01) and f.normal.z < -0.9:
                is_cap = True
                
            # Branch Caps
            # Check deviation from branch axis
            # This is tricky after boolean.
            # Use distance from origin?
            dist = c.length
            if dist > (max(self.branch_len, self.trunk_len) - rad):
                # Potential cap
                # Check normal alignment with branch vectors
                v_r = Vector((math.sin(half_rad), 0, math.cos(half_rad)))
                v_l = Vector((-math.sin(half_rad), 0, math.cos(half_rad)))
                
                if f.normal.dot(v_r) > 0.9 or f.normal.dot(v_l) > 0.9:
                    is_cap = True

            if is_cap:
                f.material_index = 1
                f.smooth = False
            else:
                f.material_index = 0
                f.smooth = True

        # ----------------------------------------------------------------------
        # 6. SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            if len(e.link_faces) >= 2:
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    continue
                # Sharp edges
                f1, f2 = e.link_faces[0], e.link_faces[1]
                if f1.smooth and f2.smooth:
                    if f1.normal.dot(f2.normal) < 0.5:
                        e.seam = True

        # ----------------------------------------------------------------------
        # 7. UV MAPPING
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale
        
        # Box Map Logic
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
