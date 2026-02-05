"""
Filename: modules/cartridges/prim_con_truss.py
Content: Modular Truss Generator (Planar & Box)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector

CARTRIDGE_META = {
    "name": "Con: Truss",
    "id": "prim_con_truss",
    "icon": "MESH_GRID",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_truss(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_truss"
    bl_label = "Construction Truss"
    bl_description = "Modular Truss Segment (Planar or Box)"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMS ---
    length: FloatProperty(name="Length", default=3.0, min=0.5, unit="LENGTH")
    height: FloatProperty(name="Height", default=0.5, min=0.1, unit="LENGTH")
    width: FloatProperty(
        name="Width",
        default=0.5,
        min=0.0,
        unit="LENGTH",
        description="Set to 0 for Planar",
    )

    # --- STRUTS ---
    radius: FloatProperty(name="Tube Radius", default=0.04, min=0.005)
    sections: IntProperty(name="Bays", default=4, min=1)
    x_brace: BoolProperty(name="X-Bracing", default=False)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.prop(self, "length")
        box.prop(self, "height")
        box.prop(self, "width")

        box = layout.box()
        box.label(text="Structure", icon="MESH_GRID")
        box.prop(self, "radius")
        box.prop(self, "sections")
        box.prop(self, "x_brace")

    def get_slot_meta(self):
        return {
            0: {"name": "Truss_Frame", "uv": "TUBE_Y", "phys": "METAL_ALUMINUM"},
            1: {"name": "Joints", "uv": "BOX", "phys": "METAL_STEEL"},
            3: {"name": "Socket", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def build_shape(self, bm):
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 0. HELPER: CREATE TUBE SEGMENT
        def make_tube(p1, p2, rad, mat_idx):
            vec = p2 - p1
            length = vec.length
            if length < 0.001:
                return

            # Orientation
            up = Vector((0, 0, 1))
            if abs(vec.normalized().dot(up)) > 0.99:
                up = Vector((1, 0, 0))
            quat = Vector((0, 0, 1)).rotation_difference(vec)
            mat = quat.to_matrix().to_4x4()
            mat.translation = p1

            # Create Circle
            verts = []
            segs = 6  # Optimized
            for i in range(segs):
                ang = (i / segs) * 2 * math.pi
                v_local = Vector((math.cos(ang) * rad, math.sin(ang) * rad, 0))
                v_world = mat @ v_local
                verts.append(bm.verts.new(v_world))

            f = bm.faces.new(verts)
            f.material_index = mat_idx

            # Extrude
            ret = bmesh.ops.extrude_face_region(bm, geom=[f])
            verts_ext = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
            faces_side = [f for f in ret["geom"] if isinstance(f, bmesh.types.BMFace)]

            bmesh.ops.translate(bm, verts=verts_ext, vec=vec)

            # Tag Edges (Contour)
            for f_side in faces_side:
                f_side.material_index = mat_idx
                for e in f_side.edges:
                    v_edge = (e.verts[1].co - e.verts[0].co).normalized()
                    if abs(v_edge.dot(vec.normalized())) > 0.9:
                        e[edge_slots] = 3  # Guide

        # 1. CALCULATE RAIL NODES
        l, h, w = self.length, self.height, self.width
        is_box = w > 0.001

        rails = []
        if is_box:
            rails.append([Vector((0, -w / 2, 0)), Vector((l, -w / 2, 0))])  # BL
            rails.append([Vector((0, w / 2, 0)), Vector((l, w / 2, 0))])  # BR
            rails.append([Vector((0, -w / 2, h)), Vector((l, -w / 2, h))])  # TL
            rails.append([Vector((0, w / 2, h)), Vector((l, w / 2, h))])  # TR
        else:
            rails.append([Vector((0, 0, 0)), Vector((l, 0, 0))])  # Bottom
            rails.append([Vector((0, 0, h)), Vector((l, 0, h))])  # Top

        # 2. GENERATE LONGITUDINAL RAILS
        for r_pts in rails:
            make_tube(r_pts[0], r_pts[1], self.radius, 0)

        # 3. GENERATE BRACING
        def brace_pair(r1_start, r1_end, r2_start, r2_end, count):
            step_1 = (r1_end - r1_start) / count
            step_2 = (r2_end - r2_start) / count

            for i in range(count):
                p1_a = r1_start + (step_1 * i)
                p1_b = r1_start + (step_1 * (i + 1))
                p2_a = r2_start + (step_2 * i)
                p2_b = r2_start + (step_2 * (i + 1))

                make_tube(p1_a, p2_b, self.radius * 0.7, 0)
                make_tube(p2_b, p1_b, self.radius * 0.7, 0)

                if self.x_brace:
                    make_tube(p1_a, p2_a, self.radius * 0.7, 0)  # Vertical
                    make_tube(p1_b, p2_a, self.radius * 0.7, 0)  # Crossing

        if is_box:
            brace_pair(
                rails[0][0], rails[0][1], rails[2][0], rails[2][1], self.sections
            )  # Left
            brace_pair(
                rails[1][0], rails[1][1], rails[3][0], rails[3][1], self.sections
            )  # Right

            for i in range(self.sections + 1):
                fac = i / self.sections
                x = l * fac
                make_tube(
                    Vector((x, -w / 2, 0)), Vector((x, w / 2, 0)), self.radius * 0.6, 1
                )  # Bot
                make_tube(
                    Vector((x, -w / 2, h)), Vector((x, w / 2, h)), self.radius * 0.6, 1
                )  # Top
        else:
            brace_pair(
                rails[0][0], rails[0][1], rails[1][0], rails[1][1], self.sections
            )
            for i in range(self.sections + 1):
                fac = i / self.sections
                x = l * fac
                make_tube(Vector((x, 0, 0)), Vector((x, 0, h)), self.radius * 0.6, 1)

        if self._get_cartridge_meta()["flags"]["USE_WELD"]:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
