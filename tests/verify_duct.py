import bpy
import bmesh
import os
import sys
import shutil

# --- Setup Package Environment for Relative Imports ---
# We need to make the addon directory importable as a package 'massa_addon'
# so that relative imports (from ...operators) resolve correctly.

repo_root = os.getcwd()
addon_dir = os.path.join(repo_root, "MASSA_BMESH_CONSOLE-main")
alias_dir = os.path.join(repo_root, "massa_addon")

if not os.path.exists(alias_dir):
    try:
        # Try symlink
        os.symlink(addon_dir, alias_dir)
    except OSError:
        # Fallback: Copy if symlink fails (e.g. some Windows environments)
        # or just fail gracefully and try direct import
        print("Warning: Could not create symlink, relative imports might fail.")
        pass

if os.path.exists(alias_dir):
    if repo_root not in sys.path:
        sys.path.append(repo_root)
    try:
        from massa_addon.modules.cartridges.cart_prim_22_duct import MASSA_OT_PrimDuct
    except ImportError as e:
        print(f"Package Import Error: {e}")
        # Try direct import as fallback (might fail on relative)
        if addon_dir not in sys.path:
            sys.path.append(addon_dir)
        try:
            from modules.cartridges.cart_prim_22_duct import MASSA_OT_PrimDuct
        except ImportError as e2:
            print(f"Direct Import Error: {e2}")
            sys.exit(1)
else:
    # Fallback if alias creation failed
    if addon_dir not in sys.path:
        sys.path.append(addon_dir)
    try:
        from modules.cartridges.cart_prim_22_duct import MASSA_OT_PrimDuct
    except ImportError as e:
        print(f"Import Error: {e}")
        # Mocking Massa_OT_Base might be needed here if verification fails
        sys.exit(1)


def verify_duct_shapes():
    print("=" * 40)
    print("VERIFYING DUCT CARTRIDGE")
    print("=" * 40)

    shapes = ["STRAIGHT", "ELBOW", "TEE", "REDUCER", "CAP", "COUPLER"]

    for shape in shapes:
        print(f"\nTesting Shape: {shape}")

        bm = bmesh.new()

        try:
            op = MASSA_OT_PrimDuct()
            op.shape_type = shape
            op.width = 0.5
            op.height = 0.3
            op.length = 2.0
            op.wall_thick = 0.01
            op.uv_scale = 1.0
            op.flange_style = "BOTH"
            op.has_ribs = False # Simplify for basic check

            # Specifics
            if shape == "ELBOW":
                op.bend_angle = 90
                op.bend_radius = 0.5
            elif shape == "TEE":
                op.branch_width = 0.2
                op.branch_height = 0.2
                op.branch_offset = 0.5
            elif shape == "REDUCER":
                op.reducer_ratio = 0.5
                op.reducer_offset = 0.1
                op.flange_style = "START" # Avoid end flange issue if any

            op.build_shape(bm)

            if not bm.is_valid:
                print("  FAILURE: Invalid BMesh")
                continue

            vol = 0.0
            try:
                vol = bm.calc_volume()
            except:
                pass

            print(f"  Faces: {len(bm.faces)}")
            print(f"  Verts: {len(bm.verts)}")
            print(f"  Volume: {vol:.4f}")

            if len(bm.faces) == 0:
                print("  FAILURE: No faces generated")
            elif vol < 0:
                print("  FAILURE: Negative Volume (Inside-Out)")
            else:
                print("  SUCCESS")

        except Exception as e:
            print(f"  CRITICAL FAILURE: {e}")
            import traceback
            traceback.print_exc()

        bm.free()

    # Clean up alias
    if os.path.exists(alias_dir) and os.path.islink(alias_dir):
        os.remove(alias_dir)

if __name__ == "__main__":
    verify_duct_shapes()
