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

print(f"Testing URB_09 Utility Cabinet...")

try:
    from massa.modules.cartridges import cart_urb_09_utility_cabinet

    # Mock Op
    class MockOp:
        def report(self, type, message):
            print(f"Report: {message}")
        bl_idname = "mock.op"

        # Default Params
        width = 1.2
        depth = 0.8
        height = 1.8
        style = 'TRAFFIC'
        base_height = 0.2
        door_inset = 0.02
        uv_scale = 1.0

    # Test Traffic
    print("  -> Testing TRAFFIC...")
    op = MockOp()
    bm = bmesh.new()
    cart_urb_09_utility_cabinet.MASSA_OT_UrbUtilityCabinet.build_shape(op, bm)

    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")

    slots = set(f.material_index for f in bm.faces)
    print(f"  -> Slots found: {slots}")
    if 9 not in slots: raise Exception("Missing Slot 9")

    bm.free()

    # Test Telecom
    print("  -> Testing TELECOM...")
    op.style = 'TELECOM'
    bm = bmesh.new()
    cart_urb_09_utility_cabinet.MASSA_OT_UrbUtilityCabinet.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    # Test Electrical
    print("  -> Testing ELECTRICAL...")
    op.style = 'ELECTRICAL'
    bm = bmesh.new()
    cart_urb_09_utility_cabinet.MASSA_OT_UrbUtilityCabinet.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    print("  -> PASS")

except Exception as e:
    print(f"  -> FAIL: {e}")
    sys.exit(1)
