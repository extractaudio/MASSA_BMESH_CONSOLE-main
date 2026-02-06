from mcp.server.fastmcp import FastMCP
import socket
import json
import subprocess
import os

mcp = FastMCP("Massa_Modular_Architect")

# CONSTANTS
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
BRIDGE_PORT = 5555
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARTRIDGE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../modules/cartridges"))
DEBUG_SYSTEM_DIR = os.path.abspath(os.path.join(BASE_DIR, "../modules/debugging_system"))
AGENT_WORKFLOWS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../.agent/workflows"))

def send_bridge(skill, params=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', BRIDGE_PORT))
            payload = json.dumps({"skill": skill, "params": params or {}})
            s.sendall(payload.encode('utf-8'))
            
            # Read response
            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                chunks.append(chunk)
            return json.loads(b"".join(chunks).decode('utf-8'))
    except ConnectionRefusedError:
        return {"status": "error", "msg": "Bridge unreachable. Is Blender running?"}

# --- RESOURCES ---

@mcp.resource("massa://protocol/orchestration")
def get_orchestration():
    """Reads WF_MCP_ORCHESTRATION.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_MCP_ORCHESTRATION.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/repair")
def get_repair_protocol():
    """Reads WF_DEBUG_PROTOCOLS.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_DEBUG_PROTOCOLS.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/iterate")
def get_iterate_protocol():
    """Reads WF_ITERATION_LOGIC.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_ITERATION_LOGIC.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/generator_workflow")
def get_generator_workflow():
    """Reads WF_UNIFIED_Cart_Generator.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_UNIFIED_Cart_Generator.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/iterator_workflow")
def get_iterator_workflow():
    """Reads WF_UNIFIED_Cart_Iterator.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_UNIFIED_Cart_Iterator.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/repair_workflow")
def get_repair_workflow():
    """Reads WF_Cart_Repair.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_Cart_Repair.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/console_understanding")
def get_console_understanding():
    """Reads WF_Console_Understanding.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_Console_Understanding.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/audit_cartridge")
def get_audit_cartridge_protocol():
    """Reads audit_cartridge.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "audit_cartridge.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/audit_console")
def get_audit_console_protocol():
    """Reads audit_console.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "audit_console.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/cartridge_search")
def get_cartridge_search_protocol():
    """Reads WF_Cartridge_Search.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_Cartridge_Search.md")
    with open(path, "r") as f: return f.read()

@mcp.resource("massa://protocol/slot_standardization")
def get_slot_standardization_protocol():
    """Reads WF_Slot_Standardization.md"""
    path = os.path.join(AGENT_WORKFLOWS_DIR, "WF_Slot_Standardization.md")
    with open(path, "r") as f: return f.read()

# --- TOOLS ---

@mcp.tool()
def session_launch(headless: bool = False):
    """
    Launches Blender. 
    headless=True: Launches background tester (Option B).
    headless=False: Launches GUI (Option A).
    """
    cmd = [BLENDER_EXE]
    if headless:
        # Use the helper script to auto-enable addon and start listener
        cmd.extend(["--background", "--python", "headless_launcher.py"])
    subprocess.Popen(cmd)
    return "Blender Launch Initiated."

@mcp.tool()
def generate_cartridge(command_str: str):
    """[Generate State] Sends a creation string to the console."""
    return send_bridge("console_command", {"command": command_str})

@mcp.tool()
def iterate_parameters(properties: dict):
    """[Iterate State] Modifies Redo properties and Resurrects."""
    return send_bridge("set_redo_prop", properties)

@mcp.tool()
def scan_telemetry():
    """[Repair State] Returns ghost faces, manifold status, stats."""
    return send_bridge("get_telemetry")

@mcp.tool()
def scan_slots():
    """[Slot State] Returns Face ID distribution."""
    return send_bridge("get_slots")

@mcp.tool()
def scan_geometry_data():
    """[Engineer State] Returns Bounding Box, Dimensions, and Location of active object."""
    return send_bridge("get_bounds")

@mcp.tool()
def scan_visuals(view_mode: str = "WIRE"):
    """[Polish State] Returns Base64 image of viewport."""
    return send_bridge("get_vision", {"mode": view_mode})

@mcp.tool()
def file_system_edit(filename: str, mode: str, content: str = None):
    """[Repair State] Read/Write cartridge Python files."""
    path = os.path.join(CARTRIDGE_DIR, filename)
    if mode == 'READ':
        with open(path, 'r') as f: return f.read()
    elif mode == 'WRITE':
        with open(path, 'w') as f: f.write(content)
        return "File updated."

@mcp.tool()
def list_cartridges():
    """[Discovery State] Lists all available cartridge files in the library."""
    if not os.path.exists(CARTRIDGE_DIR):
        return "Error: Cartridge Directory not found."
    files = [f for f in os.listdir(CARTRIDGE_DIR) if f.endswith(".py") and not f.startswith("_")]
    return json.dumps(files)

@mcp.tool()
def read_library_source(filename: str):
    """[Discovery State] Reads a reference cartridge from the library (Read-Only)."""
    path = os.path.join(CARTRIDGE_DIR, filename)
    if not os.path.exists(path): return "Error: File not found."
    with open(path, 'r') as f: return f.read()

@mcp.tool()
def audit_cartridge(filename: str):
    """[Audit State] Runs the background auditor on a specific cartridge."""
    bridge_script = os.path.join(DEBUG_SYSTEM_DIR, "bridge.py")
    filename = os.path.basename(filename)
    cartridge_path = os.path.join(CARTRIDGE_DIR, filename)

    if not os.path.exists(cartridge_path):
        return f"Error: Cartridge {filename} not found."

    cmd = ["python", bridge_script, cartridge_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Audit execution failed: {str(e)}"

@mcp.tool()
def audit_console():
    """[Audit State] Runs the background auditor on the Massa Console architecture."""
    bridge_script = os.path.join(DEBUG_SYSTEM_DIR, "bridge_console.py")

    cmd = ["python", bridge_script]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Audit execution failed: {str(e)}"

if __name__ == "__main__":
    mcp.run()