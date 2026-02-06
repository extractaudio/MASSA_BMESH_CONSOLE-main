import subprocess
import os
import sys
import json
import config

def audit_cartridge(cartridge_path, mode="AUDIT", payload=None):
    """
    Spawns background Blender to execute the cartridge and run auditors.
    """
    runner_script = os.path.join(os.path.dirname(__file__), "runner.py")
    cartridge_abs_path = os.path.abspath(cartridge_path)

    # Command to run Blender Headless (Background Mode)
    cmd = [
        config.BLENDER_PATH,
        "--background",      # No UI
        "--factory-startup", # Clean state (no user addons)
        "--python", runner_script,
        "--",                # Args passed to python script follow
        "--cartridge", cartridge_abs_path,
        "--mode", mode
    ]
    
    if payload:
        cmd.extend(["--payload", json.dumps(payload)])

    print(f"[System] Running {mode} on {os.path.basename(cartridge_path)}...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse JSON output from Blender's stdout
        # We filter for a specific tag to avoid Blender startup log noise
        json_output = ""
        capture = False
        for line in result.stdout.splitlines():
            if "---AUDIT_START---" in line:
                capture = True
                continue
            if "---AUDIT_END---" in line:
                capture = False
                continue
            if capture:
                json_output += line

        if not json_output:
            # Fallback if Blender crashes
            return {
                "status": "SYSTEM_FAILURE", 
                "message": "Blender crashed or returned no data.", 
                "log": result.stdout[-500:] 
            }

        return json.loads(json_output)

    except Exception as e:
        return {"status": "SYSTEM_FAILURE", "message": str(e)}

if __name__ == "__main__":
    # Usage: python bridge.py <path_to_cartridge.py> [mode] [json_payload]
    if len(sys.argv) < 2:
        print("Usage: python bridge.py <geometry_script.py> [mode] [payload]")
        sys.exit(1)

    c_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "AUDIT"
    payload_str = sys.argv[3] if len(sys.argv) > 3 else None
    
    payload = None
    if payload_str:
        try:
            payload = json.loads(payload_str)
        except:
            print(json.dumps({"status": "ERROR", "message": "Invalid JSON Payload"}))
            sys.exit(1)

    report = audit_cartridge(c_path, mode, payload)
    print(json.dumps(report, indent=4))