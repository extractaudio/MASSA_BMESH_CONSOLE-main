import os
import re
import json
import subprocess
import time
from typing import Literal, Optional, Dict, Any
from core.server import mcp

# --- CONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CARTRIDGE_DIR = os.path.join(BASE_DIR, "geometry_cartridges")
OUTPUT_DIR = os.path.join(BASE_DIR, "audit_output")
BRIDGE_SCRIPT = os.path.join(BASE_DIR, "modules", "debugging_system", "runner.py")

# Ensure output directory exists for visual dumps
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- HELPER FUNCTIONS ---

def _invoke_bridge(target_file: str, mode: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Internal helper to communicate with the Blender Bridge.
    Executes the bridge.py script which runs inside/controls Blender.
    """
    if not os.path.exists(BRIDGE_SCRIPT):
        return {
            "status": "SYSTEM_FAILURE",
            "message": f"Bridge script not found at {BRIDGE_SCRIPT}. Check configuration."
        }

    # Construct command: python runner.py --cartridge [target] --mode [mode] [--payload [json]]
    cmd = ["python", BRIDGE_SCRIPT, "--cartridge", target_file, "--mode", mode]
    
    if payload:
        cmd.extend(["--payload", json.dumps(payload)])

    try:
        # Run the bridge process
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        
        if result.returncode != 0:
            return {
                "status": "CRASH",
                "message": f"Blender/Bridge crashed: {result.stderr}"
            }
            
        # Attempt to parse the JSON output from the bridge
        try:
            # Assuming the bridge prints the JSON result to stdout last
            output_lines = result.stdout.strip().split('\n')
            json_str = output_lines[-1] if output_lines else "{}"
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "status": "PARSE_ERROR",
                "raw_output": result.stdout
            }
            
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "message": "Execution took too long."}
    except Exception as e:
        return {"status": "SYSTEM_FAILURE", "message": str(e)}

# --- MCP TOOLS ---

@mcp.tool()
def audit_cartridge_geometry(filename: str) -> str:
    """
    Performs the 'Shadow Audit' (Phase 6) on a geometry cartridge.
    
    This runs the code in a headless Blender instance to verify:
    1. Topology Health (Zero-area faces, Non-manifold edges).
    2. Slot Integrity (Are edges actually selected?).
    3. Execution Stability (Does it crash?).
    
    Args:
        filename: The name of the cartridge file (e.g., 'Tank_Tread.py').
        
    Returns:
        JSON string containing the Audit Report (Pass/Fail, Stats, Errors).
    """
    if not filename.endswith(".py"):
        filename += ".py"
    
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    if not os.path.exists(filepath):
        return f"Error: File {filename} not found."

    # Invoke the bridge in 'audit' mode
    telemetry = _invoke_bridge(filepath, mode="AUDIT")
    
    return json.dumps(telemetry, indent=2)

@mcp.tool()
def inspect_viewport(
    filename: str, 
    angle: Literal["FRONT", "RIGHT", "TOP", "ISO_CAM", "FOCUS_SELECTED"] = "ISO_CAM",
    view_mode: Literal["SOLID", "WIREFRAME", "MATERIAL"] = "WIREFRAME"
) -> str:
    """
    'Sees' the mesh by rendering a viewport snapshot.
    Use this to visually verify seam placement, shape proportions, and topology flow.
    
    Args:
        filename: The cartridge to visualize.
        angle: Camera position. 'FOCUS_SELECTED' centers the view on the generated object.
        view_mode: 'WIREFRAME' is best for checking topology and seams.
        
    Returns:
        str: Path to the generated image file.
    """
    if not filename.endswith(".py"):
        filename += ".py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)

    payload = {
        "camera_angle": angle,
        "shading": view_mode,
        "resolution": [1024, 1024]
    }

    # Invoke bridge in 'render' mode
    result = _invoke_bridge(filepath, mode="RENDER", payload=payload)
    
    if result.get("status") == "SUCCESS":
        image_path = result.get("image_path")
        return f"Viewport Captured: {image_path}"
    else:
        return f"Failed to capture viewport: {result.get('message')}"

@mcp.tool()
def stress_test_ui_parameters(filename: str, parameter_json: str) -> str:
    """
    Simulates the 'Redo Panel' by injecting new parameters into the script 
    and attempting generation. This ensures the script is robust enough for user interaction.
    
    Args:
        filename: The cartridge to test.
        parameter_json: JSON string of variables to override. 
                        Example: '{"size": 4.5, "subdivisions": 3}'
                        
    Returns:
        str: Audit report for the modified parameters.
    """
    try:
        params = json.loads(parameter_json)
    except json.JSONDecodeError:
        return "Error: parameter_json must be valid JSON."
        
    if not filename.endswith(".py"):
        filename += ".py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)

    # Invoke bridge in 'stress_test' mode with params
    result = _invoke_bridge(filepath, mode="STRESS_TEST", payload=params)
    
    return json.dumps(result, indent=2)

@mcp.tool()
def run_blender_analysis(filename: str, tool_name: str) -> str:
    """
    Calls specific Blender analysis tools for deeper inspection.
    
    Args:
        filename: The cartridge to analyze.
        tool_name: The analysis to run. Options:
                   - 'PRINT3D': Checks for 3D printing suitability (overhangs, wall thickness).
                   - 'UV_OVERLAP': Checks for overlapping UV islands.
                   - 'FACE_AREA': Returns distribution of face sizes (detects tiny faces).
                   
    Returns:
        str: Analysis results.
    """
    if not filename.endswith(".py"):
        filename += ".py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    payload = {"tool": tool_name}
    result = _invoke_bridge(filepath, mode="DEEP_ANALYSIS", payload=payload)
    
    return json.dumps(result, indent=2)
@mcp.tool()
def visual_regression_diff(filename_a: str, filename_b: str) -> str:
    """
    [Phase 1] Visual Diffing.
    Overlays the wireframe of Version A (Red) onto Version B (Green).
    
    Args:
        filename_a: The baseline cartridge filename.
        filename_b: The new version filename.
        
    Returns:
        str: Path to the generated diff image.
    """
    if not filename_a.endswith(".py"): filename_a += ".py"
    if not filename_b.endswith(".py"): filename_b += ".py"
    
    path_a = os.path.join(CARTRIDGE_DIR, filename_a)
    path_b = os.path.join(CARTRIDGE_DIR, filename_b)
    
    if not os.path.exists(path_a): return f"Error: {filename_a} not found."
    if not os.path.exists(path_b): return f"Error: {filename_b} not found."

    payload = {"filename_b": path_b}
    
    # Invoke bridge in 'VISUAL_DIFF' mode
    result = _invoke_bridge(path_a, mode="VISUAL_DIFF", payload=payload)
    
    if result.get("status") == "SUCCESS":
        return f"Diff Generated: {result.get('image_path')}"
    else:
        return f"Diff Failed: {result.get('message')}"

@mcp.tool()
def inspect_uv_heatmap(filename: str) -> str:
    """
    [Phase 2] UV Heatmaps.
    Generates a heatmap of UV stretching (Blue=Good, Red=Bad).
    
    Args:
        filename: The cartridge to inspect.
        
    Returns:
        str: Path to the heatmap image.
    """
    if not filename.endswith(".py"): filename += ".py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    if not os.path.exists(filepath): return f"Error: {filename} not found."
    
    # Invoke bridge in 'UV_HEATMAP' mode
    result = _invoke_bridge(filepath, mode="UV_HEATMAP")
    
    if result.get("status") == "SUCCESS":
        return f"Heatmap Generated: {result.get('image_path')}"
    else:
        return f"Heatmap Failed: {result.get('message')}"

@mcp.tool()
def audit_performance(filename: str) -> str:
    """
    [Phase 3] Performance Budgeting.
    Checks execution time and polycount against safety limits.
    
    Args:
        filename: The cartridge to audit.
        
    Returns:
        str: JSON report with execution_time_ms, poly_count, and budget_status.
    """
    if not filename.endswith(".py"): filename += ".py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    if not os.path.exists(filepath): return f"Error: {filename} not found."
    
    # Invoke bridge in 'PERFORMANCE' mode
    result = _invoke_bridge(filepath, mode="PERFORMANCE")
    
    return json.dumps(result, indent=2)

@mcp.tool()
def debug_csg_tree(filename: str, angle: str = "ISO_CAM") -> str:
    """
    [Phase 4] CSG Tree Visualization.
    Visualizes boolean 'cutter' objects that are typically hidden.
    
    Args:
        filename: The cartridge to debug.
        angle: Camera angle.
        
    Returns:
        str: Path to the CSG debug image.
    """
    if not filename.endswith(".py"): filename += ".py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    if not os.path.exists(filepath): return f"Error: {filename} not found."
    
    payload = {"camera_angle": angle}
    
    # Invoke bridge in 'CSG_DEBUG' mode
    result = _invoke_bridge(filepath, mode="CSG_DEBUG", payload=payload)
    
    if result.get("status") == "SUCCESS":
        return f"CSG Debug View: {result.get('image_path')} (Cutters visible: {result.get('cutters_visualized')})"
    else:
        return f"CSG Debug Failed: {result.get('message')}"

@mcp.tool()
def visualize_edge_slots(filename: str, slot_name: str = "seam") -> str:
    """
    [Phase 4] Edge Slot Visualization.
    Visualizes specific edge slots (e.g., 'seam', 'bevel', 'crease') by highlighting them.
    Crucial for verifying that procedural selection logic is working correctly.
    
    Args:
        filename: The cartridge to inspect.
        slot_name: The key in the 'slots' dictionary to highlight (default: 'seam').
        
    Returns:
        str: Path to the visualization image.
    """
    if not filename.endswith(".py"): filename += ".py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    payload = {"highlight_slot": slot_name}
    result = _invoke_bridge(filepath, mode="SLOT_VISUALIZATION", payload=payload)
    
    if result.get("status") == "SUCCESS":
        return f"Slot '{slot_name}' Visualized: {result.get('image_path')}"
    else:
        return f"Slot Visualization Failed: {result.get('message')}"

@mcp.tool()
def verify_material_logic(filename: str) -> str:
    """
    [Phase 4] Static Analysis of Material Slot Logic.
    Checks if the cartridge code attempts to assign material indices (MAT_TAG).
    This ensures the 'Hard 10' mandate is being followed in the code structure.
    """
    if not filename.endswith(".py"): filename += ".py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    if not os.path.exists(filepath): return f"Error: {filename} not found."
    
    with open(filepath, 'r') as f: content = f.read()
    
    report = []
    
    # Check for Layer retrieval
    if 'bm.faces.layers.int.get("MAT_TAG")' in content:
        report.append("PASS: MAT_TAG layer retrieved.")
    else:
        report.append("FAIL: MAT_TAG layer not retrieved. Faces cannot be assigned materials.")
        
    return "\n".join(report)
