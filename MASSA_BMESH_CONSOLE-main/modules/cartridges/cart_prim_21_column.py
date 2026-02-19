import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_21: Architectural Column",
    "id": "prim_21_column",
    "icon": "MESH_CYLINDER",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
    },
}

class MASSA_OT_PrimColumn(Massa_OT_Base):
    bl_idname = "massa.gen_prim_21_column"
    bl_label = "PRIM_21: Column"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMENSIONS ---
    width: FloatProperty(name="Base Width", default=0.6, min=0.1, unit="LENGTH", description="Diameter/Width at the base")
    height: FloatProperty(name="Height", default=4.0, min=0.1, unit="LENGTH")
    
    # --- SHAPE ---
    segments: IntProperty(name="Resolution", default=16, min=3, max=64, description="Radial segments for the column shaft")
    taper_ratio: FloatProperty(name="Taper Ratio", default=0.85, min=0.1, max=2.0, description="Ratio of Top Width to Bottom Width")
    
    # --- DETAIL ---
    flute_depth: FloatProperty(name="Flute Depth", default=0.05, min=0.0, max=0.5, description="Depth of vertical grooves (Fluting)")
    vertical_cuts: IntProperty(name="Vertical Segments", default=4, min=0, max=32, description="Horizontal loops along the shaft for vertex painting/deformation")
    
    # --- CAPS ---
    cap_scale: FloatProperty(name="Cap Scale", default=1.2, min=1.0, max=2.0, description="Size of Base/Capital relative to Shaft")
    cap_height: FloatProperty(name="Cap Height", default=0.15, min=0.01, unit="LENGTH")

    # --- UVs ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Shaft Surface", "uv": "SKIP", "phys": "CONSTR_CONCRETE"},
            1: {"name": "Base & Capital", "uv": "BOX", "phys": "CONSTR_CONCRETE"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="arrow_up_down")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        
        layout.separator()
        layout.label(text="PROFILE & TAPER", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "segments")
        col.prop(self, "taper_ratio")

        layout.separator()
        layout.label(text="DETAILING", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "flute_depth")
        col.prop(self, "vertical_cuts")
        
        layout.separator()
        layout.label(text="CAPS / TRIM", icon="MOD_BUILD")
        col = layout.column(align=True)
        col.prop(self, "cap_scale")
        col.prop(self, "cap_height")

        layout.separator()
        layout.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. Setup
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # Parameters
        base_radius = self.width / 2
        h = self.height
        c_h = min(self.cap_height, h * 0.45) # Clamp cap height
        shaft_h = h - (c_h * 2)
        shaft_bot_z = c_h

        # --- HELPER: Create Ring Coords ---
        def get_ring_coords(z, r, is_fluted=False):
            coords = []
            segs = self.segments
            if is_fluted and self.flute_depth > 0.001:
                # Double resolution for flutes: Even=Outer, Odd=Inner
                count = segs * 2
                for i in range(count):
                    angle = (i / count) * 2 * math.pi
                    curr_r = r if (i % 2 == 0) else (r - self.flute_depth)
                    x = math.cos(angle) * curr_r
                    y = math.sin(angle) * curr_r
                    coords.append(Vector((x, y, z)))
            else:
                for i in range(segs):
                    angle = (i / segs) * 2 * math.pi
                    x = math.cos(angle) * r
                    y = math.sin(angle) * r
                    coords.append(Vector((x, y, z)))
            return coords

        # --- STEP 1: SHAFT (Stacked Rings) ---
        num_rings = self.vertical_cuts + 2
        shaft_rings_verts = [] # List of lists of BMVerts
        
        for i in range(num_rings):
            factor = i / (num_rings - 1)
            # Z Interpolation
            z = shaft_bot_z + (shaft_h * factor)
            
            # Radius Interpolation (Linear Taper)
            # r = base_r * (1 - factor) + top_r * factor
            # top_r = base_r * taper_ratio
            r_factor = (1.0 - factor) + (self.taper_ratio * factor)
            current_r = base_radius * r_factor
            
            # Generate Coords
            ring_coords = get_ring_coords(z, current_r, is_fluted=True)

            # Create Verts
            ring_verts = [bm.verts.new(co) for co in ring_coords]
            shaft_rings_verts.append(ring_verts)

        bm.verts.ensure_lookup_table()

        # Skin Rings
        shaft_faces = []
        is_fluted = (self.flute_depth > 0.001)

        for i in range(len(shaft_rings_verts) - 1):
            ring_bot = shaft_rings_verts[i]
            ring_top = shaft_rings_verts[i+1]
            num_v = len(ring_bot)

            for j in range(num_v):
                v1 = ring_bot[j]
                v2 = ring_bot[(j + 1) % num_v] # Next in ring
                v3 = ring_top[(j + 1) % num_v] # Next in top ring
                v4 = ring_top[j]               # Current in top ring

                f = bm.faces.new((v1, v2, v3, v4))
                f.material_index = 0
                shaft_faces.append(f)

                # Mark Vertical Edges (Detail/Sharpness)
                # Vertical edge is v4-v1 (the one connecting rings at index j)
                # No, v4 is top ring j, v1 is bot ring j.
                # The edge connecting them is explicitly created or found?
                # When face is created, edges are created/found.
                # We need to find the vertical edges on this face.

                for e in f.edges:
                    # Check if vertical
                    ev = e.verts
                    is_vertical = False
                    if (ev[0] in ring_bot and ev[1] in ring_top) or \
                       (ev[1] in ring_bot and ev[0] in ring_top):
                        is_vertical = True

                    if is_vertical and is_fluted:
                        e[edge_slots] = 2 # Detail
                        # Sharpness Logic: Even index (j) is Peak (Sharp), Odd is Valley (Smooth)
                        # v1 is ring_bot[j]. So we check j.
                        # Wait, edge v4-v1 corresponds to index j.
                        # Edge v3-v2 corresponds to index j+1.
                        # Let's identify which vertical edge this is.
                        if (ev[0] == v1 and ev[1] == v4) or (ev[0] == v4 and ev[1] == v1):
                             # This is edge at index j
                             if j % 2 == 0: e.smooth = False
                             else: e.smooth = True
                        elif (ev[0] == v2 and ev[1] == v3) or (ev[0] == v3 and ev[1] == v2):
                             # This is edge at index j+1
                             if (j + 1) % 2 == 0: e.smooth = False
                             else: e.smooth = True

        # UVs for Shaft
        uv_s = self.uv_scale
        bm.faces.ensure_lookup_table()
        
        for f in shaft_faces:
            for l in f.loops:
                v = l.vert.co
                # Angle 0..1
                angle = math.atan2(v.y, v.x)
                if angle < 0: angle += 2 * math.pi
                u = angle / (2 * math.pi)

                # Height map 0..1
                v_coord = (v.z - shaft_bot_z) / shaft_h

                # Aspect Ratio Correction:
                # Circumference approx = 2 * pi * radius
                # Height = shaft_h
                # Usually we want square UVs.
                # u goes 0..1 (Circumference). v goes 0..1 (Height).
                # To make texture square: u * (Circumference / Unit), v * (Height / Unit)
                l[uv_layer].uv = (u * uv_s * 3.0, v_coord * uv_s * (shaft_h / base_radius))

            # Seam fix
            us = [l[uv_layer].uv[0] for l in f.loops]
            if max(us) - min(us) > 0.5: # Wrapped face
                for l in f.loops:
                    if l[uv_layer].uv[0] < 0.5:
                        l[uv_layer].uv = (l[uv_layer].uv[0] + 1.0, l[uv_layer].uv[1])

        # --- STEP 2: CAPS ---
        def build_cap(z_start, z_end, r_scale):
            # Simple Cylinder for Cap
            c_coords_bot = get_ring_coords(z_start, base_radius * r_scale, is_fluted=False)
            c_coords_top = get_ring_coords(z_end, base_radius * r_scale, is_fluted=False)
            
            bm_cv_bot = [bm.verts.new(v) for v in c_coords_bot]
            bm_cv_top = [bm.verts.new(v) for v in c_coords_top]
            
            # Side Faces
            cap_side_faces = []
            n = len(bm_cv_bot)
            for i in range(n):
                f = bm.faces.new((
                    bm_cv_bot[i],
                    bm_cv_bot[(i+1)%n],
                    bm_cv_top[(i+1)%n],
                    bm_cv_top[i]
                ))
                f.material_index = 1
                cap_side_faces.append(f)
                
            # Fill Top/Bottom
            f_bot = bm.faces.new(reversed(bm_cv_bot))
            f_top = bm.faces.new(bm_cv_top)
            f_bot.material_index = 1
            f_top.material_index = 1
            
            # UVs for Caps
            for f in cap_side_faces:
                 for l in f.loops:
                    v = l.vert.co
                    angle = math.atan2(v.y, v.x)
                    if angle < 0: angle += 2 * math.pi
                    u = angle / (2 * math.pi)
                    v_c = (v.z - z_start) / (z_end - z_start)
                    l[uv_layer].uv = (u * uv_s, v_c * uv_s)

                 us = [l[uv_layer].uv[0] for l in f.loops]
                 if max(us) - min(us) > 0.5:
                    for l in f.loops:
                        if l[uv_layer].uv[0] < 0.5:
                            l[uv_layer].uv = (l[uv_layer].uv[0] + 1.0, l[uv_layer].uv[1])
            
            for f in [f_bot, f_top]:
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * uv_s, l.vert.co.y * uv_s)

        # Base
        build_cap(0, c_h, self.cap_scale)
        
        # Capital
        top_r_scale = self.taper_ratio * self.cap_scale
        build_cap(h - c_h, h, top_r_scale)

        # Cleanup
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def execute(self, context):
        rt = super().execute(context)
        if "FINISHED" in rt:
            obj = context.active_object

            def ensure_socket(name_suffix, loc_local, rot_euler):
                s_name = f"SOCKET_{obj.name}_{name_suffix}"
                sock = None
                for child in obj.children:
                    if child.name.startswith(f"SOCKET_{obj.name}") and name_suffix in child.name:
                        sock = child
                        break

                if not sock:
                    sock = bpy.data.objects.new(s_name, None)
                    sock.empty_display_type = 'ARROWS'
                    sock.empty_display_size = 0.2
                    context.collection.objects.link(sock)
                    sock.parent = obj

                sock.location = loc_local
                sock.rotation_euler = rot_euler

            # Bottom Socket (Up)
            ensure_socket("Bottom", (0, 0, 0), (0, 0, 0))

            # Top Socket (Up for stacking)
            h = self.height
            ensure_socket("Top", (0, 0, h), (0, 0, 0))

        return rt
