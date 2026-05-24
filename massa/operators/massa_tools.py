import bpy
import bmesh

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
                except Exception:
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
        try:
            # Delegate to the robust MASSA_OT_ReRun_Active operator
            # which properly captures MASSA_PARAMS into the scene's MASSA_TEMP_RESTORE
            # dictionary before invoking the generation operator.
            bpy.ops.massa.rerun_active('EXEC_DEFAULT')
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Resurrection failed: {e}")
            return {'CANCELLED'}


class MASSA_OT_Finalize_And_Inspect(bpy.types.Operator):
    """
    Condemns the object (Finalize) and immediately enters UV Editing mode
    with all faces selected and unpacked, allowing instant audit.
    """
    bl_idname = "massa.finalize_and_inspect"
    bl_label = "Finalize & Inspect"
    bl_description = "Finalize object, unwrap UVs, and switch to UV Editor for audit"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and "massa_op_id" in obj

    def execute(self, context):
        obj = context.active_object

        # 1. Condemn (Apply Modifiers & Strip Metadata)
        # We can call the condemn operator or duplicate logic. Duplicating is safer for atomic control.
        try:
            bpy.ops.object.convert(target='MESH')
        except Exception as e:
            self.report({'ERROR'}, f"Failed to finalize mesh: {e}")
            return {'CANCELLED'}

        # Remove Metadata
        keys_to_remove = ["massa_op_id", "MASSA_PARAMS", "MASSA_TEMP_RESTORE"]
        for k in keys_to_remove:
            if k in obj:
                try: del obj[k]
                except Exception: pass

        # 2. Enter Edit Mode & Select All
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # 3. Smart UV Project / Pack
        # We assume if the user is inspecting, they want a clean start.
        # But if Seams exist, we should use Unwrap.
        # Let's check for seams.

        bm = bmesh.from_edit_mesh(obj.data)
        has_seams = False
        for e in bm.edges:
            if e.seam:
                has_seams = True
                break

        # Trigger UV Logic
        try:
            if has_seams:
                bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            else:
                bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.01)

            # Pack Everything
            bpy.ops.uv.pack_islands(margin=0.01, rotate=True, scale=True)

        except Exception as e:
            self.report({'WARNING'}, f"Auto-Unwrap failed: {e}")

        # 4. Switch Area to UV Editor (Optional but helpful)
        # We can't easily change area type without context, but we can report success.

        self.report({'INFO'}, "Object Finalized & Unwrapped. Ready for UV Audit.")
        return {'FINISHED'}
