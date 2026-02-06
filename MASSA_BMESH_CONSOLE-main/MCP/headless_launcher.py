import bpy
import os
import sys
import time

# 1. Force Enable the Addon
addon_name = "BMESH_MASSA_CONSOLE" 
try:
    if addon_name not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=addon_name)
        print(f"HEADLESS: Enabled {addon_name}")
except Exception as e:
    print(f"HEADLESS ERROR: {e}")

# 2. Start the MCP Server
try:
    bpy.ops.massa.start_mcp_server()
    print("HEADLESS: MCP Server Started on Port 5555")
except Exception as e:
    print(f"HEADLESS ERROR: {e}")

# 3. Keep Alive Loop
# In background mode, scripts exit immediately unless we loop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass