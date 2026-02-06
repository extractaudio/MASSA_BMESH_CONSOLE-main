import socket
import json

def verify_remote():
    HOST = '127.0.0.1'
    PORT = 5555
    
    # We embed the verification logic inside the 'code' param
    code_str = """
import bpy
import bmesh
import json

results = {
    "sockets": [],
    "edge_slots": {},
    "geometry_check": "Pending"
}

try:
    # 1. Ensure PRIM_07 exists
    if hasattr(bpy.ops.massa, "gen_prim_07_louver"):
        # Clear scene for clean test
        # bpy.ops.object.select_all(action='SELECT')
        # bpy.ops.object.delete() 
        # Don't delete, assume it exists from previous step or create new one safely
        
        # Create fresh one to be sure
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
             
        bm.free()
    else:
        results["error"] = "Operator gen_prim_07_louver not found"
        
except Exception as e:
    results["error"] = str(e)

print(json.dumps(results, indent=2))
"""

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            payload = json.dumps({
                "skill": "execute_code", 
                "params": {"code": code_str}
            })
            s.sendall(payload.encode('utf-8'))
            
            # Read response
            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                chunks.append(chunk)
                if len(chunk) < 4096: break
            
            print("Response:", b"".join(chunks).decode('utf-8'))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_remote()
