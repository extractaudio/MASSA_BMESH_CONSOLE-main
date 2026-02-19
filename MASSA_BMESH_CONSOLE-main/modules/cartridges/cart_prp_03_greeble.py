import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRP_03: Tech Panel",
    "id": "prp_03_greeble",
    "icon": "MOD_WIREFRAME",
    "scale_class": "MICRO",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_PrpGreeble(Massa_OT_Base):
    bl_idname = "massa.gen_prp_03_greeble"
    bl_label = "PRP Greeble"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    size_x: FloatProperty(name="Size X", default=1.0, min=0.1)
    size_y: FloatProperty(name="Size Y", default=1.0, min=0.1)
    thickness: FloatProperty(name="Thickness", default=0.1, min=0.01)

    # Randomness
    seed: IntProperty(name="Seed", default=0)
    density: IntProperty(name="Density", default=5, min=1)
    greeble_depth: FloatProperty(name="Greeble Depth", default=0.05, min=0.01)
    light_chance: FloatProperty(name="Light Probability", default=0.2, min=0.0, max=1.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Base Plate", "uv": "SKIP", "phys": "PLASTIC"},
            1: {"name": "Mechanical", "uv": "BOX", "phys": "METAL_DARK"},
            4: {"name": "LED Lights", "uv": "SKIP", "phys": "GLASS_EMISSIVE"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        random.seed(self.seed)

        sx, sy = self.size_x, self.size_y
        th = self.thickness
        gd = self.greeble_depth

        # 2. Base Plate
        # Create Plane
        ret = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
        bmesh.ops.scale(bm, vec=Vector((sx, sy, 1.0)), verts=ret['verts'])

        # Extrude Thickness
        # ret_ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        # verts_ext = [e for e in ret_ext['geom'] if isinstance(e, bmesh.types.BMVert)]
        # bmesh.ops.translate(bm, vec=Vector((0, 0, -th)), verts=verts_ext)

        # Base Face is at Z=0. We will greeble UP (positive Z).
        # Or greeble down? Usually panels stick out.
        # Let's say Z=0 is wall.

        base_face = bm.faces[0]
        base_face.material_index = 0

        # 3. Random Bisection (Grid)
        # Use simple bisection

        for i in range(self.density):
            # Random axis: X or Y
            axis = random.choice(['X', 'Y'])

            # Random position: -0.5 to 0.5 relative to size
            # Range: -sx/2 to sx/2

            if axis == 'X':
                cut_pos = (random.random() - 0.5) * sx * 0.9 # Keep within bounds
                plane_co = Vector((cut_pos, 0, 0))
                plane_no = Vector((1, 0, 0))
            else:
                cut_pos = (random.random() - 0.5) * sy * 0.9
                plane_co = Vector((0, cut_pos, 0))
                plane_no = Vector((0, 1, 0))

            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:]+bm.verts[:], plane_co=plane_co, plane_no=plane_no)

        # 4. Inset/Extrude Faces
        # Iterate faces
        # Need to collect faces because list changes
        faces = [f for f in bm.faces]

        for f in faces:
            # Chance to be greebled
            if random.random() > 0.3:
                # Random Inset/Extrude

                # Inset amount
                inset_amt = random.uniform(0.01, 0.05)
                # Extrude height (positive or negative)
                extrude_h = random.uniform(0.01, gd)

                # Inset Individual
                ret_inset = bmesh.ops.inset_individual(bm, faces=[f], thickness=inset_amt, use_even_offset=True)

                # Extrude the inner face
                # The inner face is usually the one created/modified.
                # Inset returns faces added (rim). The modified face is f?
                # Usually yes.

                # Identify center face
                # Center of original face f
                c = f.calc_center_median()

                # If f is still valid?
                if f.is_valid:
                    # Extrude
                    ret_ext = bmesh.ops.extrude_face_region(bm, geom=[f])
                    verts_move = [e for e in ret_ext['geom'] if isinstance(e, bmesh.types.BMVert)]
                    bmesh.ops.translate(bm, vec=Vector((0, 0, extrude_h)), verts=verts_move)

                    # Top face of extrusion
                    top_f = [g for g in ret_ext['geom'] if isinstance(g, bmesh.types.BMFace)][0]
                    top_f.material_index = 1 # Mechanical

                    # Chance for Light (Emission)
                    # On small faces? Or inset again.
                    if random.random() < self.light_chance:
                        # Inset again deeply?
                        ret_inset2 = bmesh.ops.inset_individual(bm, faces=[top_f], thickness=0.02, depth=-0.01)
                        # Center face
                        if top_f.is_valid:
                            top_f.material_index = 4 # LED

        # 5. Base Thickness
        # Extrude everything down?
        # Select all bottom faces (Z=0)
        # Inset created holes?
        # Just create back face.
        # Or extrude all boundary edges down.

        # Let's extrude the perimeter edges down to create thickness.
        perimeter_edges = [e for e in bm.edges if e.is_boundary]
        if perimeter_edges:
            ret_wall = bmesh.ops.extrude_edge_only(bm, edges=perimeter_edges)
            verts_wall = [e for e in ret_wall['geom'] if isinstance(e, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=Vector((0, 0, -th)), verts=verts_wall)

            # Close bottom?
            # bmesh.ops.context_create(bm, geom=ret_wall['geom']) # Doesn't exist
            # Create face from bottom loop
            # Try to fill holes.
            # bmesh.ops.edgeloop_fill(bm, edges=...)
            pass

        # 6. Sockets
        # Center of base
        # Create socket on back?
        # Or on top of highest greeble?
        # Mandate: "Slap this on any flat wall". So socket should be on BACK (Z=-th).
        # Or Z=0 if we assume origin is back.
        # Origin is back.

        # 7. Manual UVs
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
        col.prop(self, "size_x")
        col.prop(self, "size_y")
        col.prop(self, "thickness")
        layout.separator()
        col.prop(self, "seed")
        col.prop(self, "density")
        col.prop(self, "greeble_depth")
        col.prop(self, "light_chance")
