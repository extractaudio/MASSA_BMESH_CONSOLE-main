import bpy
import bmesh
import sys
import os
import shutil

# Setup paths
repo_root = os.getcwd()
src_dir = os.path.join(repo_root, "MASSA_BMESH_CONSOLE-main")
link_name = os.path.join(repo_root, "massa")

if not os.path.exists(link_name):
    try:
        os.symlink(src_dir, link_name)
    except OSError:
        pass

if repo_root not in sys.path:
    sys.path.append(repo_root)

print(f"Testing URB_07 Trash Bin...")

try:
    from massa.modules.cartridges import cart_urb_07_trash_bin

    # Mock Op
    class MockOp:
        def report(self, type, message):
            print(f"Report: {message}")
        bl_idname = "mock.op"

        # Default Params
        width = 0.6
        depth = 0.6
        height = 1.0
        style = 'STANDARD'
        opening_radius = 0.2
        wall_thickness = 0.05
        uv_scale = 1.0

    # Test Standard
    print("  -> Testing STANDARD...")
    op = MockOp()
    bm = bmesh.new()
    cart_urb_07_trash_bin.MASSA_OT_UrbTrashBin.build_shape(op, bm)

    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")

    slots = set(f.material_index for f in bm.faces)
    print(f"  -> Slots found: {slots}")
    if 9 not in slots: raise Exception("Missing Slot 9")

    # Check Bounds
    min_z = min(v.co.z for v in bm.verts)
    max_z = max(v.co.z for v in bm.verts)
    print(f"  -> Z Bounds: {min_z:.2f} to {max_z:.2f} (Height: {max_z - min_z:.2f})")

    bm.free()

    # Test Dome
    print("  -> Testing DOME...")
    op.style = 'DOME'
    bm = bmesh.new()
    cart_urb_07_trash_bin.MASSA_OT_UrbTrashBin.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    # Test Recycler
    print("  -> Testing RECYCLER...")
    op.style = 'RECYCLER'
    bm = bmesh.new()
    cart_urb_07_trash_bin.MASSA_OT_UrbTrashBin.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    print("  -> PASS")

except Exception as e:
    print(f"  -> FAIL: {e}")
    sys.exit(1)
finally:
    if os.path.islink(link_name):
        os.remove(link_name)
