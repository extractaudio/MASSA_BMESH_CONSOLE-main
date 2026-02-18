import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_03: Corrugated Sheet",
    "id": "prim_03_sheet",
    "icon": "MOD_WAVE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,  # Zigzag edges break with chamfer
    },
}


class MASSA_OT_PrimCorrugated(Massa_OT_Base):
    bl_idname = "massa.gen_prim_03_sheet"
    bl_label = "PRIM_03: Sheet"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. SHAPE ---
    wave_type: EnumProperty(
        name="Wave Type",
        items=[
            ("SINE", "Sine", ""),
            ("TRIANGLE", "Triangle", ""),
            ("SQUARE", "Square", ""),
            ("SAWTOOTH", "Sawtooth", ""),
            ("CLIPPED_SINE", "Clipped Sine", ""),
        ],
        default="SINE",
    )
    width: FloatProperty(name="Width (X)", default=2.0, min=0.1)
    length: FloatProperty(name="Length (Y)", default=2.0, min=0.1)
    thickness: FloatProperty(name="Thickness", default=0.02, min=0.001)
    amplitude: FloatProperty(name="Amplitude", default=0.1, min=0.0)
    frequency: FloatProperty(name="Frequency", default=5.0, min=0.1)
    phase: FloatProperty(name="Phase Offset", default=0.0)
    clip_amount: FloatProperty(name="Clip Threshold", default=0.8, min=0.1, max=1.0)

    # --- 2. TOPOLOGY ---
    res_x: IntProperty(name="Resolution X", default=64, min=4)
    res_y: IntProperty(name="Resolution Y", default=2, min=2)

    # --- 3. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 PROTOCOL:
        Explicitly use 'SKIP' to prevent Console overrides unless user requests it.
        """
        return {
            0: {"name": "Surface", "uv": "SKIP", "phys": "METAL_ALUMINUM", "mat": "Metal Aluminum"},
            1: {"name": "Edge Trim", "uv": "SKIP", "phys": "METAL_ALUMINUM", "mat": "Metal Aluminum"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Wave Profile", icon="MESH_DATA")
        layout.prop(self, "wave_type", text="")
        col = layout.column(align=True)
        col.prop(self, "amplitude")
        col.prop(self, "frequency")
        col.prop(self, "phase")
        if self.wave_type == "CLIPPED_SINE":
            col.prop(self, "clip_amount", slider=True)

        layout.separator()
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "length")
        col.prop(self, "thickness")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        row = layout.row(align=True)
        row.prop(self, "res_x")
        row.prop(self, "res_y")



    def calculate_wave(self, x_norm):
        t = (x_norm * self.frequency * 2 * math.pi) + self.phase
        amp = self.amplitude
        if self.wave_type == "SINE":
            return amp * math.sin(t)
        elif self.wave_type == "TRIANGLE":
            return amp * (2.0 / math.pi) * math.asin(math.sin(t))
        elif self.wave_type == "SQUARE":
            return amp if math.sin(t) >= 0 else -amp
        elif self.wave_type == "SAWTOOTH":
            return amp * (2.0 * ((t / (2 * math.pi)) % 1.0) - 1.0)
        elif self.wave_type == "CLIPPED_SINE":
            val = math.sin(t)
            return amp * (
                max(-self.clip_amount, min(self.clip_amount, val)) / self.clip_amount
            )
        return 0.0

    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. CREATE BASE GRID
        # Note: size=0.5 usually creates range -0.25 to 0.25 in Blender BMesh.
        # We normalize manually below, so exact size param matters less than topology.
        res = bmesh.ops.create_grid(
            bm, x_segments=self.res_x, y_segments=self.res_y, size=0.5
        )
        verts = res["verts"]
        bm.verts.ensure_lookup_table()

        # 2. APPLY WAVE & DIMENSIONS
        scale_x = self.width
        scale_y = self.length

        # We need the input X range to normalize properly
        xs = [v.co.x for v in verts]
        min_in, max_in = min(xs), max(xs)
        width_in = max(0.0001, max_in - min_in)

        for v in verts:
            # Normalize X to 0-1
            x_norm = (v.co.x - min_in) / width_in

            z_wave = self.calculate_wave(x_norm)

            # Apply final dimensions
            # Re-map -0.5..0.5 range to -width/2..width/2
            v.co.x = (x_norm - 0.5) * scale_x
            v.co.y *= (
                scale_y * 2.0
            )  # Grid 0.5 needs *2 to become 1.0 unit scale multiplier
            v.co.z += z_wave

        # 3. SOLIDIFY (Extrude)
        faces_sheet = list(bm.faces)

        # Extrude logic: The faces in 'geom' are the new TOP faces and the SIDE walls.
        res_ext = bmesh.ops.extrude_face_region(bm, geom=faces_sheet)

        verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]

        # Translate extruded top UP
        bmesh.ops.translate(bm, verts=verts_ext, vec=(0, 0, self.thickness))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 4. CLASSIFY SLOTS (GEOMETRIC BOUNDARY CHECK)
        # We use strict bounding box logic to find the Trim faces.
        # If a face is part of the "Surface" (Top or Bottom), it will be inside the bounds or spanning them.
        # If a face is "Trim", it lies EXACTLY on the outer boundary walls.

        bm.verts.ensure_lookup_table()
        all_x = [v.co.x for v in bm.verts]
        all_y = [v.co.y for v in bm.verts]

        # Determine strict bounds of the generated mesh
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        EPS = 0.0001

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            # Check if all vertices of this face are on a single boundary plane
            vx = [v.co.x for v in f.verts]
            vy = [v.co.y for v in f.verts]

            is_rim = False

            # Left Rim (Min X)
            if all(abs(x - min_x) < EPS for x in vx):
                is_rim = True
            # Right Rim (Max X)
            elif all(abs(x - max_x) < EPS for x in vx):
                is_rim = True
            # Bottom Rim (Min Y)
            elif all(abs(y - min_y) < EPS for y in vy):
                is_rim = True
            # Top Rim (Max Y)
            elif all(abs(y - max_y) < EPS for y in vy):
                is_rim = True

            if is_rim:
                f.material_index = 1
                f.smooth = False
            else:
                f.material_index = 0
                f.smooth = True

        # 5. MARK SEAMS
        # Explicit Seam Logic (Aligning with Beam/Pipe behavior)
        for e in bm.edges:
            # 1. Material Boundaries (Surface vs Rim)
            if len(e.link_faces) >= 2:
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    continue

                # 2. Rim Sharp Edges (Box Mapping seams)
                # If both faces are Rim, check angle
                if all(m == 1 for m in mats):
                    n1 = e.link_faces[0].normal
                    n2 = e.link_faces[1].normal
                    # Seam if < 0.5 (60 deg) dot product (sharp corner)
                    if n1.dot(n2) < 0.5:
                        e.seam = True

        # 6. UV MAPPING
        uv_layer = bm.loops.layers.uv.verify()

        # Arc-Length Setup for Surface
        arc_table = []
        total_dist = 0.0
        samples = max(64, self.res_x * 2)

        # Helper to get wave point for arc calc
        def get_wave_point(t):
            # t is 0.0 to 1.0
            x_w = (t - 0.5) * self.width
            z_w = self.calculate_wave(t)
            return Vector((x_w, 0, z_w))

        prev_p = get_wave_point(0.0)
        arc_table.append(0.0)

        for i in range(1, samples + 1):
            t = i / samples
            curr_p = get_wave_point(t)
            dist = (curr_p - prev_p).length
            total_dist += dist
            arc_table.append(total_dist)
            prev_p = curr_p

        su = (1.0 / total_dist) if self.fit_uvs else self.uv_scale
        sv = (1.0 / self.length) if self.fit_uvs else self.uv_scale

        def get_arc_u(world_x):
            # Normalize world X (-width/2 to width/2) to 0-1
            # Clamp to prevent slight float errors
            t = (world_x / self.width) + 0.5
            t = max(0.0, min(1.0, t))

            idx_float = t * samples
            idx_low = int(idx_float)
            idx_high = min(idx_low + 1, len(arc_table) - 1)
            mix = idx_float - idx_low

            return (1.0 - mix) * arc_table[idx_low] + (mix) * arc_table[idx_high]

        # Apply UVs
        for f in bm.faces:
            mat = f.material_index
            norm = f.normal

            if mat == 0:  # SURFACE (Slot 0)
                # Using standard loop_uvs structure for consistency
                loop_uvs = []
                for l in f.loops:
                    v = l.vert
                    u_dist = get_arc_u(v.co.x)
                    # Center Y around 0 if needed, but here y depends on origin.
                    # Original code used (v.co.y + length*0.5), assuming centered extrusion?
                    # Check Step 4: translate UP but not centering Y?
                    # Step 2: v.co.y *= scale_y*2.0. Grid centers at 0.
                    # So v.co.y ranges [-L/2, L/2].
                    # To map 0..1, add L/2.
                    v_dist = v.co.y + (self.length * 0.5)

                    loop_uvs.append([l, u_dist, v_dist])

                for l, u, v in loop_uvs:
                    l[uv_layer].uv = (u * su, v * sv)

            else:  # RIM (Slot 1) - Box Map
                loop_uvs = []
                for l in f.loops:
                    co = l.vert.co
                    # Simple Box Map Logic
                    if abs(norm.x) > abs(norm.y):
                        # Side Walls (mapped to YZ)
                        u, v = co.y, co.z
                    else:
                        # End Caps (mapped to XZ)
                        u, v = co.x, co.z
                    loop_uvs.append([l, u, v])

                for l, u, v in loop_uvs:
                    l[uv_layer].uv = (u * self.uv_scale, v * self.uv_scale)
