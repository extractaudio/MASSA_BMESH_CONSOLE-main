import bpy
import bmesh
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "TEST: Builder Example",
    "id": "massa_builder_example",
    "icon": "MESH_ICOSPHERE",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": True,
        "ALLOW_SOLIDIFY": True,
    },
}

class MASSA_OT_BuilderExample(Massa_OT_Base):
    bl_idname = "massa.gen_massa_builder_example"
    bl_label = "TEST: Builder Example"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    base_size: FloatProperty(name="Base Size", default=2.0, min=0.5)
    steps: IntProperty(name="Steps", default=3, min=1, max=10)
    step_height: FloatProperty(name="Step Height", default=0.5, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Base Material", "uv": "BOX", "phys": "CONCRETE_RAW"},
            1: {"name": "Treads", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Accents", "uv": "BOX", "phys": "EMISSIVE"},
            9: {"name": "Socket Top", "uv": "SKIP", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "base_size")
        col.prop(self, "steps")
        col.prop(self, "step_height")

    def build_shape(self, bm: bmesh.types.BMesh):
        builder = MassaBuilder(bm)

        # 1. Create Base
        builder.create_box(
            width=self.base_size,
            depth=self.base_size,
            height=self.step_height,
            center=Vector((0, 0, self.step_height / 2))
        )
        builder.tag_slot(0) # Base Material

        # 2. Iterate Steps (Ziggurat)
        current_size = self.base_size

        for i in range(self.steps):
            # Select Top Face
            builder.select_faces_by_normal(Vector((0, 0, 1)))

            # Inset to create landing
            inset_amount = (self.base_size / (self.steps * 2)) * 0.5
            builder.inset(inset_amount, relative=False)

            # Tag the "Landing" (the rim created by inset is actually the original face usually?
            # Wait, bmesh inset returns the inner faces. The outer rim is the 'other' faces.
            # MassaBuilder.inset updates active_faces to the NEW INNER faces.
            # So we are now selecting the inner square.

            # Tag the inner square as Tread before extruding? No, let's keep it Base.

            # Extrude Up
            builder.extrude(self.step_height)

            # Tag the Sides of the new extrusion?
            # MassaBuilder.extrude selects the newly created side faces AND the top face?
            # Standard bmesh extrude_region returns 'faces' which are the side walls + the top cap.
            # So all new geometry is selected.

            # Let's verify selection by filtering normals.
            # Select only sides for Detail
            builder.tag_slot(1) # Make everything Metal first

            # Select Top again to reset for next loop
            builder.select_faces_by_normal(Vector((0, 0, 1)))
            builder.tag_slot(2) # Make top Accent (Emissive)

            current_size -= inset_amount * 2

        # 3. Add Socket to Top
        builder.select_faces_by_normal(Vector((0, 0, 1))) \
               .tag_socket(1)

        # 4. Report for Debug (visible in console)
        print(builder.report())

        # 5. Clean
        builder.clean()
