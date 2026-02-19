import argparse
import sys
import os
import json
import traceback

# Ensure we can import modules from the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from modules.debugging_system import logger
except ImportError:
    # Fallback if logger is not available (not strictly required for this script)
    pass

from modules.debugging_system import launcher

def run_blender_code(code: str):
    """
    Executes a python code string inside the Blender environment.
    Uses the 'execute_code' skill via the cartridge audit launcher.
    """
    payload = {
        "skill": "execute_code",
        "params": {
            "code": code
        }
    }
    
    # We use a dummy cartridge path or a specific placeholder if available.
    # The runner.py handles "global_skill_placeholder.py" or just runs logic if mode is SKILL_EXEC without loading a specific file if we use a dummy path that exists.
    # However, runner.py checks `if os.path.exists(cartridge_path)`.
    # Let's use this script itself as the "cartridge" path since it exists, but the runner won't execute it as a cartridge if mode is SKILL_EXEC.
    
    dummy_cartridge = os.path.abspath(__file__)
    
    print(f"--- Sending Code to Blender ---\n{code}\n-------------------------------")
    
    result = launcher.launch_cartridge_audit(
        cartridge_path=dummy_cartridge,
        mode="SKILL_EXEC",
        payload=payload
    )
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Run python code in Massa Blender Environment")
    parser.add_argument("--code", type=str, help="Python code string to execute")
    parser.add_argument("--file", type=str, help="Python file to execute")
    
    args = parser.parse_args()
    
    code_to_run = ""
    
    if args.file:
        if os.path.exists(args.file):
            with open(args.file, 'r') as f:
                code_to_run = f.read()
        else:
            print(f"Error: File not found {args.file}")
            return
            
    if args.code:
        code_to_run = args.code
        
    if not code_to_run:
        # Interactive mode / Default test
        print("No code provided. Running default test.")
        code_to_run = "import bpy; print(f'Connected to Blender {bpy.app.version_string}')"

    try:
        result = run_blender_code(code_to_run)
        
        if result.get("status") == "SUCCESS":
            print("\n[SUCCESS] Output from Blender:")
            print(result.get("output", ""))
        else:
            print(f"\n[FAILURE] System Error: {result.get('message', 'Unknown Error')}")
            if "errors" in result:
                print(f"Errors: {result['errors']}")
            if "log" in result:
                print(f"Log: {result['log']}")
                
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
