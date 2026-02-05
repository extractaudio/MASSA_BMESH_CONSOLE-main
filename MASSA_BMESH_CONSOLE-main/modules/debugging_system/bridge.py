import subprocess
import os
import sys
import json
import config

def audit_cartridge(cartridge_path):
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
        "--cartridge", cartridge_abs_path
    ]

    print(f"[System] Auditing {os.path.basename(cartridge_path)} in background process...")
    
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
    # Usage: python bridge.py <path_to_cartridge.py>
    if len(sys.argv) < 2:
        print("Usage: python bridge.py <geometry_script.py>")
        sys.exit(1)

    report = audit_cartridge(sys.argv[1])
    print(json.dumps(report, indent=4))