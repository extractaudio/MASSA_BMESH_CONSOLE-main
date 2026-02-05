import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty
from mathutils import Vector
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "Construction Plank",
    "id": "plank",
    "icon": "CUBE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Thickness is a parameter
        "USE_WELD": True,
    },
}


class MASSA_OT_Plank(Massa_OT_Base):
    """Generate Construction Plank V2 with Edge Slot Integration"""

    bl_idname = "massa.gen_plank"
    bl_label = "Massa Plank"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMS ---
    length: FloatProperty(name="Length (Y)", default=2.0, min=0.1, unit="LENGTH")
    width: FloatProperty(name="Width (X)", default=0.2, min=0.05, unit="LENGTH")
    thickness: FloatProperty(
        name="Thickness (Z)", default=0.05, min=0.01, unit="LENGTH"
    )

    # --- TOPOLOGY ---
    seg_l: IntProperty(name="Cuts Length", default=1, min=1)
    seg_w: IntProperty(name="Cuts Width", default=1, min=1)
    seg_h: IntProperty(name="Cuts Height", default=1, min=1)

    def get_slot_meta(self):
        """
        V2 Standard: Defines Material, UV, and Physics defaults.
        """
        return {
            0: {
                "name": "Long Grain",
                "uv": "TUBE_Y",
                "phys": "WOOD_OAK",
            },  # Runs along Y
            1: {"name": "End Cuts", "uv": "BOX", "phys": "WOOD_OAK"},  # Cross section
            2: {"name": "Detail", "uv": "BOX", "phys": "GENERIC"},
            3: {"name": "Paint", "uv": "BOX", "phys": "SYNTH_PLASTIC"},
            4: {"name": "Decal", "uv": "FIT", "phys": "GENERIC"},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "thickness")

        col.separator()
        col.label(text="Topology")
        row = col.row(align=True)
        row.prop(self, "seg_l", text="Y-Cuts")
        row.prop(self, "seg_w", text="X-Cuts")
        row.prop(self, "seg_h", text="Z-Cuts")

    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. Calculate Dimensions
        sl = max(1, self.seg_l)
        sw = max(1, self.seg_w)
        sh = max(1, self.seg_h)

        # Create Grid (Top Face initially)
        res = bmesh.ops.create_grid(bm, x_segments=sw, y_segments=sl, size=0.5)
        verts = res["verts"]

        # Scale to Length/Width
        bmesh.ops.scale(bm, vec=Vector((self.width, self.length, 1.0)), verts=verts)

        # 2. Extrude Downwards for Thickness
        faces = list({f for v in verts for f in v.link_faces})

        # Assign TOP faces to Slot 0 (Long Grain)
        for f in faces:
            f.material_index = 0

        extrude_res = bmesh.ops.extrude_face_region(bm, geom=faces)

        verts_ext = [
            v for v in extrude_res["geom"] if isinstance(v, bmesh.types.BMVert)
        ]
        faces_side = [
            f for f in extrude_res["geom"] if isinstance(f, bmesh.types.BMFace)
        ]

        # Move extruded verts down
        bmesh.ops.translate(bm, vec=Vector((0, 0, -self.thickness)), verts=verts_ext)

        # 3. Handle Side Materials
        for f in faces_side:
            norm = f.normal
            if abs(norm.y) > abs(norm.x):
                f.material_index = 1  # End Cut
            else:
                f.material_index = 0  # Long Grain Side

        # 4. Z-Min Pivot Correction
        bmesh.ops.translate(bm, vec=Vector((0, 0, self.thickness)), verts=bm.verts)

        # 5. Height Segmentation
        if sh > 1:
            step = self.thickness / sh
            for i in range(1, sh):
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    dist=0.0001,
                    plane_co=Vector((0, 0, i * step)),
                    plane_no=Vector((0, 0, 1)),
                )

        # 6. Final Cleanup
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # --- 7. EDGE SLOT MARKING (NEW LOGIC) ---
        bm.edges.ensure_lookup_table()

        # Create the Layer
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            # Logic: If edge is on the top face (approx Z = thickness) -> Slot 2 (Contour/Sharp)
            # Check Z height of both verts
            z1 = e.verts[0].co.z
            z2 = e.verts[1].co.z

            # Tolerance for float comparison
            is_top = (
                abs(z1 - self.thickness) < 0.001 and abs(z2 - self.thickness) < 0.001
            )
            is_bottom = abs(z1) < 0.001 and abs(z2) < 0.001
            is_vertical = abs(z1 - z2) > 0.001

            if is_top:
                # Mark perimeter of top face as "Contour" (Slot 2) -> Default Sharp
                if e.is_boundary or any(
                    f.material_index != 0 for f in e.link_faces
                ):  # Basic perimeter check
                    e[edge_slots] = 2

            elif is_vertical:
                # Mark vertical corners as "Guide" (Slot 3) -> Default Seam
                # We check if it's a sharp corner (angle check)
                if e.calc_face_angle() > 1.0:  # > ~57 degrees
                    e[edge_slots] = 3
