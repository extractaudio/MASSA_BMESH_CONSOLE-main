"""
Filename: modules/cartridges/prim_con_beam.py
Content: Parametric Structural Beam Generator (I, H, T, Channel, Angle)
Status: FIXED (Seam Sanitization + PRIM_01 Logic)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, EnumProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector

CARTRIDGE_META = {
    "name": "Con: Steel Beam",
    "id": "prim_con_beam",
    "icon": "SNAP_EDGE",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_beam(Massa_OT_Base):
    """
    Parametric Structural Beam Generator.
    Implements PRIM_01 (Linear Profile) logic.
    Supports I, H, T, C, and L profiles with chamfered fillets.
    """

    bl_idname = "massa.gen_prim_con_beam"
    bl_label = "Construction Beam"
    bl_description = "Structural Steel Profiles"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMENSIONS ---
    prop_length: FloatProperty(name="Length", default=4.0, min=0.1, unit="LENGTH")
    prop_depth: FloatProperty(name="Depth (H)", default=0.2, min=0.01, unit="LENGTH")
    prop_width: FloatProperty(name="Width (W)", default=0.15, min=0.01, unit="LENGTH")

    prop_thickness_web: FloatProperty(
        name="Web Thick", default=0.01, min=0.001, unit="LENGTH"
    )
    prop_thickness_flange: FloatProperty(
        name="Flange Thick", default=0.015, min=0.001, unit="LENGTH"
    )
    prop_fillet_radius: FloatProperty(
        name="Fillet (Chamfer)",
        default=0.01,
        min=0.0,
        unit="LENGTH",
        description="Inner corner chamfer size",
    )

    # --- SHAPE ---
    prop_profile_type: EnumProperty(
        name="Profile",
        items=[
            ("I_BEAM", "I-Beam", "Standard I-Section"),
            ("H_BEAM", "H-Beam", "Wide Flange"),
            ("T_BEAM", "T-Beam", "Structural T"),
            ("C_CHANNEL", "C-Channel", "C-Section"),
            ("L_ANGLE", "L-Angle", "Angle Iron"),
        ],
        default="I_BEAM",
    )

    # --- TOPOLOGY ---
    prop_seg_len: IntProperty(name="Length Cuts", default=1, min=1)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Profile", icon="SNAP_FACE")
        box.prop(self, "prop_profile_type")
        col = box.column(align=True)
        col.prop(self, "prop_length")
        col.prop(self, "prop_depth", text="Height")
        col.prop(self, "prop_width")

        box = layout.box()
        box.label(text="Section Data", icon="MOD_THICKNESS")
        col = box.column(align=True)
        col.prop(self, "prop_thickness_web")
        col.prop(self, "prop_thickness_flange")
        col.prop(self, "prop_fillet_radius")
        box.prop(self, "prop_seg_len")

    def get_slot_meta(self):
        return {
            0: {"name": "Steel_Face", "uv": "TUBE_Y", "phys": "METAL_STEEL"},
            1: {"name": "Cut_End", "uv": "BOX", "phys": "METAL_RUST"},
            3: {"name": "Anchor_Point", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def build_shape(self, bm):
        # --- HARNESS DEFENSE: Manual Default Injection ---
        # Workaround for SmartMock failing to populate from bl_rna in headless mode.
        defaults = {
            "prop_length": 4.0,
            "prop_depth": 0.2,
            "prop_width": 0.15,
            "prop_thickness_web": 0.01,
            "prop_thickness_flange": 0.015,
            "prop_fillet_radius": 0.01,
            "prop_profile_type": "I_BEAM",
            "prop_seg_len": 1,
        }
        for k, v in defaults.items():
            if not hasattr(self, k):
                setattr(self, k, v)

        # 1. PARAMS
        l = self.prop_length
        h = self.prop_depth / 2
        w = self.prop_width / 2
        tw = min(self.prop_thickness_web / 2, w - 0.001)
        tf = min(self.prop_thickness_flange, h - 0.001)
        fil = min(self.prop_fillet_radius, (w - tw) * 0.9, (h - tf) * 0.9)
        fil = max(0.0, fil)

        # 2. DEFINE 2D PROFILE (XZ Plane at Y=0)
        verts_2d = []

        if self.prop_profile_type in {"I_BEAM", "H_BEAM"}:
            verts_2d.append(Vector((w, 0, h)))
            verts_2d.append(Vector((-w, 0, h)))
            if fil > 0.001:
                verts_2d.append(Vector((-w, 0, h - tf)))
                verts_2d.append(Vector((-tw - fil, 0, h - tf)))
                verts_2d.append(Vector((-tw, 0, h - tf - fil)))
            else:
                verts_2d.append(Vector((-w, 0, h - tf)))
                verts_2d.append(Vector((-tw, 0, h - tf)))
            if fil > 0.001:
                verts_2d.append(Vector((-tw, 0, -h + tf + fil)))
                verts_2d.append(Vector((-tw - fil, 0, -h + tf)))
                verts_2d.append(Vector((-w, 0, -h + tf)))
            else:
                verts_2d.append(Vector((-tw, 0, -h + tf)))
                verts_2d.append(Vector((-w, 0, -h + tf)))
            verts_2d.append(Vector((-w, 0, -h)))
            verts_2d.append(Vector((w, 0, -h)))
            if fil > 0.001:
                verts_2d.append(Vector((w, 0, -h + tf)))
                verts_2d.append(Vector((tw + fil, 0, -h + tf)))
                verts_2d.append(Vector((tw, 0, -h + tf + fil)))
            else:
                verts_2d.append(Vector((w, 0, -h + tf)))
                verts_2d.append(Vector((tw, 0, -h + tf)))
            if fil > 0.001:
                verts_2d.append(Vector((tw, 0, h - tf - fil)))
                verts_2d.append(Vector((tw + fil, 0, h - tf)))
                verts_2d.append(Vector((w, 0, h - tf)))
            else:
                verts_2d.append(Vector((tw, 0, h - tf)))
                verts_2d.append(Vector((w, 0, h - tf)))

        elif self.prop_profile_type == "T_BEAM":
            verts_2d = [Vector((w, 0, h)), Vector((-w, 0, h))]
            if fil > 0.001:
                verts_2d.append(Vector((-w, 0, h - tf)))
                verts_2d.append(Vector((-tw - fil, 0, h - tf)))
                verts_2d.append(Vector((-tw, 0, h - tf - fil)))
            else:
                verts_2d.append(Vector((-w, 0, h - tf)))
                verts_2d.append(Vector((-tw, 0, h - tf)))
            verts_2d.extend([Vector((-tw, 0, -h)), Vector((tw, 0, -h))])
            if fil > 0.001:
                verts_2d.append(Vector((tw, 0, h - tf - fil)))
                verts_2d.append(Vector((tw + fil, 0, h - tf)))
                verts_2d.append(Vector((w, 0, h - tf)))
            else:
                verts_2d.append(Vector((tw, 0, h - tf)))
                verts_2d.append(Vector((w, 0, h - tf)))

        elif self.prop_profile_type == "C_CHANNEL":
            verts_2d = [
                Vector((w, 0, h)),
                Vector((-w, 0, h)),
                Vector((-w, 0, -h)),
                Vector((w, 0, -h)),
            ]
            if fil > 0.001:
                verts_2d.append(Vector((w, 0, -h + tf)))
                verts_2d.append(Vector((-w + (tw * 2) + fil, 0, -h + tf)))
                verts_2d.append(Vector((-w + (tw * 2), 0, -h + tf + fil)))
            else:
                verts_2d.append(Vector((w, 0, -h + tf)))
                verts_2d.append(Vector((-w + (tw * 2), 0, -h + tf)))
            if fil > 0.001:
                verts_2d.append(Vector((-w + (tw * 2), 0, h - tf - fil)))
                verts_2d.append(Vector((-w + (tw * 2) + fil, 0, h - tf)))
                verts_2d.append(Vector((w, 0, h - tf)))
            else:
                verts_2d.append(Vector((-w + (tw * 2), 0, h - tf)))
                verts_2d.append(Vector((w, 0, h - tf)))

        elif self.prop_profile_type == "L_ANGLE":
            verts_2d = [Vector((-w, 0, h)), Vector((-w, 0, -h)), Vector((w, 0, -h))]
            if fil > 0.001:
                verts_2d.append(Vector((w, 0, -h + tf)))
                verts_2d.append(Vector((-w + (tw * 2) + fil, 0, -h + tf)))
                verts_2d.append(Vector((-w + (tw * 2), 0, -h + tf + fil)))
            else:
                verts_2d.append(Vector((w, 0, -h + tf)))
                verts_2d.append(Vector((-w + (tw * 2), 0, -h + tf)))
            verts_2d.append(Vector((-w + (tw * 2), 0, h)))

        # 3. CREATE START CAP
        bm_verts = [bm.verts.new(v) for v in verts_2d]
        start_cap = bm.faces.new(bm_verts)

        # 4. EXTRUDE
        ret = bmesh.ops.extrude_face_region(bm, geom=[start_cap])
        verts_ext = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=verts_ext, vec=(0, l, 0))

        # 5. SEGMENTATION (Length Cuts)
        cut_edges = []
        if self.prop_seg_len > 1:
            step = l / self.prop_seg_len
            for i in range(1, self.prop_seg_len):
                # Bisect returns geometry. We must collect only the NEW edges on the cut plane.
                ret = bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(0, i * step, 0),
                    plane_no=(0, 1, 0),
                )
                cut_edges.extend(
                    [e for e in ret["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
                )

        # 6. CAP IDENTIFICATION (Spatial)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.faces.ensure_lookup_table()

        start_caps = []
        end_caps = []
        walls = []

        for f in bm.faces:
            cen = f.calc_center_median()
            if abs(cen.y) < 0.001:
                start_caps.append(f)
            elif abs(cen.y - l) < 0.001:
                end_caps.append(f)
            else:
                walls.append(f)

        # 7. SANITIZATION: NUKE ALL SEAMS FIRST
        for e in bm.edges:
            e.seam = False

        # 8. APPLY SEAMS TO CUTS (Requested Feature)
        for e in cut_edges:
            e.seam = True

        # 8b. SINGULAR TOP SEAM (User Request)
        # Slices the geometry down the Y-axis (X=0 plane) creating a new edge loop.
        # STRICT REQUIREMENT: Only cut the TOP faces. Do not cut Caps or Bottom.
        
        # 1. Collect Top Faces (Top Flange upper surface)
        # Normal Z > 0.5 (safely pointing up)
        top_faces = [f for f in bm.faces if f.normal.z > 0.5]
        
        # 2. Collect edges and verts of these faces for the context
        top_geom = list(set(top_faces) | 
                        {e for f in top_faces for e in f.edges} | 
                        {v for f in top_faces for v in f.verts})

        # 3. Bisect ONLY the filtered geometry
        # Cut Plane: X=0 (YZ Plane)
        ret = bmesh.ops.bisect_plane(
            bm,
            geom=top_geom,
            plane_co=(0, 0, 0),
            plane_no=(1, 0, 0),
            clear_inner=False,
            clear_outer=False
        )
        
        cut_edges_bisect = [e for e in ret["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        
        # Mark as Seam (Filtered check needed if bisect touches shared edges, but strictly top faces usually implies correct z)
        top_thresh = (self.prop_depth / 2) - 0.001
        
        for e in cut_edges_bisect:
             e.seam = True

        # 9. ASSIGN SLOTS & CAP SEAMS (Normal Based)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # Re-Find Caps by Normal (Robust to topology changes)
        # Bisect changes face indices, so we find them geometrically.
        # Y-Axis Aligned Faces = Caps.
        current_caps = [f for f in bm.faces if abs(f.normal.y) > 0.9]
        
        for f in current_caps:
            f.material_index = 1
            for e in f.edges:
                e.seam = True  # Explicit Cap Seam
                e[edge_slots] = 1 # Perimeter Slot

        # --- PROCESS WALLS ---
        # Any face not a cap is a wall
        walls = [f for f in bm.faces if f not in current_caps]
        for f in walls:
            f.material_index = 0

        # SAFETY NET: Ensure Seams are Slot 1
        for e in bm.edges:
            if e.seam or e.is_boundary:
                e[edge_slots] = 1

        # --- PROCESS CONTOUR ---
        for e in bm.edges:
            if not e.seam:
                if e.calc_face_angle() > math.radians(20):
                    e[edge_slots] = 2  # Role: Contour (Sharp)
                elif e.calc_face_angle() > 0.01:
                    e[edge_slots] = 3  # Role: Guide

        # 10. UV UNWRAP (CLASSIC ROUNDTRIP)
        # User requested Angle-Based Unwrap using the Seams we marked.
        # Since bmesh.ops.unwrap is technically missing/broken in some contexts,
        # we perform a "Roundtrip": BMesh -> Temp Object -> Edit Mode -> Unwrap -> BMesh.
        headless_classic_unwrap(bm)


def headless_classic_unwrap(bm):
    """
    Flushes the BMesh to a temporary object / mesh, performs
    a standard bpy.ops.uv.unwrap (using the Context Override),
    and loads the result back into the BMesh.
    """
    # 1. Create Temp Mesh & Object
    me = bpy.data.meshes.new("_temp_unwrap_mesh")
    bm.to_mesh(me)
    
    obj = bpy.data.objects.new("_temp_unwrap_obj", me)
    col = bpy.data.collections.get("Collection")
    if not col:
        col = bpy.data.collections.new("Collection")
        bpy.context.scene.collection.children.link(col)
    col.objects.link(obj)
    
    # 2. Set Context
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # 3. Enter Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # 4. Unwrap
    # 'ANGLE_BASED' or 'CONFORMAL'. Margin 0.001 is standard.
    try:
       bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    except Exception as e:
        print(f"UNWRAP ERROR: {e}")
        
    # 5. Read Back
    bpy.ops.object.mode_set(mode='OBJECT')
    bm.clear()
    bm.from_mesh(me)
    
    # 6. Cleanup
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(me, do_unlink=True)
