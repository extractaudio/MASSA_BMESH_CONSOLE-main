import sys
import json
import base64
import os
import queue

print("Starting Refinement Script")

# 1. Find Bridge
mod_name = "bl_ext.user_default.massa_mesh_gen.MCP.mcp_bridge"
bridge = None
if mod_name in sys.modules:
    bridge = sys.modules[mod_name]
else:
    # Search
    for k in sys.modules.keys():
        if "mcp_bridge" in k:
            bridge = sys.modules[k]
            print(f"Found Bridge at: {k}")
            break

if not bridge:
    print("Bridge NOT found")
    sys.exit()

# 2. Define Layout
# 2. Define Layout (Columns)
layout = [
    {
        "type": "CARTRIDGE",
        "id": "prim_21_column",
        "name": "Column_Main_L",
        "parameters": {
            "height": 4.0,
            "radius_bottom": 0.4,
            "radius_top": 0.3,
            "style": "CORINTHIAN"
        },
        "transforms": {
            "location": [-3.0, -4.0, 0], 
            "rotation": [0, 0, 0]
        }
    },
    {
        "type": "CARTRIDGE",
        "id": "prim_21_column",
        "name": "Column_Main_R",
        "parameters": {
            "height": 4.0,
             "radius_bottom": 0.4,
            "radius_top": 0.3,
            "style": "CORINTHIAN"
        },
        "transforms": {
            "location": [3.0, -4.0, 0],
            "rotation": [0, 0, 0]
        }
    }
]

# 3. Request
print("Sending Command...")
payload = {
    "layout": layout,
    "audit": True
}
req = {"skill": "create_scene", "params": payload}
res_q = queue.Queue()

if hasattr(bridge, "execution_queue"):
    bridge.execution_queue.put((req, res_q))
    print("Command queued.")
    
    # Trigger
    print("Processing queue...")
    try:
        bridge.process_queue() # This runs on main thread usually
        print("Queue processed.")
    except Exception as e:
        print(f"Error in process_queue: {e}")

    # Result
    if not res_q.empty():
        result = res_q.get()
        print("Got Result:")
        msg = result.get("report", {}).get("visual_capture")
        if msg:
            print(f"Visual Capture Length: {len(msg)}")
        else:
            print("No visual capture")
            print(result)
    else:
        print("No result in queue")
else:
    print("Bridge has no execution_queue")
