import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_22: HVAC Duct System",
    "id": "prim_22_duct",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_PrimDuct(Massa_OT_Base):
    bl_idname = "massa.gen_prim_22_duct"
    bl_label = "PRIM_22: HVAC Duct"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- Properties ---
    shape_type: EnumProperty(
        name="Type",
        items=[
            ("STRAIGHT", "Straight", "Standard straight duct section"),
            ("ELBOW", "Elbow", "Curved bend (90/45 degrees)"),
            ("TEE", "T-Junction", "Splitter/Branch connection"),
            ("REDUCER", "Reducer", "Size transition"),
            ("CAP", "End Cap", "Closed termination"),
            ("COUPLER", "Coupler", "Connection flange/ring"),
        ],
        default="STRAIGHT",
    )

    # Common Dimensions
    width: FloatProperty(name="Width", default=0.6, min=0.1, description="Main duct width")
    height: FloatProperty(name="Height", default=0.4, min=0.1, description="Main duct height")
    length: FloatProperty(name="Length", default=2.0, min=0.1, description="Length of section")

    wall_thick: FloatProperty(name="Thickness", default=0.01, min=0.001, description="Metal sheet thickness")
    
    # Elbow Specifics
    bend_angle: FloatProperty(name="Angle", default=90.0, min=15.0, max=180.0, description="Bend angle in degrees")
    bend_radius: FloatProperty(name="Radius", default=0.5, min=0.1, description="Inner bend radius")
    
    # Tee Specifics
    branch_width: FloatProperty(name="Branch W", default=0.4, min=0.1)
    branch_height: FloatProperty(name="Branch H", default=0.3, min=0.1)
    branch_offset: FloatProperty(name="Branch Pos", default=0.5, min=0.1, max=0.9, subtype='FACTOR')
    
    # Reducer Specifics
    reducer_ratio: FloatProperty(name="Output Ratio", default=0.6, min=0.2, max=1.5, description="Scale of output relative to input")
    reducer_offset: FloatProperty(name="Offset Y", default=0.0, min=-0.5, max=0.5, description="Vertical offset for eccentric reducers")

    # Details
    flange_style: EnumProperty(
        name="Flanges",
        items=[
            ("NONE", "None", "Raw edges"),
            ("BOTH", "Both Ends", "Flanges on both ends"),
            ("START", "Start Only", "Flange at start"),
            ("END", "End Only", "Flange at end"),
        ],
        default="BOTH",
    )
    flange_width: FloatProperty(name="F.Width", default=0.04, min=0.01)
    flange_thick: FloatProperty(name="F.Thick", default=0.005, min=0.001)
    
    has_ribs: BoolProperty(name="Ribs", default=True)
    rib_spacing: FloatProperty(name="Rib Spacing", default=0.6, min=0.2)
    rib_depth: FloatProperty(name="Rib Depth", default=0.01, min=0.002)

    uv_scale: FloatProperty(name="UV Scale", default=1.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Duct Surface", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            1: {"name": "Flange/Connection", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Ribs/Detail", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            3: {"name": "Interior", "uv": "SKIP", "phys": "METAL_ALUMINUM_DARK"},
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "shape_type")

        box = layout.box()
        box.label(text="Dimensions", icon="arrow_up_down")
        col = box.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        
        if self.shape_type in {'STRAIGHT', 'TEE', 'REDUCER'}:
            col.prop(self, "length")

        if self.shape_type == 'ELBOW':
            box.separator()
            box.label(text="Bend Settings", icon="MOD_CURVE")
            col = box.column(align=True)
            col.prop(self, "bend_angle")
            col.prop(self, "bend_radius")

        if self.shape_type == 'TEE':
            box.separator()
            box.label(text="Branch Settings", icon="BRANCH")
            col = box.column(align=True)
            col.prop(self, "branch_width")
            col.prop(self, "branch_height")
            col.prop(self, "branch_offset")

        if self.shape_type == 'REDUCER':
            box.separator()
            box.label(text="Output Settings", icon="MOD_SHRINKWRAP")
            col = box.column(align=True)
            col.prop(self, "reducer_ratio")
            col.prop(self, "reducer_offset")

        layout.separator()
        layout.label(text="Details", icon="MOD_BUILD")
        layout.prop(self, "wall_thick")

        row = layout.row(align=True)
        row.prop(self, "flange_style")
        if self.flange_style != 'NONE' or self.shape_type == 'COUPLER':
            row = layout.row(align=True)
            row.prop(self, "flange_width", text="W")
            row.prop(self, "flange_thick", text="T")
            
        if self.shape_type in {'STRAIGHT', 'ELBOW', 'TEE'}:
            layout.prop(self, "has_ribs")
            if self.has_ribs:
                row = layout.row(align=True)
                row.prop(self, "rib_spacing", text="Space")
                row.prop(self, "rib_depth", text="Depth")

    def build_shape(self, bm: bmesh.types.BMesh):
        if self.shape_type == 'STRAIGHT':
            self._build_straight(bm)
        elif self.shape_type == 'ELBOW':
            self._build_elbow(bm)
        elif self.shape_type == 'TEE':
            self._build_tee(bm)
        elif self.shape_type == 'REDUCER':
            self._build_reducer(bm)
        elif self.shape_type == 'CAP':
            self._build_cap(bm)
        elif self.shape_type == 'COUPLER':
            self._build_coupler(bm)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Post-Process: Seams & Edge Roles
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            # Mark sharp angles
            if e.is_manifold:
                angle = e.calc_face_angle(0)
                if angle > 0.5: # ~30 deg
                    e.seam = True
                    e[edge_slots] = 1 # Perimeter/Sharp

            # Mark material boundaries
            mats = {f.material_index for f in e.link_faces}
            if len(mats) > 1:
                e.seam = True
                e[edge_slots] = 2 # Material Boundary

    def _create_rect_profile(self, bm, w, h, z=0):
        pts = [
            (-w/2, -h/2, z), (w/2, -h/2, z),
            (w/2, h/2, z), (-w/2, h/2, z)
        ]
        verts = [bm.verts.new(p) for p in pts]
        face = bm.faces.new(verts)
        return face

    def _build_hollow_box(self, bm, w, h, l, t):
        # Outer
        pts_out = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]
        # Inner
        wi, hi = w - t*2, h - t*2
        pts_in = [(-wi/2, -hi/2), (wi/2, -hi/2), (wi/2, hi/2), (-wi/2, hi/2)]

        verts_out = [bm.verts.new((p[0], p[1], 0)) for p in pts_out]
        verts_in = [bm.verts.new((p[0], p[1], 0)) for p in pts_in]

        faces = []
        for i in range(4):
            v1, v2 = verts_out[i], verts_out[(i+1)%4]
            v3, v4 = verts_in[(i+1)%4], verts_in[i]
            faces.append(bm.faces.new((v1, v2, v3, v4)))

        r = bmesh.ops.extrude_face_region(bm, geom=faces)
        verts = [v for v in r['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=verts, vec=(0, 0, l))

        for f in bm.faces:
            f.material_index = 0

        self._apply_box_uvs(bm)

    def _build_straight(self, bm):
        w, h, l = self.width, self.height, self.length
        t = self.wall_thick
        self._build_hollow_box(bm, w, h, l, t)
        if self.has_ribs:
            self._add_ribs(bm, w, h, l)
        self._add_flanges(bm, w, h, l, start=True, end=True)

    def _build_elbow(self, bm):
        w, h = self.width, self.height
        radius = self.bend_radius
        angle = math.radians(self.bend_angle)
        t = self.wall_thick
        
        cx = radius
        pts = []
        pts.extend([
            (cx - w/2, -h/2, 0), (cx + w/2, -h/2, 0),
            (cx + w/2, h/2, 0), (cx - w/2, h/2, 0)
        ])
        wi, hi = w - t*2, h - t*2
        pts.extend([
            (cx - wi/2, -hi/2, 0), (cx + wi/2, -hi/2, 0),
            (cx + wi/2, hi/2, 0), (cx - wi/2, hi/2, 0)
        ])
        
        verts = [bm.verts.new(p) for p in pts]
        faces = []
        for i in range(4):
            v1, v2 = verts[i], verts[(i+1)%4]
            v3, v4 = verts[4 + (i+1)%4], verts[4 + i]
            faces.append(bm.faces.new((v1, v2, v3, v4)))

        steps = int(max(4, self.bend_angle / 5))
        bmesh.ops.spin(
            bm,
            geom=faces,
            angle=-angle,
            steps=steps,
            axis=(0, 1, 0),
            cent=(0, 0, 0)
        )
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        
        # Move elbow to start at (0,0,0)
        # Shift back by radius in X
        bmesh.ops.translate(bm, verts=bm.verts, vec=(-radius, 0, 0))
        
        self._apply_box_uvs(bm)

    def _build_tee(self, bm):
        w, h, l = self.width, self.height, self.length
        t = self.wall_thick
        self._build_hollow_box(bm, w, h, l, t)
        
        bw, bh = self.branch_width, self.branch_height
        offset_z = l * self.branch_offset
        bl = 0.5
        
        r = bmesh.ops.create_cube(bm, size=1.0)
        b_verts = r['verts']
        bmesh.ops.scale(bm, verts=b_verts, vec=(bl, bh, bw))
        bmesh.ops.translate(bm, verts=b_verts, vec=(w/2 + bl/2 - 0.02, 0, offset_z))
        
        self._add_flanges(bm, w, h, l, start=True, end=True)

    def _build_reducer(self, bm):
        w1, h1 = self.width, self.height
        l = self.length
        t = self.wall_thick
        ratio = self.reducer_ratio
        w2, h2 = w1 * ratio, h1 * ratio
        off_y = self.reducer_offset
        
        pts1_out = [(-w1/2, -h1/2), (w1/2, -h1/2), (w1/2, h1/2), (-w1/2, h1/2)]
        pts1_in = [(-w1/2+t, -h1/2+t), (w1/2-t, -h1/2+t), (w1/2-t, h1/2-t), (-w1/2+t, h1/2-t)]
        
        pts2_out = [(-w2/2, -h2/2 + off_y), (w2/2, -h2/2 + off_y), (w2/2, h2/2 + off_y), (-w2/2, h2/2 + off_y)]
        pts2_in = [(-w2/2+t, -h2/2+t + off_y), (w2/2-t, -h2/2+t + off_y), (w2/2-t, h2/2-t + off_y), (-w2/2+t, h2/2-t + off_y)]

        v1o = [bm.verts.new((p[0], p[1], 0)) for p in pts1_out]
        v1i = [bm.verts.new((p[0], p[1], 0)) for p in pts1_in]
        v2o = [bm.verts.new((p[0], p[1], l)) for p in pts2_out]
        v2i = [bm.verts.new((p[0], p[1], l)) for p in pts2_in]

        for i in range(4):
            bm.faces.new((v1o[i], v1o[(i+1)%4], v1i[(i+1)%4], v1i[i]))
        for i in range(4):
            bm.faces.new((v2o[(i+1)%4], v2o[i], v2i[i], v2i[(i+1)%4]))
        for i in range(4):
            bm.faces.new((v1o[i], v2o[i], v2o[(i+1)%4], v1o[(i+1)%4]))
        for i in range(4):
            bm.faces.new((v1i[(i+1)%4], v2i[(i+1)%4], v2i[i], v1i[i]))
            
        self._add_flanges(bm, w1, h1, l, start=True, end=False)
        if self.flange_style in {'BOTH', 'END'}:
            self._create_flange_geo(bm, w2, h2, l, self.flange_width, self.flange_thick, mat_idx=1)

        self._apply_box_uvs(bm)

    def _build_cap(self, bm):
        w, h = self.width, self.height
        l = 0.05
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, h, l), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, l/2), verts=bm.verts)
        self._add_flanges(bm, w, h, l, start=True, end=False)
        self._apply_box_uvs(bm)

    def _build_coupler(self, bm):
        w, h = self.width, self.height
        ft = self.flange_thick
        fw = self.flange_width
        self._create_flange_geo(bm, w, h, 0, fw, ft*2, mat_idx=1)
        self._apply_box_uvs(bm)

    def _add_flanges(self, bm, w, h, l, start=False, end=False):
        fw = self.flange_width
        ft = self.flange_thick
        style = self.flange_style
        if style == 'NONE': return
        if start and style in {'BOTH', 'START'}:
            self._create_flange_geo(bm, w, h, 0, fw, ft, mat_idx=1)
        if end and style in {'BOTH', 'END'}:
            self._create_flange_geo(bm, w, h, l - ft, fw, ft, mat_idx=1)

    def _create_flange_geo(self, bm, w, h, z, fw, ft, mat_idx=1):
        pts_out = [(-(w/2+fw), -(h/2+fw)), ((w/2+fw), -(h/2+fw)), ((w/2+fw), (h/2+fw)), (-(w/2+fw), (h/2+fw))]
        pts_in = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]

        v_out = [bm.verts.new((p[0], p[1], z)) for p in pts_out]
        v_in = [bm.verts.new((p[0], p[1], z)) for p in pts_in]
        
        faces = []
        for i in range(4):
            f = bm.faces.new((v_out[i], v_out[(i+1)%4], v_in[(i+1)%4], v_in[i]))
            f.material_index = mat_idx
            faces.append(f)

        r = bmesh.ops.extrude_face_region(bm, geom=faces)
        verts = [v for v in r['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=verts, vec=(0, 0, ft))

        for f in r['geom']:
            if isinstance(f, bmesh.types.BMFace):
                f.material_index = mat_idx

    def _add_ribs(self, bm, w, h, l):
        spacing = self.rib_spacing
        depth = self.rib_depth
        count = int(l / spacing)
        if count < 1: return
        step = l / (count + 1)
        for i in range(1, count + 1):
            z = i * step
            self._create_flange_geo(bm, w, h, z - 0.01, depth, 0.02, mat_idx=2)

    def _apply_box_uvs(self, bm):
        scale = self.uv_scale
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
            n = f.normal
            for l in f.loops:
                v = l.vert.co
                nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
                if nx > ny and nx > nz:
                    u, v_ = v.y, v.z
                elif ny > nx and ny > nz:
                    u, v_ = v.x, v.z
                else:
                    u, v_ = v.x, v.y
                l[uv_layer].uv = (u * scale, v_ * scale)
