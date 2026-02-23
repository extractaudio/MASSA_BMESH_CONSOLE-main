import bpy

# Load the MASSA addon if needed, or if it's already installed, just call the operator.
try:
    bpy.ops.massa.gen_arc_03_window()
    print("SUCCESS: cart_arc_03_window generated geometry without errors.")
except Exception as e:
    print(f"FAILED: error: {e}")
