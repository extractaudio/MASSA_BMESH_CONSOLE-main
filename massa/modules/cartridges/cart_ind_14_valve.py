import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_14: Valve",
    "id": "ind_14_valve",
    "icon": "DRIVER", # Wheel icon
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndValve(Massa_OT_Base):
    bl_idname = "massa.gen_ind_14_valve"
    bl_label = "IND Valve"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("GATE", "Gate Valve", "Vertical lifting gate, large body"),
            ("GLOBE", "Globe Valve", "Spherical body"),
            ("BUTTERFLY", "Butterfly Valve", "Thin wafer body"),
        ],
        default="GATE",
    )

    # Dimensions
    length: FloatProperty(name="Length (X)", default=0.6, min=0.1)
    pipe_radius: FloatProperty(name="Pipe Radius", default=0.15, min=0.05)
    valve_radius: FloatProperty(name="Body Radius", default=0.25, min=0.05)

    # Flanges
    flange_width: FloatProperty(name="Flange Width", default=0.05, min=0.01) # Extra radius
    flange_thick: FloatProperty(name="Flange Thickness", default=0.03, min=0.01)
    bolt_count: IntProperty(name="Bolt Count", default=8, min=0, soft_max=16)

    # Control
    stem_height: FloatProperty(name="Stem Height", default=0.4, min=0.1)
    stem_thick: FloatProperty(name="Stem Thickness", default=0.03, min=0.01)
    handle_radius: FloatProperty(name="Handle Radius", default=0.2, min=0.05)
    handle_thick: FloatProperty(name="Handle Thickness", default=0.03, min=0.01)

    # Topology
    segments: IntProperty(name="Segments", default=16, min=4, soft_max=64)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Body", "uv": "SKIP", "phys": "METAL_IRON"},
            1: {"name": "Trim", "uv": "SKIP", "phys": "METAL_BRASS"}, # Stem/Internal
            2: {"name": "Handle", "uv": "SKIP", "phys": "METAL_PAINTED"}, # Red wheel usually
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style", text="")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Dimensions", icon="FIXED_SIZE")
        col.prop(self, "length")
        col.prop(self, "pipe_radius")
        col.prop(self, "valve_radius")
        col.prop(self, "segments")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Flanges", icon="MOD_SCREW")
        col.prop(self, "flange_width")
        col.prop(self, "flange_thick")
        col.prop(self, "bolt_count")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Control", icon="DRIVER")
        col.prop(self, "stem_height")
        col.prop(self, "stem_thick")
        col.prop(self, "handle_radius")
        col.prop(self, "handle_thick")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")

        l = self.length
        pr = self.pipe_radius
        vr = self.valve_radius
        segs = self.segments
        fw = self.flange_width
        ft = self.flange_thick

        # Axis: X is flow direction. Y/Z are cross section. Stem usually +Z.

        # 1. Main Body
        if self.style == "BUTTERFLY":
            # Thin wafer body
            # Just a cylinder with flanges integrated? Or sandwiched?
            # Wafer style is usually just the body.
            builder.create_cylinder(radius=vr, depth=l, segments=segs, center=Vector((0,0,0)))
            # Rotate to align with X axis (create_cylinder makes Z cylinder)
            builder.rotate(90, axis='Y')
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

        elif self.style == "GLOBE":
            # Spherical center
            # Using sphere or approximation
            # BMesh ops create_icosphere or uv_sphere
            bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs//2, diameter=vr*2)
            # Sphere is created at origin?
            # Need to select it to tag.
            # Usually create_ops returns 'verts'.
            # But MassaBuilder doesn't have create_sphere wrapped yet?
            # Let's create a box for approximation or use create_cylinder for intersection?
            # Or use `bmesh.ops.create_uvsphere` manually and update builder.

            # Since `MassaBuilder` doesn't wrap sphere, let's stick to "Golden Standard" using `MassaBuilder` or `bmesh.ops`.
            ret = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs//2, diameter=vr*2)
            verts = ret['verts']
            builder.active_verts = verts
            builder.bm.verts.ensure_lookup_table()
            builder.active_faces = list(set(f for v in verts for f in v.link_faces))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER') # Sphere map better but cylinder works for bands

            # Add Pipe segments at ends
            # Left Pipe
            builder.create_cylinder(radius=pr, depth=l/2, segments=segs, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y').translate(-l/4, 0, 0).tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')
            # Right Pipe
            builder.create_cylinder(radius=pr, depth=l/2, segments=segs, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y').translate(l/4, 0, 0).tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

        elif self.style == "GATE":
            # Vertical Rectangular/Cylindrical Body housing the gate
            # Central Cylinder (Vertical)
            body_h = vr * 2.5
            builder.create_cylinder(radius=vr, depth=body_h, segments=segs, center=Vector((0,0, vr*0.5)))
            builder.tag_slot(0)

            # Split UVs
            all_f = builder.active_faces[:]
            caps = [f for f in all_f if abs(f.normal.z) > 0.5]
            walls = [f for f in all_f if abs(f.normal.z) <= 0.5]
            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls:
                builder.active_faces = walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            # Horizontal Pipe
            builder.create_cylinder(radius=pr, depth=l, segments=segs, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y').tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

        # 2. Flanges (Ends)
        fr = pr + fw
        # Left Flange
        builder.create_cylinder(radius=fr, depth=ft, segments=segs, center=Vector((0,0,0)))
        builder.rotate(90, axis='Y').translate(-l/2 + ft/2, 0, 0).tag_slot(0)
        # UVs for flange
        # Select Caps (X normal) and Walls (Radial)
        # Rotate makes normals X.
        # So caps are X +/-
        builder.select_faces_by_normal(Vector((-1,0,0)), tolerance=0.5)
        caps = builder.active_faces[:]
        builder.select_faces_by_normal(Vector((1,0,0)), tolerance=0.5)
        caps.extend(builder.active_faces)

        walls = [f for f in builder.bm.faces if f in builder.active_faces] # Wait, select_faces overwrites active.
        # Re-select all faces of last operation?
        # MassaBuilder operations update active_faces to the NEW faces.
        # So right after create & rotate, active_faces are the flange faces.
        all_flange = builder.active_faces[:]

        f_caps = [f for f in all_flange if abs(f.normal.x) > 0.5]
        f_walls = [f for f in all_flange if abs(f.normal.x) <= 0.5]

        if f_caps:
            builder.active_faces = f_caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
        if f_walls:
            builder.active_faces = f_walls
            builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

        # Right Flange
        builder.create_cylinder(radius=fr, depth=ft, segments=segs, center=Vector((0,0,0)))
        builder.rotate(90, axis='Y').translate(l/2 - ft/2, 0, 0).tag_slot(0)

        all_flange = builder.active_faces[:]
        f_caps = [f for f in all_flange if abs(f.normal.x) > 0.5]
        f_walls = [f for f in all_flange if abs(f.normal.x) <= 0.5]
        if f_caps:
            builder.active_faces = f_caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
        if f_walls:
            builder.active_faces = f_walls
            builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

        # Bolts
        if self.bolt_count > 0:
            # Ring of bolts on both flanges
            bolt_r = pr + fw/2
            bolt_rad = 0.02

            for side in [-1, 1]:
                x = side * (l/2 - ft/2) # Centered on flange? or sticking out?
                # Usually through flange. Head on outside.
                x_head = side * (l/2 + 0.01)

                for i in range(self.bolt_count):
                    angle = (i / self.bolt_count) * 2 * math.pi
                    y = math.cos(angle) * bolt_r
                    z = math.sin(angle) * bolt_r

                    # Hex Bolt Head
                    # Create at origin, rotate, then translate
                    builder.create_cylinder(radius=bolt_rad*1.5, depth=bolt_rad, segments=6, center=Vector((0,0,0)))
                    builder.rotate(90, axis='Y').translate(x_head, y, z)
                    builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Stem & Handle
        # Stem starts from top of body
        stem_start_z = vr if self.style != "GATE" else (vr * 1.5) # Gate valve body is taller
        sh = self.stem_height
        st = self.stem_thick

        # Stem
        builder.create_cylinder(radius=st, depth=sh, segments=8, center=Vector((0, 0, stem_start_z + sh/2)))
        builder.tag_slot(1)

        # Split UVs Stem
        all_f = builder.active_faces[:]
        caps = [f for f in all_f if abs(f.normal.z) > 0.5]
        walls = [f for f in all_f if abs(f.normal.z) <= 0.5]
        if caps:
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
        if walls:
            builder.active_faces = walls
            builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        # Handle
        handle_z = stem_start_z + sh
        hr = self.handle_radius
        ht = self.handle_thick

        if self.style == "BUTTERFLY":
            # Lever handle
            builder.create_box(st, hr*2, ht, center=Vector((0, hr/2, handle_z)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
        else:
            # Wheel handle
            # Torus/Ring
            builder.create_cylinder(radius=hr, depth=ht, segments=segs, center=Vector((0, 0, handle_z)))
            builder.tag_slot(2)
            # UV Fix for Handle
            all_h = builder.active_faces[:]
            h_caps = [f for f in all_h if abs(f.normal.z) > 0.5]
            h_walls = [f for f in all_h if abs(f.normal.z) <= 0.5]
            if h_caps:
                builder.active_faces = h_caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if h_walls:
                builder.active_faces = h_walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            # Spokes
            builder.create_box(hr*2, st, ht, center=Vector((0, 0, handle_z)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(st, hr*2, ht, center=Vector((0, 0, handle_z)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 4. Sockets
        # Anchor (Center Bottom?) or Flow In/Out?
        # Usually centered.
        # Let's tag the flange faces as sockets.

        # Left Flange Face (-X)
        builder.select_faces_by_normal(Vector((-1, 0, 0)), tolerance=0.1)
        # Filter by X location?
        # Select faces near -l/2
        faces_neg = [f for f in builder.active_faces if f.calc_center_median().x < -l/2 + 0.1]
        if faces_neg:
            builder.active_faces = faces_neg
            builder.tag_socket(1) # In

        # Right Flange Face (+X)
        builder.select_faces_by_normal(Vector((1, 0, 0)), tolerance=0.1)
        faces_pos = [f for f in builder.active_faces if f.calc_center_median().x > l/2 - 0.1]
        if faces_pos:
            builder.active_faces = faces_pos
            builder.tag_socket(2) # Out

        # Anchor (Center Bottom of body)
        # Find faces pointing down near origin
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.5)
        # Filter near 0,0,0
        faces_anchor = [f for f in builder.active_faces if abs(f.calc_center_median().x) < vr and abs(f.calc_center_median().y) < vr]
        if faces_anchor:
            builder.active_faces = faces_anchor
            builder.tag_socket(9) # Anchor

        # Update normals before selection
        bm.normal_update()

        # FINAL UV FIX: Ensure all horizontal faces (Caps) use BOX to prevent pinching
        # Handle Z normals
        builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.6)
        up_faces = builder.active_faces[:]
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.6)
        down_faces = builder.active_faces[:]

        builder.active_faces = up_faces + down_faces
        builder.tag_uvs(scale=self.uv_scale, projection='BOX')

        # Also X normals (Flange Caps)
        builder.select_faces_by_normal(Vector((1,0,0)), tolerance=0.6)
        x_pos = builder.active_faces[:]
        builder.select_faces_by_normal(Vector((-1,0,0)), tolerance=0.6)
        x_neg = builder.active_faces[:]

        builder.active_faces = x_pos + x_neg
        builder.tag_uvs(scale=self.uv_scale, projection='BOX')

        builder.clean()
