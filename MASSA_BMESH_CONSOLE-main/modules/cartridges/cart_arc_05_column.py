import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARC_05: Arch Column",
    "id": "arc_05_column",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcColumn(Massa_OT_Base):
    bl_idname = "massa.gen_arc_05_column"
    bl_label = "ARC Column"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    total_height: FloatProperty(name="Height", default=4.0, min=0.1)
    radius_base: FloatProperty(name="Base Radius", default=0.4, min=0.1)
    radius_top: FloatProperty(name="Top Radius", default=0.3, min=0.1)
    segments: IntProperty(name="Segments", default=16, min=3)

    # Details
    plinth_height: FloatProperty(name="Plinth H", default=0.3, min=0.0)
    capital_height: FloatProperty(name="Capital H", default=0.4, min=0.0)

    fluted: BoolProperty(name="Fluted Shaft", default=False)
    flute_depth: FloatProperty(name="Flute Depth", default=0.02, min=0.001)

    def get_slot_meta(self):
        return {
            0: {"name": "Stone", "uv": "SKIP", "phys": "STONE"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        # 2. Base Circle
        # Create Circle at Origin
        # Segments must be even for fluting? Usually better if divisible by 2.
        segs = self.segments if self.segments % 2 == 0 else self.segments + 1

        # Create Circle
        ret = bmesh.ops.create_circle(bm, cap_ends=True, radius=self.radius_base, segments=segs)
        base_face = ret['verts'][0].link_faces[0] # The cap face (n-gon)

        # 3. Extrude Plinth
        ph = self.plinth_height
        th = self.total_height
        ch = self.capital_height
        sh = th - ph - ch # Shaft Height

        curr_z = 0

        # Base Plinth Block (Square or Circle? Usually square base for columns)
        # But let's stick to profile extrusion for now.
        # Extrude Up
        ret = bmesh.ops.extrude_face_region(bm, geom=[base_face])
        verts_extruded = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, 0, ph)), verts=verts_extruded)

        # Top face of plinth
        shaft_start_face = [f for f in ret['geom'] if isinstance(f, bmesh.types.BMFace)][0]

        # 4. Extrude Shaft
        # Extrude Up
        ret = bmesh.ops.extrude_face_region(bm, geom=[shaft_start_face])
        verts_extruded = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, 0, sh)), verts=verts_extruded)

        # Taper Shaft?
        # Scale top verts to radius_top / radius_base ratio
        scale_fac = self.radius_top / self.radius_base if self.radius_base > 0 else 1.0
        # Scale around Z-axis center (0,0, current_z)
        # Current Z is ph + sh
        center = Vector((0, 0, ph + sh))
        bmesh.ops.scale(bm, vec=Vector((scale_fac, scale_fac, 1.0)), cent=center, verts=verts_extruded)

        capital_start_face = [f for f in ret['geom'] if isinstance(f, bmesh.types.BMFace)][0]

        # 5. Extrude Capital
        # Extrude Up
        ret = bmesh.ops.extrude_face_region(bm, geom=[capital_start_face])
        verts_extruded = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, 0, ch)), verts=verts_extruded)

        # Scale Capital Top (Usually wider)
        # Let's scale out a bit to match base radius or wider
        scale_fac_cap = (self.radius_base * 1.2) / (self.radius_top) if self.radius_top > 0 else 1.0
        center = Vector((0, 0, th))
        bmesh.ops.scale(bm, vec=Vector((scale_fac_cap, scale_fac_cap, 1.0)), cent=center, verts=verts_extruded)

        # 6. Fluting Logic
        if self.fluted:
            # Select vertical faces of the SHAFT
            # Shaft is between Z=ph and Z=ph+sh
            # Faces whose center Z is roughly ph + sh/2
            shaft_mid_z = ph + sh/2
            shaft_faces = []
            for f in bm.faces:
                cz = f.calc_center_median().z
                # Check if face is vertical (normal Z ~ 0)
                if abs(f.normal.z) < 0.1:
                    # Check Z range
                    if (ph < cz < (ph + sh)):
                        shaft_faces.append(f)

            # Alternate Selection
            # We need to sort them radially to alternate correctly?
            # Or just rely on index order if created sequentially?
            # Create Circle usually orders them.
            # But let's sort by angle to be safe.
            shaft_faces.sort(key=lambda f: math.atan2(f.calc_center_median().y, f.calc_center_median().x))

            faces_to_flute = []
            for i, f in enumerate(shaft_faces):
                if i % 2 == 0:
                    faces_to_flute.append(f)

            # Inset Individual
            # bmesh.ops.inset_individual(bm, faces=faces_to_flute, thickness=0, depth=-self.flute_depth)
            # Inset with depth only (move face in normal direction)
            # Standard inset creates a rim. We want to just push the face in?
            # Or make a groove.
            # Let's use inset_region with depth? No, individual.

            # Inset 0 thickness, negative depth?
            bmesh.ops.inset_individual(bm, faces=faces_to_flute, thickness=0.01, depth=-self.flute_depth)

        # 7. Sockets
        # At Z=0 and Z=Total Height
        # We can mark the bottom and top faces as Socket Anchors if needed.
        # But Mandate asks for Snap points.
        # Let's create specific socket faces or rely on implicit center.

        # 8. Manual UVs
        # Cylinder Mapping
        scale_u = getattr(self, "uv_scale_0", 1.0)
        scale_v = scale_u

        for f in bm.faces:
            n = f.normal
            if abs(n.z) > 0.8:
                # Top/Bottom Caps -> Planar XY
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale_u, l.vert.co.y * scale_u)
            else:
                # Side -> Cylindrical
                for l in f.loops:
                    angle = math.atan2(l.vert.co.y, l.vert.co.x)
                    u = (angle / (2*math.pi)) * self.radius_base * 3.0 # Approximate circumference
                    v = l.vert.co.z
                    l[uv_layer].uv = (u * scale_u, v * scale_v)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "total_height")
        col.prop(self, "radius_base")
        col.prop(self, "radius_top")
        col.prop(self, "segments")
        layout.separator()
        col.prop(self, "plinth_height")
        col.prop(self, "capital_height")
        layout.separator()
        col.prop(self, "fluted")
        if self.fluted:
            col.prop(self, "flute_depth")
