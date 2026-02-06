import sys
import json
import base64
import os
import queue

# 1. Find Bridge
mod_name = "bl_ext.user_default.massa_mesh_gen.MCP.mcp_bridge"
bridge = None
if mod_name in sys.modules:
    bridge = sys.modules[mod_name]
else:
    for k in sys.modules.keys():
        if "mcp_bridge" in k:
            bridge = sys.modules[k]
            break

if not bridge:
    print("Bridge Not Found")
    sys.exit()

# 2. Test 'inspect_cartridge_live'
print("Invoking inspect_cartridge_live...")
req = {
    "skill": "inspect_cartridge_live",
    "params": {
        "cartridge_id": "prim_21_column", # Use known good cartridge
        "keep_in_scene": False # Test cleanup
    }
}

res_q = queue.Queue()
bridge.execution_queue.put((req, res_q))

# 3. Process
try:
    bridge.process_queue()
except Exception as e:
    print(f"Queue Error: {e}")

# 4. Result
if not res_q.empty():
    res = res_q.get()
    if "image" in res:
        print("Success: Image captured.")
        print(f"Image Size: {len(res['image'])}")
        print(f"Message: {res.get('msg')}")
    else:
        print(f"Failed: {res}")
else:
    print("No Response")
