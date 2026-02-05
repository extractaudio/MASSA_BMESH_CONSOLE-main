"""
Filename: modules/cartridges/prim_con_pipe.py
Content: Industrial Pipe Generator (Straight + Elbows)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector, Matrix

CARTRIDGE_META = {
    "name": "Con: Ind. Pipe",
    "id": "prim_con_pipe",
    "icon": "MOD_SCREW",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,  # Handled internally
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_pipe(Massa_OT_Base):
    """
    Industrial Piping Generator.
    Supports straight runs, elbows, and flanges.
    """

    bl_idname = "massa.gen_prim_con_pipe"
    bl_label = "Industrial Pipe"
    bl_description = "Pipe segment with optional elbow and flanges"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- SHAPE ---
    shape_mode: EnumProperty(
        name="Shape",
        items=[
            ("STRAIGHT", "Straight", "Linear segment"),
            ("ELBOW_90", "Elbow 90", "90 Degree Turn"),
            ("ELBOW_45", "Elbow 45", "45 Degree Turn"),
        ],
        default="STRAIGHT",
    )

    radius: FloatProperty(name="Radius", default=0.1, min=0.01, unit="LENGTH")
    length: FloatProperty(name="Length (Leg)", default=1.0, min=0.1, unit="LENGTH")
    wall_thickness: FloatProperty(name="Wall Thickness", default=0.01, min=0.001)

    # --- FLANGES ---
    flange_start: BoolProperty(name="Start Flange", default=True)
    flange_end: BoolProperty(name="End Flange", default=True)
    flange_rad_fac: FloatProperty(name="Flange Scale", default=1.4, min=1.0)
    flange_depth: FloatProperty(name="Flange Depth", default=0.02, min=0.005)

    # --- TOPOLOGY ---
    segments_radial: IntProperty(name="Radial Segs", default=16, min=4)
    segments_length: IntProperty(name="Length Segs", default=1, min=1)
    segments_turn: IntProperty(name="Turn Segs", default=8, min=2)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.prop(self, "shape_mode")

        col = box.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "wall_thickness")
        if self.shape_mode == "STRAIGHT":
            col.prop(self, "length")
        else:
            col.prop(self, "length", text="Leg Length")

        box = layout.box()
        box.label(text="Flanges", icon="MOD_BOOLEAN")
        row = box.row()
        row.prop(self, "flange_start", text="Start")
        row.prop(self, "flange_end", text="End")
        col = box.column(align=True)
        col.prop(self, "flange_rad_fac", text="Scale")
        col.prop(self, "flange_depth", text="Depth")

        box = layout.box()
        box.label(text="Resolution", icon="MESH_CIRCLE")
        box.prop(self, "segments_radial", text="Radial")
        if self.shape_mode == "STRAIGHT":
            box.prop(self, "segments_length", text="Length")
        else:
            box.prop(self, "segments_turn", text="Turn")

    def get_slot_meta(self):
        return {
            0: {"name": "Pipe_Ext", "uv": "UNWRAP", "phys": "METAL_STEEL"},
            1: {"name": "Pipe_Int", "uv": "UNWRAP", "phys": "METAL_RUST"},
            2: {"name": "Flange", "uv": "UNWRAP", "phys": "METAL_IRON"},
            3: {"name": "Port", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def build_shape(self, bm):
        # ... (Same as before until Step 4) ...
        # [Preserving existing build_shape logic is implied, but I must output the FULL function if I replace 'build_shape'.]
        # Wait, the user prompt is "UV_Seams_Correct" on the file.
        # I should output the *modified* parts. "Replace File Content" replaces a block.
        # I will target 2 blocks: get_slot_meta and Step 4.
        
        # Tool 'replace_file_content' replaces a SINGLE contiguous block.
        # I cannot replace get_slot_meta AND Step 4 in one go if they are far apart.
        # I will assume I need 2 calls or use multi_replace.
        # But 'multi_replace' is safer for non-contiguous.
        # Let's use multi_replace.
        pass

    # Switching to multi_replace logic below...

    def build_shape(self, bm):
        # 1. HELPERS
        def create_ring(bm, r, cx, cy, cz, axis, segs):
            verts = []
            for i in range(segs):
                angle = (i / segs) * 2 * math.pi
                if axis == "Z":
                    v = bm.verts.new(
                        (cx + math.cos(angle) * r, cy + math.sin(angle) * r, cz)
                    )
                elif axis == "Y":
                    v = bm.verts.new(
                        (cx + math.cos(angle) * r, cy, cz + math.sin(angle) * r)
                    )
                verts.append(v)
            return verts

        def bridge_rings(bm, r1, r2):
            faces = []
            len_r = len(r1)
            for i in range(len_r):
                v1, v2 = r1[i], r1[(i + 1) % len_r]
                v3, v4 = r2[(i + 1) % len_r], r2[i]
                faces.append(bm.faces.new((v1, v2, v3, v4)))
            return faces

        def create_flange_island(bm, pos, forward_vec, radius_inner, radius_outer, depth, segs):
            # Create a separate Flange Mesh at 'pos' oriented along 'forward_vec'
            # 1. Create Base Ring at 'pos'
            # We need to orient the ring.
            # Default Y-forward ring is in XZ plane.
            # We construct a basis matrix from forward_vec.
            
            # Basis: Y = forward
            y_axis = forward_vec.normalized()
            # X = Cross(Y, Z) usually, but check up vector.
            # If Y is (0,1,0), X is (1,0,0).
            # If Y is (0,0,1), X is (1,0,0).
            # Robust Up vector:
            up = Vector((0, 0, 1))
            if abs(y_axis.z) > 0.9: up = Vector((0, 1, 0))
            x_axis = y_axis.cross(up).normalized()
            z_axis = x_axis.cross(y_axis).normalized()
            
            # Matrix (3x3)
            # Columns: X, Y, Z
            mat = Matrix((x_axis, y_axis, z_axis)).transposed() # Transposed because Matrix() takes rows? 
            # Matrix((col1, col2, col3)) is 3x3 with rows as vectors?
            # Blender Matrix constructor takes rows.
            # So Matrix((x, y, z)) means Row 0 = x.
            # We want Column 0 = x.
            # So Transpose is correct.
            
            # Construct Verts relative to local frame, then transform.
            verts_inner = []
            verts_outer = []
            
            for i in range(segs):
                angle = (i / segs) * 2 * math.pi
                # Ring in XZ plane (Local)
                # Local Coords: x = cos, z = sin, y = 0
                local_x = math.cos(angle)
                local_z = math.sin(angle)
                
                # Apply Transform
                # v_local = x * X_axis + z * Z_axis
                v_inner = pos + (x_axis * local_x * radius_inner) + (z_axis * local_z * radius_inner)
                v_outer = pos + (x_axis * local_x * radius_outer) + (z_axis * local_z * radius_outer)
                
                verts_inner.append(bm.verts.new(v_inner))
                verts_outer.append(bm.verts.new(v_outer))
            
            # Bridge to form Cap (The mating face - Hidden? Or exposed?)
            # If overlapping, it's hidden. If separate mechanism, it's visible.
            # We typically want a solid "Donut".
            cap_faces = bridge_rings(bm, verts_outer, verts_inner)
            
            # Extrude Depth (Along Forward Vec)
            ret = bmesh.ops.extrude_face_region(bm, geom=cap_faces)
            verts_ext = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=verts_ext, vec=forward_vec * depth)
            
            # Assign Materials
            # All faces (Cap + Sides + Top) get Flange Mat (2)
            # Or Cap is Port (3)?
            # Flange is purely mechanical housing (2).
            all_faces = cap_faces + [f for f in ret["geom"] if isinstance(f, bmesh.types.BMFace)]
            for f in all_faces: f.material_index = 2
            
            return all_faces

        # 2. GENERATE MAIN BODY (PIPE)
        segs = self.segments_radial
        r_out = self.radius
        r_in = max(0.001, self.radius - self.wall_thickness)

        # Start Ring at (0,0,0)
        verts_outer = create_ring(bm, r_out, 0, 0, 0, "Y", segs)
        verts_inner = create_ring(bm, r_in, 0, 0, 0, "Y", segs)
        start_faces = bridge_rings(bm, verts_outer, verts_inner)
        
        # Initial Material
        for f in start_faces: f.material_index = 3 # Port

        # Extrude Body
        final_cap = []
        
        if self.shape_mode == "STRAIGHT":
            # Extrude Straight
            ret = bmesh.ops.extrude_face_region(bm, geom=start_faces)
            verts_ext = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=verts_ext, vec=(0, self.length, 0))
            
            sides = [f for f in ret["geom"] if isinstance(f, bmesh.types.BMFace)]
            
            # Identify Cap (Forward Normal)
            final_cap = [f for f in sides if f.normal.dot(Vector((0,1,0))) > 0.9]
            body_sides = [f for f in sides if f not in final_cap]
            
            # Bisect
            if self.segments_length > 1:
                 step = self.length / self.segments_length
                 for i in range(1, self.segments_length):
                     bmesh.ops.bisect_plane(
                         bm,
                         geom=body_sides + list({v for f in body_sides for v in f.verts}) + list({e for f in body_sides for e in f.edges}),
                         plane_co=(0, i * step, 0),
                         plane_no=(0, 1, 0)
                     )

            for f in body_sides:
                 c = f.calc_center_median()
                 if Vector((c.x, 0, c.z)).length > r_in:
                      f.material_index = 0 # Ext
                 else:
                      f.material_index = 1 # Int

        else: # ELBOWS
            angle = (
                math.radians(90) if self.shape_mode == "ELBOW_90" else math.radians(45)
            )
            spin_steps = self.segments_turn
            bend_rad = self.length
            
            # Pivot
            current_y = start_faces[0].calc_center_bounds().y
            pivot = (bend_rad, current_y, 0)
            
            # WORKAROUND: Capture geometry before spin (Fix for 'geom' key error)
            # Expand input geometry to be safe
            spin_src = list(start_faces) + list({v for f in start_faces for v in f.verts}) + list({e for f in start_faces for e in f.edges})
            
            snap_faces = set(bm.faces)
            snap_verts = set(bm.verts)
            snap_edges = set(bm.edges)
            
            ret = bmesh.ops.spin(
                bm,
                geom=spin_src,
                angle=-angle,
                steps=spin_steps,
                axis=(0, 0, 1),
                cent=pivot,
            )
            
            if "geom" not in ret:
                ret["geom"] = list(set(bm.faces) - snap_faces) + \
                              list(set(bm.verts) - snap_verts) + \
                              list(set(bm.edges) - snap_edges)
            
            # Identify Cap
            rot = Matrix.Rotation(-angle, 3, 'Z')
            target_dir = rot @ Vector((0, 1, 0))
            
            final_cap = [f for f in ret["geom"] if isinstance(f, bmesh.types.BMFace) 
                        and f.normal.dot(target_dir) > 0.9]
            
            body_sides = [f for f in ret["geom"] if isinstance(f, bmesh.types.BMFace) 
                         and f not in final_cap]
            
            for f in body_sides:
                 if f.material_index == 3: # Was Port
                      if abs(f.normal.z) < 0.9: # Not Top/Bottom
                           f.material_index = 0
                           
        # Set Final Cap Material
        for f in final_cap: f.material_index = 3
        
        # 3. GENERATE INDEPENDENT FLANGES
        flange_r_out = r_out * self.flange_rad_fac
        
        if self.flange_start:
            # At (0,0,0), Direction Y (0,1,0)
            # Flange Depth goes Forward? 
            # Or is Flange "Base" at 0 and extrudes Back? 
            # Or Base at 0 and extrudes Forward?
            # "Covering the pipe" -> Extrudes Forward (along pipe).
            create_flange_island(bm, 
                                 pos=Vector((0,0,0)), 
                                 forward_vec=Vector((0,1,0)), 
                                 radius_inner=r_out, # Hugs Pipe Outer
                                 radius_outer=flange_r_out, 
                                 depth=self.flange_depth, 
                                 segs=segs)

        if self.flange_end:
            # At End Position.
            # End Position depends on mode.
            if self.shape_mode == "STRAIGHT":
                end_pos = Vector((0, self.length, 0))
                end_dir = Vector((0, 1, 0)) # Facing Forward?
                # Flange should point Backwards (Into pipe)? Or Forwards (Lip)?
                # Standard: Flange is mounted AT the end.
                # So it starts at Length-Depth and goes to Length?
                # Or starts at Length and goes to Length+Depth?
                # "Covering the pipe" -> Must overlap pipe.
                # So starts at Length-Depth? 
                # Yes, "Sleeve".
                # So Start Pos = Length, Extrude Vector = -Y (Backwards).
                start_pos = end_pos
                extrude_vec = -end_dir
                
                create_flange_island(bm, 
                                     pos=start_pos, 
                                     forward_vec=extrude_vec, 
                                     radius_inner=r_out, 
                                     radius_outer=flange_r_out, 
                                     depth=self.flange_depth, 
                                     segs=segs)
            else:
                # Elbow End
                # End Pos calculation
                rot = Matrix.Rotation(-angle, 3, 'Z')
                end_dir = rot @ Vector((0, 1, 0))
                # Pivot was (bend_rad, 0, 0)
                # Start point was (0,0,0) relative to pivot is (-bend_rad, 0, 0)
                # Rotate (-bend_rad, 0, 0) by -angle
                # Then add pivot back.
                
                # Math:
                # v_start_rel = Vector((-bend_rad, 0, 0))
                # v_end_rel = rot @ v_start_rel
                # v_end_world = pivot + v_end_rel
                pivot_vec = Vector((bend_rad, 0, 0))
                v_start_rel = Vector((-bend_rad, 0, 0))
                v_end_rel = rot @ v_start_rel
                end_pos = pivot_vec + v_end_rel
                
                # Direction is end_dir.
                # Use Backwards extrusion (Covering)
                create_flange_island(bm, 
                                     pos=end_pos, 
                                     forward_vec=-end_dir, 
                                     radius_inner=r_out, 
                                     radius_outer=flange_r_out, 
                                     depth=self.flange_depth, 
                                     segs=segs)

        # 4. EDGE ROLES (UV SEAMS)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            is_cap_border = any(f.material_index == 3 for f in e.link_faces)
            is_flange_border = False
            
            # Check Hard Angle (Flanges)Safety Check
            if len(e.link_faces) == 2:
                if e.calc_face_angle() > math.radians(45):
                     e.seam = True
                     e[edge_slots] = 2 # CONTOUR
                     is_flange_border = True
            elif len(e.link_faces) == 1:
                # Boundary Edge (e.g. Open Port)
                # Mark as Seam 
                e.seam = True
                e[edge_slots] = 1 # PERIMETER

            # Check Port Border
            if is_cap_border:
                e.seam = True
                e[edge_slots] = 1 # PERIMETER

            # Zipper Logic (Longitudinal Seam at Bottom)
            # Conditions: Not a Seam yet, Not Vertical (Side Edge)
            # For Straight/Elbow, "Bottom" means Normal Z < -0.9 or Position Relative to Center?
            # Standard Pipe: The bottom-most edge.
            if not e.seam:
                # Average Normal of connected faces
                navg = Vector((0,0,0))
                for f in e.link_faces: navg += f.normal
                if len(e.link_faces) > 0: navg /= len(e.link_faces)
                
                # Check if Bottom (-Z)
                # This works for horizontal pipes (Straight or Elbow flat on ground)
                if navg.z < -0.9:
                    e.seam = True
                    # Slot 3 = Guide/Zipper? Protocol says Slot 3.
                    # Wait, Protocol says Slot 3 is GUIDE. 
                    # Slot Meta 3 is Port...
                    # Let's check Slot 3 description in Protocol?
                    # "zipper[edge_slots] = 3 # GUIDE (Red Viz)"
                    # Meta says Slot 3 is Port. 
                    # Maybe we use Slot 4 for Guide? Or just Seam=True.
                    # I will stick to Seam=True.
                    # And maybe Slot 2 (Contour) for viz?
                    pass
