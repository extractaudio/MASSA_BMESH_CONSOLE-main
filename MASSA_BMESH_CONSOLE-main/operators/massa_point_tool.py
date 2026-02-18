import bpy
import bpy_extras.view3d_utils

class MASSA_OT_PickCoordinate(bpy.types.Operator):
    bl_idname = "massa.pick_coordinate"
    bl_label = "Pick Coordinate"
    bl_options = {"REGISTER", "UNDO"}

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            context.window.cursor_modal_restore()
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.update_target(context, event)
            context.window.cursor_modal_restore()
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            pass

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            context.window.cursor_modal_set('PAINT_CROSS')
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

    def update_target(self, context, event):
        # Raycast Logic
        region = context.region
        rv3d = context.region_data
        coord = event.mouse_region_x, event.mouse_region_y

        # Get ray from viewport
        view_vector = bpy_extras.view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = bpy_extras.view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        # Raycast into scene
        hit, loc, norm, idx, obj, mat = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)

        if hit:
            context.scene.massa_console.massa_target_coord = loc
            self.report({'INFO'}, f"Target Set: {loc}")
        else:
            # Fallback: Project onto grid (Z=0 plane)
            # ray_origin + t * view_vector. Z = 0 => ray_origin.z + t * view_vector.z = 0 => t = -ray_origin.z / view_vector.z
            if abs(view_vector.z) > 0.0001:
                t = -ray_origin.z / view_vector.z
                if t > 0:
                     loc = ray_origin + t * view_vector
                     context.scene.massa_console.massa_target_coord = loc
                     self.report({'INFO'}, f"Target Set (Grid): {loc}")
