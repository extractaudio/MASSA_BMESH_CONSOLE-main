import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_09: Heavy Chain",
    "id": "prim_09_chain",
    "icon": "CONSTRAINT_BONE",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": False,  # CRITICAL: Links must remain separate islands
        "ALLOW_FUSE": False,
        "ALLOW_SOLIDIFY": False,
        "ALLOW_CHAMFER": False,
    },
}


class MASSA_OT_PrimChain(Massa_OT_Base):
    bl_idname = "massa.gen_prim_09_chain"
    bl_label = "PRIM_09: Chain"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    # Updated MIN values to allow Micro-Scale (0.0001 = 0.1mm)
    link_count: IntProperty(name="Link Count", default=12, min=1, max=1000)
    link_length: FloatProperty(name="Link Length", default=0.12, min=0.001)
    link_width: FloatProperty(name="Link Width", default=0.06, min=0.001)
    wire_radius: FloatProperty(name="Wire Radius", default=0.015, min=0.0001)

    # --- 2. PHYSICS ---
    # 0.0 = Taut (Max Length), 1.0 = Slack (Compressed/Bunched)
    spacing: FloatProperty(name="Slack", default=0.0, min=0.0, max=1.0)

    # --- 3. TOPOLOGY ---
    segments_radial: IntProperty(name="Wire Segs", default=12, min=4)
    segments_bend: IntProperty(name="Bend Segs", default=12, min=4)

    # --- 4. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 Standard: UV set to 'SKIP' to preserve custom parametric mapping.
        """
        return {
            0: {"name": "Metal Surface", "uv": "SKIP", "phys": "METAL_IRON"},
            1: {"name": "Weld Detail", "uv": "BOX", "phys": "GENERIC"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        col.prop(self, "link_count")
        col.prop(self, "link_length")
        col.prop(self, "link_width")
        col.prop(self, "wire_radius")
        col.separator()
        col.prop(self, "spacing")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        row = layout.row(align=True)
        row.prop(self, "segments_radial", text="Radial")
        row.prop(self, "segments_bend", text="Bend (Half)")



    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. GEOMETRY & SAFETY MATH
        r = self.wire_radius

        # Clamp Width: Must accommodate 2 walls (4r) + hole (2r) + padding
        # We enforce a strict physical minimum to prevent self-intersection
        safe_width = max(self.link_width, r * 6.05)

        # Clamp Length: Must be > Width to allow rotation
        # A perfect circle link (Length = Width) would bind. 1.1 ratio ensures clearance.
        safe_length = max(self.link_length, safe_width * 1.1)

        bend_r = (safe_width / 2) - r
        straight_l = (safe_length - safe_width) / 2

        # --- PITCH CALCULATOR (The Slack Logic) ---
        # Taut (Max Extent): Links pulling against each other.
        # Distance = Length - (2 * WireThickness) = L - 4r
        p_taut = safe_length - (4.0 * r)

        # Slack (Compressed): Links sliding into each other.
        # Allowing compression down to r (1x radius spacing) handles "Piling"
        p_slack = safe_length - (8.0 * r)
        if p_slack < r:
            p_slack = r  # Safety floor

        # Interpolate: 0.0 -> Taut, 1.0 -> Slack
        pitch = p_taut - (self.spacing * (p_taut - p_slack))

        # Z-Offset: Lift chain so bottom tip of first link is at Z=0
        # First link center is at 0. Bottom tip is at -(safe_length/2).
        z_offset = safe_length / 2.0

        uv_layer = bm.loops.layers.uv.verify()

        # 2. GENERATION LOOP
        for i_link in range(self.link_count):
            # --- A. GENERATE PATH POINTS ---
            # Path: Left Straight -> Top Arc -> Right Straight -> Bottom Arc
            raw_path = []  # (Pos, Norm)

            # Left Straight (Up)
            raw_path.append((Vector((-bend_r, -straight_l, 0)), Vector((-1, 0, 0))))
            raw_path.append((Vector((-bend_r, straight_l, 0)), Vector((-1, 0, 0))))

            # Top Arc
            for s in range(1, self.segments_bend + 1):
                t = s / self.segments_bend
                angle = math.pi * (1.0 - t)
                x = math.cos(angle) * bend_r
                y = math.sin(angle) * bend_r
                raw_path.append(
                    (
                        Vector((x, straight_l + y, 0)),
                        Vector((math.cos(angle), math.sin(angle), 0)),
                    )
                )

            # Right Straight (Down)
            raw_path.append((Vector((bend_r, -straight_l, 0)), Vector((1, 0, 0))))

            # Bottom Arc
            for s in range(1, self.segments_bend):
                t = s / self.segments_bend
                angle = 0.0 - (math.pi * t)
                x = math.cos(angle) * bend_r
                y = math.sin(angle) * bend_r
                raw_path.append(
                    (
                        Vector((x, -straight_l + y, 0)),
                        Vector((math.cos(angle), math.sin(angle), 0)),
                    )
                )

            # --- B. CALCULATE EXACT UV LENGTHS ---
            path_data = []  # (Pos, Norm, Accumulated_Dist)
            total_dist = 0.0

            for k in range(len(raw_path)):
                p, n = raw_path[k]
                if k > 0:
                    dist = (p - raw_path[k - 1][0]).length
                    total_dist += dist
                path_data.append((p, n, total_dist))

            # Measure closing gap (Last point back to First point)
            closing_dist = (raw_path[0][0] - raw_path[-1][0]).length
            total_len = total_dist + closing_dist

            # UV Scaling Factor
            tube_perim = 2 * math.pi * r
            su = 1.0 if self.fit_uvs else (self.uv_scale * tube_perim)
            sv = 1.0 if self.fit_uvs else (self.uv_scale * total_len)
            v_mult = sv / total_len

            # --- C. GENERATE MESH RINGS ---
            # Matrices for Link Transform
            mat_x = Matrix.Rotation(math.radians(90), 4, "X")
            mat_z = Matrix.Identity(4)
            if i_link % 2 != 0:
                mat_z = Matrix.Rotation(math.radians(90), 4, "Z")

            vec_trans = Vector((0, 0, z_offset - (i_link * pitch)))

            final_mat = Matrix.Translation(vec_trans) @ mat_z @ mat_x

            grid_verts = []  # [ring][radial] -> (BMVert, u_raw, v_dist_raw)

            for pt_pos, pt_norm, pt_dist in path_data:
                ring = []
                for r_idx in range(self.segments_radial):
                    theta = (r_idx / self.segments_radial) * 2 * math.pi
                    cos_t = math.cos(theta)
                    sin_t = math.sin(theta)

                    off_vec = (pt_norm * cos_t * r) + (Vector((0, 0, 1)) * sin_t * r)
                    local_pos = pt_pos + off_vec
                    world_pos = final_mat @ local_pos

                    v = bm.verts.new(world_pos)
                    u_coord = theta / (2 * math.pi)

                    ring.append((v, u_coord, pt_dist))
                grid_verts.append(ring)

            # --- D. CREATE FACES & SEAMS ---
            bm.verts.ensure_lookup_table()

            num_rings = len(grid_verts)
            num_rad = self.segments_radial

            for i in range(num_rings):
                next_i = (i + 1) % num_rings
                is_v_seam = next_i == 0  # Closing the length loop

                ring_curr = grid_verts[i]
                ring_next = grid_verts[next_i]

                for j in range(num_rad):
                    next_j = (j + 1) % num_rad
                    is_u_seam = next_j == 0  # Closing the radial loop

                    # Vert Data: (BMVert, u_raw, dist_raw)
                    d1 = ring_curr[j]
                    d2 = ring_next[j]
                    d3 = ring_next[next_j]
                    d4 = ring_curr[next_j]

                    try:
                        f = bm.faces.new((d1[0], d2[0], d3[0], d4[0]))
                        f.material_index = 0
                        f.smooth = True

                        # Apply UVs per loop
                        for l in f.loops:
                            vert = l.vert
                            u_val, v_dist = 0.0, 0.0

                            # Identify corner
                            if vert == d1[0]:
                                u_val, v_dist = d1[1], d1[2]
                            elif vert == d2[0]:
                                u_val, v_dist = d2[1], d2[2]
                            elif vert == d3[0]:
                                u_val, v_dist = d3[1], d3[2]
                            elif vert == d4[0]:
                                u_val, v_dist = d4[1], d4[2]

                            # 1. Handle V-Seam (Length Wrap)
                            if is_v_seam and (vert == d2[0] or vert == d3[0]):
                                v_dist += total_len

                            # 2. Handle U-Seam (Radial Wrap)
                            if is_u_seam and (vert == d3[0] or vert == d4[0]):
                                u_val += 1.0

                            l[uv_layer].uv = (u_val * su, v_dist * v_mult)

                    except ValueError:
                        pass  # Face exists

        # 3. GLOBAL CLEANUP
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 4. MARK SEAMS FROM UVs
        # Since UVs are procedurally perfect, we mark seams where UVs are disjoint.
        for e in bm.edges:
            if e.seam: 
                continue
            
            # Check for UV discontinuity
            if len(e.link_loops) >= 2:
                # Get UVs for this edge from adjacent faces
                uvs = []
                for l in e.link_loops:
                    uvs.append(l[uv_layer].uv)
                
                # If UVs are far apart, it's a seam
                # Simple check: Take the first loop's UV, compare against others
                # Note: This is an approximation loop. 
                # A generic "Is Seam" check usually involves checking adjacent loop UV coords for the same vertex.
                
                # Robust approach: Check edge verts.
                # If a vert has different UV coords in different loops connected to this edge, it's a boundary.
                
                # Optimization: We know specific topology.
                # But generic "Seam from UV" is safer for this complex torus.
                
                pass # Placeholder for more complex logic if needed.
                
        # SIMPLER: Force Material 0/1 Boundaries (if any)
        # Chain only has Slot 0 currently in generation (Material 1 is unused in loop)
        
        # Explicitly Mark Seams via Geometric Check?
        # NO, sticking to UV check pattern:
        for v in bm.verts:
            # If a vertex has multiple UV coordinates that are far apart, the edges using those splits are seams.
            pass
            
        # ACTUALLY: Let's use the explicit "Seam" flags we could have set in the loop.
        # But since we didn't, let's use a geometric property.
        # The chain links are smooth.
        # Let's mark the "Inner Loop" as a seam?
        # Or just rely on the UVs being correct, and if the user unwraps again, they lose the perfect mapping?
        # The USER REQUESTED: "make sure the seams... are aligned... so they unwrap correctly"
        # If we provide explicit UVs, we don't strictly *need* seams for the initial state.
        # BUT if the user hits "Unwrap", it fails without seams.
        # So we MUST reverse-engineer the seams.
        
        for e in bm.edges:
            if len(e.link_loops) < 2:
                continue
            
            l1 = e.link_loops[0]
            l2 = e.link_loops[1]
            
            # Compare UVs of the SAME vertex in the two loops
            # l.vert is the vertex at the start of the loop edge.
            # We need to find the specific shared vertex data.
            
            is_seam = False
            for v_target in e.verts:
                uv1 = None
                uv2 = None
                
                # Find the loop pointing to v_target (or starting at it)
                # This is tedious in BMesh API without helper.
                pass
                
        # BACKUP PLAN: Mark Edge Loops based on Topology
        # We know Radial Segs and Bend Segs.
        # This is hard to select on the fly.
        
        # FINAL DECISION for CHAIN:
        # Mark ALL edges that have sharp angles (there shouldn't be any).
        # Mark edges where UVs wrap (U ~ 0 and U ~ 1).
        
        for f in bm.faces:
            for l in f.loops:
                # Check adjacent loop across edge
                if l.edge.seam: continue
                if not l.link_loop_radial_next: continue
                
                l_other = l.link_loop_radial_next
                
                u1, v1 = l[uv_layer].uv
                u2, v2 = l_other[uv_layer].uv
                
                # Check dist
                if abs(u1 - u2) > 0.5 or abs(v1 - v2) > 0.5:
                    l.edge.seam = True
