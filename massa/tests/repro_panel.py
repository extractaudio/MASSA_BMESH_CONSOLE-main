
import sys
import os
import bpy
import bmesh
import traceback

# Add repo root to path
# We use the path found in the user state
repo_root = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\MASSA_BMESH_CONSOLE-main"
if repo_root not in sys.path:
    sys.path.append(repo_root)

try:
    from modules.cartridges.cart_prim_04_panel import MASSA_OT_PrimPanel
except ImportError as e:
    print(f"ImportError: {e}")
    # If running inside blender where modules is not directly in path, we might need to adjust
    pass
except Exception as e:
    print(f"Error during import: {e}")
    pass

def run_test():
    print("Testing MASSA_OT_PrimPanel...")
    
    # 1. Clear Scene (Just in case, though we use BMesh)
    # bpy.ops.wm.read_factory_settings(use_empty=True)

    # 2. Instantiate Base
    # Note: Operators in Blender are usually instantiated by Blender. 
    # When using them directly as python classes, we just instantiate them.
    op = MASSA_OT_PrimPanel()
    
    # 3. Set Defaults
    op.size = (2.0, 2.0, 0.1)
    op.cuts_x = 4
    op.cuts_y = 4
    op.gap = 0.02
    op.frame_width = 0.1
    op.frame_height = 0.05
    op.tile_height = 0.05
    op.inset_amount = 0.05
    op.inset_depth = -0.02
    op.use_cutout = False
    op.cutout_ratio = 0.3
    op.uv_scale = 1.0
    op.fit_uvs = False

    # 4. Build
    bm = bmesh.new()
    
    try:
        print("Calling build_shape...")
        op.build_shape(bm)
        print("Build Shape Successful!")
        
        # Check for valid geometry
        if not bm.is_valid:
            print("BMesh is invalid!")
        
        print(f"Verts: {len(bm.verts)}")
        print(f"Faces: {len(bm.faces)}")
        
    except Exception as e:
        print(f"Build Shape Failed: {e}")
        traceback.print_exc()
    finally:
        bm.free()

if __name__ == "__main__":
    run_test()
else:
    # If executed via exec() or import, run the test
    run_test()
