
import bpy
import bmesh
import os
import sys

# Add module path
sys.path.append(os.getcwd())

try:
    from modules.cartridges.cart_prim_06_gusset import MASSA_OT_PrimGusset
except ImportError:
    pass

def verify_gusset_seams():
    print("-" * 30)
    print("VERIFYING GUSSET SEAMS")
    print("-" * 30)
    
    # 1. Setup BMesh
    bm = bmesh.new()
    
    # 2. Instantiate and Build
    op = MASSA_OT_PrimGusset()
    op.shape_mode = "L_SHAPE"
    op.arm_length = 0.5
    op.width = 0.2
    op.thickness = 0.05
    op.resolution = 16
    op.has_holes = False # Simplify geometry
    
    op.build_shape(bm)
    
    # 3. Analyze Edge Slots
    edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    if not edge_slots:
        print("FAILURE: No Edge Slots Layer Found")
        return

    slot3_y_axis_count = 0
    slot3_vertical_corner_count = 0
    
    # Assuming Z-up extrusion
    # Vertical edges have v1.z != v2.z (approx) and same x,y
    
    for e in bm.edges:
        is_slot3 = (e[edge_slots] == 3)
        if not is_slot3: continue
            
        v1, v2 = e.verts
        
        # Check Y-Axis Guide (X=0)
        # It should lie on X=0 plane.
        if abs(v1.co.x) < 0.001 and abs(v2.co.x) < 0.001:
            slot3_y_axis_count += 1
            
        # Check Vertical Corner
        # Vertical edge: x1==x2, y1==y2, z1!=z2
        is_vertical = (abs(v1.co.x - v2.co.x) < 0.001 and 
                       abs(v1.co.y - v2.co.y) < 0.001 and
                       abs(v1.co.z - v2.co.z) > 0.001)
                       
        if is_vertical:
            slot3_vertical_corner_count += 1

    print("Stats:")
    print(f"  Slot 3 (Y-Axis Guide) Edges: {slot3_y_axis_count}")
    print(f"  Slot 3 (Vertical Corner) Edges: {slot3_vertical_corner_count}")
    
    if slot3_y_axis_count > 0:
        print("SUCCESS: Y-Axis Guide Edges Found")
    else:
        print("FAILURE: No Y-Axis Guide Edges Found")
        
    if slot3_vertical_corner_count > 0:
        print("SUCCESS: Vertical Corner Edges Found")
    else:
        print("FAILURE: No Vertical Corner Edges Found")

    bm.free()

if __name__ == "__main__":
    verify_gusset_seams()
