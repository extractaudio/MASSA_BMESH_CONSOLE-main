import bpy
from bpy.types import GizmoGroup
from mathutils import Vector, Matrix

class MASSA_GGT_GizmoGroup(GizmoGroup):
    bl_idname = "MASSA_GGT_gizmo_group"
    bl_label = "Massa Gizmos"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'DEPTH_3D', 'SHOW_MODAL_ALL'}

    @classmethod
    def poll(cls, context):
        # Only show if object is selected and is a Massa object
        obj = context.active_object
        if not obj:
            return False
        # Ensure we are in Object Mode
        if context.mode != 'OBJECT':
            return False
        # Check for Massa ID
        return "massa_op_id" in obj

    def setup(self, context):
        # 1. Resurrection Button (Top)
        gz_res = self.gizmos.new("GIZMO_GT_button_2d")
        gz_res.icon = 'ORPHAN_DATA'

        # Yellow
        gz_res.color = 0.8, 0.8, 0.0
        gz_res.color_highlight = 1.0, 1.0, 0.2
        gz_res.alpha = 0.8
        gz_res.scale_basis = 0.15 # Small size



        gz_res.target_set_operator("massa.resurrect_wrapper")
        self.gizmo_resurrect = gz_res

        # 2. Condemnation Button (Bottom)
        gz_con = self.gizmos.new("GIZMO_GT_button_2d")
        gz_con.icon = 'MATFLUID'

        # Red
        gz_con.color = 0.8, 0.1, 0.1
        gz_con.color_highlight = 1.0, 0.2, 0.2
        gz_con.alpha = 0.8
        gz_con.scale_basis = 0.15



        gz_con.target_set_operator("massa.condemn")
        self.gizmo_condemn = gz_con

    def draw_prepare(self, context):
        """
        Updates the matrix of the gizmos so they track the object.
        Called every redraw.
        """
        try:
            # Validate Gizmos exist
            if not hasattr(self, "gizmo_condemn") or not hasattr(self, "gizmo_resurrect"):
                return
    
            obj = context.active_object
            if not obj: 
                return
    
            # [ARCHITECT FIX] Robust World Space Calculation
            # This ensures even if bound_box is weird, we have a fallback
            pos_x, pos_y, top_z = 0.0, 0.0, 0.0
            
            # Use Matrix World Translation as base
            base_loc = obj.matrix_world.translation
            pos_x, pos_y = base_loc.x, base_loc.y
            top_z = base_loc.z
    
            # Attempt to add Bounding Box height
            if obj.type == 'MESH' and obj.bound_box:
                # Transform all 8 corners to world space to find true max Z
                # This handles rotation correctly
                world_corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
                top_z = max(v.z for v in world_corners)
                
                # Approximate center (optional, but nicer)
                pos_x = sum(v.x for v in world_corners) / 8.0
                pos_y = sum(v.y for v in world_corners) / 8.0
    
            # Set Positions
            # Condemn (Red) -> Lower
            self.gizmo_condemn.matrix_basis = Matrix.Translation((pos_x, pos_y, top_z + 0.5))
            
            # Resurrect (Yellow) -> Upper
            self.gizmo_resurrect.matrix_basis = Matrix.Translation((pos_x, pos_y, top_z + 1.0))
            
        except Exception as e:
            # Fail silently to avoid spamming console during interaction
            # print(f"Gizmo Draw Error: {e}")
            pass
