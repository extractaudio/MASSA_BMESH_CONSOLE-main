import bpy
import bmesh
import random
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty, BoolProperty, FloatVectorProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_13: Fracture Shard",
    "id": "prim_13_shard",
    "icon": "MOD_EXPLODE",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": True,  # Merge vertices within the single shard
        "FIX_DEGENERATE": False,  # CRITICAL: Keep razor-thin edges for sharpness
        "ALLOW_SOLIDIFY": False,  # Shard is a solid volume
        "ALLOW_CHAMFER": True,  # Chamfering sharp shards creates nice highlights
    },
}


class MASSA_OT_PrimShard(Massa_OT_Base):
    bl_idname = "massa.gen_prim_13_shard"
    bl_label = "PRIM_13: Shard"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Bounding Size", default=(1.0, 1.0, 1.0), min=0.1)

    # --- 2. DESTRUCTION ---
    cuts: IntProperty(name="Fracture Cuts", default=8, min=1, max=50)
    roughness: FloatProperty(name="Chaos Factor", default=0.5, min=0.0, max=1.0)
    seed: IntProperty(name="Seed", default=777)

    # --- 3. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 Standard:
        All UVs set to 'SKIP' because the cartridge calculates
        Tri-Planar mapping internally for the irregular geometry.
        """
        return {
            0: {"name": "Outer Shell", "uv": "SKIP", "phys": "CONCRETE_POL"},
            1: {"name": "Inner Core", "uv": "SKIP", "phys": "CONCRETE_RAW"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")

        # UI UPDATE: Compact XYZ Row
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "size", index=0, text="X")
        row.prop(self, "size", index=1, text="Y")
        row.prop(self, "size", index=2, text="Z")

        layout.separator()
        layout.label(text="Fracture Logic", icon="MOD_EXPLODE")
        layout.prop(self, "cuts")
        layout.prop(self, "roughness")
        layout.prop(self, "seed")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        rng = random.Random(self.seed)

        # 1. INITIALIZE BASE SHAPE (Cube)
        # ----------------------------------------------------------------------
        # We start with a cube sized to the bounding box
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=self.size, verts=bm.verts)

        # Assign Slot 0 (Outer Shell)
        for f in bm.faces:
            f.material_index = 0
            f.smooth = False

        # 2. DESTRUCTIVE LOOP (Whittling)
        # ----------------------------------------------------------------------
        center = Vector((0, 0, 0))
        max_dim = max(self.size)

        for i in range(self.cuts):
            if not bm.verts:
                break

            # A. Generate Cutting Plane
            # Normal: Random direction
            nx = rng.uniform(-1.0, 1.0)
            ny = rng.uniform(-1.0, 1.0)
            nz = rng.uniform(-1.0, 1.0)
            norm = Vector((nx, ny, nz)).normalized()

            # Point: Offset from center
            # Roughness 0.0 -> Cuts pass near center (Splinters)
            # Roughness 1.0 -> Cuts pass near edges (Chipping)

            # We want the plane to clip the mesh, but not delete it entirely.
            # Range: 0 to max_dim/2
            offset_dist = rng.uniform(0.1, max_dim * 0.45)

            # Apply chaos to move the cutting plane away from origin
            # We purposefully bias the cuts to "shave" the object
            plane_co = norm * offset_dist * (0.5 + (self.roughness * 0.5))

            # B. Bisect & Clear Outer
            # This slices the mesh and removes the "positive" side of the plane
            try:
                res = bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    dist=0.0001,
                    plane_co=plane_co,
                    plane_no=norm,
                    clear_outer=True,
                    clear_inner=False,
                )

                # C. Cap the Hole
                # Bisect leaves a hole. We must find boundary edges and fill them.
                # Since we are cutting a convex shape (cube) with a plane,
                # the result is always a planar hole.
                edges_cut = [e for e in bm.edges if e.is_boundary]

                if edges_cut:
                    res_fill = bmesh.ops.holes_fill(bm, edges=edges_cut, sides=0)

                    # Assign Slot 1 (Inner Core) to the new cut face
                    new_faces = [
                        f
                        for f in res_fill["faces"]
                        if isinstance(f, bmesh.types.BMFace)
                    ]
                    for f in new_faces:
                        f.material_index = 1
                        f.smooth = False  # Sharp cuts
            except:
                pass  # Bisect failed (plane missed mesh), continue

        # 3. MARK SEAMS
        # ----------------------------------------------------------------------
        # Mark sharp edges and material boundaries (Inner Core vs Shell)
        for e in bm.edges:
            if len(e.link_faces) >= 2:
                mats = {f.material_index for f in e.link_faces}
                
                # Material Boundary
                if len(mats) > 1:
                    e.seam = True
                    continue
                
                # Sharp Edges (Fractured bits are sharp)
                # We mark ALL sharp edges as seams for better UV islands on shards
                n1 = e.link_faces[0].normal
                n2 = e.link_faces[1].normal
                if n1.dot(n2) < 0.5: # 60 deg
                    e.seam = True

        # 4. CLEANUP
        # ----------------------------------------------------------------------
        # Remove any microscopic leftovers
        bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 4. UV MAPPING (Tri-Planar Box Map)
        # ----------------------------------------------------------------------
        # Since shards are random, we cannot use parametric UVs.
        # We project UVs based on face normal direction.

        uv_layer = bm.loops.layers.uv.verify()
        scale_val = self.uv_scale

        # Calculate bounding box for "Fit UVs" mode
        min_v = Vector((float("inf"), float("inf"), float("inf")))
        max_v = Vector((float("-inf"), float("-inf"), float("-inf")))

        if self.fit_uvs:
            for v in bm.verts:
                min_v.x = min(min_v.x, v.co.x)
                min_v.y = min(min_v.y, v.co.y)
                min_v.z = min(min_v.z, v.co.z)
                max_v.x = max(max_v.x, v.co.x)
                max_v.y = max(max_v.y, v.co.y)
                max_v.z = max(max_v.z, v.co.z)

            dims = max_v - min_v
            dims.x = max(0.001, dims.x)
            dims.y = max(0.001, dims.y)
            dims.z = max(0.001, dims.z)

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            # Determine projection axis
            for l in f.loops:
                co = l.vert.co
                u, v = 0.0, 0.0

                if nz > nx and nz > ny:
                    # Top/Bottom -> XY
                    u, v = co.x, co.y
                    if self.fit_uvs:
                        u = (u - min_v.x) / dims.x
                        v = (v - min_v.y) / dims.y

                elif nx > ny and nx > nz:
                    # Side X -> YZ
                    u, v = co.y, co.z
                    if self.fit_uvs:
                        u = (u - min_v.y) / dims.y
                        v = (v - min_v.z) / dims.z

                else:
                    # Side Y -> XZ
                    u, v = co.x, co.z
                    if self.fit_uvs:
                        u = (u - min_v.x) / dims.x
                        v = (v - min_v.z) / dims.z

                if not self.fit_uvs:
                    u *= scale_val
                    v *= scale_val

                l[uv_layer].uv = (u, v)

        # 5. PIVOT ALIGNMENT (Center Mass)
        # ----------------------------------------------------------------------
        # Shards usually need their pivot at the volumetric center for physics.
        # The base class handles pivot_mode, but we ensure the geo is roughly centered first
        # by the nature of the cutting process (cutting around 0,0,0).
