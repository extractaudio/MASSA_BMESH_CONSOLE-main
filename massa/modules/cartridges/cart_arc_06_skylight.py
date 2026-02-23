import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_06: Industrial Skylight",
    "id": "arc_06_skylight",
    "icon": "LIGHT_SUN",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcSkylight(Massa_OT_Base):
    bl_idname = "massa.gen_arc_06_skylight"
    bl_label = "ARC Skylight"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("PYRAMID", "Pyramid / Hip", "Four-sided sloped glass"),
            ("SAWTOOTH", "Sawtooth", "Angled industrial monitor"),
            ("VAULT", "Barrel Vault", "Curved polycarbonate/glass"),
        ],
        default="PYRAMID"
    )

    # Dimensions
    length: FloatProperty(name="Length", default=3.0, min=0.5)
    width: FloatProperty(name="Width", default=2.0, min=0.5)
    height: FloatProperty(name="Apex Height", default=0.8, min=0.1)

    # Curb (Base)
    curb_height: FloatProperty(name="Curb Height", default=0.3, min=0.05)
    curb_thick: FloatProperty(name="Curb Thickness", default=0.15, min=0.05)

    # Frame Details
    frame_width: FloatProperty(name="Frame Width", default=0.08, min=0.01)
    frame_depth: FloatProperty(name="Frame Depth", default=0.05, min=0.01)

    # Glazing Grid
    segments_l: IntProperty(name="Length Segs", default=3, min=1, max=20)
    segments_w: IntProperty(name="Width Segs", default=2, min=1, max=20)

    glass_inset: FloatProperty(name="Glass Inset", default=0.02, min=0.0)

    # Sawtooth Specific
    sawtooth_angle: FloatProperty(name="Angle", default=30.0, min=10.0, max=80.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            1: {"name": "Glass", "uv": "SKIP", "phys": "GLASS_PANE"},
            2: {"name": "Curb", "uv": "BOX", "phys": "CONCRETE"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CUBE')
        col = box.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")

        box = layout.box()
        box.label(text="Base / Curb", icon='MOD_BUILD')
        col = box.column(align=True)
        col.prop(self, "curb_height")
        col.prop(self, "curb_thick")

        box = layout.box()
        box.label(text="Frame & Grid", icon='MESH_GRID')
        col = box.column(align=True)
        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")
        col.prop(self, "segments_l")
        col.prop(self, "segments_w")
        col.prop(self, "glass_inset")

        if self.style == "SAWTOOTH":
             box.prop(self, "sawtooth_angle")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        l, w, h = self.length, self.width, self.height
        ch = self.curb_height
        ct = min(self.curb_thick, min(l, w) * 0.45) # Clamp curb thickness

        # Clamp frame width to avoid self-intersection
        min_dim = min(l, w)
        max_segs = max(self.segments_l, self.segments_w)
        fw = min(self.frame_width, (min_dim / max_segs) * 0.45)

        fd = self.frame_depth

        # 1. Curb (Base)
        builder.create_box(w, l, ch, center=Vector((0,0,ch/2))) \
               .tag_slot(2) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Inset Top Face for Seat
        builder.select_faces_by_normal(Vector((0,0,1))) \
               .inset(ct, relative=False)

        # Select Inner Face (the hole)
        # Inset returns the inner face as active
        # Extrude down slightly to create lip/seat
        builder.extrude(-0.05)

        # Delete the face to open it up?
        # MassaBuilder doesn't have delete.
        if builder.active_faces:
            bmesh.ops.delete(bm, geom=builder.active_faces, context='FACES')
            builder.active_faces = []

        # 2. Skylight Structure
        # It sits on the curb rim.
        # Rim inner dims: w - 2*ct, l - 2*ct.
        # Or outer?
        # Usually frame sits on the curb.
        # Let's generate it at Z=ch based on outer dims w, l, inset by a bit.

        start_z = ch
        base_w = w - ct # Centered on curb wall
        base_l = l - ct

        if self.style == "PYRAMID":
            # Hip Roof Construction

            # Create base footprint
            builder.create_box(base_w, base_l, 0.001, center=Vector((0,0,start_z)))

            # Select Top
            builder.select_faces_by_normal(Vector((0,0,1)))

            # Extrude to Apex
            builder.extrude(h)

            # Form Ridge
            ridge_l = max(0, base_l - base_w) if base_l >= base_w else max(0, base_w - base_l)
            ridge_axis = 'Y' if base_l >= base_w else 'X'

            # Scale Top Face
            if ridge_axis == 'Y':
                sy = ridge_l / base_l if base_l > 0 else 0
                sx = 0.001
                builder.scale(sx, sy, 1.0)
            else:
                sx = ridge_l / base_w if base_w > 0 else 0
                sy = 0.001
                builder.scale(sx, sy, 1.0)

            # Now we have the volume.
            # Select Sloped Faces
            active_faces = [f for f in bm.faces if 0.1 < f.normal.z < 0.99]
            builder.active_faces = active_faces
            builder.tag_slot(0) # Frame default

            # 2.1 Subdivide (Grid)
            # We must refresh geometry lists after cuts

            # X Cuts (Width Segments)
            if self.segments_w > 1:
                step = base_w / self.segments_w
                start = -base_w/2
                for i in range(1, self.segments_w):
                    x = start + i*step
                    bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(x,0,0), plane_no=(1,0,0))

            # Y Cuts (Length Segments)
            if self.segments_l > 1:
                step = base_l / self.segments_l
                start = -base_l/2
                for i in range(1, self.segments_l):
                    y = start + i*step
                    bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(0,y,0), plane_no=(0,1,0))

            # Re-select sloped faces
            bm.faces.ensure_lookup_table()
            sloped_faces = [f for f in bm.faces if 0.1 < f.normal.z < 0.99]

            # 2.2 Inset for Frames
            if sloped_faces:
                # Use depth to move glass in
                res = bmesh.ops.inset_individual(bm, faces=sloped_faces, thickness=fw/2, depth=-self.glass_inset)
                glass_faces = res['faces']

                # Tag Glass
                for f in glass_faces:
                    f.material_index = 1
                    builder.active_faces = [f]
                    builder.tag_uvs(scale=1.0, projection='FIT')

            # Frame UVs
            frame_faces = [f for f in sloped_faces if f.material_index == 0]
            builder.active_faces = frame_faces
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "VAULT":
             # Barrel Vault
             radius = base_w / 2.0
             # Cap ends if L > W

             # Create Cylinder (Horizontal)
             # Default create_cylinder is Z aligned.
             # We create it, rotate Y 90 (to align with X axis) -> Length along X?
             # User Params: Length is Y usually.
             # So we want Cylinder aligned Y. Rotate X 90.

             builder.create_cylinder(radius=radius, depth=base_l, segments=16, center=Vector((0,0,0)))
             builder.rotate(90, axis='X')
             builder.translate(0, 0, start_z)

             # Cut bottom half
             # Select faces with normal Z < -0.1
             builder.select_faces_by_normal(Vector((0,0,-1)))
             if builder.active_faces:
                 bmesh.ops.delete(bm, geom=builder.active_faces, context='FACES')
                 builder.active_faces = []

             # Scale Height if needed
             if radius > 0:
                 builder.scale(1.0, 1.0, h/radius)

             # Grid Cuts
             if self.segments_l > 1:
                  step = base_l / self.segments_l
                  start = -base_l/2
                  for i in range(1, self.segments_l):
                      y = start + i*step
                      bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:], plane_co=(0,y,0), plane_no=(0,1,0))

             # Select Curved Faces (Not Caps)
             # Caps have normal +/- Y
             bm.faces.ensure_lookup_table()
             curved_faces = [f for f in bm.faces if abs(f.normal.y) < 0.9]

             # Tag Frame
             for f in curved_faces: f.material_index = 0

             # Inset
             if curved_faces:
                 # Use depth
                 res = bmesh.ops.inset_individual(bm, faces=curved_faces, thickness=fw/2, depth=-self.glass_inset)
                 glass_faces = res['faces']

                 for f in glass_faces:
                     f.material_index = 1
                     builder.active_faces = [f]
                     builder.tag_uvs(scale=1.0, projection='FIT')

             # Frame UVs
             frame_faces = [f for f in curved_faces if f.material_index == 0]
             builder.active_faces = frame_faces
             builder.tag_uvs(scale=self.uv_scale, projection='BOX')

             # Caps
             caps = [f for f in bm.faces if abs(f.normal.y) >= 0.9]
             for f in caps:
                 f.material_index = 0 # Metal ends
                 builder.active_faces = [f]
                 builder.tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "SAWTOOTH":
             # Wedge shape

             # Create wedge
             builder.create_box(base_w, base_l, h, center=Vector((0,0,start_z + h/2)))

             # Cut Slope
             # Keep X- (Vertical) as glass?
             # Plane normal: Vector(h, 0, base_w) cuts off X+ top corner.
             # Point on plane: (base_w/2, 0, start_z) (bottom right) and (-base_w/2, 0, start_z+h) (top left)
             # Actually, simpler:
             # Just create box, select Top, move vertices?
             # Or collapse edge?

             # Let's use vertex manipulation for Sawtooth, it's reliable.
             # Select verts at X+ Top
             # X > 0, Z > start_z + h/2

             # Find verts
             targets = [v for v in bm.verts if v.co.x > 0 and v.co.z > start_z + h*0.4]
             for v in targets:
                 v.co.z = start_z # Drop them to base height

             builder.clean()

             # Now we have a wedge.
             # Vertical Face (X-) is the monitor.
             builder.select_faces_by_normal(Vector((-1, 0, 0)), tolerance=0.5)
             glass_wall = builder.active_faces

             # Grid on Glass Wall
             # Segments W (vertical cuts)
             # Segments L (horizontal cuts?) No, Segments L is length (Y).

             if self.segments_l > 1:
                 # Y cuts
                 step = base_l / self.segments_l
                 start = -base_l/2
                 for i in range(1, self.segments_l):
                     y = start + i*step
                     bmesh.ops.bisect_plane(bm, geom=glass_wall, plane_co=(0,y,0), plane_no=(0,1,0))
                     # Note: glass_wall list might be stale if bisect splits it?
                     # Re-select
                     builder.select_faces_by_normal(Vector((-1, 0, 0)), tolerance=0.5)
                     glass_wall = builder.active_faces

             # Inset
             if glass_wall:
                 # Tag Frame First
                 for f in glass_wall: f.material_index = 0

                 res = bmesh.ops.inset_individual(bm, faces=glass_wall, thickness=fw, depth=-self.glass_inset)
                 inner = res['faces']

                 for f in inner:
                     f.material_index = 1
                     builder.active_faces = [f]
                     builder.tag_uvs(scale=1.0, projection='FIT')

             # Roof Face
             # Normal has +X and +Z component
             # Tag as Curb (2) or Frame (0)? Usually roofing. Slot 0 (Frame/Metal) is fine.
             builder.select_faces_by_normal(Vector((1, 0, 1)), tolerance=0.5)
             builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

             # Sides (Y+, Y-)
             builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.5)
             builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
             builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.5)
             builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Finalize
        builder.select_all_faces()
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)

        # Socket 9
        # Bottom of curb
        builder.select_faces_by_normal(Vector((0,0,-1)))
        builder.tag_socket(9)

    def execute(self, context):
        return super().execute(context)
