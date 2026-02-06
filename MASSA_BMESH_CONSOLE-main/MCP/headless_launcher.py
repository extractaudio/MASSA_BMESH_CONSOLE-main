import bpy
import os
import sys
import time

# 1. Force Enable the Addon
possible_names = ["BMESH_MASSA_CONSOLE", "MASSA_BMESH_CONSOLE-main", "MASSA_BMESH_CONSOLE"]
enabled_name = None

for name in possible_names:
    try:
        if name not in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_enable(module=name)
            print(f"HEADLESS: Enabled {name}")
        else:
            print(f"HEADLESS: {name} already enabled")
        enabled_name = name
        break
    except Exception:
        # Continue to next name
        pass

if not enabled_name:
    print(f"HEADLESS ERROR: Failed to enable addon. Tried: {possible_names}")

# 2. Start the MCP Server
try:
    if hasattr(bpy.ops.massa, "start_mcp_server"):
        bpy.ops.massa.start_mcp_server()
        print("HEADLESS: MCP Server Started on Port 5555")
    else:
        print("HEADLESS ERROR: massa.start_mcp_server operator not found. Is the addon loaded?")
except Exception as e:
    print(f"HEADLESS ERROR: {e}")

# 3. Keep Alive Loop
# In background mode, scripts exit immediately unless we loop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
