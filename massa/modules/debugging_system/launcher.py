import subprocess
import os
import sys
import json
from . import config

def _run_blender_process(cmd, capture_output=True, timeout=300):
    """
    Helper to run a Blender process and parse the marker-delimited audit JSON.

    On any failure path it returns a SYSTEM_FAILURE dict carrying the process
    return code and the tails of BOTH stdout and stderr — Blender writes Python
    tracebacks to stderr, so capturing it is essential for diagnosing crashes.
    """
    try:
        if not capture_output:
            subprocess.Popen(cmd)
            return {"status": "LAUNCHED", "message": "Blender process started."}

        # For audit, we capture output. A timeout prevents a hung Blender (e.g.
        # a keep-alive loop or a modal prompt) from blocking the caller forever.
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            return {
                "status": "SYSTEM_FAILURE",
                "message": f"Blender timed out after {timeout}s.",
                "stdout_tail": (e.stdout or "")[-2000:] if isinstance(e.stdout, str) else "",
                "stderr_tail": (e.stderr or "")[-2000:] if isinstance(e.stderr, str) else "",
            }

        # Parse JSON output from Blender's stdout (robust marker scan).
        json_output = ""
        capture = False
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
            return {
                "status": "SYSTEM_FAILURE",
                "message": "Blender crashed or returned no audit data (markers not found).",
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-2000:] if result.stdout else "No Output",
                "stderr_tail": result.stderr[-2000:] if result.stderr else "No Errors",
            }

        try:
            parsed = json.loads(json_output)
        except json.JSONDecodeError as e:
            return {
                "status": "SYSTEM_FAILURE",
                "message": f"Failed to parse audit JSON: {str(e)}",
                "returncode": result.returncode,
                "raw_tail": json_output[-2000:],
                "stderr_tail": result.stderr[-2000:] if result.stderr else "",
            }

        # Attach non-destructive process diagnostics for inspection.
        if isinstance(parsed, dict):
            parsed.setdefault("_process", {"returncode": result.returncode})
            if result.returncode != 0 and result.stderr:
                parsed["_process"]["stderr_tail"] = result.stderr[-1500:]
        return parsed

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
    Spawns background Blender to run the CONSOLE_AUDIT health checks.

    Uses the unified runner.py (CONSOLE_AUDIT mode); runner_console.py is
    deprecated. The cartridge arg is a placeholder — CONSOLE_AUDIT ignores it.
    """
    runner_script = os.path.join(os.path.dirname(__file__), "runner.py")

    # Command to run Blender Headless
    cmd = [
        config.BLENDER_PATH,
        "--background",
        "--factory-startup",
        "--python", runner_script,
        "--",
        "--cartridge", "global_skill_placeholder.py",
        "--mode", "CONSOLE_AUDIT",
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
