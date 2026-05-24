# Massa MCP -- deterministic mesh operations with optional HardOps support.

from __future__ import annotations

from typing import Literal

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

BooleanOperation = Literal["DIFFERENCE", "UNION", "INTERSECT", "SLASH", "INSET", "KNIFE"]
BooleanSolver = Literal["FAST", "EXACT"]
CleanMode = Literal["ACTIVE", "SELECTED", "VISIBLE"]


def _payload_code(payload: dict[str, object]) -> str:
    return repr(payload)


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Massa Mesh Boolean", destructiveHint=True))
    def mesh_boolean(
        target_object: str,
        cutter_objects: list[str],
        operation: BooleanOperation,
        solver: BooleanSolver = "EXACT",
        inset_thickness: float = 0.5,
        inset_outset: bool = False,
        force_native: bool = False,
    ) -> dict[str, object]:
        """
        Add a boolean-style operation to a target mesh.

        Uses HardOps object-mode operators when they are registered in the live
        Blender instance, then falls back to native Boolean modifiers for
        DIFFERENCE/UNION/INTERSECT.
        """
        payload = {
            "target_object": target_object,
            "cutter_objects": cutter_objects,
            "operation": operation,
            "solver": solver,
            "inset_thickness": float(inset_thickness),
            "inset_outset": bool(inset_outset),
            "force_native": bool(force_native),
        }
        code = f"""
import bpy

p = {_payload_code(payload)}

VALID_NATIVE = {{"DIFFERENCE", "UNION", "INTERSECT"}}
HOPS_OPS = {{
    "DIFFERENCE": ("bool_difference", {{}}),
    "UNION": ("bool_union", {{}}),
    "INTERSECT": ("bool_intersect", {{}}),
    "SLASH": ("slash", {{}}),
    "INSET": ("bool_inset", {{
        "thickness": p["inset_thickness"],
        "outset": p["inset_outset"],
        "inset_slice": False,
    }}),
    "KNIFE": ("bool_knife", {{}}),
}}


def hops_available():
    return hasattr(bpy.ops, "hops") and hasattr(bpy.ops.hops, "slash")


def set_object_mode():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def resolve_mesh(name, role):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(role + " object '" + name + "' was not found.")
    if obj.type != "MESH":
        raise ValueError(role + " object '" + obj.name + "' is type " + obj.type + ", expected MESH.")
    return obj


def select_for_boolean(target, cutters):
    bpy.ops.object.select_all(action="DESELECT")
    for cutter in cutters:
        cutter.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target


def call_operator(op, kwargs):
    try:
        return op("EXEC_DEFAULT", **kwargs)
    except TypeError:
        return op(**kwargs)


def hops_property():
    try:
        from HOps.utility import addon  # type: ignore
        pref = addon.preference()
        prop = getattr(pref, "property", None)
        if prop is not None:
            return prop
    except Exception:
        pass

    for key, entry in bpy.context.preferences.addons.items():
        if "hops" not in key.lower() and "hard" not in key.lower():
            continue
        prop = getattr(getattr(entry, "preferences", None), "property", None)
        if prop is not None:
            return prop
    return None


def snapshot_attrs(obj, names):
    if obj is None:
        return {{}}
    return {{name: getattr(obj, name) for name in names if hasattr(obj, name)}}


def restore_attrs(obj, values):
    if obj is None:
        return
    for name, value in values.items():
        try:
            setattr(obj, name, value)
        except Exception:
            pass


def modifier_names(obj):
    return {{modifier.name for modifier in obj.modifiers}}


try:
    operation = str(p["operation"]).upper()
    solver = str(p["solver"]).upper()
    if operation not in HOPS_OPS:
        raise ValueError("Unsupported operation: " + operation)
    if solver not in {{"FAST", "EXACT"}}:
        raise ValueError("Unsupported solver: " + solver)
    if not p["cutter_objects"]:
        raise ValueError("At least one cutter object is required.")

    set_object_mode()
    target = resolve_mesh(str(p["target_object"]), "Target")
    cutters = [resolve_mesh(str(name), "Cutter") for name in p["cutter_objects"]]
    select_for_boolean(target, cutters)

    before_modifiers = modifier_names(target)
    before_objects = set(bpy.data.objects.keys())
    warnings = []

    use_hardops = hops_available() and not bool(p["force_native"])
    if use_hardops:
        prop = hops_property()
        snap = snapshot_attrs(prop, ("boolean_solver",))
        try:
            if prop is not None and hasattr(prop, "boolean_solver"):
                prop.boolean_solver = solver
            op_name, op_kwargs = HOPS_OPS[operation]
            op = getattr(bpy.ops.hops, op_name)
            call_operator(op, op_kwargs)
        finally:
            restore_attrs(prop, snap)
    else:
        if not hops_available():
            warnings.append("HardOps is not registered in the running Blender instance; used native fallback.")
        elif p["force_native"]:
            warnings.append("force_native=True; skipped HardOps.")
        if operation not in VALID_NATIVE:
            raise ValueError("Native fallback only supports DIFFERENCE, UNION, and INTERSECT.")
        for cutter in cutters:
            mod = target.modifiers.new(name="MASSA_" + operation + "_" + cutter.name, type="BOOLEAN")
            mod.operation = operation
            mod.object = cutter
            if hasattr(mod, "solver"):
                mod.solver = solver

    after_modifiers = modifier_names(target)
    new_modifiers = sorted(after_modifiers - before_modifiers)
    new_objects = sorted(set(bpy.data.objects.keys()) - before_objects)
    boolshapes = set(new_objects)
    for cutter in cutters:
        if cutter.name in bpy.data.objects and (
            cutter.parent is target or cutter.hide_viewport or cutter.hide_get()
        ):
            boolshapes.add(cutter.name)

    result = {{
        "status": "ok",
        "used_hardops": use_hardops,
        "target": target.name,
        "operation": operation,
        "cutter_modifiers_added": new_modifiers,
        "boolshapes_created": sorted(boolshapes),
        "solver": solver,
        "warnings": warnings,
    }}
except Exception as exc:
    result = {{
        "status": "error",
        "used_hardops": False,
        "target": p.get("target_object", ""),
        "operation": p.get("operation", ""),
        "cutter_modifiers_added": [],
        "boolshapes_created": [],
        "solver": p.get("solver", ""),
        "error": str(exc),
    }}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Massa Mesh Clean", destructiveHint=True))
    def mesh_clean(
        object_names: list[str],
        mode: CleanMode = "SELECTED",
        merge_threshold: float = 0.0001,
        dissolve_angle_deg: float = 5.0,
        degenerate_iterations: int = 1,
        delete_interior: bool = False,
        force_native: bool = False,
    ) -> dict[str, object]:
        """
        Clean mesh topology on one or more objects.

        Uses HardOps clean_mesh when available and otherwise runs a native edit
        mode cleanup pass with merge-by-distance, limited dissolve, optional
        degenerate dissolve, and optional interior face deletion.
        """
        payload = {
            "object_names": object_names,
            "mode": mode,
            "merge_threshold": float(merge_threshold),
            "dissolve_angle_deg": float(dissolve_angle_deg),
            "degenerate_iterations": int(degenerate_iterations),
            "delete_interior": bool(delete_interior),
            "force_native": bool(force_native),
        }
        code = f"""
import bpy
import math

p = {_payload_code(payload)}


def hops_clean_available():
    return hasattr(bpy.ops, "view3d") and hasattr(bpy.ops.view3d, "clean_mesh")


def set_object_mode():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def resolve_meshes(names, mode):
    if names:
        meshes = []
        for name in names:
            obj = bpy.data.objects.get(name)
            if obj is None:
                raise ValueError("Object '" + str(name) + "' was not found.")
            if obj.type != "MESH":
                raise ValueError("Object '" + obj.name + "' is type " + obj.type + ", expected MESH.")
            meshes.append(obj)
        return meshes
    if mode == "ACTIVE" and bpy.context.active_object is not None:
        return [bpy.context.active_object]
    if mode == "VISIBLE":
        return [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.visible_get()]
    return [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]


def select_objects(meshes, mode):
    bpy.ops.object.select_all(action="DESELECT")
    selected = meshes if mode != "ACTIVE" else meshes[:1]
    for obj in selected:
        obj.select_set(True)
    if meshes:
        bpy.context.view_layer.objects.active = meshes[0]


def hops_property():
    try:
        from HOps.utility import addon  # type: ignore
        pref = addon.preference()
        prop = getattr(pref, "property", None)
        if prop is not None:
            return prop
    except Exception:
        pass

    for key, entry in bpy.context.preferences.addons.items():
        if "hops" not in key.lower() and "hard" not in key.lower():
            continue
        prop = getattr(getattr(entry, "preferences", None), "property", None)
        if prop is not None:
            return prop
    return None


def snapshot_attrs(obj, names):
    if obj is None:
        return {{}}
    return {{name: getattr(obj, name) for name in names if hasattr(obj, name)}}


def restore_attrs(obj, values):
    if obj is None:
        return
    for name, value in values.items():
        try:
            setattr(obj, name, value)
        except Exception:
            pass


def mesh_counts(obj):
    return len(obj.data.vertices), len(obj.data.polygons)


def stats_from(before, meshes):
    stats = []
    for obj in meshes:
        verts_after, faces_after = mesh_counts(obj)
        verts_before, faces_before = before.get(obj.name, (verts_after, faces_after))
        stats.append({{
            "object": obj.name,
            "verts_before": verts_before,
            "verts_after": verts_after,
            "verts_removed": max(0, verts_before - verts_after),
            "faces_before": faces_before,
            "faces_after": faces_after,
            "faces_removed": max(0, faces_before - faces_after),
        }})
    return stats


def native_clean_object(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    if hasattr(bpy.ops.mesh, "merge_by_distance"):
        bpy.ops.mesh.merge_by_distance(distance=float(p["merge_threshold"]))
    else:
        bpy.ops.mesh.remove_doubles(threshold=float(p["merge_threshold"]))
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(float(p["dissolve_angle_deg"])))
    except Exception:
        pass
    for _idx in range(max(0, int(p["degenerate_iterations"]))):
        bpy.ops.mesh.select_all(action="SELECT")
        try:
            bpy.ops.mesh.dissolve_degenerate(threshold=float(p["merge_threshold"]))
        except Exception:
            break
    if bool(p["delete_interior"]):
        try:
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_interior_faces()
            bpy.ops.mesh.delete(type="FACE")
        except Exception:
            pass
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.update()


try:
    mode = str(p["mode"]).upper()
    if mode not in {{"ACTIVE", "SELECTED", "VISIBLE"}}:
        raise ValueError("Unsupported clean mode: " + mode)
    set_object_mode()
    meshes = resolve_meshes(list(p["object_names"]), mode)
    if not meshes:
        raise ValueError("No mesh objects were supplied or selected.")

    before = {{obj.name: mesh_counts(obj) for obj in meshes}}
    warnings = []
    use_hardops = hops_clean_available() and not bool(p["force_native"])

    if use_hardops:
        select_objects(meshes, mode)
        prop = hops_property()
        attr_names = (
            "meshclean_mode",
            "meshclean_dissolve_angle",
            "meshclean_remove_threshold",
            "meshclean_degenerate_iter",
            "meshclean_delete_interior",
        )
        snap = snapshot_attrs(prop, attr_names)
        try:
            if prop is not None:
                if hasattr(prop, "meshclean_mode"):
                    prop.meshclean_mode = mode
                if hasattr(prop, "meshclean_dissolve_angle"):
                    prop.meshclean_dissolve_angle = math.radians(float(p["dissolve_angle_deg"]))
                if hasattr(prop, "meshclean_remove_threshold"):
                    prop.meshclean_remove_threshold = float(p["merge_threshold"])
                if hasattr(prop, "meshclean_degenerate_iter"):
                    prop.meshclean_degenerate_iter = int(p["degenerate_iterations"])
                if hasattr(prop, "meshclean_delete_interior"):
                    prop.meshclean_delete_interior = bool(p["delete_interior"])
            try:
                bpy.ops.view3d.clean_mesh("EXEC_DEFAULT")
            except TypeError:
                bpy.ops.view3d.clean_mesh()
        finally:
            restore_attrs(prop, snap)
            set_object_mode()
    else:
        if not hops_clean_available():
            warnings.append("HardOps clean_mesh is not registered; used native fallback.")
        elif p["force_native"]:
            warnings.append("force_native=True; skipped HardOps clean_mesh.")
        for obj in meshes:
            native_clean_object(obj)
        set_object_mode()

    result = {{
        "status": "ok",
        "used_hardops": use_hardops,
        "mode": mode,
        "objects": stats_from(before, meshes),
        "warnings": warnings,
    }}
except Exception as exc:
    try:
        set_object_mode()
    except Exception:
        pass
    result = {{
        "status": "error",
        "used_hardops": False,
        "mode": p.get("mode", ""),
        "objects": [],
        "warnings": [],
        "error": str(exc),
    }}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Massa Apply Modifiers", destructiveHint=True))
    def apply_modifiers(
        object_name: str,
        modifier_names: list[str] | str = "ALL",
        keep_last_bevel_weighted_normal: bool = False,
        preserve_shape_keys: bool = False,
    ) -> dict[str, object]:
        """
        Apply modifiers on one object using native Blender operations.

        HardOps Smart Apply is event-driven, so this tool intentionally uses a
        deterministic native implementation. Set keep_last_bevel_weighted_normal
        to leave the final Bevel and Weighted Normal modifiers unapplied.
        """
        payload = {
            "object_name": object_name,
            "modifier_names": modifier_names,
            "keep_last_bevel_weighted_normal": bool(keep_last_bevel_weighted_normal),
            "preserve_shape_keys": bool(preserve_shape_keys),
        }
        code = f"""
import bpy

p = {_payload_code(payload)}


def set_object_mode():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


try:
    set_object_mode()
    obj = bpy.data.objects.get(str(p["object_name"]))
    if obj is None:
        raise ValueError("Object '" + str(p["object_name"]) + "' was not found.")
    if obj.type != "MESH":
        raise ValueError("Object '" + obj.name + "' is type " + obj.type + ", expected MESH.")

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    requested = p["modifier_names"]
    if isinstance(requested, str):
        if requested != "ALL":
            requested_names = {{requested}}
        else:
            requested_names = {{modifier.name for modifier in obj.modifiers}}
    else:
        requested_names = {{str(name) for name in requested}}

    applied = []
    skipped = []
    kept = []
    warnings = []
    existing_names = {{modifier.name for modifier in obj.modifiers}}
    for name in sorted(requested_names - existing_names):
        skipped.append({{"name": name, "reason": "modifier not found"}})

    keep_names = set()
    if bool(p["keep_last_bevel_weighted_normal"]):
        for wanted_type in ("BEVEL", "WEIGHTED_NORMAL"):
            matches = [modifier.name for modifier in obj.modifiers if modifier.type == wanted_type]
            if matches:
                keep_names.add(matches[-1])

    has_shape_keys = bool(getattr(obj.data, "shape_keys", None))
    if bool(p["preserve_shape_keys"]) and has_shape_keys:
        warnings.append(
            "preserve_shape_keys=True requested, but Blender modifier_apply is not deterministic with shape keys; requested modifiers were skipped."
        )
        for modifier in obj.modifiers:
            if modifier.name in requested_names:
                skipped.append({{"name": modifier.name, "reason": "shape key preservation requested"}})
    else:
        if has_shape_keys:
            warnings.append("Object has shape keys; Blender may reject applying some modifiers.")
        for modifier_name in [modifier.name for modifier in obj.modifiers]:
            if modifier_name not in requested_names:
                continue
            if modifier_name in keep_names:
                kept.append(modifier_name)
                continue
            try:
                bpy.ops.object.modifier_apply(modifier=modifier_name)
                applied.append(modifier_name)
            except Exception as exc:
                skipped.append({{"name": modifier_name, "reason": str(exc)}})

    result = {{
        "status": "ok",
        "object": obj.name,
        "applied": applied,
        "skipped": skipped,
        "kept": kept,
        "warnings": warnings,
    }}
except Exception as exc:
    result = {{
        "status": "error",
        "object": p.get("object_name", ""),
        "applied": [],
        "skipped": [],
        "kept": [],
        "warnings": [],
        "error": str(exc),
    }}
"""
        return send_code(code, strict_json=True)

    @mcp.tool(annotations=ToolAnnotations(title="Massa Apply Transform", destructiveHint=True))
    def apply_transform(
        object_name: str,
        location: bool = False,
        rotation: bool = True,
        scale: bool = True,
    ) -> dict[str, object]:
        """Apply object transforms using native Blender transform_apply."""
        payload = {
            "object_name": object_name,
            "location": bool(location),
            "rotation": bool(rotation),
            "scale": bool(scale),
        }
        code = f"""
import bpy

p = {_payload_code(payload)}


def set_object_mode():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


try:
    set_object_mode()
    obj = bpy.data.objects.get(str(p["object_name"]))
    if obj is None:
        raise ValueError("Object '" + str(p["object_name"]) + "' was not found.")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(
        location=bool(p["location"]),
        rotation=bool(p["rotation"]),
        scale=bool(p["scale"]),
    )
    result = {{
        "status": "ok",
        "object": obj.name,
        "applied": {{
            "location": bool(p["location"]),
            "rotation": bool(p["rotation"]),
            "scale": bool(p["scale"]),
        }},
    }}
except Exception as exc:
    result = {{
        "status": "error",
        "object": p.get("object_name", ""),
        "applied": {{}},
        "error": str(exc),
    }}
"""
        return send_code(code, strict_json=True)
