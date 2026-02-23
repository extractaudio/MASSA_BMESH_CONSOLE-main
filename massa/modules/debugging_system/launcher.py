import subprocess
import os
import sys
import json
from . import config

def _run_blender_process(cmd, capture_output=True):
    """Helper to run blender process and handle output."""
    try:
        if not capture_output:
            subprocess.Popen(cmd)
            return {"status": "LAUNCHED", "message": "Blender process started."}

        # For audit, we capture output
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse JSON output from Blender's stdout
        json_output = ""
        capture = False

        # Robust parsing: look for markers
        if result.stdout:
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
            # Fallback if Blender crashes or no markers found
            return {
                "status": "SYSTEM_FAILURE",
                "message": "Blender crashed or returned no data.",
                "log": result.stdout[-1000:] if result.stdout else "No Output"
            }

        return json.loads(json_output)

    except Exception as e:
        return {"status": "SYSTEM_FAILURE", "message": str(e)}

def launch_cartridge_audit(cartridge_path, mode="AUDIT", payload=None):
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

    print(f"[Launcher] Running {mode} on {os.path.basename(cartridge_path)}...")
    return _run_blender_process(cmd, capture_output=True)

def launch_console_audit():
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

    print(f"[Launcher] Auditing Massa Console Architecture...")
    return _run_blender_process(cmd, capture_output=True)

def launch_session(headless=False):
    """
    Launches Blender.
    headless=True: Launches background tester (Option B).
    headless=False: Launches GUI (Option A).
    """
    # For GUI session, just start Blender
    if not headless:
        cmd = [config.BLENDER_PATH]
        print(f"[Launcher] Launching Blender GUI...")
        subprocess.Popen(cmd)
        return {"status": "LAUNCHED", "message": "Blender GUI started."}

    # For Headless Session (Persistent Background)
    # Use the helper script to auto-enable addon and start listener
    launcher_script = os.path.join(os.path.dirname(__file__), "headless_launcher.py")
    cmd = [config.BLENDER_PATH, "--background", "--python", launcher_script]

    print(f"[Launcher] Launching Blender Background Session...")
    subprocess.Popen(cmd)
    return {"status": "LAUNCHED", "message": "Blender Background Session started."}
