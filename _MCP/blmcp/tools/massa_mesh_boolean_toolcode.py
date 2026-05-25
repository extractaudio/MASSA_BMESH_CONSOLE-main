# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple


class Params(NamedTuple):
    target_object: str
    cutter_objects: list[str]
    operation: str
    solver: str
    inset_thickness: float
    inset_outset: bool
    force_native: bool


class Result(NamedTuple):
    status: str
    used_hardops: bool
    target: str
    operation: str
    cutter_modifiers_added: list[str]
    boolshapes_created: list[str]
    solver: str
    warnings: list[str]
    error: str | None = None


def main(params: Params) -> Result:
    import bpy

    VALID_NATIVE = {"DIFFERENCE", "UNION", "INTERSECT"}
    HOPS_OPS = {
        "DIFFERENCE": ("bool_difference", {}),
        "UNION": ("bool_union", {}),
        "INTERSECT": ("bool_intersect", {}),
        "SLASH": ("slash", {}),
        "INSET": ("bool_inset", {
            "thickness": params.inset_thickness,
            "outset": params.inset_outset,
            "inset_slice": False,
        }),
        "KNIFE": ("bool_knife", {}),
    }

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
            return {}
        return {name: getattr(obj, name) for name in names if hasattr(obj, name)}

    def restore_attrs(obj, values):
        if obj is None:
            return
        for name, value in values.items():
            try:
                setattr(obj, name, value)
            except Exception:
                pass

    def modifier_names(obj):
        return {modifier.name for modifier in obj.modifiers}

    try:
        operation = str(params.operation).upper()
        solver = str(params.solver).upper()
        if operation not in HOPS_OPS:
            raise ValueError("Unsupported operation: " + operation)
        if solver not in {"FAST", "EXACT"}:
            raise ValueError("Unsupported solver: " + solver)
        if not params.cutter_objects:
            raise ValueError("At least one cutter object is required.")

        set_object_mode()
        target = resolve_mesh(str(params.target_object), "Target")
        cutters = [resolve_mesh(str(name), "Cutter") for name in params.cutter_objects]
        select_for_boolean(target, cutters)

        before_modifiers = modifier_names(target)
        before_objects = set(bpy.data.objects.keys())
        warnings = []

        use_hardops = hops_available() and not bool(params.force_native)
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
            elif params.force_native:
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

        return Result(
            status="ok",
            used_hardops=use_hardops,
            target=target.name,
            operation=operation,
            cutter_modifiers_added=new_modifiers,
            boolshapes_created=sorted(boolshapes),
            solver=solver,
            warnings=warnings,
        )
    except Exception as exc:
        return Result(
            status="error",
            used_hardops=False,
            target=params.target_object,
            operation=params.operation,
            cutter_modifiers_added=[],
            boolshapes_created=[],
            solver=params.solver,
            warnings=[],
            error=str(exc),
        )
