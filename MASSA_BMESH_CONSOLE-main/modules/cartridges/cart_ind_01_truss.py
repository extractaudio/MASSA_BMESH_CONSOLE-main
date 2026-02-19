import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "IND_01: Space Frame",
    "id": "ind_01_truss",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False, # Wireframe usually doesn't bevel well
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndTruss(Massa_OT_Base):
    bl_idname = "massa.gen_ind_01_truss"
    bl_label = "IND Truss"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=4.0, min=0.1)
    width: FloatProperty(name="Width", default=0.5, min=0.1)
    height: FloatProperty(name="Height", default=0.5, min=0.1)

    # Grid
    segs_x: IntProperty(name="Segments X", default=4, min=1)

    # Struts
    strut_thick: FloatProperty(name="Strut Thickness", default=0.05, min=0.001)
    cross_bracing: BoolProperty(name="Cross Bracing", default=True)

    def get_slot_meta(self):
        return {
            0: {"name": "Metal", "uv": "BOX", "phys": "METAL_STEEL"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 2. Create Base Box Wireframe
        # Create vertices for box
        l, w, h = self.length, self.width, self.height
        sx = self.segs_x
        dx = l / sx

        # Create parallel rails
        # 4 rails: (x, -w/2, -h/2), (x, w/2, -h/2), (x, w/2, h/2), (x, -w/2, h/2)

        rails = [[], [], [], []]

        for i in range(sx + 1):
            x = -l/2 + i*dx
            v1 = bm.verts.new(Vector((x, -w/2, -h/2)))
            v2 = bm.verts.new(Vector((x, w/2, -h/2)))
            v3 = bm.verts.new(Vector((x, w/2, h/2)))
            v4 = bm.verts.new(Vector((x, -w/2, h/2)))

            rails[0].append(v1)
            rails[1].append(v2)
            rails[2].append(v3)
            rails[3].append(v4)

        bm.verts.ensure_lookup_table()

        # Connect Rails (Longitudinal)
        for r in rails:
            for i in range(len(r)-1):
                bm.edges.new((r[i], r[i+1]))

        # Connect Frames (Transverse) at each segment
        for i in range(sx + 1):
            # Square frame
            v1, v2, v3, v4 = rails[0][i], rails[1][i], rails[2][i], rails[3][i]
            bm.edges.new((v1, v2))
            bm.edges.new((v2, v3))
            bm.edges.new((v3, v4))
            bm.edges.new((v4, v1))

            # Cross Bracing (Diagonal)
            if self.cross_bracing:
                # X pattern on sides?
                # Or just inside the cube?
                # Usually trusses have diagonals on the faces.
                pass

        # Add Face Diagonals
        if self.cross_bracing:
            for i in range(sx):
                # For each segment (cube)
                # Sides: Bottom (0-1), Right (1-2), Top (2-3), Left (3-0)

                # Bottom Face Diagonals
                v0_a = rails[0][i]; v0_b = rails[0][i+1]
                v1_a = rails[1][i]; v1_b = rails[1][i+1]
                bm.edges.new((v0_a, v1_b))
                bm.edges.new((v1_a, v0_b))

                # Top Face
                v2_a = rails[2][i]; v2_b = rails[2][i+1]
                v3_a = rails[3][i]; v3_b = rails[3][i+1]
                bm.edges.new((v2_a, v3_b))
                bm.edges.new((v3_a, v2_b))

                # Side Right (1-2)
                bm.edges.new((v1_a, v2_b))
                bm.edges.new((v2_a, v1_b))

                # Side Left (3-0)
                bm.edges.new((v3_a, v0_b))
                bm.edges.new((v0_a, v3_b))

        # 3. Solidify (Wireframe to Mesh)
        # Use bmesh.ops.wireframe to turn edges into struts
        # Note: This deletes original edges and creates faces around them.
        bmesh.ops.wireframe(bm, edges=bm.edges, thickness=self.strut_thick, use_replace=True, use_boundary=True, use_even_offset=True)

        # 4. Cleanup & Roles
        # Mark all new edges as Perimeter?
        for e in bm.edges:
            e[edge_slots] = 1 # Perimeter (Hard Edge)

        # 5. Sockets
        # Add sockets at ends (Faces at min X and max X)
        # Identify faces whose normal is (-1,0,0) or (1,0,0)
        for f in bm.faces:
            n = f.normal
            c = f.calc_center_median()
            if abs(c.x + l/2) < 0.01 and n.x < -0.9: # Left End
                f.material_index = 9 # Socket Anchor
            elif abs(c.x - l/2) < 0.01 and n.x > 0.9: # Right End
                f.material_index = 9

        # 6. Manual UVs
        # Box Mapping for everything (struts are square)
        scale = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            if f.material_index == 9: continue

            n = f.normal
            for l in f.loops:
                if abs(n.x) > 0.5:
                    l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
                elif abs(n.y) > 0.5:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
                else:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "segs_x")
        col.prop(self, "strut_thick")
        col.prop(self, "cross_bracing")
