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

def _run_blender_process(cmd, capture_output=True):
    try:
        if not capture_output:
            subprocess.Popen(cmd)
            return {"status": "LAUNCHED", "message": "Blender process started."}

        result = subprocess.run(cmd, capture_output=True, text=True)

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
                "message": "Blender crashed or returned no data.",
                "log": result.stdout[-2000:] if result.stdout else "No Output"
            }

        return json.loads(json_output)

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

    args = parser.parse_args()

    # Resolve cartridge path
    cartridge_path = args.cartridge
    if not os.path.isabs(cartridge_path):
        cartridge_path = os.path.abspath(os.path.join(repo_root, cartridge_path))

    if not os.path.exists(cartridge_path):
        print(f"Error: Cartridge file not found at {cartridge_path}")
        sys.exit(1)

    # Parse payload if present
    payload_data = {}
    if args.payload:
        try:
            payload_data = json.loads(args.payload)
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
