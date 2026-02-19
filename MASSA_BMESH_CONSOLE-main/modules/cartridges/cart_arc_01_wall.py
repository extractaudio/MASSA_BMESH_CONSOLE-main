import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARC_01: Parametric Wall",
    "id": "arc_01_wall",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcWall(Massa_OT_Base):
    bl_idname = "massa.gen_arc_01_wall"
    bl_label = "ARC Wall"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    wall_length: FloatProperty(name="Length", default=4.0, min=0.1)
    wall_height: FloatProperty(name="Height", default=3.0, min=0.1)
    wall_thick: FloatProperty(name="Thickness", default=0.2, min=0.01)

    # Hole Parameters (Window/Door)
    hole_enable: BoolProperty(name="Enable Hole", default=False)
    hole_x: FloatProperty(name="Hole X", default=2.0)
    hole_z: FloatProperty(name="Hole Z", default=1.0)
    hole_width: FloatProperty(name="Hole Width", default=1.0)
    hole_height: FloatProperty(name="Hole Height", default=1.5)

    # Baseboard
    baseboard_height: FloatProperty(name="Baseboard H", default=0.15, min=0.0)
    baseboard_depth: FloatProperty(name="Baseboard D", default=0.02, min=0.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Wall Plaster", "uv": "SKIP", "phys": "CONCRETE"},
            2: {"name": "Trim", "uv": "BOX", "phys": "WOOD"},  # Baseboard
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 2. Generate Base Grid (Front Face)
        segs_x = 8
        segs_z = 6

        # Create Grid
        bmesh.ops.create_grid(bm, x_segments=segs_x, y_segments=segs_z, size=0.5)

        # Scale to dimensions
        bmesh.ops.scale(bm, vec=Vector((self.wall_length, self.wall_height, 1)), verts=bm.verts)
        # Move to verify origin (Grid is centered)
        bmesh.ops.translate(bm, vec=Vector((self.wall_length/2, 0, self.wall_height/2)), verts=bm.verts)
        # Rotate to upright (Grid is on XY, need XZ)
        bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=bm.verts)

        # 3. Cut Holes (Delete Faces)
        if self.hole_enable:
            faces_to_delete = []
            hole_min_x = self.hole_x - self.hole_width/2
            hole_max_x = self.hole_x + self.hole_width/2
            hole_min_z = self.hole_z - self.hole_height/2
            hole_max_z = self.hole_z + self.hole_height/2

            # Find faces inside bounds
            for f in bm.faces:
                c = f.calc_center_median()
                if (hole_min_x <= c.x <= hole_max_x) and (hole_min_z <= c.z <= hole_max_z):
                    faces_to_delete.append(f)

            bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')

        # 4. Extrude Thickness
        # Extrude all faces along Y
        ret = bmesh.ops.extrude_face_region(bm, geom=bm.faces)
        extruded_geom = ret['geom']

        # Filter for vertices to move
        verts_to_move = [e for e in extruded_geom if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, self.wall_thick, 0)), verts=verts_to_move)

        # 5. Baseboard Logic
        if self.baseboard_height > 0:
            # Bisect at baseboard height
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:]+bm.verts[:], plane_co=Vector((0,0,self.baseboard_height)), plane_no=Vector((0,0,1)))

            # Assign material to faces below height
            for f in bm.faces:
                if f.calc_center_median().z < self.baseboard_height:
                    f.material_index = 2 # Trim (Slot 2)

        # 6. Sockets (Geometric Method)
        if self.hole_enable:
            # Create a small quad in the center of the hole
            # Center of hole: (self.hole_x, self.wall_thick/2, self.hole_z)
            c = Vector((self.hole_x, self.wall_thick/2, self.hole_z))
            sz = 0.1

            # Face oriented Y (Front/Back)
            v1 = bm.verts.new(c + Vector((-sz, 0, -sz)))
            v2 = bm.verts.new(c + Vector((sz, 0, -sz)))
            v3 = bm.verts.new(c + Vector((sz, 0, sz)))
            v4 = bm.verts.new(c + Vector((-sz, 0, sz)))

            f_sock = bm.faces.new((v1, v2, v3, v4))
            f_sock.material_index = 9 # Socket Anchor

        # 7. Manual UVs
        scale_u = getattr(self, "uv_scale_0", 1.0)
        scale_v = scale_u

        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            # Wall & Trim
            n = f.normal
            for l in f.loops:
                v_co = l.vert.co
                if abs(n.y) > 0.5:
                    l[uv_layer].uv = (v_co.x * scale_u, v_co.z * scale_v)
                elif abs(n.x) > 0.5:
                    l[uv_layer].uv = (v_co.y * scale_u, v_co.z * scale_v)
                else:
                    l[uv_layer].uv = (v_co.x * scale_u, v_co.y * scale_v)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "wall_length")
        col.prop(self, "wall_height")
        col.prop(self, "wall_thick")

        layout.separator()
        col = layout.column(align=True)
        col.prop(self, "hole_enable")
        if self.hole_enable:
            col.prop(self, "hole_x")
            col.prop(self, "hole_z")
            col.prop(self, "hole_width")
            col.prop(self, "hole_height")

        layout.separator()
        col = layout.column(align=True)
        col.prop(self, "baseboard_height")
