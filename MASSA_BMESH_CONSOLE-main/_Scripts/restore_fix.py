import socket
import json

def send_restore():
    HOST = '127.0.0.1'
    PORT = 5555
    
    code_str = """
try:
    import bpy
    # Force ensure it exists
    if not any("PRIM_07" in o.name for o in bpy.data.objects):
        if hasattr(bpy.ops.massa, "gen_prim_07_louver"):
            bpy.ops.massa.gen_prim_07_louver()
            print("Generated PRIM_07 via direct operator call")
        else:
            print("Operator massa.gen_prim_07_louver not found!")
    
    names = [o.name for o in bpy.data.objects]
    print(f"Objects: {names}")
    
    # Find and select
    found = False
    for name in names:
        if "PRIM_07" in name:
            obj = bpy.data.objects[name]
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            print(f"Manually Selected: {obj.name}")
            
            # ATOMIC MODIFICATION TEST
            # Simulate what iterate_parameters does
            if "MASSA_PARAMS" in obj:
                params_dict = dict(obj["MASSA_PARAMS"])
                params_dict["blade_count"] = 12
                params_dict["blade_angle"] = 0.0
                obj["MASSA_PARAMS"] = params_dict
                print("Updated MASSA_PARAMS (12 blades, 0 deg)")
                
                if hasattr(bpy.ops.massa, "resurrect_selected"):
                    bpy.ops.massa.resurrect_selected()
                    print("Resurrected with new params (Atomic)")
            else:
                print("MASSA_PARAMS missing on object")
                
            found = True
            break
            
    if not found:
        print("Could not find or create PRIM_07")
        
except Exception as e:
    print(f"Execution Error: {e}")
"""

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            payload = json.dumps({
                "skill": "execute_code", 
                "params": {"code": code_str}
            })
            s.sendall(payload.encode('utf-8'))
            print("Sent execute_code command")
            
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
    send_restore()
