import bpy

class MASSA_OT_Condemn(bpy.types.Operator):
    """
    Finalizes the Massa Smart Object.
    Applies all modifiers and strips Massa metadata/parameters,
    turning it into a standard static Mesh.
    """
    bl_idname = "massa.condemn"
    bl_label = "Condemn (Finalize)"
    bl_description = "Finalize the object: Apply modifiers and remove smart attributes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and "massa_op_id" in obj

    def execute(self, context):
        obj = context.active_object

        # Apply all modifiers to mesh (Bake)
        try:
            # This applies all modifiers and converts to mesh
            bpy.ops.object.convert(target='MESH')
        except Exception as e:
            self.report({'ERROR'}, f"Failed to apply modifiers: {e}")
            return {'CANCELLED'}

        # Remove Metadata to "dumb down" the object
        keys_to_remove = ["massa_op_id", "MASSA_PARAMS", "MASSA_TEMP_RESTORE"]
        for k in keys_to_remove:
            if k in obj:
                try:
                    del obj[k]
                except:
                    pass

        self.report({'INFO'}, "Object Condemned (Finalized)")
        return {'FINISHED'}


class MASSA_OT_Resurrect_Wrapper(bpy.types.Operator):
    """
    Wrapper to trigger the resurrection (re-run) of the specific
    operator that created this object. Used by Gizmos.
    """
    bl_idname = "massa.resurrect_wrapper"
    bl_label = "Resurrect"
    bl_description = "Regenerate this object (Open Settings)"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and "massa_op_id" in obj

    def execute(self, context):
        obj = context.active_object
        op_id = obj.get("massa_op_id")

        if not op_id:
            self.report({'ERROR'}, "No Operator ID found on object")
            return {'CANCELLED'}

        # Parse op_id (e.g. "massa.gen_box") and call it
        try:
            parts = op_id.split('.')
            if len(parts) != 2:
                 self.report({'ERROR'}, f"Invalid Operator ID format: {op_id}")
                 return {'CANCELLED'}

            category, name = parts

            if not hasattr(bpy.ops, category):
                self.report({'ERROR'}, f"Operator category '{category}' not found")
                return {'CANCELLED'}

            op_module = getattr(bpy.ops, category)

            if not hasattr(op_module, name):
                self.report({'ERROR'}, f"Operator '{name}' not found in '{category}'")
                return {'CANCELLED'}

            op_func = getattr(op_module, name)

            # Call with rerun_mode=True to trigger the resurrection logic in Massa_OT_Base
            # [ARCHITECT FIX] Use 'INVOKE_DEFAULT' to ensure properties are initialized
            # and potential UI panels are respected.
            if hasattr(op_func, "poll") and not op_func.poll():
                 self.report({'WARNING'}, f"Operator {name} poll failed. Context may be invalid.")
                 return {'CANCELLED'}
            
            # Force execution
            op_func('INVOKE_DEFAULT', rerun_mode=True)
            
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Resurrection failed: {e}")
            return {'CANCELLED'}
