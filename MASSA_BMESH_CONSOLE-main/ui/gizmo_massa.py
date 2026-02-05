import bpy
from bpy.types import GizmoGroup
from mathutils import Vector

class MASSA_GGT_GizmoGroup(GizmoGroup):
    bl_idname = "MASSA_GGT_gizmo_group"
    bl_label = "Massa Gizmos"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        # Only show if object is selected and is a Massa object
        obj = context.object
        return obj and obj.select_get() and "massa_op_id" in obj

    def setup(self, context):
        # 1. Resurrection Button (Top)
        gz_res = self.gizmos.new("GIZMO_GT_button_2d")
        gz_res.icon = 'ORPHAN_DATA'

        # Yellow
        gz_res.color = 0.8, 0.8, 0.0
        gz_res.color_highlight = 1.0, 1.0, 0.2
        gz_res.alpha = 0.8
        gz_res.scale_basis = 0.15 # Small size

        # Tooltip text
        gz_res.message = "Resurrection"

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

        # Tooltip text
        gz_con.message = "Condemnation"

        gz_con.target_set_operator("massa.condemn")
        self.gizmo_condemn = gz_con

    def draw_prepare(self, context):
        obj = context.object
        if not obj: return

        # Calculate positioning above the object
        # We use bounding box to find the highest point relative to world space
        try:
            bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            center_x = sum(v.x for v in bbox) / 8.0
            center_y = sum(v.y for v in bbox) / 8.0
            max_z = max(v.z for v in bbox)
        except:
            # Fallback if bbox calculation fails or invalid
            center_x = obj.matrix_world.translation.x
            center_y = obj.matrix_world.translation.y
            max_z = obj.matrix_world.translation.z

        # Position 1 (Condemnation - Red - Lower)
        # 0.4m above the top
        pos_con = Vector((center_x, center_y, max_z + 0.4))

        # Position 2 (Resurrection - Yellow - Upper)
        # 0.4m above Condemnation (0.8m total)
        pos_res = Vector((center_x, center_y, max_z + 0.8))

        self.gizmo_condemn.matrix_basis.translation = pos_con
        self.gizmo_resurrect.matrix_basis.translation = pos_res
