import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_23: Cable Tray (Ladder)",
    "id": "prim_23_cable_tray",
    "icon": "MOD_LATTICE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
    },
}

class MASSA_OT_PrimCableTray(Massa_OT_Base):
    bl_idname = "massa.gen_prim_23_cable_tray"
    bl_label = "PRIM_23: Cable Tray"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=0.6, min=0.1)
    height: FloatProperty(name="Height (Z)", default=0.1, min=0.02)
    length: FloatProperty(name="Length (Y)", default=2.0, min=0.1)
    
    rail_thick: FloatProperty(name="Rail Thickness", default=0.01, min=0.002)
    flange_size: FloatProperty(name="Rail Flange", default=0.015, min=0.0)
    
    rung_spacing: FloatProperty(name="Rung Spacing", default=0.3, min=0.1)
    rung_width: FloatProperty(name="Rung Width", default=0.03, min=0.01)
    rung_height: FloatProperty(name="Rung Height", default=0.015, min=0.005)
    
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Tray Metal", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "length")
        
        layout.separator()
        layout.label(text="RAILS")
        col.prop(self, "rail_thick")
        col.prop(self, "flange_size")
        
        layout.separator()
        layout.label(text="RUNGS")
        col.prop(self, "rung_spacing")
        col.prop(self, "rung_width")
        col.prop(self, "rung_height")

        layout.separator()
        layout.label(text="UV")
        col.prop(self, "uv_scale")
        col.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        w = max(0.1, self.width)
        h = max(0.02, self.height)
        l = max(0.1, self.length)
        rt = min(max(0.002, self.rail_thick), h * 0.4, w * 0.2)
        rf = min(max(0.0, self.flange_size), max(0.0, (w - rt) * 0.45))

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

        def mark_cap_face(f):
            for e in f.edges:
                mark_edge(e, slot=1, seam=True, sharp=True, protect=True)

        def mark_hard_contours(faces):
            edges = {e for f in faces for e in f.edges if e.is_valid and len(e.link_faces) == 2}
            for e in edges:
                if e[edge_slots] in {1, 3}:
                    continue
                try:
                    angle = e.calc_face_angle(0.0)
                except ValueError:
                    continue
                if angle > 0.785:
                    mark_edge(e, slot=2, sharp=True)
        
        # 1. Side Rails (C-Channel Profile pointing inwards)
        # Profile on XZ plane
        # Left Rail (at -w/2): Open to +X
        # Right Rail (at +w/2): Open to -X
        
        def create_rail(x_pos, scale_x):
            # Profile:
            #   Top Flange
            #   |
            #   Web
            #   |
            #   Bottom Flange
            
            # Verts (relative to center of rail web)
            # Center of rail wall is x_pos
            # Flanges extend inwards by rf
            
            # Simple C shape
            #    0____1
            #    |5__4|
            #    | |
            #    | |
            #    |6__7|
            #    3____2
            
            # Just use 2 boxes per rail? Or extrude profile?
            # Extrude profile is cleaner.
            
            # Local coords
            l_verts = []
            l_verts.append((-rt, h/2))    # 0
            l_verts.append((rf, h/2))     # 1
            l_verts.append((rf, h/2 - rt))# 2
            l_verts.append((0, h/2 - rt)) # 3
            l_verts.append((0, -h/2 + rt))# 4
            l_verts.append((rf, -h/2 + rt))# 5
            l_verts.append((rf, -h/2))    # 6
            l_verts.append((-rt, -h/2))   # 7
            
            # Flip X if right rail
            final_verts = []
            for vx, vy in l_verts:
                final_verts.append((vx * scale_x + x_pos, 0, vy))
                
            # Create Face
            bm_verts = [bm.verts.new(v) for v in final_verts]
            bm.verts.ensure_lookup_table()
            # Ensure correct winding?
            # Left Rail (scale_x=1): CCW
            # Right Rail (scale_x=-1): Points flipped X, winding might flip
            if scale_x < 0:
                bm_verts.reverse()
                
            try:
                f = bm.faces.new(bm_verts)
                # Extrude
                res = bmesh.ops.extrude_face_region(bm, geom=[f])
                ext_verts = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, verts=ext_verts, vec=(0, l, 0))
                rail_faces = [f] + [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]

                bm.normal_update()
                for face in rail_faces:
                    if abs(face.calc_center_median().y) < 0.001 or abs(face.calc_center_median().y - l) < 0.001:
                        mark_cap_face(face)

                seam_x = x_pos - rt if scale_x > 0 else x_pos + rt
                seam_z = -h / 2
                for e in {edge for face in rail_faces for edge in face.edges if edge.is_valid}:
                    v1, v2 = e.verts
                    on_bottom_zipper = (
                        abs(v1.co.x - seam_x) < 0.001
                        and abs(v2.co.x - seam_x) < 0.001
                        and abs(v1.co.z - seam_z) < 0.001
                        and abs(v2.co.z - seam_z) < 0.001
                    )
                    if on_bottom_zipper:
                        mark_edge(e, slot=3, seam=True, protect=True)

                mark_hard_contours(rail_faces)
            except ValueError:
                loose = [v for v in bm_verts if v.is_valid and not v.link_edges]
                if loose:
                    bmesh.ops.delete(bm, geom=loose, context="VERTS")

        # Create Rails
        create_rail(-w/2 + rt/2, 1) # Left
        create_rail(w/2 - rt/2, -1) # Right
        
        # 2. Rungs
        if self.rung_spacing > 0:
            count = int(l / self.rung_spacing)
            step = l / (count + 1)
            rw = min(max(0.005, self.rung_width), max(0.005, step * 0.65))
            rh_ = min(max(0.002, self.rung_height), max(0.002, h - rt - 0.002))
            
            # Rung width: spans between rails
            # Distance: w - 2*rt
            clearance = 0.001
            rung_len = max(0.001, w - rt - (rf * 2.0) - (clearance * 2.0))
            
            if rung_len >= 0.01:
                for i in range(1, count + 1):
                    y = i * step
                    # Box
                    res = bmesh.ops.create_cube(bm, size=1.0)
                    rv = res["verts"]
                    bmesh.ops.scale(bm, vec=(rung_len, rw, rh_), verts=rv)
                    # Keep rungs above the lower flanges so they do not leave hidden overlap faces.
                    z_pos = -h/2 + rt + rh_/2 + clearance
                    bmesh.ops.translate(bm, vec=(0, y, z_pos), verts=rv)
                    rung_faces = list({f for v in rv for f in v.link_faces if f.is_valid})

                    bm.normal_update()
                    for f in rung_faces:
                        if abs(f.normal.x) > 0.9:
                            mark_cap_face(f)

                    bottom_y = y - (rw * 0.5)
                    bottom_z = z_pos - (rh_ * 0.5)
                    for e in {edge for face in rung_faces for edge in face.edges if edge.is_valid}:
                        v1, v2 = e.verts
                        along_x = abs(v1.co.x - v2.co.x) > max(rung_len * 0.5, 0.001)
                        on_hidden_bottom_back = (
                            along_x
                            and abs(v1.co.y - bottom_y) < 0.001
                            and abs(v2.co.y - bottom_y) < 0.001
                            and abs(v1.co.z - bottom_z) < 0.001
                            and abs(v2.co.z - bottom_z) < 0.001
                        )
                        if on_hidden_bottom_back:
                            mark_edge(e, slot=3, seam=True, protect=True)

                    mark_hard_contours(rung_faces)

        # Mat
        for f in bm.faces:
            f.material_index = 0
            
        loose_verts = [v for v in bm.verts if v.is_valid and not v.link_edges]
        if loose_verts:
            bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")

        wire_edges = [e for e in bm.edges if e.is_valid and not e.link_faces]
        if wire_edges:
            bmesh.ops.delete(bm, geom=wire_edges, context="EDGES")

        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
        bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        uv_layer = bm.loops.layers.uv.verify()
        uv_data = []
        for f in bm.faces:
            nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
            for loop in f.loops:
                co = loop.vert.co
                if nz >= nx and nz >= ny:
                    u, v = co.x, co.y
                elif nx >= ny:
                    u, v = co.y, co.z
                else:
                    u, v = co.x, co.z
                uv_data.append((loop, u, v))

        if self.fit_uvs and uv_data:
            min_u = min(u for _, u, _ in uv_data)
            min_v = min(v for _, _, v in uv_data)
            max_u = max(u for _, u, _ in uv_data)
            max_v = max(v for _, _, v in uv_data)
            size_u = max(max_u - min_u, 0.0001)
            size_v = max(max_v - min_v, 0.0001)
            for loop, u, v in uv_data:
                loop[uv_layer].uv = ((u - min_u) / size_u, (v - min_v) / size_v)
        else:
            scale = self.uv_scale
            for loop, u, v in uv_data:
                loop[uv_layer].uv = (u * scale, v * scale)
