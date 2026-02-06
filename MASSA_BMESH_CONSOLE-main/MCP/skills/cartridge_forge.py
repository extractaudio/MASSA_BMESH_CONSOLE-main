import os
import shutil
from typing import Literal
from core.server import mcp  # Imports the FastMCP instance from your core server

# --- CONFIGURATION ---
# Define the path to the geometry cartridges folder relative to this skill file
# Structure: MCP/skills/cartridge_forge.py -> MCP/../geometry_cartridges
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CARTRIDGE_DIR = os.path.join(BASE_DIR, "geometry_cartridges")

# Ensure the directory exists
os.makedirs(CARTRIDGE_DIR, exist_ok=True)

# --- TEMPLATES ---
# This skeleton adheres to Phase 2 (Structure) and Phase 4 (Slots) of the Monolithic Pipeline
TEMPLATE_SKELETON = """import bpy
import bmesh
import math
from mathutils import Vector, Matrix

def generate_geometry():
    # 1. SETUP
    mesh = bpy.data.meshes.new('{name}_Mesh')
    obj = bpy.data.objects.new('{name}', mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # 2. SLOT INITIALIZATION (Phase 4)
    # Critical: Initialize slots for procedural selection (Materials/Seams/Bevels)
    slots = {{'bevel': [], 'seam': [], 'subd': [], 'connector_top': []}}

    # 3. GEOMETRY CONSTRUCTION
    {construction_logic}

    # 4. FINALIZATION (Phase 3 Cleanup)
    # Mandatory cleanup to prevent zero-face errors and ensure manifold geometry
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    bm.to_mesh(mesh)
    bm.free()
    return obj
"""

# --- TOOLS ---

@mcp.tool()
def create_primitive_cartridge(
    name: str,
    primitive: Literal["CUBE", "CYLINDER", "ICOSPHERE", "PLANE", "MONKEY"] = "CUBE",
    size: float = 2.0,
    subdivisions: int = 1
) -> str:
    """
    Generates a new BMesh cartridge file based on a standard primitive.
    This is the starting point for most procedural geometry.
    
    Args:
        name: The name of the cartridge (e.g., 'Base_Chassis'). File will be {name}.py.
        primitive: The geometric primitive to generate.
        size: The overall size, radius, or dimensions of the primitive.
        subdivisions: Resolution for spheres or grid density.
        
    Returns:
        str: The absolute path to the generated cartridge file.
    """
    
    # Construct the BMesh logic string based on the requested primitive
    logic = ""
    if primitive == "CUBE":
        logic = f"bmesh.ops.create_cube(bm, size={size})"
    elif primitive == "CYLINDER":
        # Cylinder is created as a Cone with equal diameters
        logic = f"bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, diameter1={size}, diameter2={size}, depth={size})"
    elif primitive == "ICOSPHERE":
        logic = f"bmesh.ops.create_icosphere(bm, subdivisions={subdivisions}, radius={size/2})"
    elif primitive == "PLANE":
        logic = f"bmesh.ops.create_grid(bm, x_segments={subdivisions}, y_segments={subdivisions}, size={size})"
    elif primitive == "MONKEY":
        logic = f"bmesh.ops.create_monkey(bm, matrix=Matrix.Identity(4))"
    
    # Fill the template with the logic
    code_content = TEMPLATE_SKELETON.format(
        name=name,
        construction_logic=logic
    )
    
    # Save the file
    filename = f"{name}.py"
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    with open(filepath, "w") as f:
        f.write(code_content)
        
    return f"Successfully created cartridge: {filepath}"

@mcp.tool()
def write_cartridge_script(filename: str, script_content: str) -> str:
    """
    Writes a raw Python script to a cartridge file. 
    Use this tool to:
    1. Edit parameters of an existing cartridge (Redo).
    2. Fix errors found during the Audit phase.
    3. Write complex custom geometry that exceeds the primitive generator.
    
    Args:
        filename: The name of the file (e.g., 'Complex_Gear.py').
        script_content: The complete Python code for the cartridge.
        
    Returns:
        str: Status message with file path.
    """
    if not filename.endswith(".py"):
        filename += ".py"
        
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    # Write the content directly
    with open(filepath, "w") as f:
        f.write(script_content)
        
    return f"Cartridge script saved/updated at: {filepath}"

@mcp.tool()
def read_cartridge_script(filename: str) -> str:
    """
    Reads the content of an existing cartridge script.
    Use this to inspect the current parameters before making edits.
    
    Args:
        filename: The name of the file to read.
        
    Returns:
        str: The content of the script.
    """
    if not filename.endswith(".py"):
        filename += ".py"
        
    filepath = os.path.join(CARTRIDGE_DIR, filename)
    
    if not os.path.exists(filepath):
        return f"Error: File not found at {filepath}"
        
    with open(filepath, "r") as f:
        return f.read()

@mcp.tool()
def list_geometry_cartridges() -> str:
    """
    Lists all available geometry cartridge files in the library.
    Use this to find filenames before reading or editing them.
    
    Returns:
        str: A newline-separated list of .py files.
    """
    files = [f for f in os.listdir(CARTRIDGE_DIR) if f.endswith(".py")]
    if not files:
        return "No cartridges found."
    return "\n".join(files)

@mcp.tool()
def duplicate_cartridge(source_name: str, new_name: str) -> str:
    """
    Creates a copy of a cartridge. Use this for versioning before making edits.
    Example: duplicate_cartridge('Wheel_v1', 'Wheel_v2')
    """
    if not source_name.endswith(".py"): source_name += ".py"
    if not new_name.endswith(".py"): new_name += ".py"
    
    source_path = os.path.join(CARTRIDGE_DIR, source_name)
    new_path = os.path.join(CARTRIDGE_DIR, new_name)
    
    if not os.path.exists(source_path):
        return f"Error: Source {source_name} not found."
    if os.path.exists(new_path):
        return f"Error: Destination {new_name} already exists."
        
    shutil.copy2(source_path, new_path)
    return f"Success: Copied {source_name} to {new_name}"
