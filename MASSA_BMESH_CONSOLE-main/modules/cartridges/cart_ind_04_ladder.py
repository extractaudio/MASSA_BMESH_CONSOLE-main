import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "IND_04: Ladder",
    "id": "ind_04_ladder",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndLadder(Massa_OT_Base):
    bl_idname = "massa.gen_ind_04_ladder"
    bl_label = "IND Ladder"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    height: FloatProperty(name="Height", default=4.0, min=0.1)
    width: FloatProperty(name="Width", default=0.5, min=0.1)
    rail_thick: FloatProperty(name="Rail Thick", default=0.03, min=0.01)
    rung_spacing: FloatProperty(name="Rung Spacing", default=0.3, min=0.1)
    rung_radius: FloatProperty(name="Rung Radius", default=0.015, min=0.005)

    # Cage
    has_cage: BoolProperty(name="Safety Cage", default=True)
    cage_start_height: FloatProperty(name="Cage Start H", default=2.2, min=0.0)
    cage_radius: FloatProperty(name="Cage Radius", default=0.4, min=0.1)
    cage_strips: IntProperty(name="Cage Strips", default=5, min=3)

    def get_slot_meta(self):
        return {
            0: {"name": "Metal", "uv": "BOX", "phys": "METAL_STEEL"},
            6: {"name": "Warning Paint", "uv": "BOX", "phys": "PAINT"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        # 2. Rails (Vertical)
        # Create Two Cubes/Cylinders
        w = self.width
        h = self.height
        rt = self.rail_thick

        # Left Rail
        res_L = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((rt, rt, h)), verts=res_L['verts'])
        bmesh.ops.translate(bm, vec=Vector((-w/2, 0, h/2)), verts=res_L['verts'])

        # Right Rail
        res_R = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((rt, rt, h)), verts=res_R['verts'])
        bmesh.ops.translate(bm, vec=Vector((w/2, 0, h/2)), verts=res_R['verts'])

        # 3. Rungs (Horizontal)
        num_rungs = int(h / self.rung_spacing)
        for i in range(num_rungs):
            z = (i + 0.5) * self.rung_spacing
            if z > h: break

            # Create Cylinder Rung
            # Using create_cube for low poly industrial look? Or cylinder.
            # Cylinder is better.
            res_rung = bmesh.ops.create_cube(bm, size=1.0) # Simple box rung
            # Scale: (w, rr, rr)
            rr = self.rung_radius * 2 # diameter
            bmesh.ops.scale(bm, vec=Vector((w, rr, rr)), verts=res_rung['verts'])
            bmesh.ops.translate(bm, vec=Vector((0, 0, z)), verts=res_rung['verts'])

        # 4. Safety Cage
        if self.has_cage and h > self.cage_start_height:
            # Generate Hoops
            hoop_spacing = 1.0 # Every meter?
            start_z = self.cage_start_height

            # Cage starts at start_z and goes up to h
            current_z = start_z
            hoops = []

            while current_z <= h:
                # Create Hoop
                # Half Circle or 3/4 Circle attached to rails?
                # Usually attached to rails at back.
                # Center is (0, -cage_radius, current_z) relative to ladder face (Y=0)?
                # Ladder is at Y=0. User climbs on -Y side? Or +Y side?
                # Usually ladder stands off wall. Assume wall at +Y. User climbs on -Y side.
                # Cage encloses user on -Y side.

                # Arc from Rail L to Rail R via -Y.

                # Create Circle
                res_hoop = bmesh.ops.create_circle(bm, cap_ends=False, radius=self.cage_radius, segments=12)
                # Rotate 90 X? Circle is XY. Correct.
                # Cut circle to be an arc?
                # Let's keep full circle for now or simplify.

                # Usually cage is U-shape.
                # Let's use `spin` or manual verts.

                # Verts for Hoop:
                # 5 points in semi-circle + connection to rails.

                # Easier: Create Cylinder (Thin Strip) bent into U shape.
                # Or Torus segment.

                # Placeholder: Create Ring
                # Scale Z to make flat strip
                # Position at z

                # Let's use simple approach: A few torus segments? No too heavy.

                # Build vertices manually for the hoop profile.
                vs = []
                steps = 7 # Half circle
                for s in range(steps + 1):
                    angle = math.pi + (s / steps) * math.pi # 180 to 360 (Back side)?
                    # We want front side (negative Y).
                    # Angle 0 is +X. Angle 90 is +Y. Angle 180 is -X. Angle 270 is -Y.
                    # Rails are at -w/2 (Left) and w/2 (Right).
                    # Left is -X. Right is +X.
                    # We want arc from Left to Right via Front (-Y).
                    # So angle from 180 to 360 (0).

                    a = math.pi + (s / steps) * math.pi
                    x = math.cos(a) * self.cage_radius
                    y = math.sin(a) * self.cage_radius

                    # Offset to align with rails?
                    # Rails are at +/- w/2.
                    # If cage radius > w/2, we need to bridge.

                    # Assume center of cage arc is (0,0).
                    v = bm.verts.new(Vector((x, y, current_z)))
                    vs.append(v)

                # Connect
                for k in range(len(vs)-1):
                    e = bm.edges.new((vs[k], vs[k+1]))
                    # Make thick?

                # Extrude edges to make strip
                res_ext = bmesh.ops.extrude_edge_only(bm, edges=[e for v in vs for e in v.link_edges])
                # Translate up slightly to give thickness
                verts_up = [e for e in res_ext['geom'] if isinstance(e, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, vec=Vector((0, 0, 0.05)), verts=verts_up)

                # Assign Material 6 (Warning Paint)
                for f in res_ext['geom']:
                    if isinstance(f, bmesh.types.BMFace):
                        f.material_index = 6

                current_z += hoop_spacing

            # Vertical Strips connecting hoops
            # Add vertical lines at intervals along the arc.
            pass

        # 5. Sockets
        # Top and Bottom of Rails

        # 6. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)
        for f in bm.faces:
            n = f.normal
            mat_idx = f.material_index

            # Box map everything
            if abs(n.x) > 0.5:
                l_uv = lambda v: (v.y, v.z)
            elif abs(n.y) > 0.5:
                l_uv = lambda v: (v.x, v.z)
            else:
                l_uv = lambda v: (v.x, v.y)

            for l in f.loops:
                u, v = l_uv(l.vert.co)
                l[uv_layer].uv = (u * scale, v * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "height")
        col.prop(self, "width")
        col.prop(self, "rail_thick")
        col.prop(self, "rung_spacing")
        layout.separator()
        col.prop(self, "has_cage")
        if self.has_cage:
            col.prop(self, "cage_start_height")
            col.prop(self, "cage_radius")
