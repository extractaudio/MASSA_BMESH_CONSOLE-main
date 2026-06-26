#!/usr/bin/env python
"""Run a cartridge across enum modes and print compact audit telemetry JSON."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


START = "---CART_MATRIX_START---"
END = "---CART_MATRIX_END---"


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        config = candidate / "massa" / "modules" / "debugging_system" / "config.py"
        if config.exists():
            return candidate
    raise SystemExit("Could not find repo root containing massa/modules/debugging_system/config.py")


def _load_blender_path(repo_root: Path) -> str:
    config_path = repo_root / "massa" / "modules" / "debugging_system" / "config.py"
    namespace: dict[str, object] = {}
    exec(config_path.read_text(encoding="utf-8"), namespace)
    blender_path = namespace.get("BLENDER_PATH")
    if not blender_path:
        raise SystemExit(f"BLENDER_PATH is not set in {config_path}")
    return str(blender_path)


def _parse_value(raw: str) -> object:
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _parse_sets(items: list[str]) -> dict[str, object]:
    values: dict[str, object] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--set expects name=value, got {item!r}")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"--set has an empty property name: {item!r}")
        values[key] = _parse_value(raw_value.strip())
    return values


def _write_harness(repo_root: Path, cartridge: Path, enum_prop: str, overrides: dict[str, object]) -> Path:
    payload = {
        "repo_root": str(repo_root),
        "cartridge": str(cartridge),
        "enum_prop": enum_prop,
        "overrides": overrides,
    }
    code = f"""
import json
import os
import re
import sys
import importlib.util

import bpy

payload = json.loads(r'''{json.dumps(payload)}''')
repo_root = payload["repo_root"]
runner_path = os.path.join(repo_root, "massa", "modules", "debugging_system", "runner.py")
spec = importlib.util.spec_from_file_location("massa_debug_runner", runner_path)
runner = importlib.util.module_from_spec(spec)
sys.modules["massa_debug_runner"] = runner
spec.loader.exec_module(runner)

bpy.ops.wm.read_factory_settings(use_empty=True)
runner.prepare_cartridge_env()

with open(payload["cartridge"], encoding="utf-8") as handle:
    code = handle.read()
code = re.sub(r'from\\s+\\.+\\s*operators\\.massa_base\\s+import\\s+Massa_OT_Base', '# [MOCKED] Massa_OT_Base', code)
code = re.sub(r'from\\s+\\.+\\s*(?:modules\\.)?massa_builder\\s+import\\s+MassaBuilder', '# [MOCKED] MassaBuilder', code)
code = re.sub(r'from\\s+\\.+\\s*(?:modules\\.)?massa_properties\\s+import\\s+MassaPropertiesMixin', '# [MOCKED] MassaPropertiesMixin', code)
exec(code, runner.__dict__)

op_class = runner._find_op_class()
if not op_class:
    raise RuntimeError("No MASSA_OT_* cartridge operator class found")

try:
    bpy.utils.register_class(op_class)
except ValueError:
    pass

enum_prop = payload["enum_prop"]
values = []
if enum_prop in op_class.bl_rna.properties:
    prop = op_class.bl_rna.properties[enum_prop]
    if prop.type != "ENUM":
        raise RuntimeError(f"Property {{enum_prop!r}} is {{prop.type}}, not ENUM")
    values = [item.identifier for item in prop.enum_items]
else:
    annotation = getattr(op_class, "__annotations__", {{}}).get(enum_prop)
    keywords = getattr(annotation, "keywords", None) or {{}}
    items = keywords.get("items", [])
    values = [item[0] for item in items if item]

if not values:
    raise RuntimeError(f"Enum property {{enum_prop!r}} not found on {{op_class.__name__}}")
results = []
for value in values:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    kwargs = dict(payload["overrides"])
    kwargs[enum_prop] = value
    case = {{"case": value, enum_prop: value, "overrides": payload["overrides"]}}
    try:
        category, opname = op_class.bl_idname.split(".", 1)
        getattr(getattr(bpy.ops, category), opname)(**kwargs)
        obj = runner.find_generated_object()
        telemetry = runner.gather_mesh_telemetry(obj)
        flags = runner.run_checks(obj)
        classified = runner.classify_flags(flags)
        case.update({{
            "status": "FAIL" if classified["summary"]["critical"] else "PASS",
            "summary": classified["summary"],
            "critical": classified["critical"],
            "warning": classified["warning"],
            "info": classified["info"],
            "dimensions": telemetry.get("dimensions"),
            "geometry": telemetry.get("geometry"),
            "uv": telemetry.get("uv"),
            "edge_slots": telemetry.get("edge_slots"),
            "materials": telemetry.get("materials"),
        }})
    except Exception as exc:
        case.update({{"status": "ERROR", "error": str(exc)}})
    results.append(case)

print("{START}")
print(json.dumps(results, sort_keys=True))
print("{END}")
"""
    handle = tempfile.NamedTemporaryFile("w", suffix="_cart_matrix.py", delete=False, encoding="utf-8")
    try:
        handle.write(textwrap.dedent(code))
        return Path(handle.name)
    finally:
        handle.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cartridge", help="Path to a cartridge .py file")
    parser.add_argument("--enum", required=True, dest="enum_prop", help="Enum property to iterate, e.g. shape_type")
    parser.add_argument("--set", action="append", default=[], dest="sets", help="Operator override as name=value")
    args = parser.parse_args()

    repo_root = _find_repo_root(Path.cwd().resolve())
    cartridge = Path(args.cartridge)
    if not cartridge.is_absolute():
        cartridge = repo_root / cartridge
    cartridge = cartridge.resolve()
    if not cartridge.exists():
        raise SystemExit(f"Cartridge not found: {cartridge}")
    if repo_root not in [cartridge, *cartridge.parents]:
        raise SystemExit(f"Refusing cartridge outside repo: {cartridge}")

    blender_path = _load_blender_path(repo_root)
    overrides = _parse_sets(args.sets)
    harness = _write_harness(repo_root, cartridge, args.enum_prop, overrides)

    try:
        cmd = [blender_path, "--background", "--factory-startup", "--python", str(harness)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if START not in output or END not in output:
            print(output, file=sys.stderr)
            return proc.returncode or 1
        matrix = output.split(START, 1)[1].split(END, 1)[0].strip()
        print(json.dumps(json.loads(matrix), indent=2, sort_keys=True))
        return proc.returncode
    finally:
        try:
            harness.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
