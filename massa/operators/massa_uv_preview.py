import bpy

def _activate_uv_workspace(context):
    """Try to switch to UV Editing workspace or open UV Editor in a split."""
    # Strategy 1: Find existing "UV Editing" workspace
    for ws in bpy.data.workspaces:
        if "UV" in ws.name:
            context.window.workspace = ws
            return True
    
    # Strategy 2: If current screen has an IMAGE_EDITOR, we're fine
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            return True
    
    # Strategy 3: Try to change the largest non-3D area to IMAGE_EDITOR
    best_area = None
    best_size = 0
    for area in context.screen.areas:
        if area.type not in {'VIEW_3D', 'PROPERTIES', 'OUTLINER'}:
            size = area.width * area.height
            if size > best_size:
                best_size = size
                best_area = area
    
    if best_area:
        best_area.type = 'IMAGE_EDITOR'
        return True
    
    return False

class MASSA_OT_UV_Preview(bpy.types.Operator):
    """Enter UV Preview mode — temporarily disables modifiers and enters Edit Mode"""
    bl_idname = "massa.uv_preview"
    bl_label = "UV Preview"
    bl_description = "Preview UVs in the UV Editor without finalizing the object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and "massa_op_id" in obj

    def execute(self, context):
        obj = context.active_object
        
        # 1. Store modifier states for restoration
        mod_states = {}
        for mod in obj.modifiers:
            mod_states[mod.name] = mod.show_viewport
        obj["MASSA_UV_PREVIEW_MODS"] = mod_states
        
        # 2. Disable interfering modifiers
        INTERFERING = {"Massa_Fuse", "Massa_Edge_Viz", "Massa_Bevel"}
        for mod in obj.modifiers:
            if mod.name in INTERFERING:
                mod.show_viewport = False
        
        # 3. Enter Edit Mode, select all
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        # 4. Try to switch to UV Editing workspace
        _activate_uv_workspace(context)

        # 5. Enable UV Sync in any visible UV Editor
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                for space in area.spaces:
                    if hasattr(space, 'uv_editor') and space.uv_editor:
                        space.uv_editor.use_uv_select_sync = True
        
        self.report({'INFO'}, "UV Preview active. UVs visible in UV Editor.")
        return {'FINISHED'}


class MASSA_OT_UV_Preview_Exit(bpy.types.Operator):
    """Exit UV Preview mode — restores modifiers and returns to Object Mode"""
    bl_idname = "massa.uv_preview_exit"
    bl_label = "Exit UV Preview"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and "MASSA_UV_PREVIEW_MODS" in obj

    def execute(self, context):
        obj = context.active_object
        
        # Restore modifier states
        if "MASSA_UV_PREVIEW_MODS" in obj:
            # Need to convert IDPropertyGroup to dict safely
            try:
                mod_states = dict(obj["MASSA_UV_PREVIEW_MODS"].items())
            except Exception:
                # If it's a normal dict somehow or fallback
                mod_states = obj["MASSA_UV_PREVIEW_MODS"]
                
            for mod in obj.modifiers:
                if mod.name in mod_states:
                    mod.show_viewport = bool(mod_states[mod.name])
            del obj["MASSA_UV_PREVIEW_MODS"]
        
        # Return to Object Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, "UV Preview ended. Modifiers restored.")
        return {'FINISHED'}
