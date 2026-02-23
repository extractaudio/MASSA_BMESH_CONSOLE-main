import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_15: Turbine",
    "id": "ind_15_turbine",
    "icon": "MOD_FLUIDSIM", # Fluid/Gas dynamics
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndTurbine(Massa_OT_Base):
    bl_idname = "massa.gen_ind_15_turbine"
    bl_label = "IND Turbine"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("STEAM", "Steam Turbine", "Multi-stage cylindrical casing"),
            ("GAS", "Gas Turbine", "Jet engine style, conical"),
            ("HYDRO", "Hydro Turbine", "Scroll case / Francis style"),
        ],
        default="STEAM",
    )

    # Dimensions
    length: FloatProperty(name="Length (X)", default=4.0, min=1.0)
    radius: FloatProperty(name="Radius", default=1.0, min=0.5)

    # Flow
    inlet_radius: FloatProperty(name="Inlet Radius", default=0.8, min=0.2)
    outlet_radius: FloatProperty(name="Outlet Radius", default=0.6, min=0.2)

    # Structure
    casing_thick: FloatProperty(name="Casing Thickness", default=0.1, min=0.01)
    shaft_radius: FloatProperty(name="Shaft Radius", default=0.15, min=0.05)

    # Details
    blade_count: IntProperty(name="Blade Count", default=12, min=0)
    mount_width: FloatProperty(name="Mount Width", default=2.5, min=0.5)
    segments: IntProperty(name="Segments", default=32, min=8, soft_max=64)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Casing", "uv": "SKIP", "phys": "METAL_PAINTED"},
            1: {"name": "Internal", "uv": "SKIP", "phys": "METAL_STEEL"}, # Blades/Shaft
            2: {"name": "Mount", "uv": "SKIP", "phys": "CONCRETE_ROUGH"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style", text="")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Dimensions", icon="FIXED_SIZE")
        col.prop(self, "length")
        col.prop(self, "radius")
        col.prop(self, "segments")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Flow", icon="FORCE_WIND")
        col.prop(self, "inlet_radius")
        col.prop(self, "outlet_radius")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Internal", icon="MOD_SCREW")
        col.prop(self, "casing_thick")
        col.prop(self, "shaft_radius")
        col.prop(self, "blade_count")

        col.separator()
        col.prop(self, "mount_width")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")

        l = self.length
        r = self.radius
        ir = self.inlet_radius
        ore = self.outlet_radius
        segs = self.segments
        ct = self.casing_thick

        # Axis: X is flow direction (Length).

        # 1. Casing (Main Body)
        if self.style == "STEAM":
            # Stepped Cylinder (High/Low pressure stages)
            # 3 sections: High (small), Mid (med), Low (large)
            # Just approximate with cone segments

            # Section 1: Inlet (X-)
            l1 = l * 0.3
            r1 = r * 0.8
            builder.create_cylinder(radius=r1, depth=l1, segments=segs, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y').translate(-l/2 + l1/2, 0, 0)
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

            # Section 2: Mid
            l2 = l * 0.3
            r2 = r
            builder.create_cylinder(radius=r2, depth=l2, segments=segs, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y').translate(-l/2 + l1 + l2/2, 0, 0)
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

            # Section 3: Outlet (X+)
            l3 = l - l1 - l2
            r3 = r * 1.2
            builder.create_cylinder(radius=r3, depth=l3, segments=segs, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y').translate(l/2 - l3/2, 0, 0)
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

            # Inlet Pipe (Top)
            # On Section 1
            builder.create_cylinder(radius=ir, depth=r1*1.5, segments=segs, center=Vector((-l/2 + l1/2, 0, r1)))
            builder.tag_slot(0)
            # UVs for Inlet Pipe (Vertical)
            # Side walls CYLINDER Z. Caps BOX.
            all_f = builder.active_faces[:]
            caps = [f for f in all_f if abs(f.normal.z) > 0.5]
            walls = [f for f in all_f if abs(f.normal.z) <= 0.5]
            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls:
                builder.active_faces = walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER') # Default Z

        elif self.style == "GAS":
            # Conical Engine
            # Intake (Large) -> Compressor (Cone) -> Combustion -> Turbine -> Exhaust (Small)
            # Simplified: Cone
            builder.create_cone(radius_bottom=ir, radius_top=ore, depth=l, segments=segs, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y').tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

        elif self.style == "HYDRO":
            # Scroll Case (Spiral)
            # Hard to gen procedurally with simple primitives.
            # Use Cylinder + Pipe inlet on side.
            builder.create_cylinder(radius=r, depth=l*0.5, segments=segs, center=Vector((0,0,0)))
            # Rotate to X axis
            builder.rotate(90, axis='Y').tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

            # Penstock Inlet (Side)
            builder.create_cylinder(radius=ir, depth=r*2, segments=segs, center=Vector((0, r, 0)))
            builder.rotate(90, axis='X').tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='Y') # Along Y

        # 2. Shaft (Through center)
        sr = self.shaft_radius
        builder.create_cylinder(radius=sr, depth=l + 0.5, segments=segs, center=Vector((0,0,0)))
        builder.rotate(90, axis='Y').tag_slot(1).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

        # 3. Blades (Visible at ends?)
        if self.blade_count > 0:
            # Rotor at front/back
            # Just a disk with alpha? Or simple geometry.
            # Simple blades: Boxes rotated.

            # Position: -l/2 (Intake)
            bx = -l/2
            br = ir if self.style != "STEAM" else (r*0.8) # Radius fits casing

            for i in range(self.blade_count):
                angle = (i / self.blade_count) * 2 * math.pi
                # Blade vector
                y = math.cos(angle) * (br/2) # Center of blade
                z = math.sin(angle) * (br/2)

                # Blade Box
                # Thin, long (radius), wide (chord)
                # Aligned radially
                # We create at origin, rotate Z (twist) and Y (around shaft)?
                # Easier: Create at origin, rotate Z to angle, then translate.

                # Box dims: X=thickness, Y=width (radius), Z=chord
                # Actually: X=chord, Y=thickness, Z=radius?
                # Blade length is radius.
                # Create box: width=0.02, depth=br, height=0.1
                builder.create_box(0.1, 0.02, br, center=Vector((0,0,0)))
                # Rotate to angle around X (since shaft is X)
                # Rotate X by angle
                builder.rotate(math.degrees(angle), axis='X')

                # Move to front
                builder.translate(bx, 0, 0)

                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 4. Mounts
        mw = self.mount_width
        # Feet under the casing
        # 2 feet: Front and Back

        # Front Foot
        fx = -l/3
        # Z pos: Bottom of casing to Z=0? Or casing center is Z=R?
        # Assuming casing center at Z=0?
        # Yes, created at (0,0,0).
        # So bottom of casing is -R.
        # Floor is at -R*1.5?
        floor_z = -r * 1.2

        foot_h = abs(floor_z - (-r)) + 0.1 # Connect

        builder.create_box(0.5, mw, foot_h, center=Vector((fx, 0, floor_z + foot_h/2)))
        builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Back Foot
        bx = l/3
        builder.create_box(0.5, mw, foot_h, center=Vector((bx, 0, floor_z + foot_h/2)))
        builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Anchor Sockets on feet bottom
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1)
        # Filter near floor_z
        anchors = [f for f in builder.active_faces if abs(f.calc_center_median().z - floor_z) < 0.2]
        if anchors:
            builder.active_faces = anchors
            builder.tag_socket(9)

        # Flow Sockets (In/Out)
        # Intake (-X)
        builder.select_faces_by_normal(Vector((-1,0,0)), tolerance=0.1)
        # Find face near -l/2
        intake = [f for f in builder.active_faces if f.calc_center_median().x < -l/2 + 0.5]
        if intake:
            builder.active_faces = intake
            builder.tag_socket(1) # In

        # Exhaust (+X)
        builder.select_faces_by_normal(Vector((1,0,0)), tolerance=0.1)
        exhaust = [f for f in builder.active_faces if f.calc_center_median().x > l/2 - 0.5]
        if exhaust:
            builder.active_faces = exhaust
            builder.tag_socket(0) # Out (0 is usually output)

        # Update normals before selection
        bm.normal_update()

        # FINAL UV FIX: Ensure all horizontal faces (Caps) use BOX to prevent pinching
        # Handle X normals (Caps of main casing)
        builder.select_faces_by_normal(Vector((1,0,0)), tolerance=0.6)
        x_pos = builder.active_faces[:]
        builder.select_faces_by_normal(Vector((-1,0,0)), tolerance=0.6)
        x_neg = builder.active_faces[:]

        builder.active_faces = x_pos + x_neg
        builder.tag_uvs(scale=self.uv_scale, projection='BOX')

        # Handle Z normals (Inlet pipe caps, Mounts)
        builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.6)
        z_pos = builder.active_faces[:]
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.6)
        z_neg = builder.active_faces[:]

        builder.active_faces = z_pos + z_neg
        builder.tag_uvs(scale=self.uv_scale, projection='BOX')

        builder.clean()
