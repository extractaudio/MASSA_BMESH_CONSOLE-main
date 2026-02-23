import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_11: Crane Assembly",
    "id": "ind_11_crane",
    "icon": "MOD_ARMATURE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndCrane(Massa_OT_Base):
    bl_idname = "massa.gen_ind_11_crane"
    bl_label = "IND Crane"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("GANTRY", "Gantry Crane", "Mobile portal crane on rails"),
            ("JIB", "Jib Crane", "Wall or pillar mounted swinging arm"),
            ("OVERHEAD", "Overhead Crane", "Bridge crane for warehouses"),
        ],
        default="GANTRY",
    )

    # Dimensions
    height: FloatProperty(name="Height (Z)", default=5.0, min=1.0)
    span: FloatProperty(name="Span (X)", default=8.0, min=2.0)
    width: FloatProperty(name="Width (Y)", default=4.0, min=1.0) # Base width for Gantry, Rail width for Overhead

    # Structure
    beam_height: FloatProperty(name="Beam Height", default=0.6, min=0.1)
    beam_width: FloatProperty(name="Beam Width", default=0.4, min=0.1)
    support_thick: FloatProperty(name="Column Thick", default=0.4, min=0.1)
    brace_count: IntProperty(name="Brace Count", default=4, min=0)

    # Mechanism
    hook_pos: FloatProperty(name="Hook Position", default=0.5, min=0.0, max=1.0, description="Position along the span")
    hook_drop: FloatProperty(name="Hook Drop", default=2.0, min=0.1)
    trolley_size: FloatProperty(name="Trolley Size", default=0.5, min=0.1)

    # Detail
    rail_thick: FloatProperty(name="Rail Thickness", default=0.1, min=0.01)
    wheel_base: FloatProperty(name="Wheel Base", default=1.5, min=0.5) # For Gantry legs

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Structure", "uv": "SKIP", "phys": "METAL_PAINTED"},
            1: {"name": "Mechanism", "uv": "SKIP", "phys": "METAL_STEEL"},
            2: {"name": "Cable", "uv": "SKIP", "phys": "WIRE_CABLE"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style", text="")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Dimensions", icon="FIXED_SIZE")
        col.prop(self, "height")
        col.prop(self, "span")
        if self.style != "JIB":
            col.prop(self, "width")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Structure", icon="MESH_GRID")
        col.prop(self, "beam_height")
        col.prop(self, "beam_width")
        col.prop(self, "support_thick")
        if self.style == "GANTRY":
            col.prop(self, "brace_count")
            col.prop(self, "wheel_base")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Mechanism", icon="HOOK")
        col.prop(self, "hook_pos")
        col.prop(self, "hook_drop")
        col.prop(self, "trolley_size")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")

        h = self.height
        s = self.span
        w = self.width
        bh = self.beam_height
        bw = self.beam_width
        st = self.support_thick

        # 1. Main Beam (Span)
        # Position depends on style
        beam_z = h - bh/2

        # Trolley Rail Logic
        trolley_y = 0
        trolley_z = beam_z - bh/2 - self.trolley_size/2

        if self.style == "GANTRY":
            # Two A-frame legs and a cross beam
            # Beam along X
            builder.create_box(s + st*2, bw, bh, center=Vector((0, 0, beam_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Legs
            leg_x_offset = s/2

            # Left Leg (A-Frame)
            # Two slanted columns meeting at top? Or parallel?
            # Standard Gantry: Parallel legs with bottom beam

            for side in [-1, 1]: # Left/Right
                lx = side * leg_x_offset

                # Vertical Columns
                col_h = h - bh

                # Front/Back legs
                wb = self.wheel_base

                # Leg 1
                builder.create_box(st, st, col_h, center=Vector((lx, -wb/2, col_h/2)))
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Leg 2
                builder.create_box(st, st, col_h, center=Vector((lx, wb/2, col_h/2)))
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Bottom Connector
                builder.create_box(st*1.5, wb + st, st, center=Vector((lx, 0, st/2)))
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Top Connector (Under beam)
                # builder.create_box(st*1.5, wb, st, center=Vector((lx, 0, h - bh - st/2)))
                # builder.tag_slot(0)

                # Bracing (X Pattern between legs)
                if self.brace_count > 0:
                    dz = col_h / self.brace_count
                    for i in range(self.brace_count):
                        z_sub = i * dz
                        # Cross bar
                        builder.create_box(st/2, wb, st/2, center=Vector((lx, 0, z_sub + dz/2)))
                        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "OVERHEAD":
            # Two parallel rails (Y axis) and a bridge beam (X axis)
            # But "Span" is usually the bridge length (X). "Width" is the travel distance (Y).

            # Bridge Beam (X)
            # Moves along Y. We place it at Y=0 for generation.
            builder.create_box(s, bw, bh, center=Vector((0, 0, beam_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # End Trucks (The parts that ride on rails)
            truck_len = self.wheel_base

            # Left Truck
            builder.create_box(bw*1.5, truck_len, bh, center=Vector((-s/2, 0, beam_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right Truck
            builder.create_box(bw*1.5, truck_len, bh, center=Vector((s/2, 0, beam_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Runway Rails (Optional context geometry, but let's add them as Slot 1 or separate)
            # Rails run along Y at +/- S/2
            rail_len = w # User defined width as travel length
            # Left Rail
            builder.create_box(st, rail_len, st, center=Vector((-s/2, 0, beam_z - bh)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX') # Mechanism slot

            # Right Rail
            builder.create_box(st, rail_len, st, center=Vector((s/2, 0, beam_z - bh)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "JIB":
            # Vertical Pillar at Origin
            # Horizontal Arm along X

            # Pillar
            builder.create_cylinder(radius=st/2, depth=h, segments=16, center=Vector((0, 0, h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX') # Cylindrical projection better but BOX safe

            # Arm (Jib)
            arm_z = h - bh
            builder.create_box(s, bw, bh, center=Vector((s/2 + st/2, 0, arm_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Diagonal Brace (Triangle)
            # From (st/2, 0, arm_z-1) to (s/3, 0, arm_z)
            brace_len = math.sqrt((s/2)**2 + (s/2)**2) # Approx
            # Creating a simple angled box is hard with create_box without math.
            # Use points?
            # Let's just use a smaller box or skip for simplicity of "Golden Cartridge" robustness.
            # Actually, a gusset plate is better.

            # Gusset
            builder.create_box(s/3, st/4, bh*2, center=Vector((st/2 + s/6, 0, arm_z - bh/2)))
            # We need to cut it or shape it.
            # Keeping it simple: Just a support strut.

            beam_z = arm_z # For trolley calculation

        # 2. Trolley & Hook
        # Trolley moves along Span (X)
        # Position: -s/2 to s/2 for Gantry/Overhead. 0 to s for Jib.

        trolley_x = 0
        if self.style == "JIB":
            # Range: st/2 to s
            start = st
            end = s + st/2 - self.trolley_size
            trolley_x = start + (end - start) * self.hook_pos
        else:
            # Range: -s/2 to s/2
            start = -s/2 + self.trolley_size
            end = s/2 - self.trolley_size
            trolley_x = start + (end - start) * self.hook_pos

        trolley_z = beam_z - bh/2 - self.trolley_size/2

        # Trolley Body
        builder.create_box(self.trolley_size, self.trolley_size*1.2, self.trolley_size, center=Vector((trolley_x, 0, trolley_z)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Cable
        cable_len = self.hook_drop
        cable_z = trolley_z - self.trolley_size/2 - cable_len/2
        builder.create_cylinder(radius=0.02, depth=cable_len, segments=6, center=Vector((trolley_x, 0, cable_z)))
        builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Hook
        hook_z = trolley_z - self.trolley_size/2 - cable_len
        builder.create_box(0.2, 0.1, 0.3, center=Vector((trolley_x, 0, hook_z)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Tag Socket on Hook (For attaching loads)
        builder.select_faces_by_normal(Vector((0, 0, -1))).tag_socket(0) # Socket 0: Hook

        # 3. Anchor Sockets (Feet)
        if self.style == "GANTRY":
            # Tag bottom of feet
            builder.select_faces_by_normal(Vector((0, 0, -1)))
            # Filter for Z ~ 0
            # builder.active_faces is updated.
            # We want only the faces at Z=0.
            # Since create_box(..., center=(..., st/2)) puts bottom at 0.
            builder.tag_socket(9) # Anchor

        elif self.style == "JIB":
            # Base of pillar
             builder.select_faces_by_normal(Vector((0, 0, -1))).tag_socket(9)

        elif self.style == "OVERHEAD":
            # Usually attached to walls.
            # Maybe ends of the rails? or ends of the bridge?
            # Let's tag the ends of the bridge trucks.
            builder.select_faces_by_normal(Vector((-1, 0, 0))).tag_socket(9)
            builder.select_faces_by_normal(Vector((1, 0, 0))).tag_socket(9)

        # 4. Final Cleanup
        builder.clean()
