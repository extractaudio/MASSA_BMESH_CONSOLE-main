import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARC_04: Universal Portal",
    "id": "arc_04_doorway",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcDoorway(Massa_OT_Base):
    bl_idname = "massa.gen_arc_04_doorway"
    bl_label = "ARC Doorway"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    door_width: FloatProperty(name="Width", default=1.0, min=0.1)
    door_height: FloatProperty(name="Height", default=2.1, min=0.1)
    frame_width: FloatProperty(name="Frame W", default=0.1, min=0.01)
    frame_depth: FloatProperty(name="Frame D", default=0.15, min=0.01)

    # Leaf
    leaf_thick: FloatProperty(name="Leaf T", default=0.05, min=0.01)
    open_angle: FloatProperty(name="Open Angle", default=0.0, min=-180, max=180)

    # Hardware
    handle_height: FloatProperty(name="Handle H", default=1.0, min=0.1)

    # === REDO-PANEL SAFE UI ELEMENTS ===
    massa_hide_ui: bpy.props.BoolProperty(name="Hide UI (Redo Trap)", default=False)
    massa_scene_proxy: bpy.props.StringProperty(name="Scene Proxy", default="null")

    def get_slot_meta(self):
        return {
            0: {"name": "Door Leaf", "uv": "SKIP", "phys": "WOOD"},
            1: {"name": "Frame", "uv": "BOX", "phys": "WOOD"},
            7: {"name": "Hardware", "uv": "BOX", "phys": "METAL_BRASS"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        # 2. Parameters
        fw = self.frame_width
        fd = self.frame_depth
        dw = self.door_width
        dh = self.door_height
        lt = self.leaf_thick

        # ---------------------------------------------------------
        # 3. FRAME GENERATION (With Stop Detail)
        # ---------------------------------------------------------
        
        # Helper lists to track geometry
        frame_faces = []
        
        # -- Left Jamb --
        res_L = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((fw, fd, dh + fw)), verts=res_L['verts'])
        bmesh.ops.translate(bm, vec=Vector((-dw/2 - fw/2, 0, (dh + fw)/2)), verts=res_L['verts'])
        frame_faces.extend([f for v in res_L['verts'] for f in v.link_faces])

        # -- Right Jamb --
        res_R = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((fw, fd, dh + fw)), verts=res_R['verts'])
        bmesh.ops.translate(bm, vec=Vector((dw/2 + fw/2, 0, (dh + fw)/2)), verts=res_R['verts'])
        frame_faces.extend([f for v in res_R['verts'] for f in v.link_faces])

        # -- Header --
        res_H = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((dw + 2*fw, fd, fw)), verts=res_H['verts'])
        bmesh.ops.translate(bm, vec=Vector((0, 0, dh + fw/2)), verts=res_H['verts'])
        frame_faces.extend([f for v in res_H['verts'] for f in v.link_faces])

        # Remove doubles to fuse frame if they touch (they might not depending on math, but good practice)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        
        # Re-gather frame faces after cleanup
        # (We rely on material index later, so let's tag them now)
        for f in bm.faces:
             f.material_index = 1

        # -- Frame Stop Detail (The strip the door hits) --
        # Logic: Select inner faces of the frame and extrude them inwards slightly
        # Inner faces:
        # Left Jamb: x > 0 (Normal approx (1,0,0))
        # Right Jamb: x < 0 (Normal approx (-1,0,0))
        # Header: z < 0 (Normal approx (0,0,-1))
        
        stop_faces = []
        for f in bm.faces:
            if f.material_index != 1: continue
            
            n = f.normal
            c = f.calc_center_median()
            
            # Left Jamb Inner (approximated location checks)
            is_left_inner = c.x < -dw/2 and abs(n.x - 1) < 0.1
            # Right Jamb Inner
            is_right_inner = c.x > dw/2 and abs(n.x + 1) < 0.1
            # Header Inner
            is_header_inner = c.z > dh and abs(n.z + 1) < 0.1
            
            if is_left_inner or is_right_inner or is_header_inner:
                stop_faces.append(f)

        if stop_faces:
            # Inset to create the stop width
            # We want a stop that is maybe 1/3 of the frame depth?
            # Or just a simple strip. Let's do a simple extrusion for the stop.
            
            # Actually, a physical stop is usually a small strip ADDED to the frame.
            # Let's simple create a cube for the stop to avoid complex inset logic on potentially non-manifold fused geometry.
            
            stop_thick = 0.02
            stop_width = 0.03
            
            # Left Stop
            res_SL = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((stop_thick, stop_width, dh)), verts=res_SL['verts'])
            # Pos: Inside face of left jamb (-dw/2), offset by stop_thick/2
            # Y Pos: slightly offset from center to stop the door? 
            # If door is centered (y=0), stop should be at y +/- something.
            # Let's put stop at y = lt/2 (behind door)
            bmesh.ops.translate(bm, vec=Vector((-dw/2 + stop_thick/2, lt/2 + stop_width/2, dh/2)), verts=res_SL['verts'])

            # Right Stop
            res_SR = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((stop_thick, stop_width, dh)), verts=res_SR['verts'])
            bmesh.ops.translate(bm, vec=Vector((dw/2 - stop_thick/2, lt/2 + stop_width/2, dh/2)), verts=res_SR['verts'])
            
            # Header Stop
            res_SH = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((dw, stop_width, stop_thick)), verts=res_SH['verts'])
            bmesh.ops.translate(bm, vec=Vector((0, lt/2 + stop_width/2, dh - stop_thick/2)), verts=res_SH['verts'])

            # Tag stops as frame
            for v in res_SL['verts'] + res_SR['verts'] + res_SH['verts']:
                for f in v.link_faces:
                    f.material_index = 1

        # ---------------------------------------------------------
        # 4. DOOR LEAF GENERATION (With Panels)
        # ---------------------------------------------------------
        
        # Create Main Leaf Cube
        res_D = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((dw, lt, dh)), verts=res_D['verts'])
        # Initial pos: Centered at (0, 0, dh/2).
        bmesh.ops.translate(bm, vec=Vector((0, 0, dh/2)), verts=res_D['verts'])
        
        door_verts = res_D['verts'][:] # copy list
        
        # Panel Detail
        # Select Front/Back faces
        panel_faces = set()
        for v in door_verts:
            for f in v.link_faces:
                f.material_index = 0
                # Front is Y-, Back is Y+ (or vice versa standard)
                if abs(f.normal.y) > 0.9:
                    panel_faces.add(f)
        
        # Convert to list for bmesh ops
        panel_faces = list(panel_faces)
        
        # Inset to create rails/stiles
        # Safety: ensure lookup
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        if panel_faces:
            # First Inset: Create the Rail/Stile border
            res_inset = bmesh.ops.inset_region(bm, faces=panel_faces, thickness=0.1, depth=0.0)
            
            # Identify the inner faces from the inset result
            # bmesh.ops.inset_region returns 'faces' which are the *new* faces (the rim?) 
            # documentation says: "faces": output faces. usually the inner faces.
            inner_faces = res_inset['faces']
            
            # Second Inset/Extrude: Create the Panel Recess
            # We can subdivide these inner faces to make multiple panels, but for ARC_04 let's keep it simple:
            # Single large shaker style panel or 2 vertical panels?
            # Let's do a simple bevel-like recess.
            
            bmesh.ops.inset_region(bm, faces=inner_faces, thickness=0.03, depth=-0.015)
            
            # Note: For complex multi-panel, we would use grid fill or bisect. 
            # This simple inset gives a "Shaker" look.

        # ---------------------------------------------------------
        # 5. HARDWARE (Improved)
        # ---------------------------------------------------------
        
        # Backplate (thin chamfered cube)
        res_Plate = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.06, 0.01, 0.2)), verts=res_Plate['verts'])
        
        # Knob (Cylinder-ish - approximate with low poly cube or modify)
        # Let's make a simple join: Plate + Handle
        
        # Move Plate to position
        # Right side: (dw/2 - 0.1, lt/2 + 0.005, handle_height)
        # Plate sits on surface of door (y = lt/2 + plate_thick/2)
        plate_y = lt/2 + 0.005
        handle_offset = Vector((dw/2 - 0.1, plate_y, self.handle_height))
        bmesh.ops.translate(bm, vec=handle_offset, verts=res_Plate['verts'])

        # Handle/Lever
        res_Hnd = bmesh.ops.create_cube(bm, size=1.0)
        # Lever shape: long horizontal
        bmesh.ops.scale(bm, vec=Vector((0.12, 0.02, 0.02)), verts=res_Hnd['verts'])
        # Offset from plate
        lever_offset = handle_offset + Vector((-0.03, 0.03, 0.0)) 
        bmesh.ops.translate(bm, vec=lever_offset, verts=res_Hnd['verts'])

        hardware_verts = res_Plate['verts'] + res_Hnd['verts']
        for v in hardware_verts:
            for f in v.link_faces:
                f.material_index = 7

        # ---------------------------------------------------------
        # 6. OPENING ROTATION
        # ---------------------------------------------------------
        
        # Pivot is Hinge Axis. Left Hinge (-dw/2, 0, 0)
        pivot = Vector((-dw/2, 0, 0)) 
        rot_mat = Matrix.Rotation(math.radians(self.open_angle), 3, 'Z')
        
        # Collect all Door + Hardware verts to rotate
        # We need to be careful to select ONLY them.
        # We can use a set of verts logic or simple traversal since we just created them.
        # But we did operations (inset) that created new verts.
        
        # Reliable method: Select by connection to the door leaf center? 
        # Or traverse from a known seed.
        # Or simpler: Rotate everything that is NOT material index 1 (Frame)
        
        rotate_verts = []
        for v in bm.verts:
            # Check if any face linked to this vert is NOT frame (Mat 1)
            is_frame = True
            if not v.link_faces: 
                 # loose vert? shouldn't happen but check
                 continue
                 
            for f in v.link_faces:
                if f.material_index != 1:
                    is_frame = False
                    break
            
            if not is_frame:
                rotate_verts.append(v)
                
        if abs(self.open_angle) > 0.001:
            bmesh.ops.rotate(bm, cent=pivot, matrix=rot_mat, verts=rotate_verts)


        # ---------------------------------------------------------
        # 7. Final UVs
        # ---------------------------------------------------------
        scale = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            uv_layer = bm.loops.layers.uv.verify()
            
            # Simple Box Mapping Logic
            n = f.normal
            if abs(n.x) > 0.5:
                # Side -> YZ
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
            elif abs(n.y) > 0.5:
                # Front -> XZ
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
            else:
                # Top -> XY
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)

    def draw_shape_ui(self, layout):
        if self.massa_hide_ui:
            layout.label(text="UI Hidden (Redo Trap)", icon='ERROR')
            layout.prop(self, "massa_hide_ui", toggle=True, text="Show UI", icon='RESTRICT_VIEW_OFF')
            return

        box = layout.box()
        row = box.row()
        row.prop(self, "massa_hide_ui", text="Lock UI", icon='LOCKED')
        row.label(text="Doorway Configuration")

        col = layout.column(align=True)
        col.prop(self, "door_width")
        col.prop(self, "door_height")
        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")
        layout.separator()
        col.prop(self, "leaf_thick")
        col.prop(self, "open_angle")
        col.prop(self, "handle_height")
