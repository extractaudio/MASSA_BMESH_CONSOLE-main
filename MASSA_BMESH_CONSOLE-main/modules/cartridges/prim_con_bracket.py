import bpy
import bmesh
import math
from mathutils import Matrix, Vector
from bpy.props import FloatProperty, IntProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

# ==============================================================================
# MASSA CARTRIDGE: CONSTRUCTION BRACKET (SOCKETS ORIENTED)
# ID: prim_con_bracket
# ==============================================================================

CARTRIDGE_META = {
    "name": "Con: Bracket",
    "id": "prim_con_bracket",
    "icon": "HOOK",
    "scale_class": "MICRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,  # Handled internally
        "FIX_DEGENERATE": False,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_bracket(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_bracket"
    bl_label = "Construction Bracket"
    bl_description = "L-Bracket with Opposing Socket Anchors"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    leg_len: FloatProperty(name="Leg Length", default=0.1, unit="LENGTH", min=0.01)
    width: FloatProperty(name="Width", default=0.04, unit="LENGTH", min=0.01)
    thick: FloatProperty(name="Thickness", default=0.004, unit="LENGTH", min=0.001)

    # Shape Logic
    shape_type: EnumProperty(
        name="Shape",
        items=[
            ("FLAT", "Flat Strip", "Single straight bracket"),
            ("L_BRACKET", "L-Bracket", "90-degree corner"),
            ("U_BRACKET", "U-Bracket", "Double 90-degree corner"),
        ],
        default="L_BRACKET",
    )

    # Features
    hole_rad: FloatProperty(name="Hole Radius", default=0.005, unit="LENGTH", min=0.0)
    hole_count: IntProperty(name="Hole Count (Length)", default=2, min=0, max=10)
    hole_stacks: IntProperty(name="Hole Stacks (Width)", default=1, min=1, max=5)

    # Topology
    segments: IntProperty(name="Segments", default=8, min=4, max=64)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon="DRIVER_DISTANCE")
        box.prop(self, "shape_type")
        box.prop(self, "leg_len")
        box.prop(self, "width")
        box.prop(self, "thick")

        box = layout.box()
        box.label(text="Mounting Grid", icon="MOD_ARRAY")
        row = box.row()
        row.prop(self, "hole_count", text="Length")
        row.prop(self, "hole_stacks", text="Width")
        box.prop(self, "hole_rad")

        box = layout.box()
        box.label(text="Topology", icon="MESH_GRID")
        box.prop(self, "segments")

    def get_slot_meta(self):
        return {
            0: {"name": "Metal_Body", "uv": "BOX", "phys": "METAL_STEEL"},
            9: {"name": "Socket_Anchor", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def build_shape(self, bm):
        # ----------------------------------------------------------------------
        # 1. SETUP & PARAMS
        # ----------------------------------------------------------------------
        l, w, th = self.leg_len, self.width, self.thick

        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # Resolution Safety
        seg = max(4, self.segments)
        if seg % 4 != 0:
            seg = (seg // 4) * 4

        # Radius Clamp
        stack_w = w / self.hole_stacks
        safe_rad_w = stack_w / 3.3

        if self.hole_count > 0:
            zone_len = l / (self.hole_count + 1)
            safe_rad_l = zone_len / 2.5
            actual_rad = min(self.hole_rad, safe_rad_w, safe_rad_l)
        else:
            actual_rad = 0.0

        # ----------------------------------------------------------------------
        # 2. CORE TOPOLOGY HELPERS
        # ----------------------------------------------------------------------
        def create_quad_face(bm, p1, p2, p3, p4):
            if (p1 - p2).length < 1e-6 or (p3 - p4).length < 1e-6:
                return None
            return bm.faces.new(
                (bm.verts.new(p1), bm.verts.new(p2), bm.verts.new(p3), bm.verts.new(p4))
            )

        def create_socket_pair(bm, cx, cy, z_offset, matrix):
            """
            Creates BACK-TO-BACK sockets.
            Top: Points UP/OUT.
            Bottom: Points DOWN/OUT.
            """
            r = 0.0025  # Anchor size

            # --- TOP SOCKET (Extruded Side) ---
            # Position: (cx, cy, z_offset)
            t1 = Vector((cx, cy + r, z_offset))
            t2 = Vector((cx - r * 0.866, cy - r * 0.5, z_offset))
            t3 = Vector((cx + r * 0.866, cy - r * 0.5, z_offset))

            # Standard Winding (CCW) -> Normal +Z
            vs_top = [bm.verts.new(matrix @ p) for p in [t1, t2, t3]]
            f_top = bm.faces.new(vs_top)
            f_top.material_index = 9

            # --- BOTTOM SOCKET (Base Side) ---
            # Position: (cx, cy, 0)
            b1 = Vector((cx, cy + r, 0))
            b2 = Vector((cx - r * 0.866, cy - r * 0.5, 0))
            b3 = Vector((cx + r * 0.866, cy - r * 0.5, 0))

            # Standard Winding (CCW) -> Normal +Z
            vs_bot = [bm.verts.new(matrix @ p) for p in [b1, b2, b3]]
            f_bot = bm.faces.new(vs_bot)
            f_bot.material_index = 9

            # FORCE FLIP NORMAL
            # This guarantees it points -Z (Opposite to Top)
            f_bot.normal_flip()

            return [f_top, f_bot]

        def build_washer_cell(bm, cx, cy, r, top_y, bot_y, segs, matrix):
            pad = r * 0.6
            box_r = r + pad
            circ_pts = []
            box_pts = []

            for i in range(segs):
                angle = (i / segs) * 2 * math.pi
                circ_pts.append(
                    Vector((cx + math.cos(angle) * r, cy + math.sin(angle) * r, 0))
                )
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                scale = 1.0 / max(abs(cos_a), abs(sin_a), 0.0001)
                box_pts.append(
                    Vector((cx + cos_a * scale * box_r, cy + sin_a * scale * box_r, 0))
                )

            c_vecs = [matrix @ p for p in circ_pts]
            b_vecs = [matrix @ p for p in box_pts]

            # Washer Loop
            for i in range(segs):
                idx_next = (i + 1) % segs
                f = create_quad_face(
                    bm, c_vecs[i], b_vecs[i], b_vecs[idx_next], c_vecs[idx_next]
                )
                if f:
                    for e in f.edges:
                        vm = matrix.inverted() @ ((e.verts[0].co + e.verts[1].co) / 2)
                        if abs(
                            (Vector((vm.x, vm.y, 0)) - Vector((cx, cy, 0))).length - r
                        ) < (r * 0.1):
                            e[edge_slots] = 1

            # Spawn Socket PAIR
            create_socket_pair(bm, cx, cy, th, matrix)

            # Outer Fill
            idx_tr = segs // 8
            idx_tl = (segs // 2) - idx_tr
            idx_bl = (segs // 2) + idx_tr
            idx_br = segs - idx_tr

            def proj_y(vec, y_val):
                v_local = matrix.inverted() @ vec
                return matrix @ Vector((v_local.x, y_val, 0))

            top_proj = []
            box_top = []
            bot_proj = []
            box_bot = []

            for i in range(idx_tr, idx_tl + 1):
                box_top.append(b_vecs[i])
                top_proj.append(proj_y(b_vecs[i], top_y))
            for k in range(len(box_top) - 1):
                create_quad_face(
                    bm, box_top[k], top_proj[k], top_proj[k + 1], box_top[k + 1]
                )

            for i in range(idx_bl, idx_br + 1):
                box_bot.append(b_vecs[i])
                bot_proj.append(proj_y(b_vecs[i], bot_y))
            for k in range(len(box_bot) - 1):
                create_quad_face(
                    bm, box_bot[k], bot_proj[k], bot_proj[k + 1], box_bot[k + 1]
                )

            left_port = [top_proj[-1]] + b_vecs[idx_tl : idx_bl + 1] + [bot_proj[0]]
            right_port = [top_proj[0]]
            curr = idx_tr
            while True:
                right_port.append(b_vecs[curr])
                if curr == idx_br:
                    break
                curr -= 1
                if curr < 0:
                    curr = segs - 1
            right_port.append(bot_proj[-1])

            return left_port, right_port

        def build_spacer_block(bm, port_left, len_x, matrix):
            off = matrix @ Vector((len_x, 0, 0)) - matrix @ Vector((0, 0, 0))
            port_right = [v + off for v in port_left]
            for i in range(len(port_left) - 1):
                create_quad_face(
                    bm, port_left[i], port_left[i + 1], port_right[i + 1], port_right[i]
                )
            return port_right

        # ----------------------------------------------------------------------
        # 3. CALCULATORS
        # ----------------------------------------------------------------------
        def get_stack_centers_and_bounds(total_w, stacks):
            zone_h = total_w / stacks
            results = []
            start_y = total_w / 2
            for i in range(stacks):
                top = start_y - (i * zone_h)
                bot = start_y - ((i + 1) * zone_h)
                cy = (top + bot) / 2
                results.append((cy, top, bot))
            return results

        def get_port_y_coords(total_w, stacks, r, segs):
            pad = r * 0.6
            box_r = r + pad
            stack_data = get_stack_centers_and_bounds(total_w, stacks)
            full_y_list = []

            for idx, (cy, top, bot) in enumerate(stack_data):
                if idx == 0:
                    full_y_list.append(top)
                idx_tr = segs // 8
                idx_tl = (segs // 2) - idx_tr
                idx_bl = (segs // 2) + idx_tr
                for k in range(idx_tl, idx_bl + 1):
                    ang = (k / segs) * 2 * math.pi
                    cos_a = math.cos(ang)
                    sin_a = math.sin(ang)
                    scale = 1.0 / max(abs(cos_a), abs(sin_a), 0.0001)
                    by = cy + (sin_a * scale * box_r)
                    full_y_list.append(by)
                full_y_list.append(bot)
            return full_y_list

        # ----------------------------------------------------------------------
        # 4. BUILDER
        # ----------------------------------------------------------------------
        def build_leg_segment(
            bm, matrix, length, width, h_rad, count, stacks, start_port=None
        ):
            current_port = start_port
            if current_port is None:
                y_coords = get_port_y_coords(width, stacks, h_rad, seg)
                current_port = [matrix @ Vector((0, y, 0)) for y in y_coords]

            step = length / (count + 1)
            for i in range(count):
                hole_x = step * (i + 1)
                curr_local_x = (matrix.inverted() @ current_port[0]).x
                pad = h_rad * 0.6
                box_r = h_rad + pad
                dist = (hole_x - box_r) - curr_local_x

                if dist > 0.0001:
                    current_port = build_spacer_block(bm, current_port, dist, matrix)

                stack_data = get_stack_centers_and_bounds(width, stacks)
                col_left_port = []
                col_right_port = []

                for s_idx, (cy, top, bot) in enumerate(stack_data):
                    l_port, r_port = build_washer_cell(
                        bm, hole_x, cy, h_rad, top, bot, seg, matrix
                    )
                    if s_idx == 0:
                        col_left_port.extend(l_port)
                        col_right_port.extend(r_port)
                    else:
                        col_left_port.extend(l_port[1:])
                        col_right_port.extend(r_port[1:])

                for k in range(min(len(current_port), len(col_left_port)) - 1):
                    create_quad_face(
                        bm,
                        current_port[k],
                        current_port[k + 1],
                        col_left_port[k + 1],
                        col_left_port[k],
                    )
                current_port = col_right_port

            curr_local_x = (matrix.inverted() @ current_port[0]).x
            rem = length - curr_local_x
            if rem > 0.0001:
                current_port = build_spacer_block(bm, current_port, rem, matrix)
            return current_port

        # ----------------------------------------------------------------------
        # 5. EXECUTION
        # ----------------------------------------------------------------------
        if self.shape_type == "FLAT":
            build_leg_segment(
                bm,
                Matrix.Identity(4),
                l,
                w,
                actual_rad,
                self.hole_count,
                self.hole_stacks,
                None,
            )
        elif self.shape_type == "L_BRACKET":
            p = build_leg_segment(
                bm,
                Matrix.Identity(4),
                l,
                w,
                actual_rad,
                self.hole_count,
                self.hole_stacks,
                None,
            )
            mat_up = Matrix.Translation((l, 0, 0)) @ Matrix.Rotation(
                math.radians(-90), 4, "Y"
            )
            build_leg_segment(
                bm, mat_up, l, w, actual_rad, self.hole_count, self.hole_stacks, p
            )
        elif self.shape_type == "U_BRACKET":
            mat_1 = Matrix.Translation((0, 0, l)) @ Matrix.Rotation(
                math.radians(90), 4, "Y"
            )
            p = build_leg_segment(
                bm, mat_1, l, w, actual_rad, self.hole_count, self.hole_stacks, None
            )
            mat_2 = Matrix.Translation((0, 0, 0))
            p = build_leg_segment(
                bm, mat_2, l, w, actual_rad, self.hole_count, self.hole_stacks, p
            )
            mat_3 = Matrix.Translation((l, 0, 0)) @ Matrix.Rotation(
                math.radians(-90), 4, "Y"
            )
            build_leg_segment(
                bm, mat_3, l, w, actual_rad, self.hole_count, self.hole_stacks, p
            )

        # ----------------------------------------------------------------------
        # 6. FINISH (SOCKET SAFEGUARD)
        # ----------------------------------------------------------------------

        # A. WELD MAIN BODY (Exclude Sockets)
        sock_verts = set()
        for f in bm.faces:
            if f.material_index == 9:
                for v in f.verts:
                    sock_verts.add(v)

        main_verts = [v for v in bm.verts if v not in sock_verts]
        bmesh.ops.remove_doubles(bm, verts=main_verts, dist=0.001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # B. EXTRUDE (Exclude Sockets)
        faces_to_extrude = [f for f in bm.faces if f.material_index != 9]
        if faces_to_extrude:
            ret = bmesh.ops.extrude_face_region(bm, geom=faces_to_extrude)
            verts_ext = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
            for v in verts_ext:
                v.co += v.normal * th

        # C. FINAL WELD (Exclude Sockets)
        sock_verts = set()
        for f in bm.faces:
            if f.material_index == 9:
                for v in f.verts:
                    sock_verts.add(v)
        main_verts = [v for v in bm.verts if v not in sock_verts]

        if CARTRIDGE_META["flags"]["USE_WELD"]:
            bmesh.ops.remove_doubles(bm, verts=main_verts, dist=0.001)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # ----------------------------------------------------------------------
        # 7. EDGE DISCIPLINE
        # ----------------------------------------------------------------------
        for e in bm.edges:
            if e[edge_slots] == 1:
                continue
            if any(f.material_index == 9 for f in e.link_faces):
                continue
            if len(e.link_faces) != 2:
                continue

            ang = e.calc_face_angle()
            if ang > math.radians(60):
                e[edge_slots] = 2
            if ang > math.radians(89):
                e[edge_slots] = 1
