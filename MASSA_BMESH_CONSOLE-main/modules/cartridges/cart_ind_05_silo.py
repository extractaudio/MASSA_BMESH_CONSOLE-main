import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_05: Silo",
    "id": "ind_05_silo",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndSilo(Massa_OT_Base):
    bl_idname = "massa.gen_ind_05_silo"
    bl_label = "IND Silo"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    height: FloatProperty(name="Tank Height", default=4.0, min=0.5)
    radius: FloatProperty(name="Radius", default=1.5, min=0.5)
    leg_height: FloatProperty(name="Leg Height", default=1.0, min=0.0)

    # Details
    segments: IntProperty(name="Segments", default=24, min=6)
    cap_height: FloatProperty(name="Cap Height", default=0.5, min=0.0)

    # Legs
    num_legs: IntProperty(name="Leg Count", default=4, min=3)
    leg_width: FloatProperty(name="Leg Width", default=0.2, min=0.05)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Tank Body", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "Legs", "uv": "BOX", "phys": "METAL_RUST"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "height")
        col.prop(self, "radius")
        col.prop(self, "segments")
        layout.separator()
        col.prop(self, "leg_height")
        col.prop(self, "cap_height")
        col.prop(self, "num_legs")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        r = self.radius
        h = self.height
        lh = self.leg_height
        ch = self.cap_height
        segs = self.segments

        # 1. Tank Body
        center_z = lh + h/2
        builder.create_cylinder(radius=r, depth=h, segments=segs, center=Vector((0, 0, center_z)))
        builder.tag_slot(0)

        # Mark Vertical Seam (Edge Role 3)
        # Find edges that are vertical and at X ~ -R? Or X ~ 0, Y ~ R.
        # Cylinder seam is usually at start/end of ring (angle 0).
        # We can pick any vertical edge.
        # Filter active_edges (create_cylinder sets active_verts, active_faces).
        # We need edges from active_faces.

        # Also, we need to Poke Caps.
        # Select Top Face
        builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.01)
        if builder.active_faces and ch > 0:
            top_face = builder.active_faces[0]
            ret_poke = bmesh.ops.poke(bm, faces=[top_face])
            c_vert = ret_poke['verts'][0]
            bmesh.ops.translate(bm, vec=Vector((0,0,ch)), verts=[c_vert])

        # Select Bottom Face
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.01)
        if builder.active_faces and ch > 0:
            bot_face = builder.active_faces[0]
            ret_poke = bmesh.ops.poke(bm, faces=[bot_face])
            c_vert = ret_poke['verts'][0]
            bmesh.ops.translate(bm, vec=Vector((0,0,-ch)), verts=[c_vert])

        # Seam logic: Select one vertical edge.
        # Find edge connecting top rim to bot rim at angle 0.
        # Angle 0 is +X.
        target_x = r
        target_y = 0
        best_edge = None
        min_dist = 999

        # Iterate all edges in BM? Or subsets?
        for e in bm.edges:
            # Check verticality
            v1, v2 = e.verts
            if abs(v1.co.x - v2.co.x) < 0.01 and abs(v1.co.y - v2.co.y) < 0.01:
                # Vertical. Check position.
                dist = math.hypot(v1.co.x - target_x, v1.co.y - target_y)
                if dist < min_dist:
                    min_dist = dist
                    best_edge = e

        if best_edge:
            layer_edge = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
            best_edge[layer_edge] = 3 # Guide
            best_edge.seam = True

        # 2. Legs
        if lh > 0:
            num = self.num_legs
            lw = self.leg_width

            for i in range(num):
                angle = (i / num) * 2 * math.pi
                lx = math.cos(angle) * r
                ly = math.sin(angle) * r

                # Leg position: centered on rim, extending down.
                # Box leg.
                # Center X/Y is lx/ly. Center Z is lh/2.

                builder.create_box(lw, lw, lh, center=Vector((0,0,0)))

                # Rotate Z to align with radial?
                rot_mat = Matrix.Rotation(angle, 4, 'Z')

                # Translate to pos
                trans_mat = Matrix.Translation(Vector((lx, ly, lh/2)))

                final_mat = trans_mat @ rot_mat
                builder.transform(final_mat)
                builder.tag_slot(1)

        # 3. Sockets (Ports) at Cardinal Directions
        mid_z = lh + h/2
        port_rad = 0.2
        port_len = 0.1

        directions = [
            (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)
        ]

        for dx, dy, dz in directions:
            # Port position: Surface + offset
            px = dx * (r + port_len/2)
            py = dy * (r + port_len/2)
            pz = mid_z

            builder.create_cylinder(radius=port_rad, depth=port_len, segments=8, center=Vector((0,0,0)))

            # Rotate to face direction (Cylinder is Z-up)
            # We want Z to point in direction (dx, dy, 0)
            target = Vector((dx, dy, 0))
            rot_quat = Vector((0,0,1)).rotation_difference(target)

            mat = Matrix.Translation(Vector((px, py, pz))) @ rot_quat.to_matrix().to_4x4()
            builder.transform(mat)
            builder.tag_slot(0) # Port matches tank material

            # Tag Cap Face as Socket
            # Cap face is the one pointing 'target'
            builder.select_faces_by_normal(target, tolerance=0.1) \
                   .tag_socket(9).tag_slot(9)

        # 4. Manual UVs
        # Tank (Slot 0): Cylindrical? Or Polar?
        # builder.tag_uvs(projection='CYLINDER') works for vertical cylinder.
        # But we poked the caps.
        # The side faces are perfect for Cylinder map.
        # The cone faces might distort.
        # Slot 1 (Legs): Box.
        # Slot 9 (Ports): Box or Cylinder.

        # Select Slot 1
        builder.select_faces_by_slot(1) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Select Slot 0 (Tank + Ports)
        # This is tricky. Ports are horizontal. Tank is vertical.
        # We should select Tank Sides separately?
        # Tank sides have normal Z ~ 0.

        # Let's use 'CYLINDER' for everything in Slot 0.
        # Horizontal ports will have messy UVs with Vertical Cylinder projection.
        # But maybe acceptable?
        # Ideally we separate them.

        # Select Tank Vertical Faces
        # Normal Z is small.
        # And distance from center is ~ Radius.

        # Better: Select ALL Slot 0.
        # If normal Z is dominant -> PLANAR (Caps).
        # Else -> CYLINDER.

        faces_0 = [f for f in bm.faces if f.material_index == 0]

        for f in faces_0:
            # Check orientation
            if abs(f.normal.z) > 0.8:
                # Cap / Flat top
                builder.active_faces = [f]
                builder.tag_uvs(scale=self.uv_scale, projection='VIEW') # Planar
            else:
                # Side
                builder.active_faces = [f]
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        builder._update()
