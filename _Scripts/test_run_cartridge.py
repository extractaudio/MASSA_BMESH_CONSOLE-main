import os
import sys
import argparse
import json
import subprocess

# Add root folder to sys.path so we can import the massa module correctly
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.append(repo_root)

# We cannot directly import `launcher` because it might trigger `massa.__init__.py`
# which assumes we are inside blender (`import bpy`).
# Instead, we pull the config directly.
config_path = os.path.join(repo_root, "massa", "modules", "debugging_system", "config.py")
config = {}
with open(config_path, 'r') as f:
    exec(f.read(), config)

BLENDER_PATH = config.get("BLENDER_PATH")

def _run_blender_process(cmd, capture_output=True, timeout=300):
    try:
        if not capture_output:
            subprocess.Popen(cmd)
            return {"status": "LAUNCHED", "message": "Blender process started."}

        # Timeout guards against a hung Blender blocking the runner indefinitely.
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            return {
                "status": "SYSTEM_FAILURE",
                "message": f"Blender timed out after {timeout}s.",
                "stdout_tail": (e.stdout or "")[-2000:] if isinstance(e.stdout, str) else "",
                "stderr_tail": (e.stderr or "")[-2000:] if isinstance(e.stderr, str) else "",
            }

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
            # Capture BOTH streams — Blender prints Python tracebacks to stderr.
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

        if isinstance(parsed, dict):
            parsed.setdefault("_process", {"returncode": result.returncode})
            if result.returncode != 0 and result.stderr:
                parsed["_process"]["stderr_tail"] = result.stderr[-1500:]
        return parsed

    except Exception as e:
        return {"status": "SYSTEM_FAILURE", "message": str(e)}

def launch_cartridge_audit(cartridge_path, mode="AUDIT", payload=None):
    runner_script = os.path.join(repo_root, "massa", "modules", "debugging_system", "runner.py")
    cartridge_abs_path = os.path.abspath(cartridge_path)

    cmd = [
        BLENDER_PATH,
        "--background",
        "--factory-startup",
        "--python", runner_script,
        "--",
        "--cartridge", cartridge_abs_path,
        "--mode", mode
    ]

    if payload:
        cmd.extend(["--payload", json.dumps(payload)])

    print(f"[Launcher] Running {mode} on {os.path.basename(cartridge_path)}...")
    return _run_blender_process(cmd, capture_output=True)


def main():
    parser = argparse.ArgumentParser(
        description="MASSA Universal Cartridge Test Runner.\n"
                    "This script interfaces with the internal debugging system to audit, test, and render ANY cartridge.\n"
                    "You can pass the path to any generated or existing cartridge to validate it.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "cartridge",
        help="Path to ANY cartridge file to test\n(Example reference: massa/modules/cartridges/cart_prim_06_gusset.py)"
    )
    parser.add_argument(
        "--mode", 
        default="AUDIT",
        choices=["AUDIT", "VISUAL_DIFF", "UV_HEATMAP", "UV_INSPECT", "PERFORMANCE", "CSG_DEBUG", "RENDER", "SKILL_EXEC", "CONSOLE_AUDIT"],
        help="The debugging mode to run."
    )
    parser.add_argument(
        "--payload",
        default=None,
        help="Optional JSON string of payload data (e.g., for VISUAL_DIFF: '{\"filename_b\": \"other_file.py\"}')"
    )
    parser.add_argument(
        "--payload-env",
        default=None,
        help="Name of an environment variable containing payload JSON. Useful on Windows when shell quoting mangles --payload."
    )

    args = parser.parse_args()

    # Resolve cartridge path
    cartridge_path = args.cartridge
    if not os.path.isabs(cartridge_path):
        cartridge_path = os.path.abspath(os.path.join(repo_root, cartridge_path))

    if not os.path.exists(cartridge_path):
        print(f"Error: Cartridge file not found at {cartridge_path}")
        sys.exit(1)

    # Parse payload if present
    payload_json = args.payload
    if args.payload_env:
        payload_json = os.environ.get(args.payload_env)
        if payload_json is None:
            print(f"Error: payload environment variable not found: {args.payload_env}")
            sys.exit(1)

    payload_data = {}
    if payload_json:
        try:
            payload_data = json.loads(payload_json)
        except json.JSONDecodeError as e:
            print(f"Error parsing payload JSON: {e}")
            sys.exit(1)

    print(f"--- Running MASSA Test Runner ---")
    print(f"Cartridge : {os.path.basename(cartridge_path)}")
    print(f"Mode      : {args.mode}")
    print("---------------------------------")

    # Launch background audit
    result = launch_cartridge_audit(
        cartridge_path=cartridge_path,
        mode=args.mode,
        payload=payload_data
    )

    print("\n--- TEST RESULTS ---")
    print(json.dumps(result, indent=4))
    
    # If a render was created, notify the user
    if result and isinstance(result, dict) and result.get("status") == "SUCCESS":
        if "image_path" in result:
            print(f"\n[!] Visual output generated at: {result['image_path']}")

if __name__ == "__main__":
    main()
