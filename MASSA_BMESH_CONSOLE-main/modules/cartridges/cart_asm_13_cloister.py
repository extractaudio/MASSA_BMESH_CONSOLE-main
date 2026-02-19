import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_13: Cloister Corridor",
    "id": "asm_13_cloister",
    "icon": "MESH_CUBE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_AsmCloister(Massa_OT_Base):
    bl_idname = "massa.gen_asm_13_cloister"
    bl_label = "ASM_13 Cloister"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    length: FloatProperty(name="Length", default=4.0, min=1.0, unit="LENGTH")
    width: FloatProperty(name="Width", default=3.0, min=1.0, unit="LENGTH")
    wall_height: FloatProperty(name="Wall Height", default=2.5, min=1.0, unit="LENGTH")
    vault_height: FloatProperty(name="Vault Height", default=1.5, min=0.5, unit="LENGTH")

    # --- 2. VAULT ---
    vault_segments: IntProperty(name="Segments", default=8, min=3)
    rib_thick: FloatProperty(name="Rib Thick", default=0.1, min=0.01)
    rib_depth: FloatProperty(name="Rib Depth", default=0.1, min=0.01)

    # --- 3. DETAILS ---
    floor_thick: FloatProperty(name="Floor Thick", default=0.2, min=0.01)
    wall_thick: FloatProperty(name="Wall Thick", default=0.3, min=0.01)

    # --- 4. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Floor", "uv": "BOX", "phys": "STONE_MARBLE"},
            1: {"name": "Walls", "uv": "BOX", "phys": "STONE_BRICK"},
            2: {"name": "Vault", "uv": "BOX", "phys": "PLASTER"},
            3: {"name": "Ribs", "uv": "BOX", "phys": "STONE_MARBLE"},
            9: {"name": "Sockets", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "wall_height")
        col.prop(self, "vault_height")

        col.separator()
        col.label(text="Vault")
        col.prop(self, "vault_segments")
        col.prop(self, "rib_thick")
        col.prop(self, "rib_depth")

        col.separator()
        col.label(text="Structure")
        col.prop(self, "floor_thick")
        col.prop(self, "wall_thick")

    def build_shape(self, bm: bmesh.types.BMesh):
        l = self.length
        w = self.width
        wh = self.wall_height
        vh = self.vault_height
        segs = self.vault_segments
        wt = self.wall_thick
        ft = self.floor_thick
        rt = self.rib_thick
        rd = self.rib_depth

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale

        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 1. FLOOR
        # Center at origin? Or start at origin?
        # Let's center X (width) and start Y (length) at 0 to L.
        # X: -w/2 to w/2.

        res_floor = bmesh.ops.create_cube(bm, size=1.0)
        verts_floor = res_floor['verts']
        bmesh.ops.scale(bm, vec=(w + wt*2, l, ft), verts=verts_floor) # Add wall thickness to floor width?
        bmesh.ops.translate(bm, vec=(0, l/2, -ft/2), verts=verts_floor)

        for f in list({f for v in verts_floor for f in v.link_faces}):
            f.material_index = 0
            self.apply_box_map(f, uv_layer, scale)

        # 2. WALLS
        # Left Wall (-w/2 - wt/2)
        res_w1 = bmesh.ops.create_cube(bm, size=1.0)
        verts_w1 = res_w1['verts']
        bmesh.ops.scale(bm, vec=(wt, l, wh), verts=verts_w1)
        bmesh.ops.translate(bm, vec=(-w/2 - wt/2, l/2, wh/2), verts=verts_w1)

        # Right Wall (w/2 + wt/2)
        res_w2 = bmesh.ops.create_cube(bm, size=1.0)
        verts_w2 = res_w2['verts']
        bmesh.ops.scale(bm, vec=(wt, l, wh), verts=verts_w2)
        bmesh.ops.translate(bm, vec=(w/2 + wt/2, l/2, wh/2), verts=verts_w2)

        for f in list({f for v in verts_w1 + verts_w2 for f in v.link_faces}):
            f.material_index = 1
            self.apply_box_map(f, uv_layer, scale)

        # 3. VAULT
        # Proper Loop with Ribs at intervals
        y_segs = max(1, int(l)) # 1 segment per unit length approx
        dy = l / y_segs

        prev_verts = []
        # Create start profile
        for i in range(segs + 1):
            theta = (i / segs) * math.pi
            x = (w/2) * math.cos(theta)
            z = wh + vh * math.sin(theta)
            prev_verts.append(bm.verts.new((x, 0, z)))

        # Extrude in steps
        for j in range(y_segs):
            # Create edges from prev_verts
            edges_cross = []
            for i in range(len(prev_verts)-1):
                e = bm.edges.new((prev_verts[i], prev_verts[i+1]))
                edges_cross.append(e)
                e[edge_slots] = 2 # Rib (Cross edge)

            # Extrude
            res_ex = bmesh.ops.extrude_edge_only(bm, edges=edges_cross)
            verts_new = [v for v in res_ex['geom'] if isinstance(v, bmesh.types.BMVert)]
            faces_new = [f for f in res_ex['geom'] if isinstance(f, bmesh.types.BMFace)]

            bmesh.ops.translate(bm, vec=(0, dy, 0), verts=verts_new)

            for f in faces_new:
                f.material_index = 2
                self.apply_box_map(f, uv_layer, scale)

            # Update prev_verts (sorted by connection)
            # Extrude creates vertices in order usually, but safer to trace
            # Simplified: assuming order is preserved or we can deduce
            # Actually, `verts_new` order matches `edges_cross` order? Not guaranteed.
            # Best to trace edges.

            # Or simpler: Just create new verts and faces manually.
            # But extrude is convenient.
            # Let's just collect new verts.
            # We need them ordered for the NEXT loop.
            # The edges_cross[i] connects prev_verts[i] and [i+1].
            # The extruded face connects these to new verts.
            # We can find the new verts from the face loops.

            # Prepare next iteration:
            # We need the new vertices in order.
            # edges_cross[0] connects v0, v1.
            # Extruded face has v0, v1, v1_new, v0_new.
            # So we can map old->new.
            v_map = {}
            for f in faces_new:
                # Quad. 2 old verts, 2 new verts.
                vs = f.verts
                old_v = [v for v in vs if v in prev_verts]
                new_v = [v for v in vs if v not in prev_verts]
                # We need to map specific old to specific new.
                # Edges: (old1, old2), (new1, new2), (old1, new1), (old2, new2).
                for v_o in old_v:
                    for v_n in new_v:
                        if any(e.other_vert(v_o) == v_n for e in v_o.link_edges):
                            v_map[v_o] = v_n

            next_verts = [v_map[v] for v in prev_verts]
            prev_verts = next_verts

            # Mark final loop ribs
            if j == y_segs - 1:
                for i in range(len(prev_verts)-1):
                    e = bm.edges.get((prev_verts[i], prev_verts[i+1]))
                    if e: e[edge_slots] = 2

        # 4. SOCKETS
        # End-to-End
        # Input: (0, 0, wh/2) ? Center of wall height? Or Center of Vault?
        # Usually centered at Z=0 for snapping.
        # Or floor level.
        # Let's put them at (0, 0, 0) and (0, l, 0).

        # Start Socket (Input) - Facing -Y
        res_s1 = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.2)
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 4, 'X'), verts=res_s1['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, 0), verts=res_s1['verts']) # At origin
        for f in res_s1['faces']:
            f.material_index = 9
            f.normal_flip()

        # End Socket (Output) - Facing +Y
        res_s2 = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.2)
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 4, 'X'), verts=res_s2['verts'])
        bmesh.ops.translate(bm, vec=(0, l, 0), verts=res_s2['verts']) # At end
        for f in res_s2['faces']:
            f.material_index = 9
            # Normal is +Y by default (plane Z up rotated 90 X -> -Y? No. Z(0,0,1) -> X(90) -> (0,-1,0).
            # So S1 is -Y. S2 needs -Y? No, S2 is Target for next. Next S1 (-Y) snaps to S2 (+Y).
            # So S2 normal should be +Y.
            # Plane normal is +Z. Rot 90 X -> -Y.
            # So S1 is correct (-Y).
            # S2 needs flip to be +Y.
            pass # Keep default -Y? No, S2 needs to be +Y so S1 (-Y) mates with it (Normal alignment usually opposes).
            # If Snap aligns Normal to -Normal: S1(-Y) to S2(+Y). Correct.
            # If S1 is -Y (facing out from start).
            # S2 should be +Y (facing out from end).
            f.normal_flip() # Now +Y

        # Apex Sockets
        # At Z = wh + vh. Along Y.
        # Spaced every segment or center.
        # Let's do Center.
        apex_z = wh + vh - 0.1 # Slightly below ceiling
        res_sa = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.2)
        bmesh.ops.translate(bm, vec=(0, l/2, apex_z), verts=res_sa['verts'])
        for f in res_sa['faces']:
            f.material_index = 9
            # Facing Down? Plane normal Z.
            f.normal_flip() # Facing Down (-Z) to hang lights.

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

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
