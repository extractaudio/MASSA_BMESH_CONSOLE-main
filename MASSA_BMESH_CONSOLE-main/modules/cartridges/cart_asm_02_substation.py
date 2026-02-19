import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_02: HV Substation",
    "id": "asm_02_substation",
    "icon": "MOD_EXPLODE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmSubstation(Massa_OT_Base):
    bl_idname = "massa.gen_asm_02_substation"
    bl_label = "ASM_02: HV Substation"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=2.5, min=0.5)
    length: FloatProperty(name="Length (Y)", default=3.0, min=0.5)
    height: FloatProperty(name="Height (Z)", default=2.0, min=0.5)

    fin_density: IntProperty(name="Fin Density", default=8, min=2)
    insulator_count: IntProperty(name="Insulators", default=4, min=1)

    insulator_height: FloatProperty(name="Insulator Height", default=1.5, min=0.5)

    def get_slot_meta(self):
        return {
            0: {"name": "Core", "uv": "SKIP", "phys": "METAL_PAINTED"},
            1: {"name": "Fins", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            2: {"name": "Chassis", "uv": "SKIP", "phys": "METAL_PAINTED"},
            3: {"name": "Insulators", "uv": "SKIP", "phys": "CERAMIC"},
            4: {"name": "Insulator Tip", "uv": "SKIP", "phys": "CERAMIC", "sock": True},
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
        col.prop(self, "fin_density")
        col.prop(self, "insulator_count")
        col.prop(self, "insulator_height")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, l, h = self.width, self.length, self.height

        # 1. Main Block
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, l, h), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, h/2), verts=bm.verts)

        for f in bm.faces:
            f.material_index = 0 # Core

        # 2. Cooling Fins
        # Bisect X
        num_cuts_x = max(2, int(self.fin_density * (w/2.0)))
        step_x = w / num_cuts_x
        for i in range(1, num_cuts_x):
            x = -w/2 + i * step_x
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:]+bm.verts[:], plane_co=(x,0,0), plane_no=(1,0,0))

        # Bisect Y
        num_cuts_y = max(2, int(self.fin_density * (l/2.0)))
        step_y = l / num_cuts_y
        for i in range(1, num_cuts_y):
            y = -l/2 + i * step_y
            bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:]+bm.verts[:], plane_co=(0,y,0), plane_no=(0,1,0))

        # Select alternating faces
        bm.faces.ensure_lookup_table()
        fin_faces = []

        for f in bm.faces:
            center = f.calc_center_median()
            is_fin = False

            if abs(f.normal.x) > 0.9: # Side face (X)
                # Check Y index
                # Map y from [-l/2, l/2] to index
                idx = int( (center.y + l/2) / (l / num_cuts_y) )
                if idx % 2 == 1:
                    is_fin = True

            elif abs(f.normal.y) > 0.9: # Front/Back face (Y)
                # Check X index
                idx = int( (center.x + w/2) / (w / num_cuts_x) )
                if idx % 2 == 1:
                    is_fin = True

            if is_fin:
                fin_faces.append(f)

        # Extrude fins
        if fin_faces:
            res = bmesh.ops.extrude_face_region(bm, geom=fin_faces)
            verts_ext = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]

            # Fatten (push along normals)
            bmesh.ops.shrink_fatten(bm, verts=verts_ext, dist=0.15)

            # Assign material to new faces
            for g in res['geom']:
                if isinstance(g, bmesh.types.BMFace):
                    g.material_index = 1 # Fins

        # 3. Insulators on Top
        top_z = h

        rows = 2
        cols = max(1, self.insulator_count // 2)

        spacing_x = w * 0.5
        spacing_y = l / (cols + 1)

        # Pre-calc to avoid lookups in loop
        ins_faces = []
        tip_faces = []

        for r in range(rows):
            for c in range(cols):
                px = -spacing_x/2 + r * spacing_x
                py = -l/2 + (c + 1) * spacing_y

                # Stacked Rings
                num_ribs = 6
                rib_h = self.insulator_height / num_ribs
                current_z = top_z

                for i in range(num_ribs):
                    ret = bmesh.ops.create_cone(
                        bm,
                        cap_ends=True,
                        cap_tris=False,
                        segments=12,
                        diameter1=0.25,
                        diameter2=0.15,
                        depth=rib_h * 0.9, # Slight gap for rib effect
                        matrix=Matrix.Translation((px, py, current_z + rib_h/2))
                    )
                    # Collect faces for material assignment
                    # Note: create_cone returns 'verts' usually, but 'faces' key might be missing?
                    # BMesh ops usually return what they created.
                    # Since we are adding to main BM, indices shift.
                    # We can use geometry tagging.
                    # But simpler: we will assign by Z height later.
                    current_z += rib_h

                # Tip (Socket)
                tip_z = top_z + self.insulator_height
                ret = bmesh.ops.create_cone(
                    bm,
                    cap_ends=True,
                    segments=8,
                    diameter1=0.05,
                    diameter2=0.05,
                    depth=0.1,
                    matrix=Matrix.Translation((px, py, tip_z + 0.05))
                )

        # 4. Material Assignment by Height/Normal
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            center = f.calc_center_median()

            if center.z > h + 0.01:
                # It's an insulator part
                f.material_index = 3 # Insulator Body

                # Check if it's the tip
                if center.z > h + self.insulator_height - 0.05:
                    if f.normal.z > 0.9:
                        f.material_index = 4 # Tip (Socket)

        # 5. UV Mapping
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
             for l in f.loops:
                 # Simple Tri-planar / Box projection
                 nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                 if nz > 0.5:
                     u, v = l.vert.co.x, l.vert.co.y
                 elif ny > 0.5:
                     u, v = l.vert.co.x, l.vert.co.z
                 else:
                     u, v = l.vert.co.y, l.vert.co.z
                 l[uv_layer].uv = (u * 0.5, v * 0.5)

    def execute(self, context):
        return super().execute(context)
