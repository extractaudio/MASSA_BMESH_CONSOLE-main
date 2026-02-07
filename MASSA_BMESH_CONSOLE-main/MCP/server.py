from mcp.server.fastmcp import FastMCP
import socket
import json
import subprocess
import os
import collections

mcp = FastMCP("Massa_Modular_Architect")

# CONSTANTS
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
BRIDGE_PORT = 5555
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARTRIDGE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../modules/cartridges"))
DEBUG_SYSTEM_DIR = os.path.abspath(os.path.join(BASE_DIR, "../modules/debugging_system"))
AGENT_WORKFLOWS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../.agent/workflows"))

import struct

def send_bridge(skill, params=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', BRIDGE_PORT))
            
            # Send Request
            payload_bytes = json.dumps({"skill": skill, "params": params or {}}).encode('utf-8')
            s.sendall(struct.pack('>I', len(payload_bytes)) + payload_bytes)
            
            # Read Response Length
            raw_len = recv_all(s, 4)
            if not raw_len: return {"status": "error", "msg": "Empty response from bridge"}
            msg_len = struct.unpack('>I', raw_len)[0]
            
            # Read Response Payload
            data = recv_all(s, msg_len)
            return json.loads(data.decode('utf-8'))
            
    except ConnectionRefusedError:
        return {"status": "error", "msg": "Bridge unreachable. Is Blender running?"}
    except Exception as e:
        return {"status": "error", "msg": f"Bridge Error: {str(e)}"}

def recv_all(conn, n):
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet: return None
        data += packet
    return data

def get_execution_mode():
    """
    Helper to check if we should run in Direct Mode (Active Viewport) or Background Mode.
    Returns: True for Direct Mode, False for Background Mode.
    """
    config_resp = send_bridge("get_server_config")
    if "config" in config_resp:
        return config_resp["config"].get("use_direct_mode", False)
    return False

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
def generate_scene(layout: list, filename: str = None):
    """
    [Integration State] Creates a scene in the Active Viewport based on the provided layout.

    Args:
        layout: List of objects/cartridges to create.
                Example: [{"type": "CARTRIDGE", "id": "cart_prim_cube", "transforms": {"location": [0,0,0]}}]
        filename: Optional filename to save the build profile/layout JSON.

    Returns:
        JSON string containing the Overview (Build Profile) and the Execution Report.
    """
    # 1. Enforce Direct Mode
    is_direct = get_execution_mode()
    if not is_direct:
        return "Action Aborted: 'Generate Scene' requires Direct Mode (Active Viewport). Please enable 'Direct Execution' in the N-Panel."

    # 2. Generate Overview (Build Profile)
    overview = {
        "total_objects": len(layout),
        "cartridges": collections.Counter(),
        "primitives": collections.Counter()
    }

    for item in layout:
        obj_type = item.get("type", "PRIMITIVE")
        obj_id = item.get("id", "unknown")
        if obj_type == "CARTRIDGE":
            overview["cartridges"][obj_id] += 1
        else:
            overview["primitives"][obj_id] += 1

    # Convert counters to dicts for JSON serialization
    overview["cartridges"] = dict(overview["cartridges"])
    overview["primitives"] = dict(overview["primitives"])

    # 3. Execute Creation
    # We pass 'audit=True' implicitly to get the full report
    params = {"layout": layout, "audit": True}
    if filename:
        params["filepath"] = filename

    # Send to Bridge
    bridge_response = send_bridge("create_scene", params)

    # 4. Combine and Return
    result = {
        "overview": overview,
        "execution_report": bridge_response.get("report", bridge_response)
    }

    return json.dumps(result, indent=4)

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
def inspect_scene(limit: int = 20, offset: int = 0, object_type: str = None):
    """[Engineer State] Lists objects in the scene with basic info (Location, Type, Visibility)."""
    return send_bridge("get_scene_info", {"limit": limit, "offset": offset, "object_type": object_type})

@mcp.tool()
def inspect_object(object_name: str):
    """[Engineer State] Detailed info about a specific object (Modifiers, Constraints, Parents, Health)."""
    return send_bridge("get_object_info", {"object_name": object_name})

@mcp.tool()
def scan_visuals(view_mode: str = "WIRE"):
    """[Polish State] Returns Base64 image of viewport."""
    return send_bridge("get_vision", {"mode": view_mode})

@mcp.tool()
def restore_selection():
    """[Error Recovery] Reselects the last object targeted by a Massa operation. Fixes 'No Active Object' errors."""
    return send_bridge("restore_last_selection")

@mcp.tool()
def run_script(code: str):
    """[Repair State] Executes raw Python code in Blender context. Use for advanced debugging or one-off queries."""
    return send_bridge("execute_code", {"code": code})

@mcp.tool()
def massa_generator(cartridge_id: str, creation_params: dict = None, modification_params: dict = None):
    """
    [Integration Test] Automated UI Tester.
    1. Creates a cartridge (cartridge_id) with initial properties (creation_params).
    2. OPTIONAL: Sets new properties (modification_params) and triggers 'Resurrect' to test Redo logic.
    """
    params = {
        "cartridge_id": cartridge_id,
        "creation_params": creation_params or {},
        "modification_params": modification_params
    }
    return send_bridge("test_generator_ui", params)

@mcp.tool()
def forge_bmesh(script_content: str, name: str = "New_Object"):
    """[Forge State] Creates a mesh from a raw BMesh script (bypassing Cartridge system). Useful for prototyping geometry logic."""
    return send_bridge("create_bmesh", {"script_content": script_content, "name": name})

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
def list_materials():
    """[Discovery State] Lists all materials currently in the Blender file. Use this to find valid inputs for 'mat_' slots."""
    return send_bridge("get_materials")

@mcp.tool()
def audit_cartridge(filename: str):
    """[Audit State] Runs the background auditor on a specific cartridge."""
    filename = os.path.basename(filename)
    cartridge_path = os.path.join(CARTRIDGE_DIR, filename)

    if not os.path.exists(cartridge_path):
        return f"Error: Cartridge {filename} not found."

    use_direct = get_execution_mode()

    if use_direct:
        # Run Direct
        resp = send_bridge("audit_cartridge_direct", {"path": cartridge_path})
        if "report" in resp:
            return json.dumps(resp["report"], indent=4)
        else:
            return json.dumps(resp, indent=4)
    else:
        # Run Background (Headless Safety Check)
        # Uses modules/debugging_system/bridge.py to spawn a fresh process
        headless_launcher = os.path.join(DEBUG_SYSTEM_DIR, "bridge.py")
        cmd = ["python", headless_launcher, cartridge_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Audit execution failed: {str(e)}"

@mcp.tool()
def audit_console():
    """[Audit State] Runs the background auditor on the Massa Console architecture."""
    use_direct = get_execution_mode()

    if use_direct:
        # Run Direct
        resp = send_bridge("audit_console_direct")
        if "report" in resp:
            return json.dumps(resp["report"], indent=4)
        else:
            return json.dumps(resp, indent=4)
    else:
        headless_launcher = os.path.join(DEBUG_SYSTEM_DIR, "bridge_console.py")
        cmd = ["python", headless_launcher]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Audit execution failed: {str(e)}"

@mcp.tool()
def execute_contextual_op(op_id: str, space_type: str = "VIEW_3D"):
    """
    [System State] Executes a Blender Operator inside a temporary context override.
    Crucial for Blender 5.0+ strict context rules.
    """
    return send_bridge("execute_contextual_op", {"op_id": op_id, "space_type": space_type})

@mcp.tool()
def edit_node_graph(object_name: str, tree_type: str, operation: str, params: dict):
    """
    [Engineer State] Adds, links, or modifies nodes in Geometry, Shader, or Compositor trees.
    operation: 'ADD_NODE', 'CONNECT', 'SET_VALUE'.
    """
    p = {"object_name": object_name, "tree_type": tree_type, "operation": operation}
    p.update(params)
    return send_bridge("edit_node_graph", p)

@mcp.tool()
def inspect_evaluated_data(object_name: str):
    """
    [Engineer State] Returns the mesh statistics from the Dependency Graph (Evaluated).
    Essential for Geometry Nodes where the source mesh differs from the viewport result.
    """
    return send_bridge("inspect_evaluated_data", {"object_name": object_name})

@mcp.tool()
def manage_action_slots(object_name: str, operation: str, slot_name: str, action_name: str = None):
    """
    [Iterate State] Creates and assigns Animation Layers using the new Slotted Action system.
    operation: 'CREATE' or 'ASSIGN'.
    """
    return send_bridge("manage_action_slots", {
        "object_name": object_name, 
        "operation": operation, 
        "slot_name": slot_name, 
        "action_name": action_name
    })

@mcp.tool()
def query_asset_browser(query: str = None, library_name: str = None):
    """
    [Integration State] Searches for assets in local and external libraries.
    """
    return send_bridge("query_asset_browser", {"query": query, "library_name": library_name})

@mcp.tool()
def configure_eevee_next(settings: dict):
    """
    [Polish State] Configures settings for the new EEVEE Next render engine.
    settings example: {"raytracing": True, "shadows": True, "gtao": True}
    """
    return send_bridge("configure_eevee_next", {"settings": settings})

@mcp.tool()
def organize_outliner(method: str = "BY_NAME", rules: dict = None, ignore_hidden: bool = True):
    """
    [Polish State] Organizes the Blender Outliner by grouping objects into collections.
    
    Args:
        method: Strategy to use. 
               - "BY_NAME": Groups by Name Prefix (e.g. Wall_01 -> Wall). 
               - "BY_TYPE": Groups by Object Type (MESH, LIGHT, CAMERA).
               - "BY_PREFIX": Uses 'rules' dict {prefix: collection_name}.
        rules: Dictionary for "BY_PREFIX" mode. e.g. {"rect_": "Rectangles", "circle_": "Circles"}
        ignore_hidden: If True, skips objects hidden in the viewport.
    """
    return send_bridge("organize_outliner", {"method": method, "rules": rules, "ignore_hidden": ignore_hidden})

@mcp.tool()
def verify_material_logic(filename: str) -> str:
    """
    [Phase 4] Static Analysis of Material Slot Logic.
    Checks if the cartridge code attempts to assign material indices (MAT_TAG).
    """
    path = os.path.join(CARTRIDGE_DIR, filename)
    if not os.path.exists(path): return f"Error: {filename} not found."
    
    with open(path, 'r') as f: content = f.read()
    
    report = []
    if 'bm.faces.layers.int.get("MAT_TAG")' in content or 'bm.faces.layers.int.new("MAT_TAG")' in content:
        report.append("PASS: MAT_TAG layer detected.")
    else:
        report.append("FAIL: MAT_TAG layer missing.")

    if 'bm.edges.layers.int.get("MASSA_EDGE_SLOTS")' in content or 'bm.edges.layers.int.new("MASSA_EDGE_SLOTS")' in content:
        report.append("PASS: MASSA_EDGE_SLOTS layer detected.")
    else:
        report.append("FAIL: MASSA_EDGE_SLOTS layer missing.")
        
    return "\n".join(report)

if __name__ == "__main__":
    mcp.run()