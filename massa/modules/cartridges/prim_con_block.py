import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

# ==============================================================================
# MASSA CARTRIDGE: CONSTRUCTION BLOCK (Y-AXIS ORIENTATION)
# ID: prim_con_block
# ==============================================================================

CARTRIDGE_META = {
    "name": "Con: Block",
    "id": "prim_con_block",
    "icon": "MESH_GRID",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_block(Massa_OT_Base):
    """
    Operator to generate a primitive construction block (CMU style) with configurable cores,
    dimensions, and segmentation.
    """

    bl_idname = "massa.gen_prim_con_block"
    bl_label = "Construction Block"
    bl_description = "CMU with Holes along Y-Axis"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- Properties ---
    length: FloatProperty(name="Length", default=0.4, unit="LENGTH")
    width: FloatProperty(name="Width", default=0.2, unit="LENGTH")
    height: FloatProperty(name="Height", default=0.2, unit="LENGTH")
    wall_th: FloatProperty(name="Wall Thickness", default=0.035, unit="LENGTH")
    cores: IntProperty(name="Cores", default=2, min=1, max=3)

    # --- Topology / SubD Controls ---
    seg_x: IntProperty(name="Seg X", default=4, min=1, description="Length Cuts")
    seg_y: IntProperty(name="Seg Y", default=2, min=1, description="Width Cuts")
    seg_z: IntProperty(name="Seg Z", default=2, min=1, description="Height Cuts")
    
    # --- UV Controls ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.01)
    fit_uvs: bpy.props.BoolProperty(name="Fit UVs", default=False)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Block Size", icon="CUBE")
        box.prop(self, "length")
        box.prop(self, "width")
        box.prop(self, "height")

        box = layout.box()
        box.label(text="Structure", icon="MOD_WIREFRAME")
        box.prop(self, "wall_th")
        box.prop(self, "cores")

        box = layout.box()
        box.label(text="SubD Topology", icon="MESH_GRID")
        row = box.row(align=True)
        row.prop(self, "seg_x", text="X")
        row.prop(self, "seg_y", text="Y")
        row.prop(self, "seg_z", text="Z")
        
        box = layout.box()
        box.label(text="UV Mapping", icon="UV_DATA")
        row = box.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs", toggle=True)

    def get_slot_meta(self):
        # Update UV mode to SKIP for explicit manual UV mapping
        return {0: {"name": "Concrete", "uv": "SKIP", "phys": "CONCRETE_BLOCK"}}

    def build_shape(self, bm):
        # 1. SETUP PARAMETERS
        l = max(0.01, getattr(self, "length", 0.4))
        w = max(0.01, getattr(self, "width", 0.2))  # Extrusion Depth (Y)
        h = max(0.01, getattr(self, "height", 0.2))  # Grid Height (Z)

        cores = max(1, getattr(self, "cores", 2))
        th = max(0.001, min(l / (cores + 1.1), h / 2.1, getattr(self, "wall_th", 0.035)))

        seg_x = getattr(self, "seg_x", 4)
        seg_y = getattr(self, "seg_y", 2)
        seg_z = getattr(self, "seg_z", 2)

        # Calculate Core Dimensions (Along X)
        total_void_l = l - (th * (cores + 1))
        core_l = total_void_l / cores

        # 2. DEFINE BASE GRID (XZ Plane at Y=0)
        z_coords = [
            -h / 2,  # Bottom
            -h / 2 + th,  # Inner Bottom
            0.0,  # CENTERLINE (Z-Axis Slice)
            h / 2 - th,  # Inner Top
            h / 2,  # Top
        ]

        x_coords = []
        current_x = -l / 2
        x_coords.append(current_x)

        for i in range(cores):
            current_x += th
            x_coords.append(current_x)
            current_x += core_l
            x_coords.append(current_x)

        current_x += th
        x_coords.append(current_x)

        # 3. GENERATE VERTEX GRID (XZ Plane)
        grid_verts = []
        for x_val in x_coords:
            col = []
            for z_val in z_coords:
                col.append(bm.verts.new((x_val, 0, z_val)))
            grid_verts.append(col)

        # 4. SKINNING (XZ Faces)
        base_faces = []
        for i in range(len(x_coords) - 1):
            for j in range(len(z_coords) - 1):
                # Void Logic: X odd = Hole, Z middle (1,2) = Hole
                x_is_hole = i % 2 != 0
                z_is_hole = j == 1 or j == 2

                if not (x_is_hole and z_is_hole):
                    v1 = grid_verts[i][j]
                    v2 = grid_verts[i + 1][j]
                    v3 = grid_verts[i + 1][j + 1]
                    v4 = grid_verts[i][j + 1]
                    base_faces.append(bm.faces.new((v1, v2, v3, v4)))

        # 5. EXTRUDE (Y-Axis)
        ret = bmesh.ops.extrude_face_region(bm, geom=base_faces)
        geom_generated = ret["geom"]
        verts_extruded = [
            v for v in geom_generated if isinstance(v, bmesh.types.BMVert)
        ]

        # Move BASE verts to start position (-w/2)
        base_verts = [v for col in grid_verts for v in col]
        bmesh.ops.translate(bm, verts=base_verts, vec=(0, -w / 2, 0))

        # Move EXTRUDED verts to end position (+w/2)
        bmesh.ops.translate(bm, verts=verts_extruded, vec=(0, w, 0))

        # 6. SUBD SEGMENTATION PASS
        # Slice Length (X)
        if seg_x > 1:
            step = l / seg_x
            start = -l / 2
            for i in range(1, seg_x):
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(start + i * step, 0, 0),
                    plane_no=(1, 0, 0),
                )

        # Slice Width (Y)
        if seg_y > 1:
            step = w / seg_y
            start = -w / 2
            for i in range(1, seg_y):
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(0, start + i * step, 0),
                    plane_no=(0, 1, 0),
                )

        # Slice Height (Z)
        if seg_z > 1:
            step = h / seg_z
            start = -h / 2
            for i in range(1, seg_z):
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(0, 0, start + i * step),
                    plane_no=(0, 0, 1),
                )

        # 7. CLEANUP & NORMALS
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        
        faces_small = [f for f in bm.faces if f.calc_area() < 0.000001]
        if faces_small:
            bmesh.ops.delete(bm, geom=faces_small, context='FACES')
            
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 8. SEAMING STRATEGY
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
            
        force_seam = bm.edges.layers.int.get("massa_force_seam")
        if not force_seam:
            force_seam = bm.edges.layers.int.new("massa_force_seam")
            
        def mark_edge(e, slot=None, seam=False, sharp=False, protect=False):
            if slot is not None:
                e[edge_slots] = slot
            if seam:
                e.seam = True
            if sharp:
                e.smooth = False
            if protect:
                e[force_seam] = 1

        # Clear existing
        for e in bm.edges:
            e.seam = False
            e.smooth = True
            e[edge_slots] = 0

        # A. CAP IDENTIFICATION (Normal Y)
        cap_faces = set([f for f in bm.faces if abs(f.normal.y) > 0.8])
        cap_edges = set()
        for f in cap_faces:
            for e in f.edges:
                # Only mark perimeter edges of the cap (where the edge connects a cap face to a non-cap face)
                link_caps = sum(1 for lf in e.link_faces if lf in cap_faces)
                if link_caps == 1:
                    cap_edges.add(e)
                    mark_edge(e, slot=1, seam=True, sharp=True, protect=True)

        # B. MARK SHARP CONTOURS (90 degree angles)
        for e in bm.edges:
            if e not in cap_edges and e.is_manifold and len(e.link_faces) == 2:
                try:
                    if e.calc_face_angle(0.0) > math.radians(80):
                        mark_edge(e, slot=2, sharp=True)
                except ValueError:
                    pass

        # C. SMART ZIPPERS (Vertical Cuts)
        wall_faces = set(bm.faces) - set(cap_faces)
        
        # Group wall faces into islands
        islands = []
        visited = set()
        for f in wall_faces:
            if f not in visited:
                island = set()
                stack = [f]
                while stack:
                    curr = stack.pop()
                    if curr not in visited:
                        visited.add(curr)
                        island.add(curr)
                        for e in curr.edges:
                            if e not in cap_edges:
                                for lf in e.link_faces:
                                    if lf in wall_faces and lf not in visited:
                                        stack.append(lf)
                islands.append(island)
                
        # For each island, pick a zipper path from front cap to back cap.
        for island in islands:
            island_edges = {e for f in island for e in f.edges if e not in cap_edges}
            island_y_edges = [
                e for e in island_edges
                if abs((e.verts[1].co - e.verts[0].co).normalized().y) > 0.9
            ]
            
            if not island_y_edges:
                continue
                
            # Prefer edges that are sharp corners for the zipper to hide the seam
            def is_sharp_enough(e):
                if not e.is_manifold or len(e.link_faces) != 2:
                    return False
                try:
                    return e.calc_face_angle(0.0) > math.radians(45)
                except ValueError:
                    return False

            sharp_y_edges = [e for e in island_y_edges if is_sharp_enough(e)]
            candidate_edges = sharp_y_edges if sharp_y_edges else island_y_edges
                
            # Group into pillars
            pillars = {}
            for e in candidate_edges:
                mid = (e.verts[0].co + e.verts[1].co) / 2
                key = (round(mid.x, 3), round(mid.z, 3))
                if key not in pillars:
                    pillars[key] = []
                pillars[key].append(e)
                
            if pillars:
                # Pick the pillar with the lowest Z, then lowest X
                zipper_key = min(pillars.keys(), key=lambda k: (k[1], k[0]))
                for e in pillars[zipper_key]:
                    mark_edge(e, slot=3, seam=True, protect=True)

        # 9. MANUAL UV MAPPING (SKIP Mode)
        uv_layer = bm.loops.layers.uv.verify()
        
        su = self.uv_scale
        sv = self.uv_scale
        fit = self.fit_uvs
        
        for f in cap_faces:
            for loop in f.loops:
                u = loop.vert.co.x
                v = loop.vert.co.z
                if fit:
                    u = (u + l/2) / l
                    v = (v + h/2) / h
                else:
                    u *= su
                    v *= sv
                loop[uv_layer].uv = (u, v)
                
        def get_tube_u(x, z, min_x, max_x, min_z, max_z):
            eps = 0.001
            w_x = max_x - min_x
            w_z = max_z - min_z
            if abs(z - min_z) < eps: return x - min_x
            elif abs(x - max_x) < eps: return w_x + (z - min_z)
            elif abs(z - max_z) < eps: return w_x + w_z + (max_x - x)
            elif abs(x - min_x) < eps: return w_x + w_z + w_x + (max_z - z)
            return 0.0

        for island in islands:
            min_x = min(v.co.x for f in island for v in f.verts)
            max_x = max(v.co.x for f in island for v in f.verts)
            min_z = min(v.co.z for f in island for v in f.verts)
            max_z = max(v.co.z for f in island for v in f.verts)
            perim = 2 * (max_x - min_x) + 2 * (max_z - min_z)
            
            for f in island:
                loop_uvs = []
                for loop in f.loops:
                    u = get_tube_u(loop.vert.co.x, loop.vert.co.z, min_x, max_x, min_z, max_z)
                    v = loop.vert.co.y
                    loop_uvs.append([loop, u, v])
                
                # Fix wrapping seam
                us = [item[1] for item in loop_uvs]
                if max(us) - min(us) > perim * 0.5:
                    for item in loop_uvs:
                        if item[1] < perim * 0.5:
                            item[1] += perim
                            
                for loop, u, v in loop_uvs:
                    if fit:
                        u = u / perim if perim > 0 else 0
                        v = (v + w/2) / w
                    else:
                        u *= su
                        v *= sv
                    loop[uv_layer].uv = (u, v)
