import bpy
import sys
import base64
import os
import json

# Logic from 'inspect_cartridge_live' implementation
def test_direct_visual_audit(cartridge_id, cleanup=True):
    print(f"Testing Direct Audit for {cartridge_id}...")
    
    # -- CREATION BLOCK --
    # Find Module
    from bl_ext.user_default.massa_mesh_gen.modules import cartridges
    target_mod = None
    for mod in cartridges.MODULES:
        meta = getattr(mod, "CARTRIDGE_META", {})
        if meta.get("id") == cartridge_id:
            target_mod = mod
            break
            
    if not target_mod: 
        print(f"Error: Cartridge {cartridge_id} not found")
        return

    # Find Operator
    op_idname = None
    for name in dir(target_mod):
        obj = getattr(target_mod, name)
        if isinstance(obj, type) and issubclass(obj, bpy.types.Operator):
            if hasattr(obj, "bl_idname"):
                op_idname = obj.bl_idname
                break
    
    if not op_idname:
        print("Error: No Operator ID")
        return

    print(f"Found Operator: {op_idname}")
    
    # Execute
    try:
        cat, name = op_idname.split(".")
        op_func = getattr(getattr(bpy.ops, cat), name)
        # Use simple params
        op_func('EXEC_DEFAULT')
        obj = bpy.context.active_object
    except Exception as e:
        print(f"Creation Error: {e}")
        return

    if not obj:
        print("Error: Object not created")
        return
        
    print(f"Created Object: {obj.name}")

    # -- CAPTURE BLOCK --
    # Focus
    try:
        for area in bpy.context.screen.areas:
             if area.type == 'VIEW_3D':
                 for region in area.regions:
                     if region.type == 'WINDOW':
                         with bpy.context.temp_override(area=area, region=region):
                            bpy.ops.view3d.view_selected()
                            # Capture
                            bpy.ops.render.opengl(write_still=True)
                            print("Rendered successfully")
                            break
    except Exception as e:
        print(f"Render Error: {e}")

    # -- CLEANUP --
    if cleanup:
        print("Cleaning up...")
        bpy.ops.object.delete()
    else:
        print("Kept in scene.")

test_direct_visual_audit("prim_21_column", cleanup=True)
