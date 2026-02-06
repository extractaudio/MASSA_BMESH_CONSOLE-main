import bpy
import bmesh
import json

def verify():
    results = {
        "sockets": [],
        "edge_slots": {},
        "geometry_check": "Pending"
    }
    
    # 1. Ensure PRIM_07 exists or create it
    if hasattr(bpy.ops.massa, "gen_prim_07_louver"):
        # Clear scene for clean test
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        bpy.ops.massa.gen_prim_07_louver()
        obj = bpy.context.active_object
        
        # 2. Check Sockets (Children)
        for child in obj.children:
            results["sockets"].append({
                "name": child.name, 
                "loc": [round(c, 3) for c in child.location]
            })
            
        # 3. Check Edge Slots (BMesh)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        
        slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if slot_layer:
            counts = {}
            for e in bm.edges:
                val = e[slot_layer]
                if val > 0:
                    counts[val] = counts.get(val, 0) + 1
            results["edge_slots"] = counts
        else:
             results["edge_slots"] = "Layer Missing"
             
        # 4. Check Screen Scaling (Z-Fighting)
        # Bounding box of Material Slot 2?
        # Requires identifying faces by material
        
        bm.free()
    else:
        results["error"] = "Operator gen_prim_07_louver not found"

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    verify()
