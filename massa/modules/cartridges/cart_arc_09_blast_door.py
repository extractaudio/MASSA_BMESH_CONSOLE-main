import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_09: Blast Door",
    "id": "arc_09_blast_door",
    "icon": "MOD_BOOLEAN",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcBlastDoor(Massa_OT_Base):
    bl_idname = "massa.gen_arc_09_blast_door"
    bl_label = "ARC Blast Door"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("SLIDING", "Sliding Gear", "Heavy sliding door on rails"),
            ("HINGED", "Pressure Hinged", "Bank vault style hinges"),
            ("IRIS", "Iris / Bulkhead", "Circular pressure door"),
        ],
        default="SLIDING"
    )

    # Dimensions
    width: FloatProperty(name="Aperture Width", default=2.0, min=0.5)
    height: FloatProperty(name="Aperture Height", default=2.5, min=1.0)
    thickness: FloatProperty(name="Door Thickness", default=0.2, min=0.05)

    # Frame
    frame_width: FloatProperty(name="Frame Width", default=0.3, min=0.1)
    frame_depth: FloatProperty(name="Frame Depth", default=0.4, min=0.1)

    # Details
    wheel_radius: FloatProperty(name="Wheel/Hinge Size", default=0.15, min=0.05)
    handle_height: FloatProperty(name="Handle Height", default=1.1, min=0.0)
    rib_count: IntProperty(name="Reinforcement Ribs", default=2, min=0, max=10)

    window_enable: BoolProperty(name="Window", default=False)
    window_size: FloatProperty(name="Window Size", default=0.4, min=0.1)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Door Surface", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Frame/Mech", "uv": "BOX", "phys": "METAL_DARK"},
            2: {"name": "Details/Handle", "uv": "BOX", "phys": "METAL_BRASS"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "GLASS_THICK"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CUBE')
        col = box.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "thickness")

        box = layout.box()
        box.label(text="Frame", icon='MOD_BUILD')
        col = box.column(align=True)
        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")

        box = layout.box()
        box.label(text="Mechanism", icon='PHYSICS')
        col = box.column(align=True)
        col.prop(self, "wheel_radius")
        col.prop(self, "handle_height")
        col.prop(self, "rib_count")

        box = layout.box()
        box.label(text="Features", icon='MOD_BOOLEAN')
        col = box.column(align=True)
        col.prop(self, "window_enable")
        if self.window_enable:
            col.prop(self, "window_size")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        h = self.height
        th = self.thickness
        fw = self.frame_width
        fd = self.frame_depth

        # 1. Frame
        # Surround aperture (w, h)
        # Outer w = w + 2*fw
        # Outer h = h + fw (assuming floor at bottom)

        outer_w = w + 2*fw
        outer_h = h + fw

        # Create Frame Box
        # Center X=0. Z=outer_h/2.
        builder.create_box(outer_w, fd, outer_h, center=Vector((0, 0, outer_h/2)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Cut Aperture
        # Using inset/bridge or boolean logic?
        # MassaBuilder manual cut:
        # Bisect X at -w/2, w/2
        # Bisect Z at h
        # Select center block and delete?

        # Bisect X
        bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(-w/2, 0, 0), plane_no=(1,0,0))
        bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(w/2, 0, 0), plane_no=(1,0,0))
        # Bisect Z
        bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(0, 0, h), plane_no=(0,0,1))

        # Select Aperture Block
        # X between -w/2 and w/2
        # Z between 0 and h
        # Y any (full depth)

        to_delete = []
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            c = f.calc_center_median()
            if (-w/2 <= c.x <= w/2) and (0 <= c.z <= h):
                to_delete.append(f)

        bmesh.ops.delete(bm, geom=to_delete, context='FACES')

        # Cap the hole?
        # Deleting faces leaves open mesh. We need to bridge the gap or build frame differently.
        # Bridge the inner loops?
        # Actually, simpler: Build 3 boxes (Left, Right, Top)

        # Let's restart Frame logic with 3 boxes for cleaner topology.
        builder.clear_selection()
        # Delete all? No, we just started.
        bmesh.ops.delete(bm, geom=bm.verts[:], context='VERTS') # Reset

        # Left Jamb
        builder.create_box(fw, fd, h + fw, center=Vector((-w/2 - fw/2, 0, (h+fw)/2)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Right Jamb
        builder.create_box(fw, fd, h + fw, center=Vector((w/2 + fw/2, 0, (h+fw)/2)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Header
        # Spans full width? Or between jambs?
        # Top of jambs is h+fw.
        # Header from h to h+fw?
        # Usually header sits on top or between.
        # Let's put header between jambs at top.
        # builder.create_box(w, fd, fw, center=Vector((0, 0, h + fw/2)))
        # Actually, let's span full width for "Lintel" look
        builder.create_box(outer_w, fd + 0.05, fw, center=Vector((0, 0, h + fw/2)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 2. Door Leaf
        # Dimensions depends on style.
        # Fits in w x h aperture.

        if self.style == "SLIDING":
            # Door overlaps frame?
            # Usually slides on outside.
            # Size: w + 2*overlap, h + overlap.
            overlap = 0.1
            door_w = w + overlap*2
            door_h = h + overlap

            # Position: In front of frame? Y = -fd/2 - th/2 - gap
            gap = 0.05
            door_y = -fd/2 - th/2 - gap

            # Create Leaf
            builder.create_box(door_w, th, door_h, center=Vector((0, door_y, door_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Rail
            rail_y = -fd/2 - gap - th - 0.05
            rail_h = h + overlap + 0.2
            builder.create_box(outer_w + w, 0.1, 0.1, center=Vector((w/2, rail_y + 0.1, rail_h))) # Rail above
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Wheels (Hangers)
            wr = self.wheel_radius
            for x_off in [-door_w/3, door_w/3]:
                # Hanger arm
                builder.create_box(0.05, 0.05, 0.4, center=Vector((x_off, door_y, door_h + 0.1)))
                builder.tag_slot(1)
                # Wheel
                builder.create_cylinder(radius=wr, depth=0.05, center=Vector((0,0,0)))
                builder.rotate(90, axis='Y')
                builder.translate(x_off, rail_y, rail_h) # Align with rail
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        elif self.style == "HINGED":
            # Door fits inside or flush?
            # Flush with front.
            door_w = w - 0.02
            door_h = h - 0.01
            door_y = 0 # Center in frame?

            # Create Leaf
            builder.create_box(door_w, th, door_h, center=Vector((0, door_y, door_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Hinges
            hr = self.wheel_radius
            hinge_x = -w/2 # Left side

            for z_fac in [0.2, 0.8]:
                hz = h * z_fac
                # Frame part
                builder.create_box(hr*2, hr*2, hr*2, center=Vector((hinge_x - hr, -fd/2, hz)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Door part
                builder.create_box(hr*2, hr, hr, center=Vector((hinge_x + hr/2, -fd/2 - 0.05, hz))) # Strap
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Pin
                builder.create_cylinder(radius=hr/2, depth=hr*3, center=Vector((hinge_x, -fd/2, hz)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        elif self.style == "IRIS":
            # Circular Door in square frame?
            # Bulkhead style.
            # Create octagonal or circular door.

            radius = min(w, h) / 2
            center_z = h/2

            # Door Leaf (Cylinder)
            builder.create_cylinder(radius=radius, depth=th, segments=16, center=Vector((0,0,0)))
            builder.rotate(90, axis='X')
            builder.translate(0, 0, center_z)
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='Y')

            # Frame Ring?
            # Add detail ring
            builder.create_cylinder(radius=radius + 0.1, depth=th/2, segments=16, center=Vector((0,0,0)))
            builder.rotate(90, axis='X')
            builder.translate(0, -th/2, center_z)
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='Y')

            # Iris Segments (Visual grooves)
            for i in range(8):
                angle = math.radians(i * 45)
                # Create a radial bar/groove
                builder.create_box(radius, 0.05, 0.05, center=Vector((radius/2, 0, 0)))
                # Rotate Z (in local frame of door? Door is rotated X 90)
                # Door is in YZ plane essentially (center_z).
                # We want to rotate around Y axis?
                # Cylinder was created at origin then rotated X 90.
                # So cylinder axis is Y. (Default Z -> X90 -> -Y or Y?)
                # Z -> X90 -> Y (Y->Z, Z->-Y? No).
                # Rot X 90: Y -> Z, Z -> -Y.
                # So Cylinder along -Y.

                # Let's just create detail at origin and apply same transform.
                # Radial spoke in XY plane.
                builder.rotate(math.degrees(angle), axis='Z')
                builder.translate(0, 0, th/2 + 0.02) # On face

                # Apply Door Transform
                builder.rotate(90, axis='X')
                builder.translate(0, 0, center_z)

                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Details (Handle & Ribs)
        # Handle
        hh = self.handle_height
        if self.style != "IRIS":
            # Handle on right side usually
            hx = w/3
            hy = -th/2 - 0.05 # Front face

            if self.style == "HINGED":
                # Wheel Handle
                r = 0.2
                builder.create_cylinder(radius=r, depth=0.05, center=Vector((0,0,0)))
                builder.rotate(90, axis='X')
                builder.translate(hx, hy - 0.1, hh)
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
                # Spocls?
                builder.create_box(r*2, 0.02, 0.02, center=Vector((hx, hy - 0.1, hh)))
                builder.tag_slot(2)
                builder.create_box(0.02, 0.02, r*2, center=Vector((hx, hy - 0.1, hh)))
                builder.tag_slot(2)
            else:
                # Pull Handle
                builder.create_box(0.05, 0.1, 0.4, center=Vector((hx, hy, hh)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Ribs
        if self.rib_count > 0 and self.style != "IRIS":
            # Vertical or Horizontal ribs?
            # Horizontal usually.
            step = h / (self.rib_count + 1)
            for i in range(self.rib_count):
                z = step * (i+1)
                builder.create_box(w, 0.05, 0.05, center=Vector((0, -th/2 - 0.025, z)))
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Window
        if self.window_enable:
            ws = self.window_size
            wz = h * 0.7 # Eye level ish

            # Boolean cutout? No boolean.
            # Add a frame ON TOP of door surface + Glass plane.
            # Visual window.

            wy = -th/2 - 0.03

            # Frame
            builder.create_box(ws + 0.1, 0.05, ws + 0.1, center=Vector((0, wy, wz)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Glass
            builder.create_box(ws, 0.02, ws, center=Vector((0, wy - 0.01, wz)))
            builder.tag_slot(3)
            # Fit UVs for Glass
            builder.tag_uvs(scale=1.0, projection='FIT')

        # 4. Sockets
        # Base
        builder.active_faces = []
        builder.create_grid(size=0.5, center=Vector((0,0,0))) # Hidden anchor
        builder.tag_socket(9)
        # Delete grid faces? No, need geometry for socket.
        # But should be invisible/slot 9?
        builder.tag_slot(9)

        builder.clean()

    def execute(self, context):
        return super().execute(context)
