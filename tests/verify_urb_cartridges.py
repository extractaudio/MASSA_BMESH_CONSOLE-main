import bpy
import bmesh
import sys
import os
import importlib
import shutil

# Setup paths
repo_root = os.getcwd()

if repo_root not in sys.path:
    sys.path.append(repo_root)

# Import modules via 'massa' package
try:
    from massa.modules.cartridges import (
        cart_urb_01_sidewalk,
        cart_urb_02_railing,
        cart_urb_03_streetlight,
        cart_urb_04_barrier,
        cart_urb_05_fence
    )

    cartridges = [
        cart_urb_01_sidewalk.MASSA_OT_UrbSidewalk,
        cart_urb_02_railing.MASSA_OT_UrbRailing,
        cart_urb_03_streetlight.MASSA_OT_UrbStreetlight,
        cart_urb_04_barrier.MASSA_OT_UrbBarrier,
        cart_urb_05_fence.MASSA_OT_UrbFence
    ]
except ImportError as e:
    print(f"Error importing cartridges: {e}")
    sys.exit(1)

print("--- Verifying Urban Cartridges ---")

failed = False

class MockOp:
    def report(self, type, message):
        print(f"Report: {message}")
    bl_idname = "mock.op"

for cls in cartridges:
    print(f"Testing {cls.bl_label}...")
    try:
        op = MockOp()
        for k, v in cls.__annotations__.items():
            if hasattr(v, 'keywords') and 'default' in v.keywords:
                setattr(op, k, v.keywords['default'])
            elif hasattr(v, 'default'):
                 setattr(op, k, v.default)
            if "EnumProperty" in str(v) and hasattr(v, 'keywords') and 'items' in v.keywords:
                 setattr(op, k, v.keywords['items'][0][0])

        bm = bmesh.new()
        cls.build_shape(op, bm)

        print(f"  -> Verts: {len(bm.verts)}, Faces: {len(bm.faces)}")
        slots = set(f.material_index for f in bm.faces)
        print(f"  -> Slots used: {slots}")

        zero_area = [f for f in bm.faces if f.calc_area() < 0.000001]
        if zero_area:
            print(f"  -> WARNING: {len(zero_area)} Zero Area Faces detected!")

        uv_layer = bm.loops.layers.uv.verify()
        pinched = []
        for f in bm.faces:
            if f.material_index == 9: continue
            uvs = [l[uv_layer].uv for l in f.loops]
            area = 0.5 * abs(sum(x0*y1 - x1*y0 for ((x0, y0), (x1, y1)) in zip(uvs, uvs[1:] + [uvs[0]])))
            if area < 0.000001 and f.calc_area() > 0.000001:
                pinched.append(f.index)

        if pinched:
            print(f"  -> WARNING: {len(pinched)} Pinched UV Faces detected!")

        bm.free()
        print("  -> OK")

    except Exception as e:
        print(f"  -> FAILED: {e}")
        import traceback
        traceback.print_exc()
        failed = True

print("--- Verification Complete ---")
if failed:
    sys.exit(1)
