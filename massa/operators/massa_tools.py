import bpy
import bmesh
from .massa_uv_preview import _activate_uv_workspace

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


# [REMOVED] MASSA_OT_Resurrect_Wrapper — replaced by dynamic per-object dispatch.
# The N-panel and gizmo now call `bpy.ops.massa.gen_XXX('INVOKE_DEFAULT', rerun_mode=True)`
# directly using the op_id stored on the object. See:
#   - massa/ui/ui_massa_panel.py (N-panel button)
#   - massa/ui/gizmo_massa.py    (yellow resurrect gizmo, retargeted in draw_prepare)
# The `rerun_mode` branch in Massa_OT_Base.invoke() handles param restore + transform
# + scheduled deletion of the old object.


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
        has_seams = any(e.seam for e in bm.edges)
        has_uv_data = False
        uv_layer = bm.loops.layers.uv.active
        if uv_layer:
            for f in bm.faces:
                for l in f.loops:
                    if l[uv_layer].uv.length > 0.001:
                        has_uv_data = True
                        break
                if has_uv_data:
                    break
        
        try:
            if not has_uv_data:
                # No UV data at all — force smart project
                bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.01)
            elif has_seams and not has_uv_data:
                # Seams exist but no UV data — unwrap using seams
                bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            
            # Pack Everything
            bpy.ops.uv.pack_islands(margin=0.01, rotate=True, scale=True)
            
            bmesh.update_edit_mesh(obj.data)
        except Exception as e:
            self.report({'WARNING'}, f"UV Error: {e}")

        # 4. Try to switch to UV Editing workspace
        _activate_uv_workspace(context)
        
        # 5. Enable UV Sync in any visible UV Editor
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                for space in area.spaces:
                    if hasattr(space, 'uv_editor') and space.uv_editor:
                        space.uv_editor.use_uv_select_sync = True

        self.report({'INFO'}, "Object Finalized & Ready for UV Audit.")
        return {'FINISHED'}
