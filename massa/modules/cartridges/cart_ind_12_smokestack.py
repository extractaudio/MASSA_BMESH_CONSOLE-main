import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_12: Smokestack",
    "id": "ind_12_smokestack",
    "icon": "MOD_FLUID", # Closest to smoke/fluid
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": True, # Walls can be solidified
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndSmokestack(Massa_OT_Base):
    bl_idname = "massa.gen_ind_12_smokestack"
    bl_label = "IND Smokestack"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("BRICK", "Brick Chimney", "Classic industrial brick stack"),
            ("STEEL", "Steel Stack", "Modern metal exhaust"),
            ("REINFORCED", "Reinforced Concrete", "Heavy duty concrete stack"),
        ],
        default="BRICK",
    )

    # Dimensions
    height: FloatProperty(name="Height (Z)", default=10.0, min=2.0)
    radius_base: FloatProperty(name="Base Radius", default=1.5, min=0.5)
    radius_top: FloatProperty(name="Top Radius", default=1.0, min=0.2)
    wall_thick: FloatProperty(name="Wall Thickness", default=0.2, min=0.05)

    # Topology
    segments: IntProperty(name="Segments", default=16, min=4, soft_max=64)

    # Details
    rings_count: IntProperty(name="Rings Count", default=3, min=0)
    ring_width: FloatProperty(name="Ring Width", default=0.2, min=0.05)
    ring_thick: FloatProperty(name="Ring Thickness", default=0.1, min=0.01)

    has_ladder: BoolProperty(name="Ladder", default=True)
    has_platform: BoolProperty(name="Platform", default=False)
    platform_height: FloatProperty(name="Platform Height", default=0.7, min=0.1, max=0.9, description="Normalized height (0-1)")

    # Vent Cap
    cap_style: EnumProperty(
        name="Cap Style",
        items=[
            ("NONE", "None", ""),
            ("RIM", "Reinforced Rim", ""),
            ("CONE", "Conical Hood", ""),
        ],
        default="RIM",
    )

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        base_mat = "STONE_BRICK" if self.style == "BRICK" else ("CONCRETE_RAW" if self.style == "REINFORCED" else "METAL_RUST")
        return {
            0: {"name": "Wall", "uv": "SKIP", "phys": base_mat},
            1: {"name": "Details", "uv": "SKIP", "phys": "METAL_IRON"},
            2: {"name": "Interior", "uv": "SKIP", "phys": "MUD_DRY"}, # Soot
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style", text="")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Dimensions", icon="FIXED_SIZE")
        col.prop(self, "height")
        col.prop(self, "radius_base")
        col.prop(self, "radius_top")
        col.prop(self, "wall_thick")
        col.prop(self, "segments")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Details", icon="MOD_BUILD")
        col.prop(self, "rings_count")
        if self.rings_count > 0:
            col.prop(self, "ring_width")
            col.prop(self, "ring_thick")

        col.separator()
        col.prop(self, "has_ladder")
        col.prop(self, "has_platform")
        if self.has_platform:
            col.prop(self, "platform_height")

        layout.separator()
        layout.prop(self, "cap_style")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")

        h = self.height
        rb = self.radius_base
        rt = self.radius_top
        segs = self.segments
        wt = self.wall_thick

        # 1. Main Stack (Outer)
        # Create Cone (Hollow manually or create solid and inset/bridge?)
        # Let's create outer shell, select top/bottom, bridge?
        # Or create cylinder, inset top/bottom, bridge.

        # Create Outer Cone
        builder.create_cone(radius_bottom=rb, radius_top=rt, depth=h, segments=segs, cap_ends=True, center=Vector((0,0,h/2)))

        # Tag Outer Walls
        # Select by normal (horizontal-ish)
        # Top/Bottom caps are vertical normals (0,0,1), (0,0,-1)
        # Everything else is wall.

        # Select Caps
        caps = []
        builder.select_faces_by_normal(Vector((0,0,1))) # Top
        caps.extend(builder.active_faces)
        builder.select_faces_by_normal(Vector((0,0,-1))) # Bottom
        caps.extend(builder.active_faces)

        # Invert selection manually or just tag everything first?
        # Let's tag all as 0 (Wall)
        builder.select_all_faces().tag_slot(0)

        # Tag Vertical Seam (Edge Slot 3) for UV
        # Find edges close to X+
        builder.select_all_faces()
        for f in builder.active_faces:
            for e in f.edges:
                # Vertical edges check
                v1, v2 = e.verts
                if abs(v1.co.z - v2.co.z) > 0.1: # It's vertical
                    # Check angle (atan2)
                    angle = math.atan2(v1.co.y, v1.co.x)
                    if abs(angle) < 0.1: # Close to X axis (angle 0)
                        builder.active_edges = [e]
                        builder.tag_edge_role(3) # Guide

        # Apply Cylindrical UV to Walls
        # Filter out caps
        walls = [f for f in bm.faces if f not in caps]
        builder.active_faces = walls
        builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        # Caps UV
        builder.active_faces = caps
        builder.tag_uvs(scale=self.uv_scale, projection='BOX') # Or PLANAR

        # 2. Hollow Interior
        # Inset Top Cap
        builder.select_faces_by_normal(Vector((0,0,1)))
        # Inset amount depends on radius at top
        # Using wall thickness
        # Inset distance on a circle reduces radius by approx distance.
        builder.inset(wt)

        # The inset creates a new inner face (the hole) and a ring face (the rim).
        # We want to bridge the inner face to the bottom?
        # Actually, bridge requires two loops.
        # Let's inset Bottom Cap too.

        top_hole = builder.active_faces

        builder.select_faces_by_normal(Vector((0,0,-1)))
        builder.inset(wt)
        bottom_hole = builder.active_faces

        # Delete the hole faces? Or Bridge them to create inner wall.
        # Bridge loops of top_hole and bottom_hole.
        # But we need to select faces to delete them? Or just use bridge on faces (which replaces them with tube)

        # Bridge Selection needs faces or edges.
        # If we select top_hole and bottom_hole faces and bridge, it should create a tunnel.
        if top_hole and bottom_hole:
            builder.active_faces = top_hole + bottom_hole
            builder.bridge_selection()
            # The bridge creates inner walls.
            # Tag inner walls as Slot 2 (Interior)
            builder.tag_slot(2)
            # UV Inner Walls
            builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        # 3. Details: Rings
        if self.rings_count > 0:
            dz = h / (self.rings_count + 1)
            for i in range(1, self.rings_count + 1):
                z = i * dz
                # Calculate radius at height Z
                # Linear interpolation
                t = z / h
                r = rb * (1-t) + rt * t

                # Create Ring (Torus-ish)
                # Cylinder with hole? Or just a band.
                # Band: Cylinder slightly larger than r
                ring_r = r + self.ring_thick
                # Height of ring
                rh = self.ring_width

                builder.create_cylinder(radius=ring_r, depth=rh, segments=segs, center=Vector((0,0,z)))
                # Remove caps to make it a band? Or keep solid?
                # Solid is better for "Golden Standard".
                # But we need hole in middle to fit stack.
                # Inset and bridge?
                # Or just let it intersect (simple).
                # Intersecting is cleaner for UVs usually.
                builder.tag_slot(1)

                # Split UVs for Rings
                all_faces = builder.active_faces[:]
                caps = [f for f in all_faces if abs(f.normal.z) > 0.5]
                walls = [f for f in all_faces if abs(f.normal.z) <= 0.5]

                if caps:
                    builder.active_faces = caps
                    builder.tag_uvs(scale=self.uv_scale, projection='BOX')
                if walls:
                    builder.active_faces = walls
                    builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        # 4. Platform
        if self.has_platform:
            z = h * self.platform_height
            t = z / h
            r = rb * (1-t) + rt * t

            plat_r = r + 1.5 # 1.5m wide platform
            plat_h = 0.2

            # Platform Floor
            builder.create_cylinder(radius=plat_r, depth=plat_h, segments=segs, center=Vector((0,0,z)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Railing? (Simplified as a ring for now)
            rail_h = 1.0
            rail_r = plat_r - 0.1
            rail_th = 0.05

            # Top Rail
            builder.create_cylinder(radius=rail_r, depth=rail_th, segments=segs, cap_ends=False, center=Vector((0,0,z+rail_h)))
            # Solidify/Thicken?
            # Creating a tube is complex without `create_tube`.
            # Let's skip railing details for macro scale, or use `create_cone` with small difference.
            pass

        # 5. Ladder
        if self.has_ladder:
            # Vertical rails
            lad_w = 0.5
            lad_d = 0.1 # Distance from wall
            lad_h = h * 0.9

            # Position: X+
            # Calculate X at base and top
            # Ladder usually vertical, so it pulls away from tapered stack.
            # Or follows slope?
            # Vertical is easier.
            # Base Radius + lad_d
            lad_x = rb + lad_d

            # Left Rail
            builder.create_box(0.05, 0.05, lad_h, center=Vector((lad_x, -lad_w/2, lad_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right Rail
            builder.create_box(0.05, 0.05, lad_h, center=Vector((lad_x, lad_w/2, lad_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Rungs
            rungs = int(lad_h / 0.4)
            for i in range(rungs):
                rz = i * 0.4
                builder.create_box(0.05, lad_w, 0.05, center=Vector((lad_x, 0, rz)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 6. Cap Style
        if self.cap_style == "RIM":
            # Thick rim at top
            builder.create_cylinder(radius=rt + 0.2, depth=0.4, segments=segs, center=Vector((0,0,h)))
            builder.tag_slot(1)

            # Split UVs
            all_faces = builder.active_faces[:]
            caps = [f for f in all_faces if abs(f.normal.z) > 0.5]
            walls = [f for f in all_faces if abs(f.normal.z) <= 0.5]

            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls:
                builder.active_faces = walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        elif self.cap_style == "CONE":
            # Cone hood
            # Supported by struts
            hood_z = h + 1.0
            builder.create_cone(radius_bottom=rt*1.5, radius_top=0, depth=1.0, segments=segs, center=Vector((0,0,hood_z)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            # Struts
            for i in range(4):
                angle = i * (math.pi/2)
                x = math.cos(angle) * rt
                y = math.sin(angle) * rt
                builder.create_box(0.1, 0.1, 1.0, center=Vector((x, y, h + 0.5)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 7. Socket Anchor
        # Bottom Face
        # We need to find the bottom ring face (since we bridged hole)
        # It's at Z=0, normal -Z.
        builder.select_faces_by_normal(Vector((0,0,-1))).tag_socket(9)

        # Top Socket (Exhaust)
        builder.select_faces_by_normal(Vector((0,0,1))).tag_socket(0) # 0 = Emission/Output

        # FINAL UV FIX: Ensure all horizontal faces use BOX to prevent pinching
        builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.6) # Select Up faces
        up_faces = builder.active_faces[:]
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.6) # Select Down faces
        down_faces = builder.active_faces[:]

        builder.active_faces = up_faces + down_faces
        builder.tag_uvs(scale=self.uv_scale, projection='BOX')

        builder.clean()
