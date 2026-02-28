import bpy
import bmesh
import sys
import os
import importlib

# Add repo root to path
repo_root = os.getcwd()
sys.path.append(repo_root)

# Import modules
from massa.modules.cartridges import (
    cart_arch_01_stairs_linear,
    cart_arch_02_stairs_spiral,
    cart_arch_03_stairs_industrial,
    cart_arch_mobile_home,
    cart_arch_tiny_home
)

cartridges = [
    cart_arch_01_stairs_linear.MASSA_OT_ArchStairsLinear,
    cart_arch_02_stairs_spiral.MASSA_OT_ArchStairsSpiral,
    cart_arch_03_stairs_industrial.MASSA_OT_ArchStairsIndustrial,
    cart_arch_mobile_home.MASSA_OT_ArchMobileHome,
    cart_arch_tiny_home.MASSA_OT_ArchTinyHome
]

print("--- Verifying Architectural Cartridges ---")

for cls in cartridges:
    print(f"Testing {cls.bl_label}...")
    try:
        class MockOp(cls):
            def report(self, type, message):
                print(f"Report: {message}")

        op = MockOp()

        # Manually set property defaults because bpy.props don't work outside Blender operator registration context fully
        # We parse the class annotations
        for k, v in cls.__annotations__.items():
            if hasattr(v, 'keywords') and 'default' in v.keywords:
                setattr(op, k, v.keywords['default'])
            elif hasattr(v, 'default'):
                 setattr(op, k, v.default)
            # Handle EnumProperty specifically if possible, or fallback
            if "EnumProperty" in str(v) and hasattr(v, 'keywords') and 'items' in v.keywords:
                 setattr(op, k, v.keywords['items'][0][0]) # First item ID

        bm = bmesh.new()
        op.build_shape(bm)

        print(f"  -> Verts: {len(bm.verts)}, Faces: {len(bm.faces)}")

        # Check Slots
        slots = set(f.material_index for f in bm.faces)
        print(f"  -> Slots used: {slots}")

        bm.free()
        print("  -> OK")

    except Exception as e:
        print(f"  -> FAILED: {e}")
        import traceback
        traceback.print_exc()

print("--- Verification Complete ---")
