import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_11: Spiral Staircase",
    "id": "asm_11_spiral_staircase",
    "icon": "MESH_CONE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_AsmSpiralStaircase(Massa_OT_Base):
    bl_idname = "massa.gen_asm_11_spiral_staircase"
    bl_label = "ASM_11 Spiral Stairs"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    radius: FloatProperty(
        name="Radius", default=1.5, min=0.5, unit="LENGTH", description="Outer radius"
    )
    height: FloatProperty(name="Height", default=3.0, min=0.5, unit="LENGTH")
    turns: FloatProperty(
        name="Turns",
        default=0.75,
        min=0.1,
        step=0.05,
        description="Revolutions (1.0 = 360 degrees)",
    )

    # --- 2. TOPOLOGY ---
    step_count: IntProperty(name="Step Count", default=16, min=3)
    tread_thick: FloatProperty(
        name="Thick", default=0.05, min=0.005, unit="LENGTH"
    )

    # --- 3. STRUCTURE ---
    post_radius: FloatProperty(
        name="Post Radius", default=0.15, min=0.05, unit="LENGTH"
    )

    # --- 4. RAILING ---
    has_rail: BoolProperty(name="Railing", default=True)
    rail_height: FloatProperty(name="Rail Height", default=0.9, min=0.1, unit="LENGTH")
    rail_radius: FloatProperty(name="Rail Radius", default=0.04, min=0.005, unit="LENGTH")

    # --- 5. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Treads", "uv": "SKIP", "phys": "WOOD_OAK"},
            1: {"name": "Structure", "uv": "SKIP", "phys": "METAL_STEEL"}, # Post
            2: {"name": "Railing", "uv": "SKIP", "phys": "METAL_CHROME"},
            9: {"name": "Sockets", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "height")
        col.prop(self, "radius")
        col.prop(self, "turns")
        col.prop(self, "step_count")

        col.separator()
        col.label(text="Structure")
        col.prop(self, "post_radius")
        col.prop(self, "tread_thick")

        col.separator()
        col.label(text="Railing")
        col.prop(self, "has_rail")
        if self.has_rail:
            col.prop(self, "rail_height")
            col.prop(self, "rail_radius")

    def build_shape(self, bm: bmesh.types.BMesh):
        h = self.height
        rad = self.radius
        turns = self.turns
        count = max(3, self.step_count)
        post_r = self.post_radius

        angle_total = turns * 2 * math.pi
        angle_step = angle_total / count
        rise_step = h / count

        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        # 1. CENTRAL POLE
        # Cylinder at origin
        res_post = bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            diameter1=post_r * 2,
            diameter2=post_r * 2,
            depth=h,
            segments=16,
        )
        bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=res_post["verts"])

        # Identify Caps for Sockets
        for f in list({f for v in res_post["verts"] for f in v.link_faces}):
            if f.normal.z > 0.9 or f.normal.z < -0.9:
                f.material_index = 9 # Socket
                self.apply_box_map(f, uv_layer, s)
            else:
                f.material_index = 1 # Structure
                f.smooth = True
                self.apply_polar_map(f, uv_layer, s, post_r)

        # 2. STEPS
        # Fan shape: Inner arc at post_r, Outer arc at rad.
        # Connect inner vertices to post (conceptually, practically separate geometry welded later or just overlapping)
        # We'll create each step as a simplified wedge/box.

        step_len = rad - post_r
        step_width_mid = (2 * math.pi * (post_r + step_len/2) * turns) / count

        # Create a box for the step
        # Dimensions: X=step_len, Y=step_width_mid, Z=tread_thick
        # Start at X=post_r + step_len/2 (center of step radially)

        for i in range(count):
            theta = i * angle_step
            z = i * rise_step

            res_step = bmesh.ops.create_cube(bm, size=1.0)
            verts_step = res_step["verts"]

            # Scale to approximate dimensions
            # We use a slight overlap for Y to ensure continuity if needed, but simple steps are fine.
            bmesh.ops.scale(bm, vec=(step_len, step_width_mid * 1.1, self.tread_thick), verts=verts_step)

            # Move to radial position (local X)
            bmesh.ops.translate(bm, vec=(post_r + step_len/2, 0, self.tread_thick/2), verts=verts_step)

            # Rotate around Z
            bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(theta, 4, 'Z'), verts=verts_step)

            # Move up
            bmesh.ops.translate(bm, vec=(0,0,z), verts=verts_step)

            # Assign Material
            for f in list({f for v in verts_step for f in v.link_faces}):
                f.material_index = 0 # Treads
                f.smooth = False
                self.apply_box_map(f, uv_layer, s)

        # 3. RAILING (Spiral Sweep)
        if self.has_rail:
            path_r = rad - self.rail_radius
            pitch_angle = math.atan(h / (2 * math.pi * path_r * turns))

            # Handrail
            self.build_helix_extrusion(
                bm,
                radius=path_r,
                height=h,
                turns=turns,
                segs=count * 4,
                profile_r=self.rail_radius,
                pitch_angle=pitch_angle,
                slot_idx=2,
                z_offset=self.rail_height + self.tread_thick, # Above steps
                uv_layer=uv_layer,
                uv_scale=s
            )

            # Posts (every N steps)
            post_density = max(1, count // 4) # e.g. 4 posts total? Or every 4 steps?
            post_step_gap = 4

            indices = list(range(0, count, post_step_gap))
            if (count-1) not in indices:
                indices.append(count-1)

            for i in indices:
                theta = i * angle_step
                z_floor = i * rise_step + self.tread_thick

                x = math.cos(theta) * path_r
                y = math.sin(theta) * path_r

                h_post = self.rail_height

                mat_p = Matrix.Translation(Vector((x, y, z_floor + h_post/2)))
                res_p = bmesh.ops.create_cone(
                    bm,
                    cap_ends=True,
                    diameter1=self.rail_radius * 2,
                    diameter2=self.rail_radius * 2,
                    depth=h_post,
                    matrix=mat_p,
                    segments=12
                )

                for f in list({f for v in res_p["verts"] for f in v.link_faces}):
                    f.material_index = 2 # Railing
                    f.smooth = True
                    self.apply_polar_map(f, uv_layer, s, self.rail_radius)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def build_helix_extrusion(self, bm, radius, height, turns, segs, profile_r, pitch_angle, slot_idx, z_offset, uv_layer, uv_scale):
        total_angle = turns * 2 * math.pi
        d_theta = total_angle / segs
        d_z = height / segs
        arc_len_segment = math.sqrt((radius * d_theta)**2 + d_z**2)
        perimeter = 2 * math.pi * profile_r

        # Initial Ring (Circle)
        mat_setup = Matrix.Translation(Vector((radius, 0, z_offset))) @ Matrix.Rotation(pitch_angle, 4, 'X')
        mat_circle = mat_setup @ Matrix.Rotation(math.radians(90), 4, 'X')

        verts_ring = []
        seg_circle = 12
        for i in range(seg_circle):
            a = (i/seg_circle) * 2 * math.pi
            v_loc = Vector((math.cos(a)*profile_r, math.sin(a)*profile_r, 0))
            verts_ring.append(bm.verts.new(mat_circle @ v_loc))

        edges_ring = []
        for i in range(len(verts_ring)):
            v1 = verts_ring[i]
            v2 = verts_ring[(i+1)%len(verts_ring)]
            edges_ring.append(bm.edges.new((v1, v2)))

        start_verts = list(verts_ring)
        current_v_coord = 0.0

        for k in range(segs):
            current_v_coord += arc_len_segment * uv_scale

            res_ex = bmesh.ops.extrude_edge_only(bm, edges=edges_ring)
            verts_new = [v for v in res_ex['geom'] if isinstance(v, bmesh.types.BMVert)]
            faces_side = [f for f in res_ex['geom'] if isinstance(f, bmesh.types.BMFace)]

            bmesh.ops.translate(bm, vec=(0,0,d_z), verts=verts_new)
            bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(d_theta, 4, 'Z'), verts=verts_new)

            # UV Mapping
            if uv_layer and faces_side:
                for j, edge_old in enumerate(edges_ring):
                    target_face = None
                    for f in faces_side:
                        if edge_old in f.edges:
                            target_face = f
                            break

                    if target_face:
                        target_face.material_index = slot_idx
                        target_face.smooth = True

                        u_start = (j/len(edges_ring)) * perimeter * uv_scale
                        u_end = ((j+1)/len(edges_ring)) * perimeter * uv_scale
                        v_prev = current_v_coord - (arc_len_segment * uv_scale)
                        v_curr = current_v_coord

                        loops = list(target_face.loops)
                        # We need to assign UVs correctly based on loop vertex
                        # Assumption: Standard extrusion topology
                        # This part can be tricky, simplified:
                        for l in loops:
                            # Map U based on ring index j, V based on length
                            # We need to distinguish between 'start' (old ring) and 'end' (new ring) vertices
                            # But since we extruded, the vertices are linked.
                            # Simplified logic:
                            if l.vert in edge_old.verts:
                                # Start of segment (v_prev)
                                l[uv_layer].uv = (u_start if l.vert == edge_old.verts[0] else u_end, v_prev)
                            else:
                                # End of segment (v_curr)
                                # Check connectivity to align U
                                # If connected to edge_old.verts[0], use u_start
                                connected = False
                                for e in l.vert.link_edges:
                                    if e.other_vert(l.vert) == edge_old.verts[0]:
                                        connected = True
                                        break
                                l[uv_layer].uv = (u_start if connected else u_end, v_curr)

            # Update ring for next iteration
            new_verts_set = set(verts_new)
            next_verts_ring = [None]*len(verts_ring)
            for i, v_old in enumerate(verts_ring):
                for e in v_old.link_edges:
                    other = e.other_vert(v_old)
                    if other in new_verts_set:
                        next_verts_ring[i] = other
                        break
            verts_ring = next_verts_ring
            edges_ring = []
            for i in range(len(verts_ring)):
                v1 = verts_ring[i]
                v2 = verts_ring[(i+1)%len(verts_ring)]
                found = bm.edges.get((v1, v2))
                if found: edges_ring.append(found)

        # Cap Ends
        bmesh.ops.contextual_create(bm, geom=start_verts)
        bmesh.ops.contextual_create(bm, geom=verts_ring)
        # Fix cap normals/materials if needed
        for f in bm.faces:
            if all(v in start_verts for v in f.verts) or all(v in verts_ring for v in f.verts):
                 f.material_index = slot_idx

    def apply_box_map(self, face, uv_layer, scale):
        n = face.normal
        nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
        for l in face.loops:
            co = l.vert.co
            if nz > nx and nz > ny:
                u, v = co.x, co.y
            elif nx > ny and nx > nz:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            l[uv_layer].uv = (u * scale, v * scale)

    def apply_polar_map(self, face, uv_layer, scale, radius=1.0):
        circumference = 2 * math.pi * radius
        for l in face.loops:
            co = l.vert.co
            theta = math.atan2(co.y, co.x)
            u = ((theta + math.pi) / (2 * math.pi)) * circumference
            v = co.z
            l[uv_layer].uv = (u * scale, v * scale)
