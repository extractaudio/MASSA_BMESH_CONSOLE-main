
import bpy
import bmesh
import math
from mathutils import Vector
import sys
import os

# Mock the class structure since we can't easily import the addon structure
class MockLathe:
    def __init__(self):
        self.height = 1.0
        self.r_base = 0.5
        self.r_mid = 0.7
        self.r_rim = 0.6
        self.mid_pos = 0.5
        self.thickness = 0.1
        self.segments = 12  # Easier to count
        self.smooth_shade = True
        self.uv_scale = 1.0
        self.fit_uvs = False

    # Copy of the build_shape method logic we just injected. 
    # Since we can't easily import, we rely on the file content being correct.
    # But to VERIFY, we should try to import the file.
    
    # Strategy: Read the file, replace the relative import, then exec.
    
def test_lathe():
    # 1. Setup path
    target_file = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\MASSA_BMESH_CONSOLE-main\modules\cartridges\cart_prim_16_lathe.py"
    
    with open(target_file, 'r') as f:
        content = f.read()
        
    # 2. Patch content to avoid import errors
    # Remove "from ...operators.massa_base import Massa_OT_Base"
    # Replace it with a dummy
    content = content.replace("from ...operators.massa_base import Massa_OT_Base", "class Massa_OT_Base: pass")
    
    # 3. Exec to get the class
    namespace = {
        "bpy": bpy,
        "bmesh": bmesh,
        "math": math,
        "Vector": Vector,
        "FloatProperty": lambda **k: 0.0,
        "IntProperty": lambda **k: 0,
        "BoolProperty": lambda **k: False,
    }
    
    exec(content, namespace)
    
    LatheClass = namespace.get("MASSA_OT_PrimLathe")
    if not LatheClass:
        print("FAILED to find MASSA_OT_PrimLathe class")
        return

    # 4. Instantiate and Run
    lathe = LatheClass()
    # Manually set properties since PropertyGroup/FloatProperty logic isn't active
    lathe.height = 1.0
    lathe.r_base = 0.5
    lathe.r_mid = 0.7
    lathe.r_rim = 0.6
    lathe.mid_pos = 0.5
    lathe.thickness = 0.1
    lathe.segments = 12
    lathe.smooth_shade = True
    lathe.uv_scale = 1.0
    lathe.fit_uvs = False
    
    bm = bmesh.new()
    lathe.build_shape(bm)
    
    # 5. Verify Slots
    edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    if not edge_slots:
        print("FAILED: MASSA_EDGE_SLOTS layer not found!")
        return
        
    slot1_count = 0
    slot3_count = 0
    
    for e in bm.edges:
        val = e[edge_slots]
        if val == 1:
            slot1_count += 1
        elif val == 3:
            slot3_count += 1
            
    print(f"Slot 1 Edges: {slot1_count}")
    print(f"Slot 3 Edges: {slot3_count}")
    
    # Expected:
    # Slot 1: 4 rings * 12 segments = 48
    # Slot 3: (6 rings -> 5 vertical segments) + 2 caps = 7
    
    if slot1_count == 48 and slot3_count == 7:
        print("SUCCESS: Slot counts match expected values.")
    else:
        print(f"FAILURE: Expected Slot 1: 48, Slot 3: 7. Got {slot1_count}, {slot3_count}")

if __name__ == "__main__":
    test_lathe()
