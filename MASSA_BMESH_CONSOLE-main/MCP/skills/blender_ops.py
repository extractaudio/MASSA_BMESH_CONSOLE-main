import json
from enum import Enum
from typing import Optional, List, Literal, Tuple, Union
from core.server import mcp
from skills import inspector
from core.bridge_client import send_bridge

# --- TOOLS ---

@mcp.tool()
def get_scene_info(
    limit: int = 20, 
    offset: int = 0, 
    object_type: Optional[str] = None
) -> str:
    """
    Get detailed information about the current Blender scene.
    
    Args:
        limit: Maximum number of objects to return (default: 20)
        offset: Number of objects to skip (default: 0)
        object_type: Filter objects by type (e.g., 'MESH', 'CAMERA', 'LIGHT')
        
    Returns:
        JSON string containing scene stats and object list.
    """
    payload = {
        "limit": limit,
        "offset": offset,
        "object_type": object_type
    }
    # We use a dummy file path because _invoke_bridge requires one, 
    # even though these global skills don't strictly need a cartridge.
    # We'll use a placeholder.
    dummy_path = "global_skill_placeholder.py"
    
    result = inspector._invoke_bridge(dummy_path, mode="SKILL_EXEC", payload={
        "skill": "get_scene_info",
        "params": payload
    })
    
    return json.dumps(result, indent=2)

@mcp.tool()
def get_object_info(object_name: str) -> str:
    """
    Get detailed information about a specific object in the Blender scene.
    Acts as an Audit tool: returns transforms, dimensions, modifiers, constraints, 
    hierarchy, collections, and health check status.
    
    Args:
        object_name: The name of the object to get information about.
        
    Returns:
        JSON string with object details or error message.
    """
    payload = {"object_name": object_name}
    dummy_path = "global_skill_placeholder.py"
    
    result = inspector._invoke_bridge(dummy_path, mode="SKILL_EXEC", payload={
        "skill": "get_object_info",
        "params": payload
    })
    
    return json.dumps(result, indent=2)

@mcp.tool()
def get_viewport_screenshot(max_size: int = 800) -> str:
    """
    Capture a screenshot of the current Blender 3D viewport.
    
    Args:
        max_size: Maximum size in pixels for the largest dimension (default: 800).
                  (Note: Current bridge implementation might ignore resizing, returning native viewport res)
                  
    Returns:
        String containing the path to the captured image or Base64 data.
    """
    payload = {"mode": "SOLID"} # Defaulting to solid for screenshot
    dummy_path = "global_skill_placeholder.py"
    
    result = inspector._invoke_bridge(dummy_path, mode="SKILL_EXEC", payload={
        "skill": "get_vision", # Maps to existing bridge skill
        "params": payload
    })
    
    if result.get("image"):
        # The bridge currently returns base64 in "image" key for get_vision skill
        # Or sometimes path depending on implementation. 
        # Our updated bridge code for 'get_vision' returns "image" as base64.
        return f"Screenshot Captured (Base64 length: {len(result['image'])})"
    else:
        return f"Screenshot Failed: {result.get('msg', 'Unknown Error')}"

@mcp.tool()
def execute_blender_code(code: str) -> str:
    """
    Execute arbitrary Python code in Blender.
    
    > [!WARNING] 
    > Use with caution. This executes unchecked code within the Blender process.
    > Ensure code is broken into small, safe chunks.
    
    Args:
        code: The Python code to execute.
        
    Returns:
        String containing the stdout output of the executed code.
    """
    payload = {"code": code}
    dummy_path = "global_skill_placeholder.py"
    
    result = inspector._invoke_bridge(dummy_path, mode="SKILL_EXEC", payload={
        "skill": "execute_code",
        "params": payload
    })
    
    output = result.get("output", "")
    status = result.get("status", "unknown")
    
    if status == "error":
        return f"Execution Code: {status}\nError: {result.get('msg')}"
    return f"Execution Code: {status}\nOutput:\n{output}"

@mcp.tool()
def create_bmesh_object(name: str, script_content: str) -> str:
    """
    Create a new object using a BMesh script, following the BMesh Manifesto rules.
    
    The environment has: 'bm' (detached BMesh), 'bmesh', 'bpy', 'mathutils'.
    
    Rules:
    1. Operate on 'bm'.
    2. Lookup Law: Call 'ensure_lookup_table()' after adding/removing geometry.
    3. Direct Injection: Use 'bmesh.ops.create_*' where possible.
    
    The system automatically converts 'bm' to an object, ensures 10 material slots, 
    and links it to the scene.
    
    Args:
        name: Name of the new object.
        script_content: Python code to build the geometry on 'bm'.
        
    Returns:
        Status message.
    """
    payload = {
        "name": name,
        "script_content": script_content
    }
    dummy_path = "global_skill_placeholder.py"
    
    result = inspector._invoke_bridge(dummy_path, mode="SKILL_EXEC", payload={
        "skill": "create_bmesh",
        "params": payload
    })
    
    return json.dumps(result, indent=2)

@mcp.tool()
def transform_object(
    name: str,
    location: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
    mode: Literal["ABSOLUTE", "RELATIVE"] = "ABSOLUTE"
) -> str:
    """
    Move, Rotate, and Rescale an object in the Blender scene.
    
    Args:
        name: Name of the object to transform.
        location: [x, y, z] coordinates to move to (or offset by).
        rotation: [x, y, z] rotation in DEGREES.
        scale: [x, y, z] scale factors.
        mode: 'ABSOLUTE' (set values) or 'RELATIVE' (add/multiply values).
              - Relative Location: Adds to current location.
              - Relative Rotation: Adds to current rotation (euler).
              - Relative Scale: Multiplies current scale.
              
    Returns:
        Status message with new transforms.
    """
    payload = {
        "name": name,
        "location": location,
        "rotation": rotation,
        "scale": scale,
        "mode": mode
    }
    dummy_path = "global_skill_placeholder.py"
    
    result = inspector._invoke_bridge(dummy_path, mode="SKILL_EXEC", payload={
        "skill": "transform_object",
        "params": payload
    })
    
    return json.dumps(result, indent=2)

@mcp.tool()
def execute_contextual_op(op_id: str, space_type: str = "VIEW_3D") -> str:
    """
    [System State] Executes a Blender Operator inside a temporary context override.
    Crucial for Blender 5.0+ strict context rules.
    """
    return json.dumps(send_bridge("execute_contextual_op", {"op_id": op_id, "space_type": space_type}))

@mcp.tool()
def edit_node_graph(object_name: str, tree_type: str, operation: str, params: dict) -> str:
    """
    [Engineer State] Adds, links, or modifies nodes in Geometry, Shader, or Compositor trees.
    operation: 'ADD_NODE', 'CONNECT', 'SET_VALUE'.
    """
    p = {"object_name": object_name, "tree_type": tree_type, "operation": operation}
    p.update(params)
    return json.dumps(send_bridge("edit_node_graph", p))

@mcp.tool()
def inspect_evaluated_data(object_name: str) -> str:
    """
    [Engineer State] Returns the mesh statistics from the Dependency Graph (Evaluated).
    Essential for Geometry Nodes where the source mesh differs from the viewport result.
    """
    return json.dumps(send_bridge("inspect_evaluated_data", {"object_name": object_name}))

@mcp.tool()
def manage_action_slots(object_name: str, operation: str, slot_name: str, action_name: str = None) -> str:
    """
    [Iterate State] Creates and assigns Animation Layers using the new Slotted Action system.
    operation: 'CREATE' or 'ASSIGN'.
    """
    return json.dumps(send_bridge("manage_action_slots", {
        "object_name": object_name, 
        "operation": operation, 
        "slot_name": slot_name, 
        "action_name": action_name
    }))

@mcp.tool()
def query_asset_browser(query: str = None, library_name: str = None) -> str:
    """
    [Integration State] Searches for assets in local and external libraries.
    """
    return json.dumps(send_bridge("query_asset_browser", {"query": query, "library_name": library_name}))

@mcp.tool()
def configure_eevee_next(settings: dict) -> str:
    """
    [Polish State] Configures settings for the new EEVEE Next render engine.
    settings example: {"raytracing": True, "shadows": True, "gtao": True}
    """
    return json.dumps(send_bridge("configure_eevee_next", {"settings": settings}))
