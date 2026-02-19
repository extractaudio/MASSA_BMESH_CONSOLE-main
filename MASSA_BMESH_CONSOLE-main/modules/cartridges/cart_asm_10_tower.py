import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_10: Cell Tower",
    "id": "asm_10_tower",
    "icon": "MOD_WIREFRAME",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmTower(Massa_OT_Base):
    bl_idname = "massa.gen_asm_10_tower"
    bl_label = "ASM_10: Cell Tower"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    height: FloatProperty(name="Tower Height", default=20.0, min=10.0)
    width: FloatProperty(name="Base Width", default=2.0, min=1.0)
    taper: FloatProperty(name="Taper Amount", default=0.5, min=0.0, max=1.0)

    platforms: IntProperty(name="Platforms", default=3, min=1)
    antennas_per_plat: IntProperty(name="Antennas/Platform", default=3, min=1)

    use_triangular: BoolProperty(name="Triangular Base", default=True)

    def get_slot_meta(self):
        return {
            0: {"name": "Truss Steel", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "Platform Grate", "uv": "SKIP", "phys": "METAL_GRATE"},
            2: {"name": "Antenna Housing", "uv": "SKIP", "phys": "PLASTIC"},
            3: {"name": "Microwave Dish", "uv": "SKIP", "phys": "METAL_PAINTED"},
            9: {"name": "Cable Socket", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="STRUCTURE", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "height")
        col.prop(self, "width")
        col.prop(self, "taper")
        col.prop(self, "use_triangular")

        layout.separator()
        layout.label(text="EQUIPMENT", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "platforms")
        col.prop(self, "antennas_per_plat")

    def build_shape(self, bm: bmesh.types.BMesh):
        h, w = self.height, self.width
        sides = 3 if self.use_triangular else 4

        # 1. Truss Tower
        # Create base polygon
        # Using cone/cylinder logic but wireframe

        sections = int(h / 3.0) # Every 3 meters

        # We build section by section to control topology?
        # Or create a cylinder and poke faces?
        # Let's create a cylinder.

        r1 = w / 2
        r2 = w / 2 * (1.0 - self.taper)

        ret = bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=sides,
            diameter1=r1*2,
            diameter2=r2*2,
            depth=h,
            calc_uvs=False
        )
        # Cone creates centered at 0,0,0 with height h.
        # We need to move it up by h/2.
        t_verts = ret['verts']
        bmesh.ops.translate(bm, vec=(0, 0, h/2), verts=t_verts)

        # Subdivide vertical edges to create sections
        # Identify vertical edges
        bm.edges.ensure_lookup_table()
        vertical_edges = []
        for e in bm.edges:
            v1, v2 = e.verts
            if abs(v1.co.z - v2.co.z) > h * 0.9: # Long vertical edges
                 vertical_edges.append(e)

        if vertical_edges:
             bmesh.ops.subdivide_edges(bm, edges=vertical_edges, cuts=sections, use_grid_fill=True)

        # Wireframe logic: Convert faces to wireframe or inset?
        # Or rely on "Wireframe Modifier" in game engine?
        # Usually geometry is needed.
        # Let's use `wireframe` op.

        # Select all faces of the tower
        tower_faces = [f for f in bm.faces if f.material_index == 0] # Default 0

        # Let's poke faces to get X bracing
        res_poke = bmesh.ops.poke(bm, faces=tower_faces)
        new_tower_faces = res_poke['faces']

        # Now turn edges into tubes? Too heavy.
        # Just convert to wireframe using `wireframe` op (creates tubes around edges)
        # But this affects everything.
        # Let's select all faces again (new ones)

        # For game asset, maybe alpha texture?
        # Mandate says "using wireframe math".
        # Let's just make the main structure thick wireframe.

        bmesh.ops.wireframe(bm, faces=new_tower_faces, thickness=0.05, offset=0.0, use_replace=True)

        # Assign Slot 0 to new faces
        for f in bm.faces:
            f.material_index = 0

        # 2. Platforms
        # At top and intervals
        plat_z_levels = [h * (i+1)/(self.platforms+1) for i in range(self.platforms)]
        plat_z_levels.append(h - 0.5) # Top platform

        for z in plat_z_levels:
            # Radius at height z
            # Linear interpolation
            factor = z / h
            r = r1 * (1 - factor) + r2 * factor
            plat_r = r * 1.5 # Stick out

            ret = bmesh.ops.create_circle(
                bm,
                cap_ends=True,
                radius=plat_r,
                segments=sides,
                matrix=Matrix.Translation((0, 0, z))
            )
            plat_face = ret['faces'][0]
            plat_face.material_index = 1 # Grate

            # Extrude thickness
            res = bmesh.ops.extrude_face_region(bm, geom=[plat_face])
            verts_ext = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=verts_ext, vec=(0, 0, 0.1))

            # 3. Antennas on Platform
            # Radial array
            count = self.antennas_per_plat * sides
            for i in range(count):
                angle = (i / count) * 2 * math.pi
                ax = math.cos(angle) * (plat_r - 0.2)
                ay = math.sin(angle) * (plat_r - 0.2)

                # Drum Antenna
                # Rectangular box
                ret = bmesh.ops.create_cube(bm, size=1.0)
                a_verts = ret['verts']
                bmesh.ops.scale(bm, vec=(0.2, 0.5, 1.5), verts=a_verts)

                # Position and Rotate
                # Face outward
                rot_z = Matrix.Rotation(angle, 4, 'Z')
                trans = Matrix.Translation((ax, ay, z + 1.0))

                # Combine transform
                # First scale (already done), then rotate, then translate
                bmesh.ops.transform(bm, verts=a_verts, matrix=trans @ rot_z)

                for v in a_verts:
                    for f in v.link_faces:
                        f.material_index = 2 # Antenna Housing

                # 4. Cable Sockets
                # At base of antenna
                sock_pos = Vector((ax * 0.8, ay * 0.8, z + 0.2)) # Slightly inward
                ret = bmesh.ops.create_cube(bm, size=0.1)
                s_verts = ret['verts']
                bmesh.ops.translate(bm, vec=sock_pos, verts=s_verts)
                for v in s_verts:
                    for f in v.link_faces:
                        f.material_index = 9 # Socket

        # 5. Microwave Dishes
        # Near top
        dish_z = h - 2.0
        dish_count = 3
        dish_r = r2 * 2.0 # Stick out more

        for i in range(dish_count):
            angle = (i / dish_count) * 2 * math.pi + (math.pi / sides) # Offset
            dx = math.cos(angle) * dish_r
            dy = math.sin(angle) * dish_r

            # Create Dish (Cone/Circle)
            ret = bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                radius1=0.5,
                radius2=0.1, # Taper to back
                depth=0.3,
                segments=16
            )
            d_verts = ret['verts']

            # Rotate to face outward
            # Cone is along Z. Rotate 90 deg X to face Y.
            # Then Rotate Z to angle.
            rot_x = Matrix.Rotation(math.radians(90), 4, 'X')
            rot_z = Matrix.Rotation(angle - math.pi/2, 4, 'Z') # Adjust facing
            trans = Matrix.Translation((dx, dy, dish_z))

            bmesh.ops.transform(bm, verts=d_verts, matrix=trans @ rot_z @ rot_x)

            for v in d_verts:
                for f in v.link_faces:
                    f.material_index = 3 # Dish

        # 6. UV Mapping
        uv_layer = bm.loops.layers.uv.verify()

        for f in bm.faces:
            # Box map default
            for l in f.loops:
                nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                scale = 1.0
                if f.material_index == 0: scale = 0.5 # Truss detail

                if nz > 0.5:
                    u, v = l.vert.co.x, l.vert.co.y
                elif ny > 0.5:
                    u, v = l.vert.co.x, l.vert.co.z
                else:
                    u, v = l.vert.co.y, l.vert.co.z
                l[uv_layer].uv = (u * scale, v * scale)
