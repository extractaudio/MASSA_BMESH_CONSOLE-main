import sys
import os
import json
import time

# Setup paths
sys.path.append(os.path.join(os.getcwd(), "MCP"))

# Import inspector
try:
    from skills import inspector
except ImportError as e:
    print(f"Failed to import inspector: {e}")
    # Try alternate: inside skills?
    try:
        sys.path.append(os.path.join(os.getcwd(), "MCP", "skills"))
        import inspector
    except ImportError as e2:
        print(f"Still failed: {e2}")
        sys.exit(1)

cartridge = "prim_21_column" # Assuming this exists from previous steps

print("--- TEST 1: Background Audit ---")
try:
    res = inspector.audit_cartridge_geometry(cartridge, execution_mode="BACKGROUND")
    data = json.loads(res)
    print(f"Status: {data.get('status')}")
    if data.get('status') == 'FAIL':
        print(f"Errors: {data.get('errors')}")
except Exception as e:
    print(f"Test 1 Failed: {e}")

print("\n--- TEST 2: Live Audit ---")
try:
    res = inspector.audit_cartridge_geometry(cartridge, execution_mode="LIVE")
    data = json.loads(res)
    print(f"Status: {data.get('status')}")
    if data.get('status') == 'FAIL':
        print(f"Errors: {data.get('errors')}")
except Exception as e:
    print(f"Test 2 Failed: {e}")

print("\n--- TEST 3: Live Viewport ---")
try:
    res = inspector.inspect_viewport(cartridge, execution_mode="LIVE", view_mode="WIREFRAME")
    print(res)
except Exception as e:
    print(f"Test 3 Failed: {e}")
