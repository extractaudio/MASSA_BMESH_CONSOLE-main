import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "LND_01: Planter Wall",
    "id": "lnd_01_planter",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_LndPlanter(Massa_OT_Base):
    bl_idname = "massa.gen_lnd_01_planter"
    bl_label = "LND Planter"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=4.0, min=1.0)
    width: FloatProperty(name="Width", default=2.0, min=0.5)
    height: FloatProperty(name="Height", default=1.0, min=0.1)

    # Steps/Terrace
    steps: IntProperty(name="Steps", default=1, min=1)
    wall_thick: FloatProperty(name="Wall Thickness", default=0.2, min=0.05)
    dirt_depth: FloatProperty(name="Dirt Depth", default=0.3, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Concrete", "uv": "SKIP", "phys": "CONCRETE"},
            1: {"name": "Soil", "uv": "BOX", "phys": "ORGANIC_SOIL"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        l, w, h = self.length, self.width, self.height
        st = self.steps
        wt = self.wall_thick
        dd = self.dirt_depth

        # 2. Main Volume
        # If stepped, we create terraces.
        # Let's say we step UP or step BACK?
        # Usually stepped planter means tiered boxes.
        # Box 1 at Z=0. Box 2 at Z=h/st, recessed?

        # Let's build separate boxes stacked.

        step_h = h / st
        step_l = l # Full length? Or stepped length too?
        step_w = w / st # Width decreases?

        # Assume linear step back in Width (Y)
        curr_w = w
        curr_y = -w/2
        curr_z = 0

        # Create base block
        # Actually a single block with inset top is simpler for 1 step.
        # For multiple steps, let's create boxes.

        for i in range(st):
            # Create Box
            # Width for this step: w/st? No, usually terraces are equal width.
            # Total width W divided into steps?
            # Let's assume each step has depth `step_depth = w / st`.
            # Height of this step relative to ground: (i+1)*step_h

            # Box Base Y: -w/2 + i*step_depth
            # Box Top Y: -w/2 + (i+1)*step_depth
            # Box Z: (i+1)*step_h

            step_depth = w / st
            y_start = -w/2 + i * step_depth
            y_end = -w/2 + (i+1) * step_depth
            z_top = (i+1) * step_h

            # Verts
            v1 = bm.verts.new(Vector((-l/2, y_start, 0)))
            v2 = bm.verts.new(Vector((l/2, y_start, 0)))
            v3 = bm.verts.new(Vector((l/2, y_end, 0)))
            v4 = bm.verts.new(Vector((-l/2, y_end, 0)))

            v5 = bm.verts.new(Vector((-l/2, y_start, z_top)))
            v6 = bm.verts.new(Vector((l/2, y_start, z_top)))
            v7 = bm.verts.new(Vector((l/2, y_end, z_top)))
            v8 = bm.verts.new(Vector((-l/2, y_end, z_top)))

            # Create faces (Box)
            # Bottom, Top, Front, Back, Left, Right
            faces = []
            faces.append(bm.faces.new((v4, v3, v2, v1))) # Bottom
            top_f = bm.faces.new((v5, v6, v7, v8)) # Top
            faces.append(top_f)
            faces.append(bm.faces.new((v1, v2, v6, v5))) # Front (Y Start)
            faces.append(bm.faces.new((v2, v3, v7, v6))) # Right
            faces.append(bm.faces.new((v3, v4, v8, v7))) # Back (Y End)
            faces.append(bm.faces.new((v4, v1, v5, v8))) # Left

            # Assign Material 0 (Concrete)
            for f in faces:
                f.material_index = 0

            # 3. Create Basin (Inset Top)
            # Inset top face by wall_thick
            ret_inset = bmesh.ops.inset_individual(bm, faces=[top_f], thickness=wt, use_even_offset=True)

            # Inner Face
            # Usually the one modified or newly created center.
            # Select by normal Z > 0.9 and area?
            # Or use result.
            # Usually the face passed in `faces` becomes the center face if possible.
            # Let's check.

            center_face = top_f
            if center_face.is_valid:
                # Extrude Down for dirt
                ret_ext = bmesh.ops.extrude_face_region(bm, geom=[center_face])
                verts_down = [e for e in ret_ext['geom'] if isinstance(e, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, vec=Vector((0, 0, -dd)), verts=verts_down)

                # Bottom face is Dirt
                dirt_face = [f for f in ret_ext['geom'] if isinstance(f, bmesh.types.BMFace)][0]
                dirt_face.material_index = 1 # Soil

                # Side walls of basin are Concrete (default)
                # But extrusion creates side faces. They inherit material 0? Yes.

                # 4. Sockets (In Dirt)
                # Mandate: "Sockets generated in the dirt".
                # Add a socket anchor face in the center of the dirt face.
                # Inset the dirt face slightly? Or just mark it.
                # If dirt face is large, marking it makes the whole face a socket?
                # Engine generates socket object at face center. So marking the face works.
                # But we want multiple sockets for plants?
                # Let's mark the center face as dirt AND create a small socket face in center.

                # Let's subdivide dirt face to create a center point?
                # Poke.
                ret_poke = bmesh.ops.poke(bm, faces=[dirt_face])
                center_vert = ret_poke['verts'][0]
                # Center vert is socket location? No, need face.
                # The poke created triangles.
                # If we want a socket object, we need a face with mat index 9.
                # Let's create a tiny face at center vert?

                # Easier: Just mark the dirt face itself as Socket Anchor?
                # But usually socket anchor material is hidden/removed or used as placeholder.
                # If dirt is visible, we can't change its material to 9.
                # We need a separate face.

                # Create a small quad floating just above dirt.
                c = center_vert.co
                sz = 0.1
                v_s1 = bm.verts.new(c + Vector((-sz, -sz, 0.05)))
                v_s2 = bm.verts.new(c + Vector((sz, -sz, 0.05)))
                v_s3 = bm.verts.new(c + Vector((sz, sz, 0.05)))
                v_s4 = bm.verts.new(c + Vector((-sz, sz, 0.05)))
                f_sock = bm.faces.new((v_s1, v_s2, v_s3, v_s4))
                f_sock.material_index = 9

        # 5. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)
        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            n = f.normal
            # Box map
            for l in f.loops:
                if abs(n.z) > 0.5:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)
                elif abs(n.y) > 0.5:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
                else:
                    l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "steps")
        col.prop(self, "wall_thick")
        col.prop(self, "dirt_depth")
