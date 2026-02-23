import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

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
        # Ensure Layers exist
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        # 1. Create Base Wall (Front Face)
        # We start with a grid on XY, rotate to XZ
        # Wall is created at origin, then moved.

        # Grid Resolution based on size (approx 0.5m per segment)
        segs_x = max(2, int(self.wall_length / 0.5))
        segs_z = max(2, int(self.wall_height / 0.5))

        builder.create_grid(x_segments=segs_x, y_segments=segs_z, size=1.0) \
               .rotate(90, axis='X') \
               .scale(self.wall_length, 1.0, self.wall_height) \
               .translate(self.wall_length/2, 0, self.wall_height/2)

        # 2. Cut Hole (Manual BMesh Op)
        if self.hole_enable:
            faces_to_delete = []
            hole_min_x = self.hole_x - self.hole_width/2
            hole_max_x = self.hole_x + self.hole_width/2
            hole_min_z = self.hole_z - self.hole_height/2
            hole_max_z = self.hole_z + self.hole_height/2

            # Use builder's active faces if set, else all
            # create_grid sets active_verts, active_faces might be empty?
            # MassaBuilder.create_grid does not explicitly set active_faces, only active_verts.
            # So we iterate bm.faces
            bm.faces.ensure_lookup_table()
            for f in bm.faces:
                c = f.calc_center_median()
                if (hole_min_x <= c.x <= hole_max_x) and (hole_min_z <= c.z <= hole_max_z):
                    faces_to_delete.append(f)

            if faces_to_delete:
                bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')
                builder._update() # Refresh lookup

        # 3. Extrude Thickness
        # Select all faces (Front face remains)
        builder.select_all_faces() \
               .extrude(self.wall_thick, axis=Vector((0, 1, 0))) \
               .clean() # Remove doubles/recalc normals

        # 4. Baseboard
        if self.baseboard_height > 0:
            # Bisect Plane
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:]+bm.verts[:],
                                   plane_co=Vector((0,0,self.baseboard_height)),
                                   plane_no=Vector((0,0,1)))
            builder._update()

            # Select Bottom Faces (Front and Back? Or just Front?)
            # Usually baseboard is on both sides or just interior.
            # Let's assume both sides (Front Y=0, Back Y=Thick)
            # We select faces below height AND facing Y or -Y (vertical walls)

            # Helper: select faces by height < limit
            builder.select_faces_by_height(min_z=-0.1, max_z=self.baseboard_height - 0.001)

            # Filter for vertical faces only (normal Z near 0)
            vertical_faces = [f for f in builder.active_faces if abs(f.normal.z) < 0.1]
            builder.active_faces = vertical_faces

            # Tag Material
            builder.tag_slot(2)

            # Extrude Baseboard Depth?
            if self.baseboard_depth > 0.001:
                # We want to extrude OUTWARD (along normal)
                # MassaBuilder.extrude(distance, axis=None) extrudes along normal ("Region Extrude")
                # But region extrude on multiple disconnected faces (Front/Back) works fine.
                builder.extrude(self.baseboard_depth)

                # Tag side faces of extrusion?
                # Extrude operation updates active_faces to new faces (fronts).
                # Side faces are usually created but not selected?
                # MassaBuilder.extrude: self.active_faces = extruded_faces

                # Tag all selected (new fronts) as 2
                builder.tag_slot(2)

        # 5. Edge Roles
        # Mark perimeter edges as 1
        # Edges on sharp angles > 80 deg
        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1
            else:
                try:
                    angle = e.calc_face_angle()
                except ValueError:
                    angle = 0.0 # Wire edges

                if angle > math.radians(80):
                    e[edge_slots] = 2

        # 6. Sockets (Geometric Method)
        if self.hole_enable:
            # Create a small quad in the center of the hole
            c = Vector((self.hole_x, self.wall_thick/2, self.hole_z))
            sz = 0.1

            # Use builder to create a standalone face?
            # MassaBuilder methods usually operate on existing bm.
            # We can use create_grid but it translates.

            # Let's manual build to ensure index 9
            v1 = bm.verts.new(c + Vector((-sz, 0, -sz)))
            v2 = bm.verts.new(c + Vector((sz, 0, -sz)))
            v3 = bm.verts.new(c + Vector((sz, 0, sz)))
            v4 = bm.verts.new(c + Vector((-sz, 0, sz)))
            f_sock = bm.faces.new((v1, v2, v3, v4))
            f_sock.material_index = 9

            # Force Normal Y-
            f_sock.normal_update()
            # (If winding is wrong, we might need to flip)

        # 7. Manual UVs
        self.apply_manual_uvs(bm)

    def apply_manual_uvs(self, bm):
        uv_layer = bm.loops.layers.uv.verify()
        scale_u = getattr(self, "uv_scale_0", 1.0)
        scale_v = scale_u # Square scaling usually

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            n = f.normal

            # Baseboard (Slot 2) might need different scale?
            # Using global scale for now.

            for l in f.loops:
                v_co = l.vert.co
                # Box Mapping
                if abs(n.y) > 0.5: # Front/Back
                    l[uv_layer].uv = (v_co.x * scale_u, v_co.z * scale_v)
                elif abs(n.x) > 0.5: # Side
                    l[uv_layer].uv = (v_co.y * scale_u, v_co.z * scale_v)
                else: # Top/Bottom
                    l[uv_layer].uv = (v_co.x * scale_u, v_co.y * scale_v)

    def draw_shape_ui(self, layout):
        box_dim = layout.box()
        box_dim.label(text="Dimensions", icon='MESH_CUBE')
        col = box_dim.column(align=True)
        col.prop(self, "wall_length")
        col.prop(self, "wall_height")
        col.prop(self, "wall_thick")

        box_hole = layout.box()
        box_hole.label(text="Opening", icon='MOD_BOOLEAN')
        col = box_hole.column(align=True)
        col.prop(self, "hole_enable", toggle=True)
        if self.hole_enable:
            col.prop(self, "hole_x")
            col.prop(self, "hole_z")
            col.prop(self, "hole_width")
            col.prop(self, "hole_height")

        box_trim = layout.box()
        box_trim.label(text="Baseboard", icon='MOD_BUILD')
        col = box_trim.column(align=True)
        col.prop(self, "baseboard_height")
        col.prop(self, "baseboard_depth")
