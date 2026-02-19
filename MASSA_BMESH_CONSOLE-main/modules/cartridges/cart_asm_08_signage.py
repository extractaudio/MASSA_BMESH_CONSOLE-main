import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_08: Highway Signage Gantry",
    "id": "asm_08_signage",
    "icon": "MOD_CURVE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmSignage(Massa_OT_Base):
    bl_idname = "massa.gen_asm_08_signage"
    bl_label = "ASM_08: Highway Signage"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    pillar_height: FloatProperty(name="Pillar Height", default=6.0, min=3.0)
    overhang_length: FloatProperty(name="Overhang Length", default=8.0, min=4.0)
    thickness: FloatProperty(name="Structure Thickness", default=0.5, min=0.2)

    sign_width: FloatProperty(name="Sign Width", default=6.0, min=2.0)
    sign_height: FloatProperty(name="Sign Height", default=3.0, min=1.0)
    sign_tilt: FloatProperty(name="Sign Tilt (deg)", default=5.0, min=-15.0, max=15.0)

    truss_density: IntProperty(name="Truss Density", default=4, min=2)

    def get_slot_meta(self):
        return {
            0: {"name": "Structure (Steel)", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "Concrete Base", "uv": "SKIP", "phys": "CONCRETE"},
            2: {"name": "Truss Frame", "uv": "SKIP", "phys": "METAL_RUST"},
            4: {"name": "Sign Face (Emission)", "uv": "SKIP", "phys": "GLASS_SCREEN"}, # UV FIT
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "pillar_height")
        col.prop(self, "overhang_length")
        col.prop(self, "thickness")

        layout.separator()
        layout.label(text="SIGN", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "sign_width")
        col.prop(self, "sign_height")
        col.prop(self, "sign_tilt")
        col.prop(self, "truss_density")

    def build_shape(self, bm: bmesh.types.BMesh):
        ph, ol, th = self.pillar_height, self.overhang_length, self.thickness
        sw, sh = self.sign_width, self.sign_height

        # 1. Base Pillar (Cylinder)
        res = bmesh.ops.create_circle(bm, cap_ends=True, radius=th, segments=12)
        base_face = res['faces'][0] if 'faces' in res and len(res['faces']) > 0 else bm.faces[-1] # Usually created at origin

        # Extrude up to curve start
        curve_radius = th * 2.0
        straight_h = ph - curve_radius

        res_ext = bmesh.ops.extrude_face_region(bm, geom=[base_face])
        verts_ext = [v for v in res_ext['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=verts_ext, vec=(0, 0, straight_h))

        # Find top face
        top_face = None
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            if f.normal.z > 0.9 and abs(f.calc_center_median().z - straight_h) < 0.1:
                top_face = f
                break

        # 2. Radial Sweep (90 deg curve)
        # Spin around Y axis (if we want to overhang in X) or X axis (overhang in Y).
        # Let's overhang in +X.
        # Pivot is at (current_x + radius, current_z) if we spin 90 deg.
        # Wait, if we are at (0,0, straight_h), and we want to curve to +X.
        # We need a pivot at (radius, 0, straight_h).
        # And spin -90 degrees around Y axis?
        # A spin around Y axis at (r, 0, h) starting from (0, 0, h) would go to (r, 0, h+r). That's up.
        # We want to go from vertical (Z) to horizontal (X).
        # So we pivot around (radius, 0, straight_h) is wrong.
        # Pivot should be at (radius, 0, straight_h) relative to the top face?
        # No, if we want a 90 deg turn.
        # Center of curvature is at (radius, 0, straight_h) if we start at (0, 0, straight_h).
        # Then we spin -90 deg around Y.
        # Result: (radius, 0, straight_h + radius). No.

        # Let's rethink.
        # Start: (0, 0, h). Direction +Z.
        # End: (r, 0, h+r). Direction +X.
        # Center: (r, 0, h).
        # Spin axis: Y.
        # Angle: -90?
        # Start vector relative to center: (-r, 0, 0).
        # Rotate -90 deg around Y: (0, 0, r).
        # Position: Center + (0, 0, r) = (r, 0, h+r).
        # Tangent: Was +Z (0,0,1). Becomes +X (1,0,0). Correct.

        # So pivot is at (curve_radius, 0, straight_h).
        # But we need to ensure the spin direction.

        if top_face:
            spin_steps = 6
            bmesh.ops.spin(
                bm,
                geom=[top_face],
                cent=(curve_radius, 0, straight_h),
                axis=(0, 1, 0),
                dtheta=math.radians(-90),
                steps=spin_steps,
                use_duplicate=False
            )

            # Find the new face (now facing +X)
            # It should be at x ~ curve_radius, z ~ straight_h + curve_radius

            # 3. Straight Overhang
            # Extrude remaining length
            # Total overhang is ol. We covered curve_radius in X.
            remain_l = ol - curve_radius
            if remain_l > 0:
                bm.faces.ensure_lookup_table()
                end_face = None
                for f in bm.faces:
                    # Normal +X
                    if f.normal.x > 0.9 and f.calc_center_median().z > straight_h:
                        end_face = f
                        break

                if end_face:
                    res_ext2 = bmesh.ops.extrude_face_region(bm, geom=[end_face])
                    verts_ext2 = [v for v in res_ext2['geom'] if isinstance(v, bmesh.types.BMVert)]
                    bmesh.ops.translate(bm, verts=verts_ext2, vec=(remain_l, 0, 0))

        # Assign Slot 0 (Structure)
        for f in bm.faces:
            f.material_index = 0

        # 4. Sign Canvas
        # Positioned along the overhang.
        # Center X = curve_radius + remain_l / 2 ? Or near the end?
        # Usually centered on the road lanes.
        # Let's place it at 2/3 of the overhang.
        sign_center_x = curve_radius + (ol - curve_radius) * 0.6
        sign_center_z = straight_h + curve_radius # Height of the horizontal beam

        # Sign hangs down or sits on front?
        # Usually front face attached to the truss.
        # Let's create a separate box for the sign.

        # Create Sign Box
        ret = bmesh.ops.create_cube(bm, size=1.0)
        s_verts = ret['verts']
        bmesh.ops.scale(bm, vec=(0.2, sw, sh), verts=s_verts) # Thin in X, Wide in Y (assuming road is Y?)
        # Wait, usually the gantry crosses the road. If pillar is at X=0, road is along Y? No, road is along Y means gantry is along X.
        # Yes. So sign faces +/- Y.
        # My pillar overhangs along +X. So the beam is along X.
        # The sign should be perpendicular to Y (the road).
        # So Sign Normal is Y.
        # Dimensions: Width along X, Height along Z.

        # Re-scale:
        # Width (sw) is along X.
        # Height (sh) is along Z.
        # Thickness (0.2) is along Y.
        bmesh.ops.scale(bm, vec=(sw, 0.2, sh), verts=s_verts)

        # Translate
        # Center at (sign_center_x, 0, sign_center_z)
        # Offset Y by thickness/2 + beam thickness/2
        offset_y = -th - 0.2
        bmesh.ops.translate(bm, vec=(sign_center_x, offset_y, sign_center_z), verts=s_verts)

        # Tilt
        # Rotate around X axis at sign center
        bmesh.ops.rotate(
            bm,
            verts=s_verts,
            cent=(sign_center_x, offset_y, sign_center_z),
            matrix=Matrix.Rotation(math.radians(self.sign_tilt), 3, 'X')
        )

        # Assign Slot 4 (Sign Face)
        # Only the front face (facing -Y)
        s_faces = []
        for v in s_verts:
            for f in v.link_faces:
                s_faces.append(f)
                f.material_index = 2 # Truss/Back Frame default

        bm.faces.ensure_lookup_table()
        sign_face = None
        for f in s_faces:
            if f.normal.y < -0.8: # Facing towards oncoming traffic (-Y)
                f.material_index = 4
                sign_face = f

        # 5. Truss Support
        # Simple connections between beam and sign
        # Create struts
        # ... (Simplified for macro scale: just box connections)

        num_struts = 2
        for i in range(num_struts):
            sx = sign_center_x - sw/3 + (i * 2 * sw/3)

            ret = bmesh.ops.create_cube(bm, size=1.0)
            t_verts = ret['verts']
            bmesh.ops.scale(bm, vec=(0.2, abs(offset_y), 0.2), verts=t_verts)
            bmesh.ops.translate(bm, vec=(sx, offset_y/2, sign_center_z), verts=t_verts)
            for v in t_verts:
                for f in v.link_faces:
                    f.material_index = 0 # Steel

        # 6. UV Mapping
        uv_layer = bm.loops.layers.uv.verify()

        for f in bm.faces:
            if f.material_index == 4: # Sign Face (FIT)
                # Fit UVs 0-1
                # Project based on local XZ plane (since normal is Y)
                vs = [v.co for v in f.verts]
                min_x = min(v.x for v in vs)
                max_x = max(v.x for v in vs)
                min_z = min(v.z for v in vs)
                max_z = max(v.z for v in vs)

                dx = max_x - min_x
                dz = max_z - min_z

                for l in f.loops:
                    v = l.vert.co
                    u = (v.x - min_x) / dx if dx > 0 else 0
                    v_coord = (v.z - min_z) / dz if dz > 0 else 0
                    l[uv_layer].uv = (u, v_coord)
            else:
                # Box Map
                for l in f.loops:
                    nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                    if nz > 0.5:
                        u, v = l.vert.co.x, l.vert.co.y
                    elif ny > 0.5:
                        u, v = l.vert.co.x, l.vert.co.z
                    else:
                        u, v = l.vert.co.y, l.vert.co.z
                    l[uv_layer].uv = (u, v)
