import bpy
import bmesh
import sys
import os
import shutil

# Setup paths
repo_root = os.getcwd() # Should be repo root when run from there
src_dir = os.path.join(repo_root, "massa")


if repo_root not in sys.path:
    sys.path.append(repo_root)

print(f"Testing URB_06 Bench...")

try:
    from massa.modules.cartridges import cart_urb_06_bench

    # Mock Op
    class MockOp:
        def report(self, type, message):
            print(f"Report: {message}")
        bl_idname = "mock.op"

        # Default Params
        length = 2.0
        depth = 0.6
        height = 0.45
        style = 'STANDARD'
        slat_count = 5
        leg_thickness = 0.1
        backrest = False
        uv_scale = 1.0

    # Test Standard
    print("  -> Testing STANDARD...")
    op = MockOp()
    bm = bmesh.new()
    cart_urb_06_bench.MASSA_OT_UrbBench.build_shape(op, bm)

    if len(bm.verts) == 0:
        raise Exception("Empty Mesh Generated")

    # Check Zero Area
    zero_area = [f for f in bm.faces if f.calc_area() < 0.000001]
    if zero_area:
        print(f"  WARNING: {len(zero_area)} Zero Area Faces")

    # Check Slots
    slots = set(f.material_index for f in bm.faces)
    print(f"  -> Slots found: {slots}")
    if 9 not in slots:
        raise Exception("Missing Slot 9")

    bm.free()

    # Test Modern
    print("  -> Testing MODERN...")
    op.style = 'MODERN'
    bm = bmesh.new()
    cart_urb_06_bench.MASSA_OT_UrbBench.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    # Test Block
    print("  -> Testing BLOCK...")
    op.style = 'BLOCK'
    bm = bmesh.new()
    cart_urb_06_bench.MASSA_OT_UrbBench.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    print("  -> PASS")

except Exception as e:
    print(f"  -> FAIL: {e}")
    sys.exit(1)
