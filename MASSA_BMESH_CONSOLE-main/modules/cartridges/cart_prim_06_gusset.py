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
    
    # --- TOPOLOGY ---
    resolution: IntProperty(name="Resolution", default=16, min=4, max=64)

    def get_slot_meta(self):
        return {
            0: {"name": "Plate Surface", "uv": "SKIP", "phys": "METAL_IRON"},
            1: {"name": "Cut Edges", "uv": "SKIP", "phys": "METAL_IRON"},
            3: {"name": "Guide (Seam)", "uv": "SKIP", "phys": "NONE"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Profile", icon="MESH_DATA")
        layout.prop(self, "shape", text="")
        layout.prop(self, "size")
        layout.prop(self, "thickness")
        layout.prop(self, "resolution")

        layout.separator()
        layout.label(text="Machining", icon="MOD_BOOLEAN")
        layout.prop(self, "has_holes", toggle=True)
        if self.has_holes:
            layout.prop(self, "hole_radius")

    def build_shape(self, bm: bmesh.types.BMesh):
        s = self.size
        t = self.thickness

        # ----------------------------------------------------------------------
        # 0. SETUP
        # ----------------------------------------------------------------------
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # ----------------------------------------------------------------------
        # 1. HELPERS (Ported & Adapted from prim_con_bracket)
        # ----------------------------------------------------------------------
        def create_quad_face(bm, v1, v2, v3, v4):
            # Check for degenerate quads
            if (v1.co - v2.co).length < 1e-6 or (v3.co - v4.co).length < 1e-6:
                return None
            if (v2.co - v3.co).length < 1e-6 or (v4.co - v1.co).length < 1e-6:
                return None
            try:
                return bm.faces.new((v1, v2, v3, v4))
            except ValueError:
                return None # Duplicate verts

        def create_washer_hub(bm, cx, cy, r, segs):
            """
            Creates a washer (hole + surrounding square).
            Returns vertices of the outer square in [TopRight, TopLeft, BotLeft, BotRight] order.
            """
            pad = r * 0.8
            box_r = r + pad
            
            circ_pts = []
            box_pts = []

            for i in range(segs):
                angle = (i / segs) * 2 * math.pi
                # Circle
                circ_pts.append(Vector((cx + math.cos(angle) * r, cy + math.sin(angle) * r, 0)))
                
                # Box (Square projection)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                scale = 1.0 / max(abs(cos_a), abs(sin_a), 0.0001)
                box_pts.append(Vector((cx + cos_a * scale * box_r, cy + sin_a * scale * box_r, 0)))

            # Create Verts
            c_verts = [bm.verts.new(p) for p in circ_pts]
            b_verts = [bm.verts.new(p) for p in box_pts]

            if self.has_holes and r > 0.001:
                # Washer Face Loop
                for i in range(segs):
                    idx_next = (i + 1) % segs
                    f = bm.faces.new((c_verts[i], c_verts[idx_next], b_verts[idx_next], b_verts[i]))
            else:
                # No hole: Cap the center
                bm.faces.new(c_verts) 
                # Bridge box to circle
                for i in range(segs):
                    idx_next = (i + 1) % segs
                    bm.faces.new((c_verts[i], c_verts[idx_next], b_verts[idx_next], b_verts[i]))

            # Return "Ports": Lists of vertices for Top, Left, Bottom, Right sides of the box.
            # Orientation: 0=Right(0rad), 90=Top? 
            # standard cos/sin: 0 is +X (Right).
            # segs=16: 0=R, 4=T, 8=L, 12=B
            
            s2 = segs // 8 # 2 if segs=16
            
            idx_br = (segs - s2) % segs
            idx_tr = s2        # 2
            
            def get_range(start, end):
                ids = []
                curr = start
                while True:
                    ids.append(curr)
                    if curr == end: break
                    curr = (curr + 1) % segs
                return ids
            
            # Right: BR to TR
            ids_right = get_range(idx_br, idx_tr) 
            verts_right = [b_verts[i] for i in ids_right]
            
            # Top: TR to TL
            idx_tl = 3 * s2 # 6
            ids_top = get_range(idx_tr, idx_tl) 
            verts_top = [b_verts[i] for i in ids_top]
            
            # Left: TL to BL
            idx_bl = 5 * s2 # 10
            ids_left = get_range(idx_tl, idx_bl) 
            verts_left = [b_verts[i] for i in ids_left]

            # Bot: BL to BR
            ids_bot = get_range(idx_bl, idx_br)
            verts_bot = [b_verts[i] for i in ids_bot]

            return {
                "R": verts_right, 
                "T": verts_top, 
                "L": verts_left, 
                "B": verts_bot,
                "TR": b_verts[idx_tr],
                "TL": b_verts[idx_tl],
                "BL": b_verts[idx_bl],
                "BR": b_verts[idx_br]
            }

        def bridge_ports(port_a, port_b):
            # Connects two lists of verts with quads. Assumes orientation matches.
            # port_a: [v1, v2, ...]
            # port_b: [u1, u2, ...] (Ordered to match a)
            if len(port_a) != len(port_b):
                return
            for i in range(len(port_a) - 1):
                create_quad_face(bm, port_a[i], port_a[i+1], port_b[i+1], port_b[i])

        def extrude_port_linear(port, target_vec_rel):
             # Extrude port vertices by a vector
            new_verts = []
            for v in port:
                nv = bm.verts.new(v.co + target_vec_rel)
                new_verts.append(nv)
            
            for i in range(len(port) - 1):
                bm.faces.new((port[i], port[i+1], new_verts[i+1], new_verts[i]))
            return new_verts

        def extrude_port_to_x(port, x_val):
            # Projects port to X coordinate
            new_verts = []
            for v in port:
                nv = bm.verts.new(Vector((x_val, v.co.y, 0)))
                new_verts.append(nv)
            for i in range(len(port)-1):
                create_quad_face(bm, port[i], port[i+1], new_verts[i+1], new_verts[i])
            return new_verts

        def extrude_port_to_y(port, y_val):
            # Projects port to Y coordinate
            new_verts = []
            for v in port:
                nv = bm.verts.new(Vector((v.co.x, y_val, 0)))
                new_verts.append(nv)
            for i in range(len(port)-1):
                create_quad_face(bm, port[i], port[i+1], new_verts[i+1], new_verts[i])
            return new_verts

        def extrude_port_to_diagonal(port, size_s):
            # Projects to x + y = size_s -> y = size_s - x
            # Project along Normal (1,1)
            new_verts = []
            
            # For strict projection along (1,0) (Horizontal):
            # x = s - y
            # For strict projection along (0,1) (Vertical):
            # y = s - x
            # For "Shortest Path" (1,1):
            
            # Using Shortest Path for better UV/Topology flow
            for v in port:
                px, py = v.co.x, v.co.y
                t_val = (size_s - px - py) / 2
                dest = Vector((px + t_val, py + t_val, 0))
                new_verts.append(bm.verts.new(dest))
            
            for i in range(len(port)-1):
                create_quad_face(bm, port[i], port[i+1], new_verts[i+1], new_verts[i])
            return new_verts
            
        # ----------------------------------------------------------------------
        # 2. DEFINITION
        # ----------------------------------------------------------------------
        seg = self.resolution 

        # Dimensions
        w = s * 0.3 if self.shape == "L_SHAPE" else s * 0.3 # Base width logic

        # Coordinates
        cx, cy = w/2, w/2
        xx, xy = s - (w/2), w/2
        yx, yy = w/2, s - (w/2)

        if self.shape == "TRIANGLE":
            cx, cy = s*0.25, s*0.25
            r_clamp = self.hole_radius * 2.5
            xx, xy = s*0.7, s*0.1
            yx, yy = s*0.1, s*0.7
            if xy < r_clamp: xy = r_clamp + 0.01
            if yx < r_clamp: yx = r_clamp + 0.01

        r = self.hole_radius
        if not self.has_holes:
            r = 0.01 # Minimal hub size
        
        # Create Hubs
        hub_c = create_washer_hub(bm, cx, cy, r, seg)
        hub_x = create_washer_hub(bm, xx, xy, r, seg)
        hub_y = create_washer_hub(bm, yx, yy, r, seg)

        # ----------------------------------------------------------------------
        # 3. INTERCONNECT (BRIDGE)
        # ----------------------------------------------------------------------
        # Bridge C to X (C Right -> X Left)
        # Reverse X Left order to match C Right (BR->...->TR) vs (TL->...->BL)
        bridge_ports(hub_c["R"], hub_x["L"][::-1])

        # Bridge C to Y (C Top -> Y Bottom)
        # Reverse Y Bottom order to match C Top (TR->...->TL) vs (BL->...->BR)
        bridge_ports(hub_c["T"], hub_y["B"][::-1])

        # ----------------------------------------------------------------------
        # 4. BOUNDARY EXTRUSION
        # ----------------------------------------------------------------------
        
        # Capture generated boundary lines
        c_bot_line = extrude_port_to_y(hub_c["B"], 0)
        c_lef_line = extrude_port_to_x(hub_c["L"], 0)
        
        x_bot_line = extrude_port_to_y(hub_x["B"], 0)
        x_rig_line = extrude_port_to_x(hub_x["R"], s) # Tip X
        
        y_lef_line = extrude_port_to_x(hub_y["L"], 0)
        y_top_line = extrude_port_to_y(hub_y["T"], s) # Tip Y

        # FILL GAPS (Bottom Edge)
        gap_v1 = hub_c["B"][-1]
        gap_v2 = hub_x["B"][0]
        # X_Bot_Proj_L is x_bot_line[0]
        # C_Bot_Proj_R is c_bot_line[-1]
        create_quad_face(bm, hub_c["B"][-1], hub_x["B"][0], x_bot_line[0], c_bot_line[-1])

        # FILL GAPS (Left Edge)
        create_quad_face(bm, hub_y["L"][-1], hub_c["L"][0], c_lef_line[0], y_lef_line[-1])

        
        if self.shape == "L_SHAPE":
            # Inner corner is at (w,w) approx.
            # Project X_Top to y=w
            x_top_v = extrude_port_to_y(hub_x["T"], w)
            # Project Y_Right to x=w
            y_rig_v = extrude_port_to_x(hub_y["R"], w)
            
            # Corner Vertex
            v_corner = bm.verts.new(Vector((w, w, 0)))
            
            # Fill Corner Gap
            create_quad_face(bm, hub_c["TR"], hub_y["BR"], y_rig_v[0], v_corner)
            create_quad_face(bm, hub_c["TR"], v_corner, x_top_v[-1], hub_x["TL"])
            
            # Fill Tips
            v_tip_x = bm.verts.new(Vector((s, w, 0)))
            create_quad_face(bm, hub_x["TR"], x_top_v[0], v_tip_x, x_rig_line[-1])
            
            v_tip_y = bm.verts.new(Vector((w, s, 0)))
            create_quad_face(bm, hub_y["TR"], y_top_line[0], v_tip_y, y_rig_v[-1])

        elif self.shape == "TRIANGLE":
            # 1. Project X_Top to Diagonal
            x_diag_v = extrude_port_to_diagonal(hub_x["T"], s)
            
            # 2. Project Y_Right to Diagonal
            y_diag_v = extrude_port_to_diagonal(hub_y["R"], s)
            
            # 3. Fill the gap between C, X, Y in the center/diagonal.
            c_tr_diag_pt = Vector((0,0,0))
            px, py = hub_c["TR"].co.x, hub_c["TR"].co.y
            t = (s - px - py)/2
            c_tr_diag_pt = Vector((px+t, py+t, 0))
            v_mid = bm.verts.new(c_tr_diag_pt)
            
            # Quad 1: (C_TR, X_TL, X_TL_Proj, v_mid). 
            create_quad_face(bm, hub_c["TR"], hub_x["TL"], x_diag_v[-1], v_mid)
            
            # Quad 2: (C_TR, v_mid, Y_BR_Proj, Y_BR).
            create_quad_face(bm, hub_c["TR"], v_mid, y_diag_v[0], hub_y["BR"])
            
            # 4. Fill Tips (X Tip, Y Tip).
            # X Tip
            v_tip_x = bm.verts.new(Vector((s, 0, 0)))
            # Verts: X_TR, X_TR_Proj_X (on x=s), v_tip_x (s,0), X_TR_Proj_Diag (on diag)
            # x_rig_line[-1] is X_TR_Proj_X
            # x_diag_v[0] is X_TR_Proj_Diag
            
            # TRIANGULATION to avoid twisted quad
            # TRIANGULATION to avoid twisted quad
            try:
                # Tri 1: X_TR, v_tip_x, X_TR_Proj_X (CCW is Correct)
                # Analysis showed this was CCW: Cross +0.035
                bm.faces.new((hub_x["TR"], v_tip_x, x_rig_line[-1]))
                
                # Tri 2: X_TR, X_TR_Proj_Diag, v_tip_x (Was CW, Swap 2&3)
                # New: X_TR, v_tip_x, X_TR_Proj_Diag
                bm.faces.new((hub_x["TR"], v_tip_x, x_diag_v[0]))
            except ValueError:
                pass # Prevent crash on degenerate geometry

            # Y Tip
            v_tip_y = bm.verts.new(Vector((0, s, 0)))
            # Verts: Y_TR, Y_TR_Proj_Diag, v_tip_y (0,s), Y_TR_Proj_Y
            # y_diag_v[-1] is Y_TR_Proj_Diag
            # y_top_line[0] is Y_TR_Proj_Y

            # TRIANGULATION to avoid twisted quad
            try:
                # Tri 1: Y_TR, v_tip_y, Y_TR_Proj_Y (Was CW, Swap 2&3)
                # Analysis showed Cross -0.035 (CW). 
                # New: Y_TR, Y_TR_Proj_Y, v_tip_y
                bm.faces.new((hub_y["TR"], y_top_line[0], v_tip_y))
                
                # Tri 2: Y_TR, Y_TR_Proj_Diag, v_tip_y (CCW is Correct)
                # Analysis showed Cross +0.028 (CCW).
                bm.faces.new((hub_y["TR"], y_diag_v[-1], v_tip_y))
            except ValueError:
                pass

        
        # ----------------------------------------------------------------------
        # 5. POST-PROCESS
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.1 * self.hole_radius)

        # Extrude Thickness
        # Mark all as slot 0
        for f in bm.faces:
            f.material_index = 0

        res_ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
        faces_side = [f for f in res_ext["geom"] if isinstance(f, bmesh.types.BMFace)]
        
        # Move up
        bmesh.ops.translate(bm, vec=(0,0,t), verts=verts_ext)

        # Assign Side Mat
        for f in faces_side:
            f.material_index = 1

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # ----------------------------------------------------------------------
        # 6. SEAMS & UVs
        # ----------------------------------------------------------------------
        for e in bm.edges:
            # Vertical check
            is_vertical = (abs(e.verts[0].co.x - e.verts[1].co.x) < 0.001 and 
                           abs(e.verts[0].co.y - e.verts[1].co.y) < 0.001)
            if is_vertical:
                e.seam = True
                e[edge_slots] = 3
        
        # Standard Box UV
        uv_layer = bm.loops.layers.uv.verify()
        scale = 1.0 if self.fit_uvs else self.uv_scale
        
        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
            
            project_axis = 'Z'
            if nx > ny and nx > nz: project_axis = 'X'
            elif ny > nx and ny > nz: project_axis = 'Y'
            
            for l in f.loops:
                v = l.vert.co
                if project_axis == 'Z':
                    uv = (v.x, v.y)
                elif project_axis == 'X':
                    uv = (v.y, v.z)
                else:
                    uv = (v.x, v.z)
                l[uv_layer].uv = (uv[0] * scale, uv[1] * scale)