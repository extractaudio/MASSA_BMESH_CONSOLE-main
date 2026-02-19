import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_04: Pump Jack",
    "id": "asm_04_pumpjack",
    "icon": "MOD_ARMATURE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmPumpJack(Massa_OT_Base):
    bl_idname = "massa.gen_asm_04_pumpjack"
    bl_label = "ASM_04: Pump Jack"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Base Width (X)", default=2.0, min=1.0)
    length: FloatProperty(name="Base Length (Y)", default=4.0, min=2.0)
    height: FloatProperty(name="Pivot Height (Z)", default=3.0, min=1.0)

    beam_length: FloatProperty(name="Beam Length", default=5.0, min=2.0)
    animation_phase: FloatProperty(name="Anim Phase", default=0.0, min=0.0, max=1.0)

    def get_slot_meta(self):
        return {
            0: {"name": "A-Frame Base", "uv": "SKIP", "phys": "METAL_RUST"},
            1: {"name": "Walking Beam", "uv": "SKIP", "phys": "METAL_PAINTED"},
            2: {"name": "Counterweight", "uv": "SKIP", "phys": "METAL_IRON"},
            3: {"name": "Drill Head", "uv": "SKIP", "phys": "MECHANICAL"},
            4: {"name": "Pipe Socket", "uv": "SKIP", "phys": "MECHANICAL", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "length")
        col.prop(self, "height")
        col.prop(self, "beam_length")

        layout.separator()
        layout.label(text="ANIMATION", icon="PLAY")
        layout.prop(self, "animation_phase")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, l, h = self.width, self.length, self.height

        # Calculate Animation
        # Phase 0.0 -> 1.0 (Full Cycle)
        cycle = self.animation_phase * 2 * math.pi
        crank_angle = cycle

        # Beam Angle (approx sine wave linked to crank)
        beam_angle = math.sin(cycle) * math.radians(15)

        # 1. A-Frame Base
        pivot_y = 0.0
        pivot_z = h
        leg_thick = 0.2

        self.create_a_frame(bm, -w/2, l, h, leg_thick)
        self.create_a_frame(bm, w/2, l, h, leg_thick)

        # Cross bracing
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, h/2)) @ Matrix.Scale(w, 4, (1,0,0)) @ Matrix.Scale(0.1, 4, (0,1,0)) @ Matrix.Scale(0.1, 4, (0,0,1)))

        # Pivot Axle
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            radius1=0.15,
            radius2=0.15,
            depth=w + 0.4,
            segments=12,
            matrix=Matrix.Translation((0, pivot_y, pivot_z)) @ Matrix.Rotation(math.radians(90), 4, 'Y')
        )

        # 2. Walking Beam
        beam_front_len = self.beam_length * 0.6
        beam_back_len = self.beam_length * 0.4

        rot_beam = Matrix.Rotation(beam_angle, 4, 'X')
        pivot_mat = Matrix.Translation((0, pivot_y, pivot_z))

        beam_h = 0.4
        beam_w = 0.3

        beam_geom = bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Identity(4)
        )
        # Scale
        bmesh.ops.scale(bm, vec=(beam_w, self.beam_length, beam_h), verts=beam_geom['verts'])
        # Shift Y to align pivot
        shift_y = (beam_front_len - beam_back_len) / 2
        bmesh.ops.translate(bm, vec=(0, shift_y, 0), verts=beam_geom['verts'])

        # Apply Rotation and Translation to Pivot
        bmesh.ops.transform(bm, matrix=pivot_mat @ rot_beam, verts=beam_geom['verts'])

        # Assign Beam Slot
        for v in beam_geom['verts']:
            for f in v.link_faces:
                f.material_index = 1

        # 3. Horse Head (Drill Head) at Front
        head_pos_local = Vector((0, beam_front_len, 0))
        head_pos_world = pivot_mat @ rot_beam @ head_pos_local

        head_geom = bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(head_pos_world) @ rot_beam @ Matrix.Scale(0.4, 4, (1,0,0)) @ Matrix.Scale(0.6, 4, (0,1,0)) @ Matrix.Scale(0.8, 4, (0,0,1))
        )
        for v in head_geom['verts']:
            for f in v.link_faces:
                f.material_index = 3 # Drill Head

        # 4. Socket for Drill Pipe
        socket_pos = head_pos_world - Vector((0, 0, 0.4))

        ret = bmesh.ops.create_circle(
            bm,
            cap_ends=True,
            radius=0.1,
            segments=8,
            matrix=Matrix.Translation(socket_pos)
        )
        # Rotate 180 X to point DOWN
        bmesh.ops.rotate(
            bm,
            verts=ret['verts'],
            cent=socket_pos,
            matrix=Matrix.Rotation(math.radians(180), 4, 'X')
        )
        if ret['faces']:
            ret['faces'][0].material_index = 4

        # 5. Counterweight & Crank
        crank_center = Vector((0, -l/2, h*0.5))
        crank_radius = 1.0

        crank_vec = Vector((0, math.cos(crank_angle), math.sin(crank_angle))) * crank_radius
        crank_pos = crank_center + crank_vec

        # Crank Hub
        bmesh.ops.create_cube(
            bm,
            size=0.4,
            matrix=Matrix.Translation(crank_center)
        )

        # Counterweight Block
        cw_geom = bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(crank_pos) @ Matrix.Scale(0.8, 4, (1,1,1))
        )
        for v in cw_geom['verts']:
            for f in v.link_faces:
                f.material_index = 2

        # 6. Connecting Rod (Pitman Arm)
        beam_back_local = Vector((0, -beam_back_len, 0))
        beam_back_world = pivot_mat @ rot_beam @ beam_back_local

        mid_point = (crank_pos + beam_back_world) / 2
        vec = beam_back_world - crank_pos
        length = vec.length

        if length > 0.001:
            rot_quat = vec.to_track_quat('Z', 'Y')
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                segments=6,
                diameter1=0.1,
                diameter2=0.1,
                depth=length,
                matrix=Matrix.Translation(mid_point) @ rot_quat.to_matrix().to_4x4()
            )

        # 7. Edge Slots
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            # Check if edge belongs to Beam (Material 1)
            is_beam = False
            for f in e.link_faces:
                if f.material_index == 1:
                    is_beam = True
                    break

            if is_beam:
                if e.is_boundary or e.calc_face_angle() > 0.5:
                    e[edge_slots] = 1 # Perimeter

        # UVs
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
             for l in f.loops:
                 nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                 if nz > 0.5:
                     u, v = l.vert.co.x, l.vert.co.y
                 elif ny > 0.5:
                     u, v = l.vert.co.x, l.vert.co.z
                 else:
                     u, v = l.vert.co.y, l.vert.co.z
                 l[uv_layer].uv = (u * 0.5, v * 0.5)

    def create_a_frame(self, bm, x, l, h, thick):
        p_top = Vector((x, 0, h))
        p_front = Vector((x, l/2, 0))
        p_back = Vector((x, -l/2, 0))

        self.create_strut(bm, p_top, p_front, thick)
        self.create_strut(bm, p_top, p_back, thick)

    def create_strut(self, bm, p1, p2, thick):
        mid = (p1 + p2) / 2
        vec = p2 - p1
        length = vec.length
        if length < 0.001: return
        rot = vec.to_track_quat('Z', 'Y')

        geom = bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(mid) @ rot.to_matrix().to_4x4() @ Matrix.Scale(thick, 4, (1,0,0)) @ Matrix.Scale(thick, 4, (0,1,0)) @ Matrix.Scale(length, 4, (0,0,1))
        )
        for v in geom['verts']:
            for f in v.link_faces:
                f.material_index = 0 # Base
