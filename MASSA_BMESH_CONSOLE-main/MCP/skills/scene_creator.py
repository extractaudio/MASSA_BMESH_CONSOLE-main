import json
from typing import List, Dict, Optional, Union, Any, Literal


def create_scene(
    layout: List[Dict[str, Any]],
    audit: bool = True,
    avoid_duplicates: bool = True,
    check_collisions: bool = False,
    visual_style: Literal["SOLID", "WIREFRAME", "RENDERED"] = "SOLID",
    camera_angle: Literal["ISO_CAM", "TOP", "FRONT", "RIGHT"] = "ISO_CAM"
) -> str:
    """
    Populate the scene with multiple objects (Cartridges or Shapes) based on a layout specification,
    then perform an audit and visual capture.
    
    Intelligent Data & Gap Analysis:
    - Idempotency: 'avoid_duplicates' prevents re-creating existing objects.
    - Spatial Safety: 'check_collisions' prevents mesh-inside-mesh placement.
    - Visual Context: 'visual_style' and 'camera_angle' provide better audit shots.

    Args:
        layout: List of objects to create. Each item should have:
            - type: "CARTRIDGE" or "PRIMITIVE" (default: "PRIMITIVE")
            - id: Cartridge ID (e.g., 'prim_con_beam') or parameters for primitive.
            - name: (Optional) Name of the object.
            - parameters: (Optional) Dict of creation parameters.
            - transforms: (Optional) Dict with 'location', 'rotation', 'scale'.
        audit: If True, performs structural and visual auditing after generation.
        avoid_duplicates: If True, skips creation if an object with the same name exists.
        check_collisions: If True, checks for bounding box overlaps (prevents mesh-in-mesh).
        visual_style: Viewport shading mode for the audit screenshot.
        camera_angle: Camera angle for the audit screenshot.

    Returns:
        JSON string containing the execution report, scene stats, and visual capture.
    """
    import os
    import time
    
    # 1. Prepare File Path
    # Root finding logic (assuming this file is in MCP/skills/)
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    export_dir = os.path.join(root_dir, "_EXPORT", "scenes")
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = int(time.time())
    filename = f"scene_{timestamp}.json"
    filepath = os.path.join(export_dir, filename)
    
    # 2. Write Layout to File
    file_data = {
        "layout": layout,
        "meta": {
            "timestamp": timestamp,
            "source": "scene_creator.py"
        }
    }
    
    with open(filepath, 'w') as f:
        json.dump(file_data, f, indent=2)
        
    print(f"Scene Creator: Saved layout to {filepath}")

    # 3. Send Bridge Command (Pointing to file)
    payload = {
        "filepath": filepath, # New Mode
        # "layout": layout,   # Legacy Mode (Omitted to force file read)
        "audit": audit,
        "avoid_duplicates": avoid_duplicates,
        "check_collisions": check_collisions,
        "visual_style": visual_style,
        "camera_angle": camera_angle
    }
    
    # Invoke the new skill on the live bridge
    from core.bridge_client import send_bridge
    
    # We send the payload directly. 'create_scene' key in bridge handles the skill name.
    result = send_bridge("create_scene", payload)
    
    return json.dumps(result, indent=2)
