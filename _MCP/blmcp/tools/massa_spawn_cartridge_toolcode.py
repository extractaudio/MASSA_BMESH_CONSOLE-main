# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for spawning Massa procedural geometry cartridges.
"""

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple, Any


class Params(NamedTuple):
    cartridge_id: str
    location: list[float]
    rotation: list[float]
    console_params: dict[str, Any]
    cartridge_params: dict[str, Any]


class Result(NamedTuple):
    status: str
    object_name: str | None
    error: str | None = None


def main(params: Params) -> Result:
    import bpy  # pylint: disable=import-error,no-name-in-module
    
    cart_id = params.cartridge_id
    if not cart_id.startswith("massa.gen_"):
        cart_id = "massa.gen_" + cart_id
    
    op_name = cart_id.replace("massa.", "")
    op = getattr(bpy.ops.massa, op_name, None)
    if not op:
        return Result(status="error", object_name=None, error=f"Operator {cart_id} not found.")

    # Save original console state for keys we will modify
    console = bpy.context.scene.massa_console
    original_console_state = {}
    for k, v in params.console_params.items():
        if hasattr(console, k):
            original_console_state[k] = getattr(console, k)
            setattr(console, k, v)
    
    c_params = dict(params.cartridge_params)
    if "obj_location" not in c_params:
        c_params["obj_location"] = params.location
    if "obj_rotation" not in c_params:
        c_params["obj_rotation"] = params.rotation
        
    try:
        # Call the operator
        op(**c_params)
        
        # The newly generated object is typically the active object
        obj = bpy.context.active_object
        obj_name = obj.name if obj else None
    except Exception as e:  # pylint: disable=broad-exception-caught
        obj_name = None
        error = str(e)
    else:
        error = None
    
    # Restore console state
    for k, v in original_console_state.items():
        try:
            setattr(console, k, v)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
            
    if error:
        return Result(status="error", object_name=None, error=error)
    return Result(status="ok", object_name=obj_name)
