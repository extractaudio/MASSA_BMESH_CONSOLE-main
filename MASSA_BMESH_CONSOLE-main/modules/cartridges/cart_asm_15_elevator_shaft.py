import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_15: Elevator Shaft",
    "id": "asm_15_elevator_shaft",
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


class MASSA_OT_AsmElevatorShaft(Massa_OT_Base):
    bl_idname = "massa.gen_asm_15_elevator_shaft"
    bl_label = "ASM_15 Elevator Shaft"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    width: FloatProperty(name="Shaft Width", default=2.5, min=1.5, unit="LENGTH")
    depth: FloatProperty(name="Shaft Depth", default=2.5, min=1.5, unit="LENGTH")
    height: FloatProperty(name="Total Height", default=12.0, min=3.0, unit="LENGTH")

    # --- 2. CONFIG ---
    floor_height: FloatProperty(name="Floor Interval", default=3.0, min=2.0, unit="LENGTH")
    wall_thick: FloatProperty(name="Wall Thick", default=0.3, min=0.1, unit="LENGTH")

    # --- 3. CAR ---
    car_level: FloatProperty(name="Car Z-Pos", default=0.0, min=0.0, unit="LENGTH")
    car_height: FloatProperty(name="Car Height", default=2.5, min=2.0, unit="LENGTH")

    # --- 4. RAILS ---
    rail_size: FloatProperty(name="Rail Size", default=0.15, min=0.05, unit="LENGTH")

    # --- 5. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Shaft Walls", "uv": "BOX", "phys": "CONCRETE"},
            1: {"name": "Rails", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Car Body", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            3: {"name": "Car Floor", "uv": "BOX", "phys": "LINOLEUM"},
            9: {"name": "Sockets", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Shaft Dimensions")
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        col.prop(self, "wall_thick")

        col.separator()
        col.label(text="Elevator Car")
        col.prop(self, "car_level")
        col.prop(self, "car_height")

        col.separator()
        col.label(text="Details")
        col.prop(self, "floor_height")
        col.prop(self, "rail_size")

    def build_shape(self, bm: bmesh.types.BMesh):
        w = self.width
        d = self.depth
        h = self.height
        fh = self.floor_height
        cl = self.car_level
        ch = self.car_height
        wt = self.wall_thick
        rs = self.rail_size

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale

        # 1. SHAFT
        # U-Shape open at front (Y=0?).
        # Side Walls at X = +/- w/2.
        # Back Wall at Y = d? Or -d?
        # Usually Shaft is behind the door.
        # So Front (Door) at Y=0. Back at Y=d.

        # Left Wall
        res_w1 = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(wt, d, h), verts=res_w1['verts'])
        bmesh.ops.translate(bm, vec=(-w/2 - wt/2, d/2, h/2), verts=res_w1['verts'])

        # Right Wall
        res_w2 = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(wt, d, h), verts=res_w2['verts'])
        bmesh.ops.translate(bm, vec=(w/2 + wt/2, d/2, h/2), verts=res_w2['verts'])

        # Back Wall
        res_w3 = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w + wt*2, wt, h), verts=res_w3['verts']) # Width covers side walls?
        bmesh.ops.translate(bm, vec=(0, d + wt/2, h/2), verts=res_w3['verts'])

        for f in list({f for v in res_w1['verts'] + res_w2['verts'] + res_w3['verts'] for f in v.link_faces}):
            f.material_index = 0
            self.apply_box_map(f, uv_layer, scale)

        # 2. RAILS (T-Beams)
        # On inner faces of side walls.
        # X = -w/2 and w/2. Y centered at d/2.
        # T-Shape.

        rail_geom = []
        for side in [-1, 1]:
            # Vertical Beam
            res_r1 = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(rs/3, rs, h), verts=res_r1['verts'])
            bmesh.ops.translate(bm, vec=(side * (w/2 - rs/2), d/2, h/2), verts=res_r1['verts'])

            # Flange (Inner)
            res_r2 = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(rs/3, rs*1.5, h), verts=res_r2['verts'])
            bmesh.ops.translate(bm, vec=(side * (w/2 - rs), d/2, h/2), verts=res_r2['verts'])

            rail_geom.extend(res_r1['verts'])
            rail_geom.extend(res_r2['verts'])

        for f in list({f for v in rail_geom for f in v.link_faces}):
            f.material_index = 1
            self.apply_box_map(f, uv_layer, scale)

        # 3. ELEVATOR CAR
        # Box inside shaft.
        # Size: w - 2*clearance, d - 2*clearance.
        cw = w - 0.2
        cd = d - 0.2

        res_car = bmesh.ops.create_cube(bm, size=1.0)
        verts_car = res_car['verts']
        bmesh.ops.scale(bm, vec=(cw, cd, ch), verts=verts_car)
        # Position: Center X=0, Y=d/2. Z = cl + ch/2
        bmesh.ops.translate(bm, vec=(0, d/2, cl + ch/2), verts=verts_car)

        # Assign Materials
        # Ideally differentiate Floor/Walls
        for f in list({f for v in verts_car for f in v.link_faces}):
            if f.normal.z > 0.9: # Floor (actually Ceiling?)
                f.material_index = 2
            elif f.normal.z < -0.9: # Bottom (Floor)
                f.material_index = 3
            else:
                f.material_index = 2
            self.apply_box_map(f, uv_layer, scale)

        # 4. SOCKETS (Doorways)
        # Every floor_height up to h.
        # Start at 0? Yes.

        num_floors = int(h / fh) + 1
        for i in range(num_floors):
            z = i * fh
            if z > h: break

            res_s = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.2)
            # Facing -Y (Out of shaft front)
            # Plane normal Z. Rot 90 X -> -Y.
            bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 4, 'X'), verts=res_s['verts'])
            bmesh.ops.translate(bm, vec=(0, 0, z), verts=res_s['verts'])

            for f in res_s['faces']:
                f.material_index = 9
                # Normal is -Y.
                # Usually Door Sockets face OUT (-Y) so door snaps IN (+Y)?
                # Standard Door Cartridge (e.g. ARC_04) usually snaps to a wall socket facing OUT?
                # Actually, usually sockets face OUT from the host.
                # Host is Shaft. Socket faces OUT (-Y).
                # Door snaps its Input (facing IN/Back) to Host Output (facing OUT).
                # So -Y is correct.
                # Plane rotated 90 X is -Y.
                pass

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
