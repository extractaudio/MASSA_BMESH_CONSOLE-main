import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_18: Heat Exchanger",
    "id": "ind_18_heat_exchanger",
    "icon": "MOD_ARRAY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndHeatExchanger(Massa_OT_Base):
    bl_idname = "massa.gen_ind_18_heat_exchanger"
    bl_label = "IND Heat Exchanger"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # 1. Style Enum
    style: EnumProperty(
        name="Exchanger Type",
        items=[
            ("RADIATOR", "Radiator Array", "Block with high-density cooling fins"),
            ("TUBE_BUNDLE", "Shell & Tube", "Industrial cylindrical tube bundle"),
            ("COOLING_TOWER", "Cooling Tower", "Vertical unit with top fan"),
        ],
        default="RADIATOR"
    )

    # 2. Dimensions
    width: FloatProperty(name="Width", default=2.0, min=0.5)
    height: FloatProperty(name="Height", default=1.5, min=0.5)
    depth: FloatProperty(name="Depth", default=1.0, min=0.2)

    # 3. Details
    fin_density: IntProperty(name="Fins/Tubes", default=8, min=1, max=50)
    pipe_radius: FloatProperty(name="Pipe Radius", default=0.05, min=0.01, max=0.2)
    frame_thickness: FloatProperty(name="Frame Thick", default=0.1, min=0.01, max=0.2)

    fan_radius: FloatProperty(name="Fan Size", default=0.6, min=0.2)
    grill_inset: FloatProperty(name="Grill Inset", default=0.05, min=0.0, max=0.2)
    inlet_count: IntProperty(name="Inlets", default=2, min=0, max=4)
    mount_legs: BoolProperty(name="Mount Legs", default=True)

    # New Params for count compliance
    pipe_offset: FloatProperty(name="Pipe Offset", default=0.2, min=0.0)
    inlet_radius: FloatProperty(name="Inlet Size", default=0.1, min=0.01)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame/Shell", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Fins/Core", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            2: {"name": "Pipes/Fittings", "uv": "BOX", "phys": "METAL_COPPER"},
            3: {"name": "Fan/Grill", "uv": "BOX", "phys": "METAL_MESH"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions")
        box.prop(self, "width")
        box.prop(self, "height")
        box.prop(self, "depth")

        box = layout.box()
        box.label(text="Core")
        box.prop(self, "fin_density")
        box.prop(self, "pipe_radius")
        box.prop(self, "frame_thickness")

        box = layout.box()
        box.label(text="Features")
        box.prop(self, "fan_radius")
        box.prop(self, "inlet_count")
        box.prop(self, "mount_legs")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        h = self.height
        d = self.depth
        ft = self.frame_thickness

        if self.style == "RADIATOR":
            # Outer Frame
            # Create box
            builder.create_box(w, d, h, center=Vector((0,0,h/2)))
            builder.tag_slot(0)

            # Select Front and Back faces to inset for core
            # Front (Y-)
            builder.select_faces_by_normal(Vector((0,-1,0)))
            builder.inset(ft, depth=-0.05)

            # Create Fins inside?
            # Actually easier to build frame and core separately.

            # Build Core (Inner Box)
            core_w = w - ft*2
            core_h = h - ft*2
            core_d = d - 0.1 # Recessed

            builder.create_box(core_w, core_d, core_h, center=Vector((0,0,h/2)))
            builder.tag_slot(1) # Fins

            # Fins detail: Texture or geometry?
            # Geometry fins (Array of thin plates)
            if self.fin_density > 0:
                fin_spacing = core_w / (self.fin_density + 1)
                fin_thick = fin_spacing * 0.2

                # We can't easily boolean cut. We can add vertical slats.
                # Just add plates sticking out slightly or flush
                for i in range(self.fin_density):
                    off_x = -core_w/2 + (i+1)*fin_spacing
                    builder.create_box(fin_thick, core_d + 0.02, core_h, center=Vector((off_x, 0, h/2)))
                    builder.tag_slot(1)

        elif self.style == "TUBE_BUNDLE":
            # Horizontal Shell (Cylinder)
            # Length = Width param
            radius = h / 2.0

            # Main Shell
            builder.create_cylinder(radius=radius, depth=w, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y') # Align along X
            builder.translate(0, 0, radius + 0.2) # Lift up
            builder.tag_slot(0)

            # End Caps (Headers)
            # Create larger cylinders at ends
            cap_thick = 0.2
            # Left Cap
            builder.create_cylinder(radius=radius + 0.1, depth=cap_thick, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y')
            builder.translate(-w/2 - cap_thick/2, 0, radius + 0.2)
            builder.tag_slot(2) # Copper/Brass

            # Right Cap
            builder.create_cylinder(radius=radius + 0.1, depth=cap_thick, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y')
            builder.translate(w/2 + cap_thick/2, 0, radius + 0.2)
            builder.tag_slot(2)

            # Tubes inside? (Visible if no caps, but we added caps)
            # Let's add pipes connecting headers if "fin_density" implies tube count?
            # Actually Shell & Tube usually is enclosed.

            # Legs (Saddles)
            saddle_h = 0.4
            builder.create_box(0.3, radius*1.5, saddle_h, center=Vector((-w*0.3, 0, saddle_h/2)))
            builder.tag_slot(0)
            builder.create_box(0.3, radius*1.5, saddle_h, center=Vector((w*0.3, 0, saddle_h/2)))
            builder.tag_slot(0)

        elif self.style == "COOLING_TOWER":
            # Box with Fan on top
            # Main Housing
            builder.create_box(w, d, h, center=Vector((0,0,h/2)))
            builder.tag_slot(0)

            # Top Fan Housing
            # Select Top
            builder.select_faces_by_normal(Vector((0,0,1)))
            builder.inset(ft, depth=-0.1)

            # Fan Blades / Grill
            # Create cylinder for fan area
            # Use fan_radius, but clamp to fit geometry
            fr = min(self.fan_radius, w/2 - ft, d/2 - ft)
            builder.create_cylinder(radius=fr, depth=0.05, center=Vector((0,0,h - 0.05)))
            builder.tag_slot(3) # Mesh

            # Air Inlets at bottom sides
            # Just add Grill boxes using grill_inset

            grill_h = h * 0.3
            # grill_inset creates a recessed look by making the box slightly inside?
            # Or determines grid spacing?
            # Let's use it as depth of the grill box.

            gd = self.grill_inset if self.grill_inset > 0.01 else 0.05

            builder.create_box(gd, d*0.8, grill_h, center=Vector((w/2 - gd/2 + 0.02, 0, grill_h/2 + 0.2)))
            builder.tag_slot(3)

            builder.create_box(gd, d*0.8, grill_h, center=Vector((-w/2 + gd/2 - 0.02, 0, grill_h/2 + 0.2)))
            builder.tag_slot(3)

        # Common Details

        # Pipes / Inlets
        if self.inlet_count > 0:
            # Place randomly or symmetrically
            # For Radiator: Top/Bottom.
            # For Tube: Top/Bottom of shell.
            # For Tower: Side.

            pr = self.pipe_radius

            if self.style == "TUBE_BUNDLE":
                # Top inlet, Bottom outlet
                # Top
                builder.create_cylinder(radius=pr, depth=0.5, center=Vector((0,0,0)))
                builder.translate(-w/3, 0, h + 0.2)
                builder.tag_slot(2)
                # Flange
                builder.create_cylinder(radius=pr*2, depth=0.05, center=Vector((0,0,0)))
                builder.translate(-w/3, 0, h + 0.2 + 0.25)
                builder.tag_slot(2)

            elif self.style == "RADIATOR":
                # Side pipes
                # Use pipe_offset
                po = self.pipe_offset
                ir = self.inlet_radius

                builder.create_cylinder(radius=ir, depth=0.5, center=Vector((0,0,0)))
                builder.rotate(90, axis='Y')
                builder.translate(w/2 + 0.2, d/3, h - 0.3 - po)
                builder.tag_slot(2)

        # Mount Legs
        if self.mount_legs and self.style != "TUBE_BUNDLE": # Tube has saddles
            leg_h = 0.2
            leg_w = 0.1

            # 4 Corners
            for x in [-w/2 + 0.1, w/2 - 0.1]:
                for y in [-d/2 + 0.1, d/2 - 0.1]:
                    builder.create_box(leg_w, leg_w, leg_h, center=Vector((x,y,leg_h/2)))
                    builder.tag_slot(0)

        # Socket (Floor)
        min_z = 1000
        for f in bm.faces:
             z = f.calc_center_median().z
             if z < min_z: min_z = z

        active_faces = [f for f in bm.faces if abs(f.calc_center_median().z - min_z) < 0.05 and f.normal.z < -0.5]
        builder.active_faces = active_faces
        builder.tag_socket(9).tag_slot(9)

        # UV
        builder.select_all_faces().tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.clean()

    def execute(self, context):
        return super().execute(context)
