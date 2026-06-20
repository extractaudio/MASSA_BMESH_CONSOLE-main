# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for introspecting a Massa cartridge operator's parameter schema.

Mirrors the property iteration used by the engine's ``_capture_operator_params``
(``massa/modules/massa_engine.py``) so the reported parameters match what
``massa_spawn_cartridge`` / ``massa_rerun_cartridge`` actually accept.
"""

__all__ = ("Params", "Result", "main")

from typing import NamedTuple, Any


class Params(NamedTuple):
    cartridge_id: str


class Result(NamedTuple):
    status: str
    cartridge_id: str | None = None
    bl_idname: str | None = None
    parameters: list[dict[str, Any]] | None = None
    cartridge_specific_params: list[str] | None = None
    error: str | None = None


def _is_builtin_prop(ident: str) -> bool:
    # Operator RNA exposes bl_* builtins (bl_options, bl_cursor_pending, ...)
    # and rna_type which are not real parameters.
    return ident == "rna_type" or ident.startswith("bl_")


def main(params: Params) -> Result:
    import math
    import bpy

    try:
        from massa.modules.cartridges import CLASSES
    except ImportError as exc:
        return Result(status="error", cartridge_id=params.cartridge_id, error=str(exc))

    def _fin(value):
        # Clamp non-finite floats (inf for unbounded props) to None for clean JSON.
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value

    cid = params.cartridge_id
    norm = cid
    for pre in ("massa.gen_", "massa.", "gen_"):
        if norm.startswith(pre):
            norm = norm[len(pre):]
            break

    target = None
    for cls in CLASSES:
        bl = getattr(cls, "bl_idname", "")
        if bl == cid or bl.split(".")[-1] == "gen_" + norm:
            target = cls
            break
    if target is None:
        return Result(status="error", cartridge_id=cid, error="Cartridge '{:s}' not found.".format(cid))

    own_keys = set(getattr(target, "__annotations__", {}).keys())

    # The operator's *registered* properties live on the ops RNA type, not on the
    # class bl_rna (which only carries bl_* builtins before instantiation).
    op_name = target.bl_idname.split(".", 1)[-1]
    op = getattr(bpy.ops.massa, op_name, None)
    if op is None:
        return Result(status="error", cartridge_id=cid, error="Operator {:s} not accessible.".format(target.bl_idname))
    rna = op.get_rna_type()

    out: list[dict[str, Any]] = []
    for prop in rna.properties:
        ident = prop.identifier
        if _is_builtin_prop(ident) or prop.is_readonly:
            continue
        info: dict[str, Any] = {
            "identifier": ident,
            "type": prop.type,
            "description": getattr(prop, "description", "") or "",
            "cartridge_specific": ident in own_keys,
        }
        ptype = prop.type
        if ptype in {"FLOAT", "INT"}:
            arr = getattr(prop, "array_length", 0)
            info["array_length"] = arr
            try:
                info["default"] = [_fin(v) for v in prop.default_array] if arr and arr > 0 else _fin(prop.default)
            except Exception:
                info["default"] = None
            for attr in ("hard_min", "hard_max", "soft_min", "soft_max"):
                try:
                    info[attr] = _fin(getattr(prop, attr))
                except Exception:
                    pass
        elif ptype == "BOOLEAN":
            arr = getattr(prop, "array_length", 0)
            try:
                info["default"] = list(prop.default_array) if arr and arr > 0 else prop.default
            except Exception:
                info["default"] = None
        elif ptype == "ENUM":
            try:
                info["default"] = prop.default
            except Exception:
                info["default"] = None
            info["enum_items"] = [
                {"identifier": it.identifier, "name": it.name, "description": it.description}
                for it in prop.enum_items
            ]
        elif ptype == "STRING":
            try:
                info["default"] = prop.default
            except Exception:
                info["default"] = None
        out.append(info)

    return Result(
        status="ok",
        cartridge_id=cid,
        bl_idname=getattr(target, "bl_idname", None),
        parameters=out,
        cartridge_specific_params=[i["identifier"] for i in out if i["cartridge_specific"]],
    )
