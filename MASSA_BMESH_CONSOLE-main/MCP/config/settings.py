import os

# PORTS
BRIDGE_PORT = 5555
HOST = '127.0.0.1'

# PATHS
# specific to: MCP/config/settings.py -> MCP/
MCP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON_ROOT = os.path.dirname(MCP_ROOT)

BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"

# Modules
CARTRIDGE_DIR = os.path.join(ADDON_ROOT, "modules", "cartridges")
DEBUG_SYSTEM_DIR = os.path.join(ADDON_ROOT, "modules", "debugging_system")

# External
AGENT_WORKFLOWS_DIR = os.path.abspath(os.path.join(ADDON_ROOT, "..", ".agent", "workflows"))
DOCS_DIR = os.path.join(MCP_ROOT, "resources", "docs")
