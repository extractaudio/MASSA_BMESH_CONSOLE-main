import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_02: Parametric Pipe",
    "id": "prim_02_pipe",
    "icon": "MESH_CYLINDER",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
    }
}


class MASSA_OT_PrimPipe(Massa_OT_Base):
    bl_idname = "massa.gen_prim_02_pipe"
    bl_label = "PRIM_02: Pipe"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    shape_mode: EnumProperty(
        name="Type",
        items=[("STRAIGHT", "Straight", ""), ("ELBOW", "Elbow", "")],
        default="STRAIGHT",
    )
    # Z-AXIS IS VERTICAL
    radius: FloatProperty(name="Radius", default=0.2, min=0.01)
    thickness: FloatProperty(name="Thickness", default=0.02, min=0.001)
    length: FloatProperty(name="Height (Z)", default=2.0, min=0.1)
    bend_radius: FloatProperty(name="Bend Radius", default=0.5, min=0.01)
    segments_radial: IntProperty(name="Radial Segs", default=16, min=3)
    segments_length: IntProperty(name="Length Segs", default=8, min=1)
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    # REMOVED: remove_caps (Manifold enforcement)

    def get_slot_meta(self):
        return {
            0: {"name": "Outer Surface", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "Inner Wall", "uv": "SKIP", "phys": "GENERIC"},
            2: {"name": "Ends", "uv": "SKIP", "phys": "METAL_STEEL"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="GEOMETRY (Z-Axis)", icon="MESH_CYLINDER")
        layout.prop(self, "shape_mode", text="")
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "thickness")
        if self.shape_mode == "STRAIGHT":
            layout.prop(self, "length")
        else:
            layout.prop(self, "bend_radius")

        layout.separator()
        layout.label(text="TOPOLOGY", icon="MOD_WIREFRAME")
        layout.prop(self, "segments_radial")
        layout.prop(self, "segments_length")

        layout.separator()
        layout.label(text="UV PROTOCOLS", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        ro = self.radius
        ri = max(0.001, self.radius - self.thickness)
        mid_radius = (ro + ri) / 2.0
        sr = self.segments_radial
        sl = max(1, self.segments_length)

        # 1. CREATE BASE RING (The Donut Method)
        res_out = bmesh.ops.create_circle(bm, radius=ro, segments=sr, cap_ends=False)
        verts_out = res_out["verts"]
        edges_out = list({e for v in verts_out for e in v.link_edges})

        res_in = bmesh.ops.create_circle(bm, radius=ri, segments=sr, cap_ends=False)
        verts_in = res_in["verts"]
        edges_in = list({e for v in verts_in for e in v.link_edges})

        res_bridge = bmesh.ops.bridge_loops(bm, edges=edges_out + edges_in)
        faces_start = res_bridge["faces"]

        # 2. GENERATE BODY
        if self.shape_mode == "STRAIGHT":
            # Extrude
            res_ext = bmesh.ops.extrude_face_region(bm, geom=faces_start)
            verts_top = [
                v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)
            ]
            bmesh.ops.translate(bm, verts=verts_top, vec=(0, 0, self.length))

            # Segments
            if sl > 1:
                step = self.length / sl
                for i in range(1, sl):
                    geom_all = bm.faces[:] + bm.edges[:] + bm.verts[:]
                    bmesh.ops.bisect_plane(
                        bm,
                        geom=geom_all,
                        dist=0.0001,
                        plane_co=(0, 0, i * step),
                        plane_no=(0, 0, 1),
                    )

        else:  # ELBOW
            bmesh.ops.translate(bm, verts=bm.verts, vec=(self.bend_radius, 0, 0))
            bmesh.ops.spin(
                bm,
                geom=faces_start,
                angle=math.radians(-90),
                steps=sl,
                axis=(0, 1, 0),
                cent=(0, 0, 0),
                use_duplicate=False,
            )

        # 3. NORMALS & CLASSIFICATION
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        final_caps = []
        final_outer = []
        final_inner = []
        CAP_TOL = 0.001

        for f in bm.faces:
            cen = f.calc_center_median()
            is_cap = False

            if self.shape_mode == "STRAIGHT":
                if abs(cen.z) < CAP_TOL or abs(cen.z - self.length) < CAP_TOL:
                    is_cap = True
            else:  # ELBOW
                if abs(cen.z) < CAP_TOL and abs(cen.x - self.bend_radius) < (ro * 1.5):
                    is_cap = True
                elif abs(cen.x) < CAP_TOL and abs(cen.z - self.bend_radius) < (
                    ro * 1.5
                ):
                    is_cap = True

            if is_cap:
                final_caps.append(f)
                continue

            # Vertex Average Classification
            avg_dist = 0.0
            if self.shape_mode == "STRAIGHT":
                d_sum = sum(math.hypot(v.co.x, v.co.y) for v in f.verts)
                avg_dist = d_sum / len(f.verts)
            else:
                d_sum = 0.0
                for v in f.verts:
                    dist_xz = math.hypot(v.co.x, v.co.z)
                    dist_tube = math.hypot(dist_xz - self.bend_radius, v.co.y)
                    d_sum += dist_tube
                avg_dist = d_sum / len(f.verts)

            if avg_dist > mid_radius:
                final_outer.append(f)
            else:
                final_inner.append(f)

        # 4. ASSIGN SLOTS
        for f in final_outer:
            f.material_index = 0
            f.smooth = True
        for f in final_inner:
            f.material_index = 1
            f.smooth = True
        cap_set = set(final_caps)
        cap_set = set(final_caps)
        for f in final_caps:
            f.material_index = 2
            f.smooth = True
            for e in f.edges:
                if len(e.link_faces) == 1 or any(lf not in cap_set for lf in e.link_faces):
                    e.seam = True

        # 5. UV MAPPING
        uv_layer = bm.loops.layers.uv.verify()
        perim_out = 2 * math.pi * ro
        su_mult = (1.0) if self.fit_uvs else (self.uv_scale * perim_out)

        if self.shape_mode == "STRAIGHT":
            sv_mult = (1.0) if self.fit_uvs else (self.uv_scale * self.length)
        else:
            sv_mult = (
                (1.0)
                if self.fit_uvs
                else (self.uv_scale * (2 * math.pi * self.bend_radius / 4))
            )

        for f in bm.faces:
            if not f.is_valid:
                continue

            if f.material_index == 2:  # CAPS
                s_cap = 1.0 if self.fit_uvs else self.uv_scale
                for l in f.loops:
                    if self.shape_mode == "STRAIGHT":
                        l[uv_layer].uv = (l.vert.co.x * s_cap, l.vert.co.y * s_cap)
                    else:
                        l[uv_layer].uv = (
                            (l.vert.co.x - self.bend_radius) * s_cap,
                            l.vert.co.y * s_cap,
                        )
            else:  # WALLS
                loop_uvs = []
                for l in f.loops:
                    vec = l.vert.co.copy()
                    u, v = 0.0, 0.0
                    if self.shape_mode == "STRAIGHT":
                        phi = math.atan2(vec.y, vec.x)
                        u = (phi + math.pi) / (2 * math.pi)
                        v = vec.z / self.length
                    else:  # ELBOW
                        theta = math.atan2(vec.z, vec.x)
                        v = abs(theta) / (math.pi / 2)
                        dist_xz = math.hypot(vec.x, vec.z)
                        local_x = dist_xz - self.bend_radius
                        local_y = vec.y
                        phi = math.atan2(local_y, local_x)
                        u = (phi + math.pi) / (2 * math.pi)
                    loop_uvs.append([l, u, v])

                us = [x[1] for x in loop_uvs]
                if max(us) - min(us) > 0.5:
                    for x in loop_uvs:
                        if x[1] < 0.5:
                            x[1] += 1.0

                for l, u, v in loop_uvs:
                    if not self.fit_uvs:
                        u *= su_mult
                        v *= sv_mult
                    l[uv_layer].uv = (u, v)

        # 6. SEAMS
        for e in bm.edges:
            if self.shape_mode == "STRAIGHT":
                if (
                    e.verts[0].co.x > 0
                    and abs(e.verts[0].co.y) < 0.001
                    and abs(e.verts[1].co.y) < 0.001
                ):
                    e.seam = True
            elif self.shape_mode == "ELBOW":
                if abs(e.verts[0].co.y) < 0.001 and abs(e.verts[1].co.y) < 0.001:
                    e.seam = True
