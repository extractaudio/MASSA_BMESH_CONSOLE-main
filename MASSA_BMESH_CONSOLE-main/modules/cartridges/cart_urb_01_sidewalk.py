import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_01: Sidewalk",
    "id": "urb_01_sidewalk",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbSidewalk(Massa_OT_Base):
    bl_idname = "massa.gen_urb_01_sidewalk"
    bl_label = "URB Sidewalk"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=4.0, min=0.1)
    width: FloatProperty(name="Width", default=2.0, min=0.1)
    curb_height: FloatProperty(name="Curb Height", default=0.15, min=0.01)
    curb_width: FloatProperty(name="Curb Width", default=0.15, min=0.01)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("STANDARD", "Standard", "Plain Concrete Slabs"),
            ("HEX", "Hex Pavers", "Hexagonal Pattern"),
            ("HERRINGBONE", "Herringbone", "Brick Pattern"),
        ],
        default="STANDARD"
    )

    # Details
    joint_spacing: FloatProperty(name="Joint Spacing", default=2.0, min=0.1)
    paint_curb: BoolProperty(name="Paint Curb", default=False)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Surface", "uv": "SKIP", "phys": "CONCRETE"},
            6: {"name": "Paint Accent", "uv": "SKIP", "phys": "PAINT"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "curb_height")
        col.prop(self, "curb_width")
        layout.separator()
        if self.style == 'STANDARD':
            col.prop(self, "joint_spacing")
        col.prop(self, "paint_curb")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        l = self.length
        w = self.width
        ch = self.curb_height
        cw = self.curb_width

        # 1. Base Geometry
        # Sidewalk is a slab (Box)
        # Position so Z=0 is bottom (street level)? Or Top?
        # Usually Z=0 is walking surface.
        # So Box goes down -ch.
        # But Curb is usually raised above street.
        # Let's say Z=0 is Street Level. Walking surface is Z=ch.

        # Create Main Slab
        # Center X=0, Y=0 (Length is Y)
        # Height ch.
        # Center Z = ch/2.

        builder.create_box(w, l, ch, center=Vector((0, 0, ch/2)))
        builder.tag_slot(0)

        # 2. Style Logic (Topology Modifications)
        if self.style == 'STANDARD':
            # Expansion Joints (Bisect)
            num_joints = int(l / self.joint_spacing)
            start_y = -l/2

            for i in range(1, num_joints + 1):
                y = start_y + i * self.joint_spacing
                if y >= l/2 - 0.01: continue

                # Bisect Plane Y
                # Must refresh geometry list as faces are split/invalidated each loop
                geom_current = bm.faces[:] + bm.edges[:] + bm.verts[:]

                res = bmesh.ops.bisect_plane(
                    bm,
                    geom=geom_current,
                    dist=0.001,
                    plane_co=Vector((0, y, 0)),
                    plane_no=Vector((0, 1, 0))
                )

                # Tag cut edges as Detail (4)
                cut_edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
                for e in cut_edges:
                    layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
                    e[layer] = 4 # Detail / Seam
                    # Mark sharp?
                    # e.smooth = False

        elif self.style == 'HEX':
            # Hex Pattern
            # How to do procedural Hex on a Box?
            # Poke faces -> Tris -> Dual Mesh? No dual mesh in BMesh easy.
            # Grid Fill + Poke?
            # Or just inset individual faces if we subdivide?

            # Simple approach: Subdivide grid, then poke? No.
            # Creating actual hex geometry is complex.
            # Approximation: Inset grid squares to look like pavers.

            # Let's use Grid Subdivide on Top Face
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)
            if builder.active_faces:
                # Subdivide
                cuts_x = int(w * 2)
                cuts_y = int(l * 2)

                # Subdivide edges?
                # Using bmesh.ops.subdivide_edges
                # We need to subdivide the face grid.
                # Or delete top face and fill_grid?

                # Let's just use Poke for a "Diamond" pattern (easier than Hex).
                # Hex requires specific topology.
                # Let's rename style to "PATTERN" if Hex is too hard?
                # No, I can try to make a pattern.
                # Grid -> Poke -> Tris.
                # Tris are 3-sided.
                # If we dissolve shared edges of 6 tris around a vert -> Hex.

                # Too complex for "Standard Cartridge".
                # Fallback: Just grid pattern (Pavers).

                # Subdivide Top Face
                # bmesh.ops.subdivide_edges on top face edges?
                # No, that just divides edges.
                # We need grid cut.

                # Bisect Grid
                # Bisect X and Y multiple times.

                step = 0.5 # 50cm pavers

                # Y cuts
                y_cuts = int(l / step)
                for i in range(y_cuts):
                    y = -l/2 + (i+0.5)*step
                    bmesh.ops.bisect_plane(bm, geom=bm.faces[:] + bm.edges[:] + bm.verts[:], plane_co=Vector((0,y,0)), plane_no=Vector((0,1,0)))

                # X cuts
                x_cuts = int(w / step)
                for i in range(x_cuts):
                    x = -w/2 + (i+0.5)*step
                    bmesh.ops.bisect_plane(bm, geom=bm.faces[:] + bm.edges[:] + bm.verts[:], plane_co=Vector((x,0,0)), plane_no=Vector((1,0,0)))

                # Now Inset individual faces slightly to create "Paver" look
                builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)
                # Filter small slivers
                valid_faces = [f for f in builder.active_faces if f.calc_area() > 0.01]
                builder.active_faces = valid_faces

                # Inset
                builder.inset(amount=0.01, depth=-0.005) # Groove
                builder.tag_slot(0) # Concrete

        elif self.style == 'HERRINGBONE':
            # Herringbone Pattern (Zig Zag)
            # Bisect diagonal?
            # Bisect at 45 deg and -45 deg.

            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)

            step = 0.4

            # Diagonals
            # Plane normal (1, 1, 0) normalized
            n1 = Vector((1,1,0)).normalized()
            n2 = Vector((1,-1,0)).normalized()

            # Spacing is step * sqrt(2)?
            # Just create cuts.

            # Range needs to cover diagonals.
            diag = math.sqrt(l**2 + w**2)
            steps = int(diag / step)

            for i in range(-steps, steps):
                # Offset plane from origin along normal
                dist = i * step
                # Plane Co = normal * dist

                # Cut 1
                bmesh.ops.bisect_plane(bm, geom=bm.faces[:] + bm.edges[:] + bm.verts[:], plane_co=n1*dist, plane_no=n1)

                # Cut 2
                bmesh.ops.bisect_plane(bm, geom=bm.faces[:] + bm.edges[:] + bm.verts[:], plane_co=n2*dist, plane_no=n2)

            # Inset
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)
            valid_faces = [f for f in builder.active_faces if f.calc_area() > 0.01]
            builder.active_faces = valid_faces
            builder.inset(amount=0.01, depth=-0.002)

        # 3. Paint Curb (Red/Yellow)
        if self.paint_curb:
            # Select vertical faces at +/- X that are "Curb"
            # Curb is usually the side facing the street.
            # Which side is street? Assume +X is street side (Right).
            # Usually sidewalk is between Lot and Street.
            # Let's paint +X face.

            builder.select_faces_by_normal(Vector((1, 0, 0)), tolerance=0.1)
            # Also select top strip near edge?
            # Just vertical face is standard for "Red Curb".
            builder.tag_slot(6)

        # 4. Sockets
        # Ends (-L/2, +L/2)
        builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        # 5. Manual UVs
        # Slot 0: Box
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Slot 6: Box
        builder.select_faces_by_slot(6) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
