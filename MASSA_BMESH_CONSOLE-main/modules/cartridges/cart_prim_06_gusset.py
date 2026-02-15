import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_06: Gusset Plate",
    "id": "prim_06_gusset",
    "icon": "MOD_TRIANGULATE",
    "scale_class": "MICRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Thickness is extruded manually
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,  # Edge highlights are essential
    },
}


class MASSA_OT_PrimGusset(Massa_OT_Base):
    bl_idname = "massa.gen_prim_06_gusset"
    bl_label = "PRIM_06: Gusset"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- SHAPE ---
    shape: EnumProperty(
        name="Shape",
        items=[("TRIANGLE", "Triangle", ""), ("L_SHAPE", "L-Bracket", "")],
        default="TRIANGLE",
    )
    size: FloatProperty(name="Size", default=0.5, min=0.1)
    thickness: FloatProperty(name="Thickness", default=0.01, min=0.002)

    # --- DETAILS ---
    has_holes: BoolProperty(name="Generate Holes", default=True)
    hole_radius: FloatProperty(name="Hole Radius", default=0.03, min=0.001)

    # --- UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Plate Surface", "uv": "SKIP", "phys": "METAL_IRON"},
            1: {"name": "Cut Edges", "uv": "SKIP", "phys": "METAL_IRON"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Profile", icon="MESH_DATA")
        layout.prop(self, "shape", text="")
        layout.prop(self, "size")
        layout.prop(self, "thickness")

        layout.separator()
        layout.label(text="Machining", icon="MOD_BOOLEAN")
        layout.prop(self, "has_holes", toggle=True)
        if self.has_holes:
            layout.prop(self, "hole_radius")



    def build_shape(self, bm: bmesh.types.BMesh):
        s = self.size
        t = self.thickness

        # 1. GEOMETRY DEFINITION & SAFETY CLAMP
        pts = []
        holes_pos = []

        # Safe Radius Logic
        # Calculate the max possible radius before overlapping edges
        safe_r = 0.01

        if self.shape == "TRIANGLE":
            pts = [(0, 0, 0), (s, 0, 0), (0, s, 0)]
            holes_pos = [
                (s * 0.25, s * 0.25, 0),
                (s * 0.1, s * 0.7, 0),
                (s * 0.7, s * 0.1, 0),
            ]
            # Approx limit: Distance to edge is roughly 0.15 * size
            safe_r = s * 0.12
        else:  # L_SHAPE
            w = s * 0.3
            pts = [(0, 0, 0), (s, 0, 0), (s, w, 0), (w, w, 0), (w, s, 0), (0, s, 0)]
            holes_pos = [
                (s * 0.8, w * 0.5, 0),
                (w * 0.5, s * 0.8, 0),
                (w * 0.5, w * 0.5, 0),
            ]
            # Approx limit: Width is 0.3 * size, hole is centered -> max r is 0.15 * size
            safe_r = (s * 0.3) * 0.45

        # Apply Clamp
        actual_r = min(self.hole_radius, safe_r)

        # 2. CREATE OUTER LOOP
        v_outer = [bm.verts.new(Vector(p)) for p in pts]
        for i in range(len(v_outer)):
            bm.edges.new((v_outer[i], v_outer[(i + 1) % len(v_outer)]))

        # 3. CREATE HOLE CIRCLES
        if self.has_holes and actual_r > 0.001:
            for pos in holes_pos:
                bmesh.ops.create_circle(
                    bm,
                    radius=actual_r,
                    segments=16,
                    matrix=Matrix.Translation(Vector(pos)),
                )

        # 4. FILL (Delaunay)
        bmesh.ops.triangle_fill(
            bm, use_beauty=True, use_dissolve=False, edges=bm.edges[:]
        )

        # 5. CULL FACES INSIDE HOLES
        if self.has_holes and actual_r > 0.001:
            faces_to_cull = []
            bm.faces.ensure_lookup_table()
            for f in bm.faces:
                cent = f.calc_center_median()
                for h_pos in holes_pos:
                    dist = (Vector((cent.x, cent.y, 0)) - Vector(h_pos)).length
                    if dist < (actual_r * 0.9):
                        faces_to_cull.append(f)
                        break

            if faces_to_cull:
                bmesh.ops.delete(bm, geom=faces_to_cull, context="FACES")

        # 6. CLEANUP (The Anti-Spiderweb Pass)
        # We dissolve internal edges on the flat plane to create a clean N-Gon.
        # This keeps the wireframe view clean while preserving the shape.
        bmesh.ops.dissolve_limit(
            bm,
            angle_limit=0.01,  # Only merge perfectly flat faces
            use_dissolve_boundaries=False,
            verts=bm.verts[:],
            edges=bm.edges[:],
        )

        # 7. EXTRUDE THICKNESS
        for f in bm.faces:
            f.material_index = 0

        res_ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
        faces_side = [f for f in res_ext["geom"] if isinstance(f, bmesh.types.BMFace)]

        # Move top faces up
        bmesh.ops.translate(bm, vec=(0, 0, t), verts=verts_ext)

        # Assign Slot 1 to cut edges
        for f in faces_side:
            f.material_index = 1

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 8. MARK SEAMS
        for e in bm.edges:
            # 1. Material Boundaries
            if len(e.link_faces) >= 2:
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    continue

            # 2. Sharp Edges (Gusset is mostly sharp)
            # We can mark the 90-degree edges as seams for better unwrap
            if len(e.link_faces) >= 2:
                 n1 = e.link_faces[0].normal
                 n2 = e.link_faces[1].normal
                 if n1.dot(n2) < 0.5:
                     e.seam = True

        # 9. UV MAPPING (Box Projection)
        uv_layer = bm.loops.layers.uv.verify()
        s = 1.0 if self.fit_uvs else self.uv_scale

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            loop_uvs = []
            # Z-Dominant (Top/Bottom Plate) -> Project XY
            if nz > nx and nz > ny:
                for l in f.loops:
                    loop_uvs.append([l, l.vert.co.x, l.vert.co.y])

            # X-Dominant (Side Walls) -> Project YZ
            elif nx > ny and nx > nz:
                for l in f.loops:
                    loop_uvs.append([l, l.vert.co.y, l.vert.co.z])

            # Y-Dominant (Side Walls) -> Project XZ
            else:
                for l in f.loops:
                    loop_uvs.append([l, l.vert.co.x, l.vert.co.z])

            for l, u, v in loop_uvs:
                l[uv_layer].uv = (u * s, v * s)