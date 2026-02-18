
import bpy
import sys
import os

# Add repo root to path
sys.path.append(os.getcwd())

from MASSA_BMESH_CONSOLE_main.operators.massa_base import Massa_OT_Base

def verify():
    items = Massa_OT_Base.bl_rna.properties['ui_tab'].enum_items
    found = False
    print("Items in Massa_OT_Base.ui_tab:")
    for item in items:
        print(f" - {item.identifier}: {item.name}")
        if item.identifier == "COLLISION":
            found = True

    if found:
        print("\nSUCCESS: COLLISION item found.")
    else:
        print("\nFAILURE: COLLISION item NOT found.")

if __name__ == "__main__":
    # We need to register the class to access bl_rna correctly sometimes,
    # but accessing the class definition directly might work for properties if they are defined at class level.
    # However, bpy.props properties are descriptors.
    # Let's try inspecting the class attribute directly first.

    # Actually, without registration, we can inspect the `ui_tab` attribute which is an EnumProperty tuple/object.
    # But it's easier to just check the definition in the file directly via reading, which I already did.
    # The read_file clearly showed it's missing.
    pass
