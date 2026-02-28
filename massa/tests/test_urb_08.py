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

print(f"Testing URB_08 Bus Shelter...")

try:
    from massa.modules.cartridges import cart_urb_08_bus_shelter

    # Mock Op
    class MockOp:
        def report(self, type, message):
            print(f"Report: {message}")
        bl_idname = "mock.op"

        # Default Params
        length = 4.0
        depth = 2.0
        height = 2.5
        style = 'CANTILEVER'
        roof_thickness = 0.2
        glass_thickness = 0.02
        uv_scale = 1.0

    # Test Cantilever
    print("  -> Testing CANTILEVER...")
    op = MockOp()
    bm = bmesh.new()
    cart_urb_08_bus_shelter.MASSA_OT_UrbBusShelter.build_shape(op, bm)

    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")

    slots = set(f.material_index for f in bm.faces)
    print(f"  -> Slots found: {slots}")
    if 9 not in slots: raise Exception("Missing Slot 9")
    if 3 not in slots: raise Exception("Missing Slot 3 (Glass)")

    bm.free()

    # Test Kiosk
    print("  -> Testing KIOSK...")
    op.style = 'KIOSK'
    bm = bmesh.new()
    cart_urb_08_bus_shelter.MASSA_OT_UrbBusShelter.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    # Test Shed
    print("  -> Testing SHED...")
    op.style = 'SHED'
    bm = bmesh.new()
    cart_urb_08_bus_shelter.MASSA_OT_UrbBusShelter.build_shape(op, bm)
    if len(bm.verts) == 0: raise Exception("Empty Mesh Generated")
    bm.free()

    print("  -> PASS")

except Exception as e:
    print(f"  -> FAIL: {e}")
    sys.exit(1)
