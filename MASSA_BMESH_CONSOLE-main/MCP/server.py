from mcp.server.fastmcp import FastMCP
import socket
import json
import subprocess
import os

mcp = FastMCP("Massa_Modular_Architect")

# CONSTANTS
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
BRIDGE_PORT = 5555
CARTRIDGE_DIR = os.path.join(os.getcwd(), "cartridges")

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
    with open("WF_MCP_ORCHESTRATION.md", "r") as f: return f.read()

@mcp.resource("massa://protocol/repair")
def get_repair_protocol():
    """Reads WF_DEBUG_PROTOCOLS.md"""
    with open("WF_DEBUG_PROTOCOLS.md", "r") as f: return f.read()

@mcp.resource("massa://protocol/iterate")
def get_iterate_protocol():
    """Reads WF_ITERATION_LOGIC.md"""
    with open("WF_ITERATION_LOGIC.md", "r") as f: return f.read()

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

if __name__ == "__main__":
    mcp.run()