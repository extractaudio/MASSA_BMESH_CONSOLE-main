import bpy

class MASSA_OT_ShootDispatcher(bpy.types.Operator):
    bl_idname = "massa.shoot_dispatcher"
    bl_label = "Shoot Generation"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        console = context.scene.massa_console

        # 1. Get Parameters
        cart_id = console.massa_staged_cartridge
        # Fix: bpy_prop_array doesn't have .copy(), use slicing to get a tuple/list copy
        target_loc = console.massa_target_coord[:]

        # 2. Save Cursor
        # Scene.cursor.location is a FloatVectorProperty, so slicing is safer here too
        cursor_loc = context.scene.cursor.location[:]

        # 3. Move Cursor to Target
        context.scene.cursor.location = target_loc

        # 4. Call Operator
        # We construct the operator name dynamically: massa.gen_{cart_id}
        op_id = f"gen_{cart_id}"

        try:
            if hasattr(bpy.ops.massa, op_id):
                # Call with INVOKE_DEFAULT to trigger Redo Panel
                # Massa_OT_Base will sync parameters from Console automatically in invoke()
                getattr(bpy.ops.massa, op_id)('INVOKE_DEFAULT')
            else:
                self.report({'ERROR'}, f"Operator massa.{op_id} not found")
                # Restore cursor
                context.scene.cursor.location = cursor_loc
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to shoot {cart_id}: {e}")
            # Restore cursor
            context.scene.cursor.location = cursor_loc
            return {'CANCELLED'}

        # 5. Restore Cursor
        context.scene.cursor.location = cursor_loc

        # 6. Reset Mode to Active (so Redo panel works on the new object)
        console.massa_op_mode = 'ACTIVE'

        return {'FINISHED'}
