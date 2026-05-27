import sys
import os
import traceback
import bpy

with open("debug_crash.txt", "w") as f:
    try:
        addon_dir = r"D:\AntiGravity_google\MASSA_BMESH_CONSOLE-main"
        if addon_dir not in sys.path:
            sys.path.append(addon_dir)
            
        import massa
        massa.register()
        
        bpy.ops.mesh.primitive_cube_add()
        bpy.ops.massa.gen_asm_07_vending(
            width=2.5103161619836136, 
            depth=5.398151300336351, 
            height=5.582458121620399, 
            shelves_count=8, 
            inset_depth=0.7476072029895654, 
            screen_height=0.1729305011768985, 
            buttons_columns=5, 
            buttons_rows=1, 
            uv_scale=8.871375445706716, 
            fit_uvs=False
        )
        f.write("SUCCESS\n")
    except Exception as e:
        f.write("CRASH_TRACEBACK_START\n")
        traceback.print_exc(file=f)
        f.write("CRASH_TRACEBACK_END\n")
