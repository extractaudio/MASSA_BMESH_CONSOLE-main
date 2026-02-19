import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_18: Parabolic Radar Array",
    "id": "asm_18_radar_array",
    "icon": "MOD_BUILD",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_AsmRadarArray(Massa_OT_Base):
    bl_idname = "massa.gen_asm_18_radar_array"
    bl_label = "ASM_18 Radar Array"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    dish_diameter: FloatProperty(name="Dish Diameter", default=4.0, min=1.0, unit="LENGTH")
    dish_depth: FloatProperty(name="Dish Depth", default=0.8, min=0.1, unit="LENGTH")
    base_height: FloatProperty(name="Base Height", default=2.0, min=0.5, unit="LENGTH")

    # --- 2. ORIENTATION ---
    yaw: FloatProperty(name="Yaw", default=0.0, min=-180, max=180, unit="ROTATION")
    pitch: FloatProperty(name="Pitch", default=45.0, min=-90, max=90, unit="ROTATION")

    # --- 3. DETAILS ---
    strut_thick: FloatProperty(name="Strut Thickness", default=0.05, min=0.01, unit="LENGTH")
    horn_length: FloatProperty(name="Horn Length", default=1.5, min=0.5, unit="LENGTH")

    # --- 4. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Base", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Dish", "uv": "BOX", "phys": "METAL_ALUMINUM"}, # Or manual UV?
            2: {"name": "Mechanics", "uv": "BOX", "phys": "METAL_DARK"},
            3: {"name": "Receiver", "uv": "BOX", "phys": "PLASTIC_HARD"},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "dish_diameter")
        col.prop(self, "dish_depth")
        col.prop(self, "base_height")

        col.separator()
        col.label(text="Orientation")
        col.prop(self, "yaw")
        col.prop(self, "pitch")

        col.separator()
        col.label(text="Details")
        col.prop(self, "strut_thick")
        col.prop(self, "horn_length")

        col.separator()
        col.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        dd = self.dish_diameter
        depth = self.dish_depth
        bh = self.base_height
        yaw = self.yaw
        pitch = self.pitch
        st = self.strut_thick
        hl = self.horn_length

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale

        # 1. BASE (Tripod)
        # 3 legs at 120 deg.
        # Center hub.

        # Hub cylinder
        res_hub = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, diameter1=0.6, diameter2=0.6, depth=bh)
        bmesh.ops.translate(bm, vec=(0, 0, bh/2), verts=res_hub['verts'])

        # Assign base material
        for f in res_hub['faces']:
            f.material_index = 0
            self.apply_box_map(f, uv_layer, scale)

        # Legs
        for i in range(3):
            ang = i * (2 * math.pi / 3)
            # Leg from (0,0,bh*0.8) to (R, R, 0)
            leg_r = dd * 0.4

            # Vector
            start = Vector((0, 0, bh * 0.8))
            end = Vector((math.cos(ang) * leg_r, math.sin(ang) * leg_r, 0))

            # Create a cylinder/box along this vector
            # Use a simple box scaled and rotated? Or create_cone from start to end?
            # Creating a box is easier.
            vec = end - start
            length = vec.length
            mid = (start + end) / 2

            # Rotation to align Z to vec
            rot_quat = vec.to_track_quat('Z', 'Y')
            rot_mat = rot_quat.to_matrix().to_4x4()

            res_leg = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(0.2, 0.2, length), verts=res_leg['verts'])
            bmesh.ops.rotate(bm, cent=(0,0,0), matrix=rot_mat, verts=res_leg['verts'])
            bmesh.ops.translate(bm, vec=mid, verts=res_leg['verts'])

            for f in res_leg['faces']:
                f.material_index = 0
                self.apply_box_map(f, uv_layer, scale)

        # 2. YOKE (U-Shape)
        # Sits on top of hub (bh). Rotates with Yaw.

        # Yaw Matrix
        mat_yaw = Matrix.Rotation(yaw, 4, 'Z')

        # Yoke Base
        res_yoke_base = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(dd * 0.6, 0.4, 0.2), verts=res_yoke_base['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, bh + 0.1), verts=res_yoke_base['verts'])

        # Yoke Arms
        yoke_geom = res_yoke_base['verts'][:]
        for side in [-1, 1]:
            res_arm = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(0.2, 0.4, 1.0), verts=res_arm['verts'])
            # Position: side * width/2, 0, bh + 0.1 + height/2
            bmesh.ops.translate(bm, vec=(side * dd * 0.3, 0, bh + 0.1 + 0.5), verts=res_arm['verts'])
            yoke_geom.extend(res_arm['verts'])

        # Rotate Yoke by Yaw
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=mat_yaw, verts=yoke_geom)

        for f in list({f for v in yoke_geom for f in v.link_faces}):
            f.material_index = 2
            self.apply_box_map(f, uv_layer, scale)

        # 3. DISH (Parabolic)
        # Pivot point is between yoke arms: (0, 0, bh + 0.1 + 0.5 + some_offset)
        # Let's say pivot height = bh + 0.8
        pivot_z = bh + 0.8
        pivot_pt = Vector((0, 0, pivot_z))

        # Build dish at origin, then transform.
        # Parabola z = c * (x^2 + y^2)
        # At rim (radius R=dd/2), z = depth.
        # depth = c * R^2  =>  c = depth / R^2

        R = dd / 2
        c = depth / (R * R)

        # Create grid/rings
        rings = 8
        segs = 16

        dish_verts = []

        # Center vertex
        center_v = bm.verts.new((0,0,0))
        dish_verts.append(center_v)

        prev_ring_verts = []

        for r_idx in range(1, rings + 1):
            curr_r = (r_idx / rings) * R
            curr_z = c * (curr_r * curr_r)

            curr_ring_verts = []
            for s in range(segs):
                ang = s * (2 * math.pi / segs)
                x = math.cos(ang) * curr_r
                y = math.sin(ang) * curr_r
                v = bm.verts.new((x, y, curr_z))
                curr_ring_verts.append(v)
                dish_verts.append(v)

            # Skin faces
            if r_idx == 1:
                # Triangle fan to center
                for s in range(segs):
                    s_next = (s + 1) % segs
                    f = bm.faces.new((center_v, curr_ring_verts[s], curr_ring_verts[s_next]))
                    f.material_index = 1
            else:
                # Quads between rings
                for s in range(segs):
                    s_next = (s + 1) % segs
                    v1 = prev_ring_verts[s]
                    v2 = prev_ring_verts[s_next]
                    v3 = curr_ring_verts[s_next]
                    v4 = curr_ring_verts[s]
                    f = bm.faces.new((v1, v2, v3, v4))
                    f.material_index = 1

            prev_ring_verts = curr_ring_verts

        # Add thickness to dish? Mandate says ALLOW_SOLIDIFY is False, so maybe I should extrude or assume single sided.
        # Or I can just duplicate and flip normals for back side, or assume double sided shader.
        # Let's extrude slightly for thickness.
        res_ext = bmesh.ops.extrude_face_region(bm, geom=[f for f in bm.faces if f.material_index == 1])
        verts_ext = [v for v in res_ext['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, 0, -0.05), verts=verts_ext) # Backwards thickness

        # Add Horn
        # Cylinder at center, pointing up Z (local).
        res_horn = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, diameter1=0.2, diameter2=0.1, depth=hl)
        bmesh.ops.translate(bm, vec=(0, 0, hl/2), verts=res_horn['verts'])
        horn_verts = res_horn['verts']
        for f in res_horn['faces']:
            f.material_index = 3

        # Add Struts
        # From rim (prev_ring_verts) to horn tip (0, 0, hl).
        # Pick 3 points on rim.
        strut_verts = []
        for i in range(3):
            idx = int(i * segs / 3)
            rim_v = prev_ring_verts[idx]
            tip_v = Vector((0, 0, hl))

            # Create strut geom
            vec = tip_v - rim_v.co
            mid = (rim_v.co + tip_v) / 2
            length = vec.length

            rot_quat = vec.to_track_quat('Z', 'Y')
            rot_mat_strut = rot_quat.to_matrix().to_4x4()

            res_strut = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(st, st, length), verts=res_strut['verts'])
            bmesh.ops.rotate(bm, cent=(0,0,0), matrix=rot_mat_strut, verts=res_strut['verts'])
            bmesh.ops.translate(bm, vec=mid, verts=res_strut['verts'])

            strut_verts.extend(res_strut['verts'])
            for f in res_strut['faces']:
                f.material_index = 2

        # Combine Dish assembly (Dish + Horn + Struts)
        dish_assembly = dish_verts + horn_verts + strut_verts + verts_ext # Include extruded back

        # Transform Dish Assembly
        # 1. Rotate Pitch (around X axis)
        # 2. Rotate Yaw (around Z axis) - wait, Yaw is global, but Pitch is local to Yaw.
        # So: Pitch then Yaw.
        # 3. Translate to Pivot Point.

        # Pitch Matrix
        mat_pitch = Matrix.Rotation(pitch, 4, 'X')

        # Combine transforms
        # Final = Translate @ Yaw @ Pitch
        mat_final = Matrix.Translation(pivot_pt) @ mat_yaw @ mat_pitch

        bmesh.ops.transform(bm, matrix=mat_final, verts=dish_assembly)

        # UVs for Dish
        # Planar projection from camera view? Or just box.
        # Mandate says Manual UV is preferred.
        # Box map is applied in loop for simple parts.
        # For dish, box map is okay or radial.
        # I'll stick to apply_box_map for now as per "apply_box_map" function usage.

        # Re-apply box map for dish faces as they were moved
        # (Though box map function uses current normals/coords, so calling it AFTER transform is better usually,
        # unless it uses local coords. My apply_box_map uses world coords (bm verts).
        # So I should apply UVs after transform.

        for v in dish_assembly:
            for f in v.link_faces:
                self.apply_box_map(f, uv_layer, scale)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def apply_box_map(self, face, uv_layer, scale):
        n = face.normal
        nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
        for l in face.loops:
            co = l.vert.co
            if nz > nx and nz > ny:
                u, v = co.x, co.y
            elif nx > ny and nx > nz:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            l[uv_layer].uv = (u * scale, v * scale)
