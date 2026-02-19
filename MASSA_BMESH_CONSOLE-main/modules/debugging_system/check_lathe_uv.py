
import bpy
import bmesh
import sys
import os
import math
from mathutils import Vector

# Setup Path
repo_root = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\MASSA_BMESH_CONSOLE-main"
if repo_root not in sys.path:
    sys.path.append(repo_root)

try:
    from modules.cartridges import cart_prim_16_lathe
except ImportError:
    print("Could not import cart_prim_16_lathe")
    sys.exit(1)

# Dummy Operator to simulate properties
class DummyOp:
    height = 0.8
    r_base = 0.25
    r_mid = 0.45
    r_rim = 0.35
    mid_pos = 0.6
    thickness = 0.03
    segments = 32
    smooth_shade = True
    uv_scale = 1.0
    fit_uvs = False
    
    def _getAction(self, name):
        return "IGNORE"

    def __getattr__(self, name):
        # Default fallback for properties accessed via getattr(self, name)
        if name.startswith("edge_slot_"):
            return "IGNORE"
        return None

def test_uvs():
    op = DummyOp()
    # Instantiate the class (it's a Mixin/Operator structure, but logic is in build_shape)
    # The class in the file is MASSA_OT_PrimLathe
    generator = cart_prim_16_lathe.MASSA_OT_PrimLathe()
    
    # Copy properties to generator instance
    for key in dir(op):
        if not key.startswith("__") and key != "_getAction":
            setattr(generator, key, getattr(op, key))
            
    bm = bmesh.new()
    
    # Run build_shape
    try:
        generator.build_shape(bm)
    except Exception as e:
        print(f"Error building shape: {e}")
        return

    # Check UVs
    uv_layer = bm.loops.layers.uv.verify()
    
    print(f"Checking {len(bm.faces)} faces for curved UVs...")
    
    curved_faces = 0
    straight_faces = 0
    
    for f in bm.faces:
        if len(f.verts) != 4:
            continue # Cap triangles, ignore
            
        # Get UV coords
        uvs = [l[uv_layer].uv for l in f.loops]
        # v1, v2 (bot), v3, v4 (top) -> loops order: v1->v2->v3->v4 (CCW)
        # Check if v component is constant for bottom edge (u1, v_bot) -> (u2, v_bot)
        # and top edge (u2, v_top) -> (u1, v_top)
        
        # Assumption: loops[0] and loops[1] share V? loops[2] and loops[3] share V?
        # Let's check differences.
        
        # Actually easier: Check if edges in UV space are axis aligned.
        # uv0 = uvs[0], uv1 = uvs[1]. If uv0.y ~= uv1.y, it's horizontal.
        
        dy_bot = abs(uvs[0].y - uvs[1].y)
        dy_top = abs(uvs[2].y - uvs[3].y)
        
        # Also check vertical alignment: uvs[1].x ~= uvs[2].x
        dx_right = abs(uvs[1].x - uvs[2].x)
        dx_left = abs(uvs[3].x - uvs[0].x)
        
        if dy_bot < 0.001 and dy_top < 0.001 and dx_right < 0.001 and dx_left < 0.001:
            straight_faces += 1
        else:
            curved_faces += 1
            # print(f"Curved Face: dy_bot={dy_bot}, dy_top={dy_top}")
            
    print(f"Result: {straight_faces} Straight Quads, {curved_faces} Curved Quads")
    
    # Cleanup
    bm.free()

if __name__ == "__main__":
    test_uvs()
