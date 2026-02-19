import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

# ==============================================================================
# MASSA CARTRIDGE: PRIM_06 GUSSET (CONNECTOR PLATE)
# ID: prim_06_gusset
# ==============================================================================

CARTRIDGE_META = {
    "name": "PRIM_06: Connector Plate",
    "id": "prim_06_gusset",
    "icon": "MOD_TRIANGULATE",
    "scale_class": "MICRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Thickness is handled internally for better topology
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True, # Pivot at connection point
    },
}


class MASSA_OT_PrimGusset(Massa_OT_Base):
    bl_idname = "massa.gen_prim_06_gusset"
    bl_label = "PRIM_06: Connector Plate"
    bl_description = "Versatile flat connector plate with multiple configurations"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- SHAPE ---
    shape_mode: EnumProperty(
        name="Configuration",
        items=[
            ("STRAIGHT", "Straight (I)", "Linear connection (2 Holes)"),
            ("L_SHAPE", "Corner (L)", "90-degree turn (3 Holes)"),
            ("TEE", "T-Junction", "3-way split (4 Holes)"),
            ("CROSS", "Cross (X)", "4-way intersection (5 Holes)"),
        ],
        default="L_SHAPE",
    )

    # --- DIMENSIONS ---
    arm_length: FloatProperty(name="Arm Length", default=0.15, min=0.04, unit="LENGTH")
    width: FloatProperty(name="Width", default=0.06, min=0.02, unit="LENGTH")
    thickness: FloatProperty(name="Thickness", default=0.005, min=0.001, unit="LENGTH")

    # --- DETAILS ---
    corner_radius: FloatProperty(name="Corner Radius", default=0.01, min=0.0, unit="LENGTH")

    # --- HOLES ---
    has_holes: BoolProperty(name="Bolt Holes", default=True)
    hole_radius: FloatProperty(name="Hole Radius", default=0.008, min=0.001, unit="LENGTH")
    
    # --- UV / TOPOLOGY ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    resolution: IntProperty(name="Resolution", default=16, min=4, max=64)

    def get_slot_meta(self):
        return {
            0: {"name": "Plate Surface", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "Cut Edges", "uv": "SKIP", "phys": "METAL_STEEL"},
            9: {"name": "Socket Anchor", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Configuration", icon="OUTLINER_OB_LATTICE")
        box.prop(self, "shape_mode", text="")

        row = box.row()
        row.prop(self, "arm_length")
        row.prop(self, "width")

        row = box.row()
        row.prop(self, "thickness")
        row.prop(self, "corner_radius")

        box = layout.box()
        box.label(text="Machining", icon="MOD_BOOLEAN")
        box.prop(self, "has_holes", toggle=True)
        if self.has_holes:
            row = box.row()
            row.prop(self, "hole_radius")

        box = layout.box()
        box.label(text="Topology", icon="MESH_GRID")
        box.prop(self, "resolution")
        box.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        # ----------------------------------------------------------------------
        # 0. SETUP
        # ----------------------------------------------------------------------
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        uv_layer = bm.loops.layers.uv.verify()

        # Resolution Check
        segs = max(4, self.resolution)
        if segs % 4 != 0: segs = (segs // 4) * 4

        # Parameters
        L = self.arm_length
        W = self.width
        T = self.thickness
        R_hole = self.hole_radius if self.has_holes else 0.001

        # Validation
        if R_hole > W/2: R_hole = W/2 - 0.001

        # ----------------------------------------------------------------------
        # 1. TOPOLOGY HELPERS
        # ----------------------------------------------------------------------
        def create_quad_face(bm, v1, v2, v3, v4):
            if (v1.co - v2.co).length < 1e-6 or (v3.co - v4.co).length < 1e-6: return None
            try:
                return bm.faces.new((v1, v2, v3, v4))
            except ValueError:
                return None

        def create_hub(bm, cx, cy, r_hole, width, segs):
            """
            Creates a washer-like hub.
            Returns a dictionary with 'ports' (lists of verts) for bridging.
            """
            # Logic similar to prim_con_bracket but centered
            pad = width / 2 # The outer box radius (half width)

            # The circle radius should be smaller than pad
            r_circ = r_hole
            
            circ_pts = []
            box_pts = []

            # 4 corners of the box are at angles: 45, 135, 225, 315
            # We want the flat sides aligned with X and Y axes.
            # Angle 0 is Right (+X).

            for i in range(segs):
                angle = (i / segs) * 2 * math.pi
                # Circle
                circ_pts.append(Vector((cx + math.cos(angle) * r_circ, cy + math.sin(angle) * r_circ, 0)))
                
                # Box (Square projection)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                scale = 1.0 / max(abs(cos_a), abs(sin_a), 0.0001)

                bx = cos_a * scale * pad
                by = sin_a * scale * pad

                box_pts.append(Vector((cx + bx, cy + by, 0)))

            # Create Verts
            c_verts = [bm.verts.new(p) for p in circ_pts]
            b_verts = [bm.verts.new(p) for p in box_pts]

            # Faces
            if self.has_holes and r_hole > 0.001:
                # Washer Face Loop
                for i in range(segs):
                    idx_next = (i + 1) % segs
                    bm.faces.new((c_verts[i], c_verts[idx_next], b_verts[idx_next], b_verts[i]))
            else:
                # Cap center
                bm.faces.new(c_verts)
                # Bridge
                for i in range(segs):
                    idx_next = (i + 1) % segs
                    bm.faces.new((c_verts[i], c_verts[idx_next], b_verts[idx_next], b_verts[i]))

            # Define Ports
            # segs=16 -> s2=2.
            # 0=Right, 4=Top, 8=Left, 12=Bottom
            s2 = segs // 8
            
            idx_br = (segs - s2) % segs # 14
            idx_tr = s2        # 2
            idx_tl = 3 * s2    # 6
            idx_bl = 5 * s2    # 10
            
            def get_range(start, end):
                ids = []
                curr = start
                while True:
                    ids.append(curr)
                    if curr == end: break
                    curr = (curr + 1) % segs
                return ids
            
            # Right Port (Vertical line on Right side)
            # From BR to TR
            ids_right = get_range(idx_br, idx_tr) 
            verts_right = [b_verts[i] for i in ids_right]
            
            # Top Port (Horizontal line on Top side)
            # From TR to TL
            ids_top = get_range(idx_tr, idx_tl) 
            verts_top = [b_verts[i] for i in ids_top]
            
            # Left Port (Vertical line on Left side)
            # From TL to BL
            ids_left = get_range(idx_tl, idx_bl) 
            verts_left = [b_verts[i] for i in ids_left]

            # Bottom Port (Horizontal line on Bottom side)
            # From BL to BR
            ids_bot = get_range(idx_bl, idx_br)
            verts_bot = [b_verts[i] for i in ids_bot]

            return {
                "R": verts_right, 
                "T": verts_top, 
                "L": verts_left, 
                "B": verts_bot,
                "center": Vector((cx, cy, 0))
            }

        def bridge_ports(port_a, port_b):
            if len(port_a) != len(port_b): return
            for i in range(len(port_a) - 1):
                create_quad_face(bm, port_a[i], port_a[i+1], port_b[i+1], port_b[i])

        # ----------------------------------------------------------------------
        # 2. GENERATION LOGIC
        # ----------------------------------------------------------------------
        
        hubs = {}
        nodes_to_spawn = [] # (key, x, y)
        
        if self.shape_mode == "STRAIGHT":
            dist = L / 2
            nodes_to_spawn = [("L", -dist, 0), ("R", dist, 0)]
        elif self.shape_mode == "L_SHAPE":
            nodes_to_spawn = [("C", 0, 0), ("T", 0, L), ("R", L, 0)]
        elif self.shape_mode == "TEE":
            nodes_to_spawn = [("C", 0, 0), ("L", -L, 0), ("R", L, 0), ("T", 0, L)]
        elif self.shape_mode == "CROSS":
            nodes_to_spawn = [("C", 0, 0), ("L", -L, 0), ("R", L, 0), ("T", 0, L), ("B", 0, -L)]

        # Create Hubs
        for key, hx, hy in nodes_to_spawn:
            hubs[key] = create_hub(bm, hx, hy, R_hole, W, segs)

        # Bridge Hubs
        connections = []
        if self.shape_mode == "STRAIGHT":
            connections.append(("L", "R", "L"))
        elif self.shape_mode == "L_SHAPE":
            connections.append(("C", "T", "B"))
            connections.append(("C", "R", "L"))
        elif self.shape_mode in ["TEE", "CROSS"]:
            if "L" in hubs: connections.append(("C", "L", "R"))
            if "R" in hubs: connections.append(("C", "R", "L"))
            if "T" in hubs: connections.append(("C", "T", "B"))
            if "B" in hubs: connections.append(("C", "B", "T"))

        for h1_key, h2_key, h2_port_name in connections:
            p1_name = ""
            if h2_port_name == "L": p1_name = "R"
            elif h2_port_name == "R": p1_name = "L"
            elif h2_port_name == "T": p1_name = "B"
            elif h2_port_name == "B": p1_name = "T"
            
            port_1 = hubs[h1_key][p1_name]
            port_2 = hubs[h2_key][h2_port_name]
            
            bridge_ports(port_1, port_2[::-1])

        # ----------------------------------------------------------------------
        # 3. POST-PROCESS & THICKNESS
        # ----------------------------------------------------------------------
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Mark Surface Slot
        for f in bm.faces: f.material_index = 0

        # Extrude Thickness
        res_ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
        faces_side = [f for f in res_ext["geom"] if isinstance(f, bmesh.types.BMFace)]
        
        bmesh.ops.translate(bm, vec=(0,0,T), verts=verts_ext)

        for f in faces_side:
            f.material_index = 1

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # ----------------------------------------------------------------------
        # 4. MANUAL UVs ("THE MANDATE")
        # ----------------------------------------------------------------------
        faces_top = []
        faces_bot = []
        faces_wall_flat = []
        faces_wall_hole = []
        
        hub_centers = [data["center"] for data in hubs.values()]
        
        for f in bm.faces:
            n = f.normal
            if n.z > 0.9: faces_top.append(f)
            elif n.z < -0.9: faces_bot.append(f)
            else:
                # Wall logic: Is it a hole or an outer wall?
                # Check distance of face center to nearest hub center
                f_center = f.calc_center_median()
                f_center_2d = Vector((f_center.x, f_center.y, 0))

                is_hole = False
                for hc in hub_centers:
                    dist = (f_center_2d - hc).length
                    # Hole radius is R_hole.
                    # Extrusion expands it slightly? No, vertical extrusion.
                    if dist < (R_hole * 1.2):
                        is_hole = True
                        # Store reference to the hub center for UV calculation
                        f.tag = True # Use tag or just store pair
                        break

                if is_hole and self.has_holes:
                    faces_wall_hole.append(f)
                else:
                    faces_wall_flat.append(f)
            
        # Planar Map (Top/Bot)
        scale_uv = self.uv_scale
        for f in faces_top + faces_bot:
            for l in f.loops:
                v = l.vert.co
                l[uv_layer].uv = (v.x * scale_uv, v.y * scale_uv)

        # Box Map (Outer Walls)
        for f in faces_wall_flat:
            n = f.normal
            if abs(n.x) > abs(n.y): # Facing X
                u_axis, v_axis = 1, 2 # y, z
            else: # Facing Y
                u_axis, v_axis = 0, 2 # x, z

            for l in f.loops:
                v = l.vert.co
                u = v[u_axis]
                v_coord = v[v_axis]
                l[uv_layer].uv = (u * scale_uv, v_coord * scale_uv)

        # Cylinder Map (Holes)
        for f in faces_wall_hole:
            # Find nearest hub center again (expensive but robust)
            f_center = f.calc_center_median()
            f_center_2d = Vector((f_center.x, f_center.y, 0))
            best_hc = Vector((0,0,0))
            min_d = 9999.0

            for hc in hub_centers:
                d = (f_center_2d - hc).length
                if d < min_d:
                    min_d = d
                    best_hc = hc
            
            # Unwrap around best_hc
            for l in f.loops:
                v = l.vert.co
                vec = Vector((v.x, v.y, 0)) - best_hc
                angle = math.atan2(vec.y, vec.x) # -pi to pi
                u = angle / (2 * math.pi) # -0.5 to 0.5

                # seam fix?
                # If face spans the seam (pi/-pi), one vert is approx pi, other is -pi.
                # But typically BMesh faces don't span large angles.
                # We just map straight u.

                v_coord = v.z
                l[uv_layer].uv = (u * scale_uv * 4, v_coord * scale_uv) # Scale U by 4 for better aspect?

        # ----------------------------------------------------------------------
        # 5. SOCKET (FASTENER)
        # ----------------------------------------------------------------------
        sock_r = 0.004
        # Create socket at (0,0,0) facing -Z
        sv1 = bm.verts.new(Vector((-sock_r, -sock_r, 0)))
        sv2 = bm.verts.new(Vector((sock_r, -sock_r, 0)))
        sv3 = bm.verts.new(Vector((sock_r, sock_r, 0)))
        sv4 = bm.verts.new(Vector((-sock_r, sock_r, 0)))

        try:
            # CCW in XY is +Z. We want -Z.
            # v1(-,-), v2(+,-), v3(+,+), v4(-,+)
            # 1->2->3->4 is CCW (+Z).
            # 1->4->3->2 is CW (-Z).
            f_sock = bm.faces.new((sv1, sv4, sv3, sv2))
            f_sock.material_index = 9
        except ValueError:
            pass

        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
