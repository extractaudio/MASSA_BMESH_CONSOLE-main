
from typing import Dict, Literal, Optional
import json

def organize_outliner(
    method: Literal["BY_NAME", "BY_TYPE", "BY_PREFIX"] = "BY_NAME",
    rules: Optional[Dict[str, str]] = None,
    ignore_hidden: bool = True
) -> str:
    """
    Organizes the Blender Outliner by grouping objects into collections.

    Args:
        method: Strategy to use. 
               - "BY_NAME": Groups by Name Prefix (e.g. Wall_01 -> Wall). 
               - "BY_TYPE": Groups by Object Type (MESH, LIGHT, CAMERA).
               - "BY_PREFIX": Uses 'rules' dict {prefix: collection_name}.
        rules: Dictionary for "BY_PREFIX" mode. e.g. {"rect_": "Rectangles", "circle_": "Circles"}
        ignore_hidden: If True, skips objects hidden in the viewport.
        
    Returns:
        JSON string containing the execution report.
    """
    payload = {
        "method": method,
        "rules": rules,
        "ignore_hidden": ignore_hidden
    }
    
    # Invoke via bridge
    from core.bridge_client import send_bridge
    result = send_bridge("organize_outliner", payload)
    
    return json.dumps(result, indent=2)
