import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_19: Cryo-Pod / Medical Stasis Chamber",
    "id": "asm_19_cryo_pod",
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


class MASSA_OT_AsmCryoPod(Massa_OT_Base):
    bl_idname = "massa.gen_asm_19_cryo_pod"
    bl_label = "ASM_19 Cryo Pod"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    length: FloatProperty(name="Length", default=2.2, min=1.5, unit="LENGTH")
    width: FloatProperty(name="Width", default=1.0, min=0.6, unit="LENGTH")
    height: FloatProperty(name="Height", default=1.0, min=0.5, unit="LENGTH")
    slant_angle: FloatProperty(name="Slant Angle", default=15.0, min=0.0, max=45.0, unit="ROTATION")

    # --- 2. CANOPY ---
    canopy_coverage: FloatProperty(name="Canopy Arc", default=160.0, min=90.0, max=180.0, unit="ROTATION")
    glass_thick: FloatProperty(name="Glass Thickness", default=0.02, min=0.005, unit="LENGTH")

    # --- 3. DETAILS ---
    screen_size: FloatProperty(name="Screen Size", default=0.4, min=0.2, unit="LENGTH")
    tube_count: IntProperty(name="Tube Count", default=2, min=0, max=4)

    # --- 4. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Base Body", "uv": "BOX", "phys": "PLASTIC_HARD"},
            1: {"name": "Bedding", "uv": "BOX", "phys": "FABRIC"},
            2: {"name": "Mechanical", "uv": "BOX", "phys": "METAL_STEEL"},
            3: {"name": "UI Screen", "uv": "FIT", "phys": "GLASS_SCREEN"}, # Fit UV for UI
            8: {"name": "Glass Canopy", "uv": "BOX", "phys": "GLASS_CLEAR"},
            9: {"name": "Sockets", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "slant_angle")

        col.separator()
        col.label(text="Canopy")
        col.prop(self, "canopy_coverage")
        col.prop(self, "glass_thick")

        col.separator()
        col.label(text="Details")
        col.prop(self, "screen_size")
        col.prop(self, "tube_count")

        col.separator()
        col.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        l = self.length
        w = self.width
        h = self.height
        slant = self.slant_angle
        arc = self.canopy_coverage
        gt = self.glass_thick
        ss = self.screen_size

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale

        # 1. BASE
        # Box slanted.
        # Create box at origin, rotate by slant? Or shear?
        # Rotation is better for bed.

        # Bed base thickness
        base_h = h * 0.4

        # Create Bed Base
        res_bed = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, l, base_h), verts=res_bed['verts'])
        # Move up so bottom is at Z=0 (before slant) or relative to center?
        # Center of box is (0,0,0).
        # Translate to (0, 0, base_h/2).
        # Then rotate around X axis (slant).

        # But wait, slant means head is higher than feet.
        # Head at +Y usually? Or -Y. Let's say Head at +Y.
        # Rotate around X axis. Positive X rotation lifts +Y? No, Right Hand Rule: Thumb X, Curl Y->Z.
        # So Positive X lifts +Y up? No, Y becomes Z. Yes.

        rot_mat = Matrix.Rotation(math.radians(slant), 4, 'X')

        # Pivot at feet (-Y end)?
        # Feet at y = -l/2.
        pivot_y = -l/2

        # Move bed to pivot at 0
        bmesh.ops.translate(bm, vec=(0, l/2, base_h/2), verts=res_bed['verts']) # Center now at (0, l/2, base_h/2)? No.
        # Center was (0,0,0). Feet at -l/2.
        # We want Feet at (0, -l/2, 0) to stay fixed?
        # Let's just rotate around center and move up.

        # Reset:
        # Box centered at (0,0,0).
        # Move to (0, 0, base_h/2).
        # Rotate around (0, -l/2, 0).

        pivot = Vector((0, -l/2, 0))
        # Translate relative to pivot
        bmesh.ops.translate(bm, vec=-pivot, verts=res_bed['verts'])
        # Rotate
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=rot_mat, verts=res_bed['verts'])
        # Translate back
        bmesh.ops.translate(bm, vec=pivot, verts=res_bed['verts'])
        # Move up a bit if needed (feet on floor)
        # Feet corner was at Z=0 (bottom).
        # After rotation, feet bottom is still at Z=0 roughly if pivot was bottom-feet.
        # Correct.

        # Assign Material
        for f in res_bed['faces']:
            if f.normal.z > 0.5:
                f.material_index = 1 # Bedding
            else:
                f.material_index = 0 # Base Body
            self.apply_box_map(f, uv_layer, scale)

        # 2. CANOPY (Glass)
        # Arc over the top of the bed.
        # Profile: Arc in XZ plane.
        # Extruded/Spun along Y (bed length).

        # Create arc profile.
        # Radius = w/2 roughly.
        # Center at (0, 0, top_of_bed).

        # Find top center of bed after rotation.
        # Center of bed top face (local): (0, 0, base_h/2)
        # Rotated:
        p_top = Vector((0, 0, base_h/2))
        p_top = rot_mat @ p_top # Rotation around 0,0,0 (if we centered there first)
        # My previous transform logic was complex.

        # Alternative: Build canopy in local space, then apply same transform as bed.

        # Arc Profile in XY (local, before rotation). Actually XZ (width/height).
        # Create vertices for arc.
        arc_verts = []
        segs = 12
        r = w/2

        # Angle coverage: -arc/2 to +arc/2 around Z axis? No, around Y axis in local space.
        # X is width. Z is height.
        # Angle 0 is Up (Z+).
        start_ang = math.radians(90 + arc/2)
        end_ang = math.radians(90 - arc/2)

        for i in range(segs + 1):
            t = i / segs
            ang = start_ang * (1-t) + end_ang * t
            x = math.cos(ang) * r
            z = math.sin(ang) * r
            v = bm.verts.new((x, 0, z + base_h/2)) # On top of bed
            arc_verts.append(v)

        # Extrude along Y (length l)
        res_ext = bmesh.ops.extrude_vert_indiv(bm, verts=arc_verts)
        # Link faces? No, that makes edges.
        # Use extrude_edge_only? We don't have edges yet.

        # Delete those verts, let's use spin or create_grid with bending?
        # Or simple: Create a cylinder, cut it, scale it.
        # "bmesh.ops.spin for an arc".

        # Spin uses a profile.
        # Let's clean up arc_verts and make edges between them first.
        bm.verts.ensure_lookup_table()
        arc_edges = []
        for i in range(len(arc_verts)-1):
            e = bm.edges.new((arc_verts[i], arc_verts[i+1]))
            arc_edges.append(e)

        # Spin/Extrude along Y.
        # Actually just extrude edges.
        res_spin = bmesh.ops.extrude_edge_only(bm, edges=arc_edges)
        verts_spin = [v for v in res_spin['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, l, 0), verts=verts_spin) # Bed length is l.
        # Wait, bed was centered at Y=0 locally? No, Box size l implies -l/2 to l/2.
        # My bed create_cube scale was (w, l, base_h).
        # So it spans Y: -l/2 to l/2.
        # My arc was at Y=0.
        # I should move arc to -l/2 first.
        bmesh.ops.translate(bm, vec=(0, -l/2, 0), verts=arc_verts + verts_spin)

        # Now we have faces.
        # Assign glass material.
        canopy_faces = [f for f in res_spin['geom'] if isinstance(f, bmesh.types.BMFace)]
        for f in canopy_faces:
            f.material_index = 8 # Glass
            self.apply_box_map(f, uv_layer, scale)

        # Add thickness (Solidify)
        res_solid = bmesh.ops.extrude_face_region(bm, geom=canopy_faces)
        verts_solid = [v for v in res_solid['geom'] if isinstance(v, bmesh.types.BMVert)]
        # Normal direction push
        bmesh.ops.translate(bm, vec=(0, 0, -gt), verts=verts_solid) # Simplified thickness down Z (local)

        # Collect all canopy verts
        canopy_all_verts = [v for v in arc_verts + verts_spin + verts_solid if v.is_valid]

        # Transform Canopy (Same as Bed)
        # Translate -pivot, Rotate, Translate pivot
        bmesh.ops.translate(bm, vec=-pivot, verts=canopy_all_verts)
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=rot_mat, verts=canopy_all_verts)
        bmesh.ops.translate(bm, vec=pivot, verts=canopy_all_verts)

        # 3. UI SCREEN (Floating)
        # Plane on arm.
        # Attached to side of bed (e.g., Right side +X).
        # Position: X = w/2 + 0.1, Y = l/4, Z = base_h + 0.5 (approx).

        arm_root = Vector((w/2, l/4, base_h * 0.5)) # Local
        # Transform root
        arm_root_world = rot_mat @ (arm_root - pivot) + pivot

        # Screen position
        screen_pos = arm_root_world + Vector((0.3, 0.1, 0.5))

        # Arm (Cylinders/Joints)
        # Simple line from root to screen.
        vec = screen_pos - arm_root_world
        dist = vec.length
        mid = (arm_root_world + screen_pos) / 2
        rot_quat = vec.to_track_quat('Z', 'Y')
        res_arm = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(0.05, 0.05, dist), verts=res_arm['verts'])
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=rot_quat.to_matrix().to_4x4(), verts=res_arm['verts'])
        bmesh.ops.translate(bm, vec=mid, verts=res_arm['verts'])
        for f in res_arm['faces']:
            f.material_index = 2 # Mechanical

        # Screen Plane
        # Facing -X roughly (towards bed).
        res_screen = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=ss)
        # Rotate to face -X? Or towards camera?
        # Rotate 90 Y -> Face X. -90 Y -> Face -X? No.
        # Grid Normal is Z.
        # Rot 90 Y -> Normal X.
        # We want to face Bed (Left).
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-90), 4, 'Y'), verts=res_screen['verts'])
        # Tilt up slightly
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-20), 4, 'X'), verts=res_screen['verts'])

        bmesh.ops.translate(bm, vec=screen_pos, verts=res_screen['verts'])

        for f in res_screen['faces']:
            f.material_index = 3 # UI
            # Fit UV? Mandate says "Slot 3 (Fit UV)".
            # Manual UV for Fit: 0..1
            for loop in f.loops:
                # Simple planar mapping 0-1
                # Vertices are roughly square in local space before transform.
                # Assuming grid order: BL, BR, TR, TL?
                # create_grid order is usually row-major.
                # Let's map based on local coords?
                # Or just assign 0,0 1,0 1,1 0,1.
                # Grid of size 1 has 4 verts.
                pass
            # Let's just use standard box map for now, unless specific requirement.
            # "Slot 3 (Fit UV) for the UI screen plane so a game engine can project..."
            # Means UVs must be 0-1 covering the face.
            # Let's force it.
            loops = f.loops
            if len(loops) == 4:
                loops[0][uv_layer].uv = (0, 0)
                loops[1][uv_layer].uv = (1, 0)
                loops[2][uv_layer].uv = (1, 1)
                loops[3][uv_layer].uv = (0, 1)

        # 4. TUBES
        if self.tube_count > 0:
            tube_r = 0.08
            # Connect from underside of bed
            tube_start_local = Vector((0, l/3, base_h * 0.2))
            tube_start = rot_mat @ (tube_start_local - pivot) + pivot

            for i in range(self.tube_count):
                offset_x = (i - (self.tube_count-1)/2) * 0.3
                # End point on floor, slightly away
                tube_end = Vector((w/2 + 0.5 + abs(offset_x), l/3 + offset_x, 0))

                # Segments: Start -> Down -> Out -> End
                mid_z = tube_start.z * 0.4
                p1 = tube_start
                p2 = Vector((tube_start.x, tube_start.y, mid_z))
                p3 = Vector((tube_end.x, tube_end.y, mid_z))
                p4 = tube_end

                points = [p1, p2, p3, p4]

                for j in range(len(points)-1):
                    seg_start = points[j]
                    seg_end = points[j+1]
                    vec = seg_end - seg_start
                    dist = vec.length
                    if dist < 0.01: continue

                    rot_quat = vec.to_track_quat('Z', 'Y')
                    mid = (seg_start + seg_end) / 2

                    res_tube = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, diameter1=tube_r*2, diameter2=tube_r*2, depth=dist)
                    bmesh.ops.rotate(bm, cent=(0,0,0), matrix=rot_quat.to_matrix().to_4x4(), verts=res_tube['verts'])
                    bmesh.ops.translate(bm, vec=mid, verts=res_tube['verts'])

                    for f in res_tube['faces']:
                        f.material_index = 2 # Mechanical
                        self.apply_box_map(f, uv_layer, scale)

                    # Elbow joints
                    if j > 0:
                        res_joint = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=tube_r*1.2)
                        bmesh.ops.translate(bm, vec=seg_start, verts=res_joint['verts'])
                        for f in res_joint['faces']:
                            f.material_index = 2
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
