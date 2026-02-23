import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Quaternion
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_01: Space Frame",
    "id": "ind_01_truss",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True, # Weld adjacent struts? Might get messy. Let's keep separate for clean UVs or weld carefully.
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndTruss(Massa_OT_Base):
    bl_idname = "massa.gen_ind_01_truss"
    bl_label = "IND Truss"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    # Axis: X is Length (Standard for this cartridge historically)
    length: FloatProperty(name="Length (X)", default=4.0, min=0.1)
    width: FloatProperty(name="Width (Y)", default=0.5, min=0.1)
    height: FloatProperty(name="Height (Z)", default=0.5, min=0.1)

    # Grid
    segs_x: IntProperty(name="Segments", default=4, min=1)

    # Struts
    strut_thick: FloatProperty(name="Strut Thickness", default=0.05, min=0.001)
    cross_bracing: BoolProperty(name="Cross Bracing", default=True)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Metal Structure", "uv": "SKIP", "phys": "METAL_STEEL"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions", icon="FIXED_SIZE")
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")

        layout.separator()
        col.label(text="Structure", icon="MESH_GRID")
        col.prop(self, "segs_x")
        col.prop(self, "strut_thick")
        col.prop(self, "cross_bracing")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        # Ensure Layers exist upfront to prevent pointer invalidation
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")

        l, w, h = self.length, self.width, self.height
        st = self.strut_thick

        # Helper to create a strut between two points
        def create_strut(p1, p2, thick):
            vec = p2 - p1
            dist = vec.length
            if dist < 0.001: return

            mid = (p1 + p2) / 2

            # Align Z axis to vector
            direction = vec.normalized()
            rot_quat = Vector((0,0,1)).rotation_difference(direction)
            rot_mat = rot_quat.to_matrix().to_4x4()

            # Create Box at origin, then transform
            # Box is length 'dist' along Z, width/depth 'thick'
            # create_box creates axis-aligned box at center.
            # Size: (thick, thick, dist)

            # Note: create_box args are (width, depth, height)
            builder.create_box(thick, thick, dist, center=Vector((0,0,0)))

            # Rotate & Translate
            # We apply rotation, then translation to mid

            # We need to manually apply transform to active selection
            # Builder's transform applies to active selection

            # Combined Matrix: T * R
            # Wait, create_box makes it at 0,0,0.
            # So applying Rot then Trans works.

            mat = Matrix.Translation(mid) @ rot_mat
            builder.transform(mat)

            # Tag Slot 0
            builder.tag_slot(0)

            # Tag Edge Roles (Seams on long edges?)
            # Auto-detect handles cylinders well, but boxes have 4 long edges.
            # We can mark all edges as Sharp/Seam (Slot 1) because it's hard surface.
            builder.select_boundary().tag_edge_role(1)

        # 1. Rails (Longitudinal X)
        # 4 Rails at corners
        # (-l/2 to l/2)

        corners = [
            Vector((-w/2, -h/2)), # Bot-Left
            Vector((w/2, -h/2)),  # Bot-Right
            Vector((w/2, h/2)),   # Top-Right
            Vector((-w/2, h/2))   # Top-Left
        ]

        # Rails
        for c in corners:
            p1 = Vector((-l/2, c.x, c.y))
            p2 = Vector((l/2, c.x, c.y))
            create_strut(p1, p2, st)

        # 2. Segments (Rings + Cross)
        segs = self.segs_x
        dx = l / segs

        # Rings at each step (0 to segs)
        for i in range(segs + 1):
            x = -l/2 + i*dx

            # Ring struts: BL->BR, BR->TR, TR->TL, TL->BL
            # 0->1, 1->2, 2->3, 3->0

            vs = [Vector((x, c.x, c.y)) for c in corners]

            create_strut(vs[0], vs[1], st) # Bot
            create_strut(vs[1], vs[2], st) # Right
            create_strut(vs[2], vs[3], st) # Top
            create_strut(vs[3], vs[0], st) # Left

        # Cross Bracing (In between rings)
        if self.cross_bracing:
            for i in range(segs):
                x_start = -l/2 + i*dx
                x_end = -l/2 + (i+1)*dx

                v_start = [Vector((x_start, c.x, c.y)) for c in corners]
                v_end = [Vector((x_end, c.x, c.y)) for c in corners]

                # Faces:
                # Bottom: 0-1
                # Right: 1-2
                # Top: 2-3
                # Left: 3-0

                # Diagonal: Start[0] -> End[1]? Or Cross (X)?
                # "Cross Bracing" implies X.
                # Bot: S0->E1 AND S1->E0

                # Bottom (0-1)
                create_strut(v_start[0], v_end[1], st)
                create_strut(v_start[1], v_end[0], st)

                # Right (1-2)
                create_strut(v_start[1], v_end[2], st)
                create_strut(v_start[2], v_end[1], st)

                # Top (2-3)
                create_strut(v_start[2], v_end[3], st)
                create_strut(v_start[3], v_end[2], st)

                # Left (3-0)
                create_strut(v_start[3], v_end[0], st)
                create_strut(v_start[0], v_end[3], st)

        # 3. Clean
        # builder.clean() # Merges vertices where they meet.
        # With struts, they overlap. Merging might create non-manifold geometry if not careful.
        # "Golden Cartridge" usually prefers clean separate meshes if welding is messy, OR boolean union.
        # Boolean is expensive/unstable.
        # Given "USE_WELD": True in flags, we SHOULD weld.
        # But simply removing doubles on overlapping boxes creates internal faces.
        # Ideally we delete internal faces first?
        # For a "Space Frame", separate overlapping geometry is often acceptable in games/real-time unless physics requires convex hull.
        # The prompt says "Solid volumetric geometry... rather than zero-thickness shells".
        # It does NOT strictly require a single manifold mesh.
        # I will leave them separate for now to ensure clean normals and UVs.
        # Merging intersecting boxes is complex without voxel remesh or boolean.
        
        # 4. Sockets
        # Tag faces at ends.
        # Since we built struts, there are faces at +/- L/2 (Ends of rails).
        # We can tag those.

        builder._update()

        # Left End (-L/2)
        builder.select_faces_by_normal(Vector((-1, 0, 0)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        # Right End (+L/2)
        builder.select_faces_by_normal(Vector((1, 0, 0)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        # 5. Manual UVs
        # Box map everything.
        # Since we used create_box for everything, we can just apply box mapping to all Slot 0 faces.

        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Sockets (Slot 9) usually skipped or basic map
        # tag_uvs applies to active selection.
        # Sockets are separate.
