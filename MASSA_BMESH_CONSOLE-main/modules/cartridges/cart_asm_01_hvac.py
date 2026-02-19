import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_01: HVAC Rooftop Unit",
    "id": "asm_01_hvac",
    "icon": "MOD_FLUID",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmHVAC(Massa_OT_Base):
    bl_idname = "massa.gen_asm_01_hvac"
    bl_label = "ASM_01: HVAC Chiller"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=2.0, min=0.5)
    length: FloatProperty(name="Length (Y)", default=3.0, min=0.5)
    height: FloatProperty(name="Height (Z)", default=1.5, min=0.5)

    vent_count: IntProperty(name="Vent Rows", default=5, min=1)
    fan_count: IntProperty(name="Fan Blades", default=8, min=3)

    socket_flange_size: FloatProperty(name="Flange Size", default=0.4, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Chassis", "uv": "SKIP", "phys": "METAL_PAINTED"},
            1: {"name": "Fan Blades", "uv": "SKIP", "phys": "MECHANICAL"},
            2: {"name": "Vents", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            3: {"name": "Flanges", "uv": "SKIP", "phys": "METAL_IRON", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "length")
        col.prop(self, "height")

        layout.separator()
        layout.label(text="DETAILS", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "vent_count")
        col.prop(self, "fan_count")
        col.prop(self, "socket_flange_size")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, l, h = self.width, self.length, self.height

        # 1. Main Chassis Box
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, l, h), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, h/2), verts=bm.verts)

        # Assign Slot 0 (Chassis)
        for f in bm.faces:
            f.material_index = 0

        # 2. Vents on Sides
        # Bisect horizontally
        if self.vent_count > 0:
            step = h / (self.vent_count + 2)
            for i in range(1, self.vent_count + 1):
                z_cut = i * step + (h * 0.1)
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    dist=0.0001,
                    plane_co=(0, 0, z_cut),
                    plane_no=(0, 0, 1),
                    use_snap_center=False,
                    clear_outer=False,
                    clear_inner=False
                )

        # Identify and rotate vent faces
        bm.faces.ensure_lookup_table()

        # Group side faces by Z level
        faces_by_z = {}
        for f in bm.faces:
            # Check if side face (Normal perpendicular to Z)
            if abs(f.normal.z) < 0.1:
                z = f.calc_center_median().z
                z_key = round(z * 10)
                if z_key not in faces_by_z:
                    faces_by_z[z_key] = []
                faces_by_z[z_key].append(f)

        sorted_z_keys = sorted(faces_by_z.keys())

        # Alternate rings
        for i, z_key in enumerate(sorted_z_keys):
            # Skip top and bottom most rings to keep frame solid
            if i == 0 or i == len(sorted_z_keys) - 1:
                continue

            if i % 2 == 1:
                faces = faces_by_z[z_key]
                for f in faces:
                    f.material_index = 2 # Vent

                    center = f.calc_center_median()
                    normal = f.normal
                    # Tangent vector for rotation (horizontal)
                    tangent = Vector((-normal.y, normal.x, 0))

                    rot_mat = Matrix.Rotation(math.radians(-25), 4, tangent)

                    bmesh.ops.rotate(
                        bm,
                        verts=f.verts,
                        cent=center,
                        matrix=rot_mat
                    )

        # 3. Top Fan
        bm.faces.ensure_lookup_table()
        top_face = None
        # Find the highest face
        highest_z = -1
        for f in bm.faces:
             if f.normal.z > 0.9:
                 cz = f.calc_center_median().z
                 if cz > highest_z:
                     highest_z = cz
                     top_face = f

        if top_face:
            # Inset
            res = bmesh.ops.inset_individual(bm, faces=[top_face], thickness=min(w,l)*0.1, depth=0.0)
            center_face = res['faces'][0]

            # Delete center face to make hole
            bmesh.ops.delete(bm, geom=[center_face], context='FACES_ONLY')

            # Create circle for Fan Housing
            circle_r = min(w, l) * 0.35
            circle_z = h

            ret = bmesh.ops.create_circle(
                bm,
                cap_ends=False,
                radius=circle_r,
                segments=32,
                matrix=Matrix.Translation((0, 0, circle_z))
            )
            circle_edges = ret['verts'][0].link_edges # Get edges from verts
            # Actually create_circle returns 'verts' list.
            circle_verts = ret['verts']

            # Bridge hole to circle
            # Identify boundary edges of the hole (inner loop of inset)
            bm.edges.ensure_lookup_table()
            # The hole edges are boundary edges at approx height h
            hole_edges = [e for e in bm.edges if e.is_boundary and e.calc_center_median().z > h - 0.1]

            # Filter hole edges to exclude the outer rim of the box
            # The hole edges are connected to the inset rim faces.
            # Whatever, let's try bridging all boundary edges near top.
            # But we have the outer boundary of the top face too? No, top face is part of a closed box usually.
            # Wait, `inset_individual` creates new faces inside. The outer boundary of `top_face` is connected to side walls.
            # When we deleted `center_face`, we created a hole. The edges of that hole are boundary.
            # The outer edges of the box are NOT boundary because they connect to side walls.
            # So `is_boundary` should correctly identify the hole edges AND the circle edges.

            bmesh.ops.bridge_loops(bm, edges=hole_edges) # This bridges the hole edges to the circle edges (also boundary)

            # 4. Fan Blades
            # Hub
            bmesh.ops.create_circle(
                bm,
                cap_ends=True,
                radius=circle_r * 0.2,
                segments=16,
                matrix=Matrix.Translation((0, 0, circle_z - 0.2))
            )
            bm.faces.ensure_lookup_table()
            hub_face = bm.faces[-1]
            hub_face.material_index = 1

            # Blades
            for i in range(self.fan_count):
                angle = (i / self.fan_count) * 2 * math.pi
                blade_l = circle_r * 0.7
                blade_w = circle_r * 0.15

                v1 = Vector((0, -blade_w/2, 0))
                v2 = Vector((blade_l, -blade_w/2, 0))
                v3 = Vector((blade_l, blade_w/2, 0))
                v4 = Vector((0, blade_w/2, 0))

                rot = Matrix.Rotation(angle, 3, 'Z')
                tilt = Matrix.Rotation(math.radians(25), 3, 'X')

                blade_verts_co = [rot @ tilt @ v for v in [v1, v2, v3, v4]]
                offset = Vector((0, 0, circle_z - 0.2))
                blade_verts_co = [v + offset for v in blade_verts_co]

                new_verts = [bm.verts.new(co) for co in blade_verts_co]
                blade_face = bm.faces.new(new_verts)
                blade_face.material_index = 1

        # 5. Flange Socket (Back)
        flange_y = -l/2
        flange_z = h * 0.25

        # Create flange cap
        ret = bmesh.ops.create_circle(
            bm,
            cap_ends=True,
            radius=self.socket_flange_size,
            segments=16,
            matrix=Matrix.Translation((0, flange_y, flange_z)) @ Matrix.Rotation(math.radians(90), 4, 'X')
        )
        flange_cap = ret['faces'][0]
        flange_cap.material_index = 3 # Socket Slot

        # Extrude
        res = bmesh.ops.extrude_face_region(bm, geom=[flange_cap])

        verts_ext = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=verts_ext, vec=(0, -0.2, 0))

        # Identify cap and walls
        # The new faces in res['geom'] include the side walls AND the new cap face (usually).
        # Actually, in Blender's bmesh.ops.extrude_face_region, the list 'faces' in result contains the side faces.
        # The original face is kept and moved? Or a new face is created?
        # Let's search for the face at the new position.

        bm.faces.ensure_lookup_table()
        flange_cap_new = None

        # Look for face at (0, flange_y - 0.2, flange_z) with normal -Y
        target_y = flange_y - 0.2
        for f in bm.faces:
             center = f.calc_center_median()
             if abs(center.y - target_y) < 0.01 and abs(center.z - flange_z) < 0.01:
                 if f.normal.y < -0.9:
                     flange_cap_new = f
                     break

        if flange_cap_new:
            flange_cap_new.material_index = 3 # Socket Slot

        # Set side walls to Chassis (0)
        for g in res['geom']:
            if isinstance(g, bmesh.types.BMFace):
                # If it's not the cap (which might be in geom or not), set to 0.
                if g != flange_cap_new:
                    g.material_index = 0

        # 6. UV Mapping
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
            if f.material_index in [0, 2, 3]: # Chassis, Vents, Flange
                for l in f.loops:
                    nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                    if nz > 0.5:
                        u, v = l.vert.co.x, l.vert.co.y
                    elif ny > 0.5:
                        u, v = l.vert.co.x, l.vert.co.z
                    else:
                        u, v = l.vert.co.y, l.vert.co.z
                    l[uv_layer].uv = (u * 0.5, v * 0.5)
            elif f.material_index == 1: # Fan
                 for l in f.loops:
                     l[uv_layer].uv = (l.vert.co.x, l.vert.co.y)

    def execute(self, context):
        return super().execute(context)
