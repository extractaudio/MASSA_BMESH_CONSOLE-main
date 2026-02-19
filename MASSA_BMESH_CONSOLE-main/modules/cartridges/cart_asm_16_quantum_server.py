import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_16: Quantum Server Mainframe",
    "id": "asm_16_quantum_server",
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


class MASSA_OT_AsmQuantumServer(Massa_OT_Base):
    bl_idname = "massa.gen_asm_16_quantum_server"
    bl_label = "ASM_16 Quantum Server"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    width: FloatProperty(name="Width", default=1.2, min=0.5, unit="LENGTH")
    depth: FloatProperty(name="Depth", default=1.0, min=0.5, unit="LENGTH")
    height: FloatProperty(name="Height", default=2.2, min=1.0, unit="LENGTH")
    frame_thick: FloatProperty(name="Frame Thickness", default=0.1, min=0.01, unit="LENGTH")

    # --- 2. BLADES ---
    blade_count: IntProperty(name="Blade Count", default=12, min=4, max=40)
    blade_gap: FloatProperty(name="Blade Gap", default=0.02, min=0.0, unit="LENGTH")
    random_seed: IntProperty(name="Seed", default=101)

    # --- 3. DETAILS ---
    led_density: FloatProperty(name="LED Density", default=0.3, min=0.0, max=1.0)
    socket_rows: IntProperty(name="Socket Rows", default=4, min=1)
    socket_cols: IntProperty(name="Socket Cols", default=2, min=1)

    # --- 4. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Blade Body", "uv": "BOX", "phys": "PLASTIC_HARD"},
            2: {"name": "Blade Face", "uv": "BOX", "phys": "PLASTIC_HARD"},
            4: {"name": "LEDs", "uv": "BOX", "phys": "EMISSION"},
            9: {"name": "Sockets", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        col.prop(self, "frame_thick")

        col.separator()
        col.label(text="Blades")
        col.prop(self, "blade_count")
        col.prop(self, "blade_gap")
        col.prop(self, "random_seed")

        col.separator()
        col.label(text="Details")
        col.prop(self, "led_density")
        row = col.row(align=True)
        row.prop(self, "socket_rows")
        row.prop(self, "socket_cols")

        col.separator()
        col.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        w = self.width
        d = self.depth
        h = self.height
        ft = self.frame_thick

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale
        rng = random.Random(self.random_seed)

        # 1. FRAME (Outer Shell)
        # Create a cube for the frame
        res_frame = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, d, h), verts=res_frame['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, h/2), verts=res_frame['verts'])

        # Inset front face to create the opening
        # Front is usually -Y in Blender if we follow standard orientation,
        # but let's assume +Y is Front for now, or check convention.
        # Usually -Y is "Forward" in some contexts, but let's stick to standard Y-forward.
        # Wait, if I look at ASM_15 elevator, I assumed -Y is front (door).
        # Let's assume -Y is Front.

        # Actually, create frame by assembling plates is safer than boolean.
        # Delete the frame cube and build it manually.
        bmesh.ops.delete(bm, geom=res_frame['verts'], context='VERTS')

        # Back Wall (+Y)
        res_back = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, ft, h), verts=res_back['verts'])
        bmesh.ops.translate(bm, vec=(0, d/2 - ft/2, h/2), verts=res_back['verts'])

        # Side Walls
        res_left = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(ft, d, h), verts=res_left['verts'])
        bmesh.ops.translate(bm, vec=(-w/2 + ft/2, 0, h/2), verts=res_left['verts'])

        res_right = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(ft, d, h), verts=res_right['verts'])
        bmesh.ops.translate(bm, vec=(w/2 - ft/2, 0, h/2), verts=res_right['verts'])

        # Top/Bottom
        res_top = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, d, ft), verts=res_top['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, h - ft/2), verts=res_top['verts'])

        res_bot = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, d, ft), verts=res_bot['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, ft/2), verts=res_bot['verts'])

        # Assign Frame Material
        frame_geom = res_back['verts'] + res_left['verts'] + res_right['verts'] + res_top['verts'] + res_bot['verts']
        for f in list({f for v in frame_geom for f in v.link_faces}):
            f.material_index = 0
            self.apply_box_map(f, uv_layer, scale)

        # 2. BLADES (Inside)
        # Available space
        inner_w = w - 2*ft
        inner_d = d - ft # Open at front (-Y), back wall at +Y
        inner_h = h - 2*ft

        start_z = ft
        blade_h = (inner_h - (self.blade_count - 1) * self.blade_gap) / self.blade_count

        # Ensure blade_h is positive
        if blade_h < 0.01:
            blade_h = 0.01

        for i in range(self.blade_count):
            z_pos = start_z + i * (blade_h + self.blade_gap) + blade_h/2

            # Random inset depth for visual interest
            # The blade sits inside.
            # Front face at -Y = -d/2. Back face at +Y = d/2 - ft.
            # Let's say blade front varies.

            inset_depth = rng.uniform(0.0, 0.1)
            blade_d = inner_d - inset_depth

            # Center of blade in Y:
            # Back is at (d/2 - ft). Front is at (-d/2 + inset_depth).
            # Center Y = (Back + Front) / 2 = (d/2 - ft - d/2 + inset_depth) / 2 = (inset_depth - ft) / 2
            # Size Y = Back - Front = (d/2 - ft) - (-d/2 + inset_depth) = d - ft - inset_depth = blade_d

            cy = (d/2 - ft - d/2 + inset_depth) / 2

            res_blade = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(inner_w, blade_d, blade_h), verts=res_blade['verts'])
            bmesh.ops.translate(bm, vec=(0, cy, z_pos), verts=res_blade['verts'])

            # Material assignment
            for f in list({f for v in res_blade['verts'] for f in v.link_faces}):
                # Check normal to find front face (-Y)
                if f.normal.y < -0.9:
                    f.material_index = 2 # Blade Face

                    # Add LEDs?
                    # We can subdivide this face or just create small planes on top.
                    # Let's inset/subdivide.
                    if rng.random() < self.led_density:
                        # Simple logic: Assign Slot 4 to this face directly for now,
                        # or better: create a small LED geometry on it.
                        # Let's use inset to create a "panel" and then some small lights.
                        # For simplicity in this macro scale, let's just make the whole front face an interface
                        # OR pick random small faces if we had them.
                        # Let's use bmesh.ops.inset_region
                        try:
                            res_inset = bmesh.ops.inset_region(bm, faces=[f], thickness=0.05, depth=-0.01)
                            # The inner face is the result
                            # Assign random LED status to the inner face?
                            # Or subdivide inner face
                            pass
                        except:
                            pass

                        # Create a small LED grid on the front
                        if rng.random() > 0.5:
                            # Add a small emissive plane slightly in front
                            led_w = inner_w * 0.8
                            led_h = blade_h * 0.4
                            res_led = bmesh.ops.create_grid(bm, x_segments=4, y_segments=1, size=1.0)
                            bmesh.ops.scale(bm, vec=(led_w, 1.0, led_h), verts=res_led['verts'])
                            # Rotate to face -Y (Standard grid is Z up)
                            bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 4, 'X'), verts=res_led['verts'])
                            # Move to front of blade
                            bmesh.ops.translate(bm, vec=(0, -d/2 + inset_depth - 0.01, z_pos), verts=res_led['verts'])

                            for lf in res_led['faces']:
                                if rng.random() < 0.5:
                                    lf.material_index = 4 # LED
                                else:
                                    lf.material_index = 2 # Dark
                else:
                    f.material_index = 1 # Blade Body

                self.apply_box_map(f, uv_layer, scale)

        # 3. SOCKETS (Back Panel)
        # Generate array of sockets on the back.
        # Back is at +d/2.
        # Grid: socket_cols x socket_rows

        # Area on back: w x h
        # Start X, Z

        sx_step = w / (self.socket_cols + 1)
        sz_step = h / (self.socket_rows + 1)

        for r in range(self.socket_rows):
            for c in range(self.socket_cols):
                px = -w/2 + (c + 1) * sx_step
                pz = (r + 1) * sz_step

                # Create socket placeholder
                res_sock = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.1)
                # Rotate to face +Y (Standard grid is Z up). Rot 90 X -> -Y. Rot -90 X -> +Y.
                bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-90), 4, 'X'), verts=res_sock['verts'])

                # Position on back face
                bmesh.ops.translate(bm, vec=(px, d/2 + 0.02, pz), verts=res_sock['verts'])

                for f in res_sock['faces']:
                    f.material_index = 9 # Socket
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
