import sys
import os
import bpy

# Mock the addon structure by adding the repo root to sys.path
repo_root = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\MASSA_BMESH_CONSOLE-main"
if repo_root not in sys.path:
    sys.path.append(repo_root)

print("--- DEBUG START ---")
try:
    # Attempt to import the cartridges package
    import modules.cartridges as cartridges
    print("Import 'modules.cartridges' SUCCESS")
    
    # Check if Landscape is in the imported module
    if hasattr(cartridges, 'cart_prim_Landscape'):
        print("Attribute 'cart_prim_Landscape' FOUND in cartridges package")
    else:
        print("Attribute 'cart_prim_Landscape' NOT FOUND in cartridges package")
        
    # Attempt to import the specific cartridge module directly
    import modules.cartridges.cart_prim_Landscape as landscape
    print("Direct import 'modules.cartridges.cart_prim_Landscape' SUCCESS")
    
    # Check if the class exists
    if hasattr(landscape, 'MASSA_OT_cart_prim_Landscape'):
        print("Class 'MASSA_OT_cart_prim_Landscape' FOUND")
        # Try to register it
        try:
            bpy.utils.register_class(landscape.MASSA_OT_cart_prim_Landscape)
            print("Registration SUCCESS")
        except Exception as e:
            print(f"Registration FAILED: {e}")
    else:
        print("Class 'MASSA_OT_cart_prim_Landscape' NOT FOUND")
        
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"General Error: {e}")
    import traceback
    traceback.print_exc()

print("--- DEBUG END ---")
