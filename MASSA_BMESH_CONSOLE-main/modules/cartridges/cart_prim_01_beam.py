import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_01: Structural Beam",
    "id": "prim_01_beam",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}


class MASSA_OT_PrimBeam(Massa_OT_Base):
    bl_idname = "massa.gen_prim_01_beam"
    bl_label = "PRIM_01: Beam"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    profile_type: EnumProperty(
        name="Profile",
        items=[
            ("BOX", "Box / Rect", ""),
            ("I_BEAM", "I-Beam", ""),
            ("C_CHANNEL", "C-Channel", ""),
            ("T_BEAM", "T-Beam", ""),
            ("L_ANGLE", "L-Angle", ""),
        ],
        default="I_BEAM",
    )
    # AXIS STANDARD: Y-AXIS IS LENGTH
    width: FloatProperty(name="Width (X)", default=0.2, min=0.01)
    height: FloatProperty(name="Height (Z)", default=0.4, min=0.01)
    length: FloatProperty(name="Length (Y)", default=3.0, min=0.1)
    thickness: FloatProperty(name="Thickness", default=0.02, min=0.002)

    segments_y: IntProperty(name="Length Segs", default=0, min=0, soft_max=50)

    # REMOVED: remove_caps (Manifold enforcement)

    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Surface", "uv": "SKIP", "phys": "METAL_IRON"},
            1: {"name": "Caps", "uv": "BOX", "phys": "METAL_IRON"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="PROFILE (XZ Plane)", icon="MESH_DATA")
        layout.prop(self, "profile_type", text="")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        if self.profile_type != "BOX":
            layout.prop(self, "thickness")

        layout.separator()
        layout.label(text="EXTRUSION (Y+)", icon="AXIS_SIDE")
        layout.prop(self, "length")

        layout.separator()
        layout.label(text="TOPOLOGY", icon="MOD_WIREFRAME")
        layout.prop(self, "segments_y")


    def build_shape(self, bm: bmesh.types.BMesh):
        w, h, t = self.width, self.height, self.thickness
        hw, hh = w / 2.0, h / 2.0
        t = min(t, w * 0.49, h * 0.49)
        ht = t / 2.0

        # 1. PROFILE DEFINITION (XZ Plane)
        pts = []
        if self.profile_type == "BOX":
            pts = [(-hw, 0), (hw, 0), (hw, h), (-hw, h)]
        elif self.profile_type == "I_BEAM":
            pts = [
                (-hw, 0),
                (hw, 0),
                (hw, t),
                (ht, t),
                (ht, h - t),
                (hw, h - t),
                (hw, h),
                (-hw, h),
                (-hw, h - t),
                (-ht, h - t),
                (-ht, t),
                (-hw, t),
            ]
        elif self.profile_type == "C_CHANNEL":
            pts = [
                (-hw, 0),
                (hw, 0),
                (hw, t),
                (-hw + t, t),
                (-hw + t, h - t),
                (hw, h - t),
                (hw, h),
                (-hw, h),
            ]
        elif self.profile_type == "T_BEAM":
            pts = [
                (-ht, 0),
                (ht, 0),
                (ht, h - t),
                (hw, h - t),
                (hw, h),
                (-hw, h),
                (-hw, h - t),
                (-ht, h - t),
            ]
        elif self.profile_type == "L_ANGLE":
            pts = [(-hw, 0), (hw, 0), (hw, t), (-hw + t, t), (-hw + t, h), (-hw, h)]

        # 2. CREATE BASE GEOMETRY (Clean Extrusion)
        base_verts = [bm.verts.new((p[0], 0.0, p[1])) for p in pts]
        bm.verts.ensure_lookup_table()
        try:
            # Create start cap at Y=0
            start_cap = bm.faces.new(base_verts)
        except ValueError:
            return

        # Extrude the start cap to create length and end cap
        res_ext = bmesh.ops.extrude_face_region(bm, geom=[start_cap])
        verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
        # Move extruded vertices to final length
        bmesh.ops.translate(bm, verts=verts_ext, vec=(0.0, self.length, 0.0))

        # 3. SEGMENTATION
        if self.segments_y > 0:
            step = self.length / (self.segments_y + 1)
            for i in range(1, self.segments_y + 1):
                y_cut = i * step
                geom_all = bm.faces[:] + bm.edges[:] + bm.verts[:]
                bmesh.ops.bisect_plane(
                    bm,
                    geom=geom_all,
                    dist=0.0001,
                    plane_co=(0, y_cut, 0),
                    plane_no=(0, 1, 0),
                    use_snap_center=False,
                    clear_outer=False,
                    clear_inner=False,
                )

        # 4. IDENTIFY & FORCE CAP NORMALS
        final_start_caps = []
        final_end_caps = []
        final_walls = []

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            cen = f.calc_center_median()
            # Start Cap: Normal -Y, Pos Y ~ 0
            if abs(cen.y) < 0.01:
                final_start_caps.append(f)
            # End Cap: Normal +Y, Pos Y ~ Length
            elif abs(cen.y - self.length) < 0.01:
                final_end_caps.append(f)
            else:
                final_walls.append(f)

        # FORCE NORMALS
        bm.faces.ensure_lookup_table()
        for f in final_start_caps:
            f.normal_update()
            if f.normal.y > 0:
                f.normal_flip()

        for f in final_end_caps:
            f.normal_update()
            if f.normal.y < 0:
                f.normal_flip()

        bm.normal_update()
        if final_walls:
            bmesh.ops.recalc_face_normals(bm, faces=final_walls)

        # 5. ASSIGN SLOTS
        for f in final_start_caps:
            f.material_index = 1
        for f in final_end_caps:
            f.material_index = 1
        for f in final_walls:
            f.material_index = 0

        # 6. MARK SEAMS
        # Mark Caps Seams
        for f in final_start_caps + final_end_caps:
            for e in f.edges:
                e.seam = True

        # Mark Longitudinal Seam (Use pts[0] as guide)
        # using pts[0] ensures we follow a valid geometry edge (usually a corner)
        if pts:
            seam_x = pts[0][0]
            seam_z = pts[0][1]
            
            bm.edges.ensure_lookup_table()
            for e in bm.edges:
                v1 = e.verts[0]
                v2 = e.verts[1]
                
                # Check if edge lies on the seam line (v.x ~ seam_x, v.z ~ seam_z)
                # We use a slightly looser tolerance to ensure detection
                on_seam_1 = (abs(v1.co.x - seam_x) < 0.005) and (abs(v1.co.z - seam_z) < 0.005)
                on_seam_2 = (abs(v2.co.x - seam_x) < 0.005) and (abs(v2.co.z - seam_z) < 0.005)
                
                if on_seam_1 and on_seam_2:
                    e.seam = True

        # 7. UV MAPPING
        uv_layer = bm.loops.layers.uv.verify()
        perim = sum(
            math.hypot(
                pts[(i + 1) % len(pts)][0] - pts[i][0],
                pts[(i + 1) % len(pts)][1] - pts[i][1],
            )
            for i in range(len(pts))
        )
        su_s = (1.0 / perim) if (self.fit_uvs and perim > 0) else self.uv_scale
        sv_s = 1.0 / self.length if self.fit_uvs else self.uv_scale
        su_c = 1.0 / self.width if self.fit_uvs else self.uv_scale
        sv_c = 1.0 / self.height if self.fit_uvs else self.uv_scale

        def get_u(x, z):
            cu = 0.0
            for i in range(len(pts)):
                p1 = pts[i]
                if math.hypot(p1[0] - x, p1[1] - z) < 0.002:
                    return cu
                pn = pts[(i + 1) % len(pts)]
                cu += math.hypot(pn[0] - p1[0], pn[1] - p1[1])
            return 0.0

        for f in bm.faces:
            if not f.is_valid:
                continue
            if f.material_index == 1:  # CAPS
                for l in f.loops:
                    u = (l.vert.co.x + hw) * su_c
                    v = l.vert.co.z * sv_c
                    l[uv_layer].uv = (u, v)
            else:  # WALLS
                # Calculate UVs for all loops in face first to check for wrapping
                loop_uvs = []
                for l in f.loops:
                    ua = get_u(l.vert.co.x, l.vert.co.z)
                    va = l.vert.co.y
                    loop_uvs.append([l, ua, va])

                # Wrapping Check: If UVs span more than 50% of perimeter, it's the closing face
                us = [item[1] for item in loop_uvs]
                min_u, max_u = min(us), max(us)

                if (max_u - min_u) > (perim * 0.5):
                    # Fix the small values (0.0) by adding perimeter
                    for item in loop_uvs:
                        if item[1] < (perim * 0.5):
                            item[1] += perim

                # Apply scaled UVs
                for l, u, v in loop_uvs:
                    l[uv_layer].uv = (u * su_s, v * sv_s)
