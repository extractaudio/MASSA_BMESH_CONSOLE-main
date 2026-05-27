import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ASM_07: Vending Machine",
    "id": "asm_07_vending",
    "icon": "MOD_BOOLEAN",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "FIX_DEGENERATE": True,
        "REMOVE_LOOSE": True,
    },
}

class MASSA_OT_AsmVending(Massa_OT_Base):
    bl_idname = "massa.gen_asm_07_vending"
    bl_label = "ASM_07: Vending Machine"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=1.2, min=0.8)
    depth: FloatProperty(name="Depth (Y)", default=0.8, min=0.5)
    height: FloatProperty(name="Height (Z)", default=2.0, min=1.5)

    shelves_count: IntProperty(name="Shelves", default=5, min=1)
    inset_depth: FloatProperty(name="Inset Depth", default=0.1, min=0.05)
    
    screen_height: FloatProperty(name="Screen Height", default=0.3, min=0.1, max=0.8)
    buttons_columns: IntProperty(name="Button Columns", default=3, min=1, max=5)
    buttons_rows: IntProperty(name="Button Rows", default=4, min=1, max=6)
    
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Chassis", "uv": "SKIP", "phys": "PLASTIC"},
            1: {"name": "Glass Display", "uv": "FIT", "phys": "GLASS_PANE"},
            2: {"name": "Delivery Chute", "uv": "SKIP", "phys": "METAL_PAINTED"},
            3: {"name": "Shelves", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            4: {"name": "Screen", "uv": "FIT", "phys": "GENERIC"},
            5: {"name": "Buttons", "uv": "SKIP", "phys": "RUBBER"},
            9: {"name": "Socket Base", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")

        layout.separator()
        layout.label(text="DETAILS", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "shelves_count")
        col.prop(self, "inset_depth")
        
        layout.separator()
        layout.label(text="INTERFACE", icon="RESTRICT_SELECT_OFF")
        col = layout.column(align=True)
        col.prop(self, "screen_height")
        col.prop(self, "buttons_columns")
        col.prop(self, "buttons_rows")

    def build_shape(self, bm: bmesh.types.BMesh):
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        if not bm.edges.layers.int.get("massa_force_seam"):
            bm.edges.layers.int.new("massa_force_seam")
            
        w, d, h = self.width, self.depth, self.height
        
        inset = min(self.inset_depth, w * 0.15, h * 0.15)
        inset = max(inset, 0.01)

        # 1. GENERATE FRONT PANEL GRID
        x_divs = [
            -w/2,
            -w/2 + inset,
            w/2 - 0.35*w,
            w/2 - inset,
            w/2
        ]
        for i in range(1, len(x_divs)):
            if x_divs[i] <= x_divs[i-1]:
                x_divs[i] = x_divs[i-1] + 0.001
        
        h_chute = max(0.15 * h, 0.01)
        h_buttons = max(0.30 * h, 0.01)
        space_left = (h - inset) - (h_chute + h_buttons)
        h_screen = min(self.screen_height, space_left - 0.01)
        h_screen = max(h_screen, 0.01)
        
        z_divs = [
            0.0,
            h_chute,
            h_chute + h_buttons,
            h_chute + h_buttons + h_screen,
            max(h_chute + h_buttons + h_screen + 0.01, h - inset),
            max(h_chute + h_buttons + h_screen + 0.02, h)
        ]
        for i in range(1, len(z_divs)):
            if z_divs[i] <= z_divs[i-1]:
                z_divs[i] = z_divs[i-1] + 0.001

        verts = []
        for z in z_divs:
            row = []
            for x in x_divs:
                row.append(bm.verts.new((x, d/2, z)))
            verts.append(row)
        bm.verts.ensure_lookup_table()

        back_faces = []
        for r in range(len(z_divs)-1):
            for c in range(len(x_divs)-1):
                f = bm.faces.new((verts[r][c], verts[r][c+1], verts[r+1][c+1], verts[r+1][c]))
                back_faces.append(f)
        
        bmesh.ops.reverse_faces(bm, faces=back_faces)
        
        for f in back_faces:
            f.material_index = 0

        # 2. EXTRUDE MAIN BODY
        res_ext = bmesh.ops.extrude_face_region(bm, geom=back_faces)
        extruded_verts = [v for v in res_ext['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=extruded_verts, vec=(0, -d, 0))
        
        # 3. IDENTIFY FRONT FACES
        bm.faces.ensure_lookup_table()
        front_faces = [f for f in bm.faces if abs(f.calc_center_median().y - (-d/2)) < 0.001]
        
        chute_face = None
        display_faces = []
        buttons_face = None
        screen_face = None
        
        for f in front_faces:
            f.material_index = 0
            cx = f.calc_center_median().x
            cz = f.calc_center_median().z
            
            col = -1
            if x_divs[0] < cx < x_divs[1]: col = 0
            elif x_divs[1] < cx < x_divs[2]: col = 1
            elif x_divs[2] < cx < x_divs[3]: col = 2
            elif x_divs[3] < cx < x_divs[4]: col = 3
            
            row = -1
            if z_divs[0] <= cz < z_divs[1]: row = 0
            elif z_divs[1] <= cz < z_divs[2]: row = 1
            elif z_divs[2] <= cz < z_divs[3]: row = 2
            elif z_divs[3] <= cz < z_divs[4]: row = 3
            elif z_divs[4] <= cz <= z_divs[5]: row = 4
            
            if col == 1 and row == 0: chute_face = f
            elif col == 1 and row in [1, 2, 3]: display_faces.append(f)
            elif col == 2 and row == 1: buttons_face = f
            elif col == 2 and row == 2: screen_face = f

        # 4. MODIFY COMPONENTS
        if chute_face and chute_face.is_valid and chute_face.calc_area() > 0.0001:
            res = bmesh.ops.extrude_face_region(bm, geom=[chute_face])
            extruded_verts = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=(0, max(self.inset_depth * 1.5, 0.15), 0), verts=extruded_verts)
            for f in res['geom']:
                if isinstance(f, bmesh.types.BMFace) and f.is_valid:
                    f.material_index = 2 if f.normal.y > 0.9 else 0
            
        valid_display_faces = [f for f in display_faces if f.is_valid and f.calc_area() > 0.0001]
        if valid_display_faces:
            res = bmesh.ops.extrude_face_region(bm, geom=valid_display_faces)
            extruded_verts = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=(0, max(self.inset_depth, 0.1), 0), verts=extruded_verts)
            
            new_display_faces = []
            for f in res['geom']:
                if isinstance(f, bmesh.types.BMFace) and f.is_valid:
                    if f.normal.y > 0.9:
                        f.material_index = 1
                        new_display_faces.append(f)
                    else:
                        f.material_index = 0
            
            if self.shelves_count > 0:
                shelf_edges = []
                for e in bm.edges:
                    if not e.is_valid: continue
                    if len(e.link_faces) == 2:
                        try:
                            if e.link_faces[0].is_valid and e.link_faces[1].is_valid:
                                if e.link_faces[0] in new_display_faces and e.link_faces[1] in new_display_faces:
                                    shelf_edges.append(e)
                        except ReferenceError:
                            pass
                if shelf_edges:
                    res_shelf = bmesh.ops.extrude_edge_only(bm, edges=shelf_edges)
                    shelf_verts = [v for v in res_shelf['geom'] if isinstance(v, bmesh.types.BMVert)]
                    bmesh.ops.translate(bm, vec=(0, d*0.2, 0), verts=shelf_verts)
                    for f in res_shelf['geom']:
                        if isinstance(f, bmesh.types.BMFace) and f.is_valid:
                            f.material_index = 3
                            
        if screen_face and screen_face.is_valid and screen_face.calc_area() > 0.0001:
            res = bmesh.ops.extrude_face_region(bm, geom=[screen_face])
            extruded_verts = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=(0, -0.05, 0), verts=extruded_verts) # Protrude outward
            for f in res['geom']:
                if isinstance(f, bmesh.types.BMFace) and f.is_valid:
                    f.material_index = 4 if f.normal.y < -0.9 else 0
            
        if buttons_face and buttons_face.is_valid and buttons_face.calc_area() > 0.0001:
            res_btn = bmesh.ops.inset_individual(bm, faces=[buttons_face], thickness=0.02, depth=0)
            if res_btn['faces']:
                inner_btn = res_btn['faces'][0]
                
                res_ext = bmesh.ops.extrude_face_region(bm, geom=[inner_btn])
                extruded_verts = [v for v in res_ext['geom'] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, vec=(0, -0.05, 0), verts=extruded_verts) # Protrude outward
                
                inner_btn = None
                for f in res_ext['geom']:
                    if isinstance(f, bmesh.types.BMFace) and f.is_valid:
                        if f.normal.y < -0.9:
                            f.material_index = 0
                            inner_btn = f
                        else:
                            f.material_index = 0
                
                if not inner_btn:
                    faces = [f for f in res_ext['geom'] if isinstance(f, bmesh.types.BMFace) and f.is_valid]
                    if faces: inner_btn = faces[0]
                
                if inner_btn and inner_btn.is_valid:
                    cols = self.buttons_columns
                    rows = self.buttons_rows
                    bcx = inner_btn.calc_center_median().x
                    bcy = inner_btn.calc_center_median().y
                    bcz = inner_btn.calc_center_median().z
                    
                    vs = list(inner_btn.verts)
                    min_x = min(v.co.x for v in vs)
                    max_x = max(v.co.x for v in vs)
                    min_z = min(v.co.z for v in vs)
                    max_z = max(v.co.z for v in vs)
                    bw = max((max_x - min_x) * 0.8, 0.01)
                    bh = max((max_z - min_z) * 0.8, 0.01)
                    
                    start_x = bcx - bw/2
                    start_z = bcz + bh/2
                    step_x = bw / max(1, cols)
                    step_z = bh / max(1, rows)
                    
                    builder = MassaBuilder(bm)
                    for r in range(rows):
                        for c in range(cols):
                            bx = start_x + c*step_x + step_x/2
                            bz = start_z - r*step_z - step_z/2
                            builder.create_box(width=max(step_x*0.6, 0.001), depth=0.04, height=max(step_z*0.6, 0.001), center=Vector((bx, bcy - 0.02, bz)))
                            builder.tag_slot(5)

        # 5. SOCKET ANCHOR
        builder = MassaBuilder(bm)
        builder.create_grid(size=0.1, center=Vector((0, 0, 0)))
        builder.rotate(180, axis='Y')
        builder.translate(0, -d/2 + 0.1, 0)
        builder.tag_slot(9)
        builder.tag_socket(9)

        # 6. EDGE SLOTS & SEAMS
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
            
        force_seam = bm.edges.layers.int.get("massa_force_seam")
        if not force_seam:
            force_seam = bm.edges.layers.int.new("massa_force_seam")

        for e in bm.edges:
            if not e.is_valid or not e.is_manifold:
                continue
            if len(e.link_faces) == 2:
                try:
                    angle = e.calc_face_angle(0.0)
                    if angle > math.radians(60):
                        e[edge_slots] = 2 
                except (ValueError, ReferenceError):
                    pass
            
            v1, v2 = e.verts[0], e.verts[1]
            if abs(v1.co.y - d/2) < 0.001 and abs(v2.co.y - d/2) < 0.001:
                # Topological check: Edge on the perimeter connects exactly one back-facing face
                back_faces = [f for f in e.link_faces if f.normal.y > 0.9]
                if len(back_faces) == 1:
                    e.seam = True
                    e[force_seam] = 1

        # 7. UV MAPPING
        uv_layer = bm.loops.layers.uv.verify()
        
        for f in bm.faces:
            if not f.is_valid:
                continue
                
            if f.material_index in [1, 4]: 
                u_vals, v_vals = [], []
                n = f.normal
                plane = 'XZ'
                if abs(n.z) >= 0.5: plane = 'XY'
                elif abs(n.x) >= 0.5: plane = 'YZ'
                
                for l in f.loops:
                    v = l.vert.co
                    if plane == 'XY': u_vals.append(v.x); v_vals.append(v.y)
                    elif plane == 'YZ': u_vals.append(v.y); v_vals.append(v.z)
                    else: u_vals.append(v.x); v_vals.append(v.z)
                
                min_u, max_u = min(u_vals), max(u_vals)
                min_v, max_v = min(v_vals), max(v_vals)
                w_u = max_u - min_u
                h_v = max_v - min_v
                
                for l in f.loops:
                    v = l.vert.co
                    if plane == 'XY': uu, vv = v.x, v.y
                    elif plane == 'YZ': uu, vv = v.y, v.z
                    else: uu, vv = v.x, v.z
                    
                    nu = (uu - min_u) / w_u if w_u > 0.0001 else 0.5
                    nv = (vv - min_v) / h_v if h_v > 0.0001 else 0.5
                    l[uv_layer].uv = (nu, nv)
                    
            elif f.material_index == 9: 
                for l in f.loops: l[uv_layer].uv = (0.0, 0.0)
                
            else: 
                scale_val = 1.0 if self.fit_uvs else self.uv_scale
                nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                
                for l in f.loops:
                    if nz > 0.5:
                        u, v = l.vert.co.x, l.vert.co.y
                    elif ny > 0.5:
                        u, v = l.vert.co.x, l.vert.co.z
                    else:
                        u, v = l.vert.co.y, l.vert.co.z
                        
                    l[uv_layer].uv = (u * scale_val, v * scale_val)
