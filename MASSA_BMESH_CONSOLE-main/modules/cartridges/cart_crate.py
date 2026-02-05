import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_properties import MassaPropertiesMixin
from mathutils import Vector, Matrix

# ==============================================================================
# MASSA CARTRIDGE: CRATE (SCIFI CONTAINER)
# ID: cart_crate
# ==============================================================================


CARTRIDGE_META = {
    "name": "Crate",
    "id": "cart_crate",
    "icon": "MESH_CUBE",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_Crate(Massa_OT_Base, MassaPropertiesMixin):
    """
    Operator to generate a Sci-Fi Crate with standard frames and panels.
    Forked from PRIM_04(Panel) logic applied to a Cube.
    """

    bl_idname = "massa.gen_cart_crate"
    bl_label = "Crate"
    bl_description = "Standard Sci-Fi Crate"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- Custom Properties ---
    # Standard dimensions for a crate
    width: FloatProperty(name="Width (X)", default=1.0, unit="LENGTH")
    depth: FloatProperty(name="Depth (Y)", default=1.0, unit="LENGTH")
    height: FloatProperty(name="Height (Z)", default=1.0, unit="LENGTH")

    frame_width: FloatProperty(name="Frame Width", default=0.1, min=0.01, unit="LENGTH")
    inset_depth: FloatProperty(name="Inset Depth", default=0.05, min=0.0, unit="LENGTH")

    use_cross_brace: bpy.props.BoolProperty(name="Cross Brace", default=False)
    edge_extrude: FloatProperty(name="Edge Extrude", default=0.0, unit="LENGTH")

    # --- UI Draw ---
    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon="CUBE")
        box.prop(self, "width")
        box.prop(self, "depth")
        box.prop(self, "height")

        box = layout.box()
        box.label(text="Detailing", icon="MOD_BUILD")
        box.prop(self, "frame_width")
        box.prop(self, "inset_depth")
        box.prop(self, "edge_extrude")
        box.prop(self, "use_cross_brace")

    # --- Slot Protocol ---
    def get_slot_meta(self):
        return {
            0: {"name": "Frame Main", "uv": "BOX", "phys": "METAL_PAINTED"},
            1: {"name": "Panels", "uv": "BOX", "phys": "METAL_DARK"},
            2: {"name": "Details", "uv": "BOX", "phys": "METAL_RUST"},
            3: {"name": "Socket_A", "uv": "SKIP", "phys": "GENERIC", "sock": True},
            4: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            5: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            6: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            7: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            8: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            9: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
        }

    # --- Build Logic ---
    def build_shape(self, bm):
        # 1. Create Base Cube
        # Create cube at scale 1.0, centered
        bmesh.ops.create_cube(bm, size=1.0)

        # Scale to dimensions
        bmesh.ops.scale(bm, vec=(self.width, self.depth, self.height), verts=bm.verts)

        # Ensure normals are correct
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 2. INSET: Create Frame & Panels
        # We process all 6 faces of the cube
        ret = bmesh.ops.inset_individual(
            bm, faces=bm.faces[:], thickness=self.frame_width, depth=0.0
        )

        # Identify Faces
        # inset_individual returns 'faces' which are the INNER panels
        panel_faces = ret["faces"]

        # Identify Frames (The rest)
        all_faces = set(bm.faces)
        frame_faces = list(all_faces - set(panel_faces))

        # Assign Material Slots (Frame=0, Panel=1)
        for f in frame_faces:
            f.material_index = 0

        for f in panel_faces:
            f.material_index = 1

        # --- LOGIC REORDER: PANEL OPERATIONS FIRST ---
        # Operations on panels are 'local' and don't destroy frame index validity as easily.

        if self.use_cross_brace:
            # 3A. CROSS BRACE LOGIC
            # 1. Poke to get center
            valid_panels = [f for f in panel_faces if f.is_valid]
            ret_poke = bmesh.ops.poke(bm, faces=valid_panels)

            # The new faces are triangles forming the X; 'faces' from poke are the new tri-faces.
            new_faces = ret_poke["faces"]

            # 2. Inset Individual (The "Gap" of the X)
            # We want to KEEP the borders (the X) and push the INNER triangles.
            ret_b = bmesh.ops.inset_individual(
                bm, faces=new_faces, thickness=self.frame_width * 0.8, depth=0.0
            )

            # 3. Push Inner Triangles
            inner_tris = ret_b["faces"]

            for f in inner_tris:
                f.material_index = 2  # Details
                # Push IN
                vec = f.normal * (-self.inset_depth * 0.8)
                bmesh.ops.translate(bm, verts=f.verts, vec=vec)

        else:
            # 3B. FLAT PANEL LOGIC
            # Simple Translation along Normals
            for f in panel_faces:
                if not f.is_valid:
                    continue
                d = -self.inset_depth
                vec = f.normal * d
                bmesh.ops.translate(bm, verts=f.verts, vec=vec)

        # 4. FRAME LOGIC (Edge Extrude)
        # Using Extrude Region is safer than Inset Region for "Lip" creation on non-planar connections.

        if self.edge_extrude > 0.0001:
            # Validate frame_faces before operation
            valid_frames = [f for f in frame_faces if f.is_valid]

            # Extrude the Frame Faces (Creates side walls and caps)
            ret_ext = bmesh.ops.extrude_region(bm, geom=valid_frames)

            # Filter geometry to find the "Top Caps" (the faces we want to push out)
            # Strategy: The extruded faces (geom) include sides. We want the ones parallel to the original frames?
            # Simpler Strategy: Iterate the verts returned by extrude and move them along their vertex normals.
            # This mimics "Shrink/Fatten" behavior which handles the corners correctly.

            extruded_verts = [
                v for v in ret_ext["geom"] if isinstance(v, bmesh.types.BMVert)
            ]

            # We need to manually calculate the push vector.
            # Since 'bmesh.ops.translate' is global, we loop.
            # BUT efficient way: bmesh.ops.transform/translate? No.
            # Manual loop is fine for cartridge scale (low poly).

            for v in extruded_verts:
                # Move vertex ALONG its normal.
                v.co += v.normal * self.edge_extrude

        # 5. EDGE ROLE INTERPRETER (Phase 4 Logic)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # Ensure normals are clean for angle calc
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        for e in bm.edges:
            # Perimeter (Boundary or Sharp Frame Edges) matches Slot 1 (Red)
            angle = e.calc_face_angle(0)

            if angle > 1.5:
                e[edge_slots] = 1  # Perimeter / Sharp Seam

            # Inner Panel edges (Contour)
            faces = e.link_faces
            if len(faces) == 2:
                m0 = faces[0].material_index
                m1 = faces[1].material_index

                if m0 == 0 and m1 == 0:
                    # Outer Frame Edge
                    e[edge_slots] = 1  # Red
                elif m0 != m1:
                    # Border between Frame and Panel
                    e[edge_slots] = 2  # Cyan / Contour
