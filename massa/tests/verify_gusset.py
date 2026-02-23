
import bpy
import bmesh
import os
import sys

# Add module path
current_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
sys.path.append(current_dir)

try:
    from modules.cartridges.cart_prim_06_gusset import MASSA_OT_PrimGusset
except ImportError:
    # Fallback for when running in generic blender instance
    pass

def verify_gusset_normals():
    print("-" * 30)
    print("VERIFYING GUSSET NORMALS")
    print("-" * 30)
    
    # 1. Clear Scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # 2. Setup BMesh
    bm = bmesh.new()
    
    # 3. Instantiate and Build (Mocking the operator)
    op = MASSA_OT_PrimGusset()
    op.shape = "TRIANGLE"
    op.size = 1.0
    op.thickness = 0.0 # Zero thickness to check initial plane winding
    op.resolution = 16
    op.has_holes = True # To test complex geometry
    op.hole_radius = 0.05
    op.fit_uvs = False
    
    # 3a. Temporarily modify build_shape to NOT extrude so we can check the base plane
    # Actually, let's just inspect the bottom faces of the extruded mesh if we can't easily mock partial execution.
    # The current script extrudes and then translates up.
    # Let's run the full build_shape and inspect normals.
    
    op.build_shape(bm)
    
    # 4. Analyze Normals
    # In a solid, all normals should point OUT.
    # We can check face normals against their center-to-centroid vectors, but for a flat plate it's easier.
    # The top face (Z+) should have normal (0,0,1).
    # The bottom face (Z-) should have normal (0,0,-1).
    
    up_faces = 0
    down_faces = 0
    side_faces = 0
    
    for f in bm.faces:
        n = f.normal
        if n.z > 0.9:
            up_faces += 1
        elif n.z < -0.9:
            down_faces += 1
        else:
            side_faces += 1
            
    print(f"Stats:")
    print(f"  Up-Pointing Faces: {up_faces}")
    print(f"  Down-Pointing Faces: {down_faces}")
    print(f"  Side Faces: {side_faces}")
    
    # Calculate Volume just in case
    volume = 0.0
    try:
        volume = bm.calc_volume()
        print(f"  Mesh Volume: {volume}")
    except:
        print("  Volume calc failed (not manifold?)")

    # If volume is negative, geometry is inside out.
    if volume < 0:
        print("FAILURE: Negative Volume (Inside-Out)")
    elif volume > 0:
        print("SUCCESS: Positive Volume (Correct Winding)")
    else:
        print("WARNING: Zero Volume")

    bm.free()

if __name__ == "__main__":
    verify_gusset_normals()
