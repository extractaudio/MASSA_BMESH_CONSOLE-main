import bpy
import bmesh
import sys
import os
import shutil

# Setup paths
repo_root = os.getcwd()
src_dir = os.path.join(repo_root, "massa")


if repo_root not in sys.path:
    sys.path.append(repo_root)

print(f"Testing URB_10 Bollard...")

try:
    from massa.modules.cartridges import cart_urb_10_bollard

    # Mock Op
    class MockOp:
        def report(self, type, message):
            print(f"Report: {message}")
        bl_idname = "mock.op"

        # Default Params
        height = 1.0
        radius = 0.15
        style = 'POST'
        detail_ring = True
        uv_scale = 1.0

    # Test Post
    print("  -> Testing POST...")
    op = MockOp()
    bm = bmesh.new()
    cart_urb_10_bollard.MASSA_OT_UrbBollard.build_shape(op, bm)

    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")

    slots = set(f.material_index for f in bm.faces)
    print(f"  -> Slots found: {slots}")
    if 9 not in slots: raise Exception("Missing Slot 9")

    bm.free()

    # Test Sphere
    print("  -> Testing SPHERE...")
    op.style = 'SPHERE'
    bm = bmesh.new()
    cart_urb_10_bollard.MASSA_OT_UrbBollard.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    # Test Column
    print("  -> Testing COLUMN...")
    op.style = 'COLUMN'
    bm = bmesh.new()
    cart_urb_10_bollard.MASSA_OT_UrbBollard.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    print("  -> PASS")

except Exception as e:
    print(f"  -> FAIL: {e}")
    sys.exit(1)
