
import bpy
import bmesh
import os
import sys

# Add module path
repo_root = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\MASSA_BMESH_CONSOLE-main"
if repo_root not in sys.path:
    sys.path.append(repo_root)

# Mock bpy.props since we are running headless
class MockProperty:
    def __init__(self, default=None):
        self.default = default

# Mock Operator
class MASSA_OT_PrimGusset_Mock:
    def __init__(self):
        self.shape = "TRIANGLE"
        self.size = 1.0
        self.thickness = 0.1
        self.resolution = 16
        self.has_holes = True
        self.hole_radius = 0.05
        self.fit_uvs = False
        self.uv_scale = 1.0

    # Copy-paste critical methods or import if possible. 
    # Since imports are tricky with blender relative imports in standalone script, 
    # I will just run this script IN BLENDER via the debug agent.

def run_test():
    print("-" * 30)
    print("VERIFYING GUSSET NORMALS")
    print("-" * 30)
    
    # 1. Clear Scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # 2. Setup BMesh
    bm = bmesh.new()
    
    # 3. Instantiate Operator
    # We need to import the class from the file.
    # Since we are running INSIDE blender via debug_agent, modules should be importable if path is right.
    
    try:
        from modules.cartridges.cart_prim_06_gusset import MASSA_OT_PrimGusset
        op = MASSA_OT_PrimGusset()
    except Exception as e:
        print(f"Failed to import generic operator: {e}")
        return

    op.shape = "TRIANGLE"
    op.size = 1.0
    op.thickness = 0.1
    op.resolution = 16
    op.has_holes = True
    op.hole_radius = 0.05
    op.fit_uvs = False
    op.uv_scale = 1.0
    
    print("Building Shape...")
    op.build_shape(bm)
    
    # 4. Analyze Normals
    volume = bm.calc_volume()
    print(f"Mesh Volume: {volume}")
    
    if volume < 0:
        print("FAILURE: Negative Volume (Inside-Out)")
    else:
        print("SUCCESS: Positive Volume")
    
    bm.free()

# Determine if we should run
# When running via debug_agent (exec), __name__ is not __main__
# When running directly, it is.
if __name__ == "__main__":
    run_test()
else:
    # We are being exec'd
    run_test()
