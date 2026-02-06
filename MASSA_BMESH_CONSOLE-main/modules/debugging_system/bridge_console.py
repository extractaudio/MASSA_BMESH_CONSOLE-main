import subprocess
import os
import sys
import json
import config # Assumes config.py is in the same folder

def audit_console():
    """
    Spawns background Blender to execute the Console Runner.
    """
    runner_script = os.path.join(os.path.dirname(__file__), "runner_console.py")
    
    # Command to run Blender Headless
    cmd = [
        config.BLENDER_PATH,
        "--background",
        "--factory-startup",
        "--python", runner_script
    ]

    print(f"[System] Auditing Massa Console Architecture...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
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
            return {
                "status": "SYSTEM_FAILURE", 
                "message": "Blender crashed or returned no data.", 
                "log": result.stdout[-1000:] 
            }

        return json.loads(json_output)

    except Exception as e:
        return {"status": "SYSTEM_FAILURE", "message": str(e)}

if __name__ == "__main__":
    report = audit_console()
    print(json.dumps(report, indent=4))
