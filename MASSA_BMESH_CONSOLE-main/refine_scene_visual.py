import sys
import json
import base64
import os

# 1. Find Bridge
mod_name = "bl_ext.user_default.massa_mesh_gen.MCP.mcp_bridge"
if mod_name not in sys.modules:
    candidates = [k for k in sys.modules.keys() if "mcp_bridge" in k]
    if candidates:
        mod_name = candidates[0]
    else:
        # Fallback for manual path
        try:
            import mcp_bridge
            mod_name = "mcp_bridge"
        except:
            print(json.dumps({"status": "error", "msg": "Bridge not found"}))
            sys.exit()

bridge = sys.modules[mod_name]
# from core.bridge_client import send_bridge # Removed to avoid path issues


# 2. Define Refinement Layout (Louvers)
layout = [
    {
        "type": "CARTRIDGE",
        "id": "prim_07_louver",
        "name": "Louver_Main_L",
        "parameters": {
            "size": [0.8, 1.2, 0.1],
            "blade_angle": 45.0,
            "blade_count": 10,
            "frame_width": 0.08
        },
        "transforms": {
            "location": [-2.0, -2.1, 1.5], # Front Left Window of Main House
            "rotation": [90, 0, 0] # Upright
        }
    },
    {
        "type": "CARTRIDGE",
        "id": "prim_07_louver",
        "name": "Louver_Main_R",
        "parameters": {
            "size": [0.8, 1.2, 0.1],
            "blade_angle": 45.0,
            "blade_count": 10,
            "frame_width": 0.08
        },
        "transforms": {
            "location": [2.0, -2.1, 1.5], # Front Right Window
            "rotation": [90, 0, 0]
        }
    },
     {
        "type": "CARTRIDGE",
        "id": "prim_07_louver",
        "name": "Louver_Tiny",
        "parameters": {
            "size": [0.6, 0.6, 0.1],
            "blade_count": 5
        },
        "transforms": {
            "location": [10.0, 3.5, 1.2], # Side of Tiny Home
            "rotation": [90, 0, 90] # Side facing
        }
    }
]

# 3. Request Scene Creation with Audit (Visuals)
print("Sending Refinement Command...")
payload = {
    "layout": layout,
    "audit": True # This triggers capture_viewport
}

# Use the bridge client directly (simulates tool behavior)
try:
    # send_bridge expects (skill_name, params)
    # create_scene handler in bridge expects just 'params' inside the request wrapper
    # But send_bridge wraps it: {'skill': skill, 'params': params}
    
    # We can't import send_bridge easily if it's not in path, so we use the bridge module's queue directly
    # duplicating send_bridge logic for safety in this script context
    
    req = {"skill": "create_scene", "params": payload}
    
    import queue
    q = bridge.execution_queue
    res_q = queue.Queue()
    q.put((req, res_q))
    
    # Trigger processing
    bridge.process_queue()
    
    if not res_q.empty():
        result = res_q.get()
        
        # 4. Analyze Result
        report = result.get("report", {})
        visual_b64 = report.get("visual_capture", "")
        
        summary = {
            "status": "success",
            "created": report.get("created_objects", []),
            "errors": report.get("errors", []),
            "visual_captured": len(visual_b64) > 0,
            "image_size": len(visual_b64)
        }
        
        if visual_b64:
             # Save to disk for 'verification'
             with open("refinement_visual.png", "wb") as f:
                 f.write(base64.b64decode(visual_b64))
             summary["saved_image"] = "refinement_visual.png"
             
        print(json.dumps(summary, indent=2))
        
    else:
        print(json.dumps({"status": "error", "msg": "No response"}))

except Exception as e:
    print(json.dumps({"status": "error", "msg": str(e)}))
