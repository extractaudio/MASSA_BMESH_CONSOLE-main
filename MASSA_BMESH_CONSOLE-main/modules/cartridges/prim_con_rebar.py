"""
Filename: modules/cartridges/prim_con_rebar.py
Content: Twisted Steel Rebar Generator (Bent Paths)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector, Matrix, Quaternion

CARTRIDGE_META = {
    "name": "Con: Rebar",
    "id": "prim_con_rebar",
    "icon": "HAIR",
    "scale_class": "MICRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_rebar(Massa_OT_Base):
    """
    Twisted Steel Rebar Generator.
    Implements PRIM_11 (Helix/Path) Logic with Parallel Transport Frames.
    Features: Path Bending, Twisted Profile, Ridge Detailing.
    """

    bl_idname = "massa.gen_prim_con_rebar"
    bl_label = "Construction Rebar"
    bl_description = "Reinforced Steel Bar with Bends"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- SHAPE ---
    shape_mode: EnumProperty(
        name="Shape",
        items=[
            ("STRAIGHT", "Straight", "Linear Bar"),
            ("L_BEND", "L-Bend", "Corner Reinforcement"),
            ("U_HOOK", "U-Hook", "Safety End"),
            ("STIRRUP", "Stirrup", "Rectangular Tie"),
        ],
        default="STRAIGHT",
    )

    diameter: FloatProperty(name="Diameter", default=0.012, min=0.004, unit="LENGTH")
    length_a: FloatProperty(name="Length A", default=1.0, min=0.1, unit="LENGTH")
    length_b: FloatProperty(name="Length B", default=0.3, min=0.05, unit="LENGTH")
    bend_radius: FloatProperty(
        name="Bend Radius", default=0.04, min=0.01, unit="LENGTH"
    )

    # --- DETAILING ---
    rib_twist: FloatProperty(name="Twist", default=5.0, min=0.0)
    resolution_u: IntProperty(name="Profile Res", default=8, min=4)
    resolution_v: IntProperty(name="Length Res", default=32, min=4)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Configuration", icon="FORCE_CURVE")
        box.prop(self, "shape_mode")
        box.prop(self, "diameter")

        col = box.column(align=True)
        col.prop(self, "length_a")
        if self.shape_mode != "STRAIGHT":
            col.prop(self, "length_b")
            col.prop(self, "bend_radius")

        box = layout.box()
        box.label(text="Ribbing", icon="MOD_SCREW")
        box.prop(self, "rib_twist")
        row = box.row(align=True)
        row.prop(self, "resolution_u", text="U-Res")
        row.prop(self, "resolution_v", text="V-Res")

    def get_slot_meta(self):
        return {
            0: {"name": "Steel_Ribbed", "uv": "TUBE_Y", "phys": "METAL_IRON"},
            1: {"name": "Cut_End", "uv": "BOX", "phys": "METAL_RUST"},
        }

    def build_shape(self, bm):
        # 1. GENERATE PATH POINTS
        path_points = []

        l1 = self.length_a
        l2 = self.length_b
        r = self.bend_radius

        # Helper: Arc Generator
        def add_arc(center, radius, start_ang, end_ang, segments):
            pts = []
            for i in range(segments + 1):
                t = i / segments
                ang = start_ang + (end_ang - start_ang) * t
                # Assuming Flat on XY plane for simplicity of path generation
                pts.append(
                    center + Vector((math.cos(ang) * radius, math.sin(ang) * radius, 0))
                )
            return pts

        # A. Path Logic
        if self.shape_mode == "STRAIGHT":
            path_points = [Vector((0, 0, 0)), Vector((l1, 0, 0))]

        elif self.shape_mode == "L_BEND":
            # Leg 1 (X) -> Arc -> Leg 2 (Y)
            p1 = Vector((0, 0, 0))
            p2 = Vector((l1 - r, 0, 0))

            # Arc Center at (l1-r, r, 0)
            arc_pts = add_arc(Vector((l1 - r, r, 0)), r, -math.pi / 2, 0, 6)

            # Leg 2 Up
            p3 = Vector((l1, r, 0))
            p4 = Vector((l1, r + l2 - r, 0))

            path_points = [p1, p2] + arc_pts[1:] + [p4]

        elif self.shape_mode == "U_HOOK":
            # 180 Turn
            p1 = Vector((0, 0, 0))
            p2 = Vector((l1 - r, 0, 0))
            arc_pts = add_arc(Vector((l1 - r, r, 0)), r, -math.pi / 2, math.pi / 2, 12)
            p3 = Vector((l1 - r, r * 2, 0))
            p4 = Vector((l1 - r - (l2 - r), r * 2, 0))  # Go back
            path_points = [p1, p2] + arc_pts[1:] + [p4]

        elif self.shape_mode == "STIRRUP":
            # Rectangular Loop
            w = l1
            h = l2
            # Bot Edge
            path_points.append(Vector((r, 0, 0)))
            path_points.append(Vector((w - r, 0, 0)))
            # Corner 1
            path_points.extend(
                add_arc(Vector((w - r, r, 0)), r, -math.pi / 2, 0, 4)[1:]
            )
            # Right Edge
            path_points.append(Vector((w, h - r, 0)))
            # Corner 2
            path_points.extend(
                add_arc(Vector((w - r, h - r, 0)), r, 0, math.pi / 2, 4)[1:]
            )
            # Top Edge
            path_points.append(Vector((r, h, 0)))
            # Corner 3
            path_points.extend(
                add_arc(Vector((r, h - r, 0)), r, math.pi / 2, math.pi, 4)[1:]
            )
            # Left Edge
            path_points.append(Vector((0, r, 0)))
            # Corner 4
            path_points.extend(
                add_arc(Vector((r, r, 0)), r, math.pi, 3 * math.pi / 2, 4)[1:]
            )
            # Close Loop manually
            path_points.append(Vector((r, 0, 0)))

        # 2. RESAMPLE PATH
        # Even distribution for twist
        total_len = 0.0
        dists = [0.0]
        for i in range(len(path_points) - 1):
            d = (path_points[i + 1] - path_points[i]).length
            total_len += d
            dists.append(total_len)

        target_res = self.resolution_v
        step = total_len / target_res

        final_path = []
        path_idx = 0

        for i in range(target_res + 1):
            target_d = i * step
            while path_idx < len(dists) - 1 and dists[path_idx + 1] < target_d:
                path_idx += 1
            if path_idx >= len(dists) - 1:
                final_path.append(path_points[-1])
            else:
                seg_len = dists[path_idx + 1] - dists[path_idx]
                fac = (target_d - dists[path_idx]) / seg_len if seg_len > 0 else 0
                pt = path_points[path_idx].lerp(path_points[path_idx + 1], fac)
                final_path.append(pt)

        # 3. SKINNING WITH TWIST (Parallel Transport)
        rad = self.diameter / 2
        prof_res = self.resolution_u

        # Precompute Tangents
        tangents = []
        for i in range(len(final_path)):
            if i < len(final_path) - 1:
                t = (final_path[i + 1] - final_path[i]).normalized()
            else:
                t = (final_path[i] - final_path[i - 1]).normalized()
            tangents.append(t)

        # Parallel Transport Frame
        frames = []
        t0 = tangents[0]
        up = Vector((0, 0, 1))
        if abs(t0.dot(up)) > 0.9:
            up = Vector((1, 0, 0))
        r0 = t0.cross(up).normalized()
        u0 = r0.cross(t0).normalized()
        frames.append((r0, u0))

        for i in range(1, len(tangents)):
            t_prev = tangents[i - 1]
            t_curr = tangents[i]
            r_prev, u_prev = frames[-1]
            axis = t_prev.cross(t_curr)
            if axis.length < 0.001:
                frames.append((r_prev, u_prev))
            else:
                ang = t_prev.angle(t_curr)
                q = Quaternion(axis.normalized(), ang)
                r_new = q @ r_prev
                u_new = q @ u_prev
                frames.append((r_new, u_new))

        # Generate Geometry
        prev_loop = []

        for i, pt in enumerate(final_path):
            r_vec, u_vec = frames[i]

            # Apply Twist
            twist_ang = (i / target_res) * self.rib_twist * 2 * math.pi
            c_tw = math.cos(twist_ang)
            s_tw = math.sin(twist_ang)

            loop_verts = []
            for j in range(prof_res):
                ang = (j / prof_res) * 2 * math.pi
                # Deform Radius for Ribs (4 ribs)
                rib_fac = 1.0 + (0.1 * math.cos(4 * ang))
                local_r = rad * rib_fac

                lx = math.cos(ang) * local_r
                ly = math.sin(ang) * local_r

                # Rotate by Twist
                rx = lx * c_tw - ly * s_tw
                ry = lx * s_tw + ly * c_tw

                world_pt = pt + (r_vec * rx) + (u_vec * ry)
                loop_verts.append(bm.verts.new(world_pt))

            if prev_loop:
                for k in range(prof_res):
                    v1 = prev_loop[k]
                    v2 = prev_loop[(k + 1) % prof_res]
                    v3 = loop_verts[(k + 1) % prof_res]
                    v4 = loop_verts[k]
                    f = bm.faces.new((v1, v2, v3, v4))
                    f.material_index = 0
            prev_loop = loop_verts

        # 4. CAP ENDS & EDGE ROLES
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        if self.shape_mode != "STIRRUP":
            edges_boundary = [e for e in bm.edges if e.is_boundary]
            if edges_boundary:
                try:
                    bmesh.ops.contextual_create(bm, geom=edges_boundary, mat_index=1)
                except:
                    pass

        for e in bm.edges:
            if any(f.material_index == 1 for f in e.link_faces):
                e[edge_slots] = 1  # Perimeter
            elif e[edge_slots] == 0 and e.calc_face_angle() > 0.4:
                e[edge_slots] = 2  # Ribs
