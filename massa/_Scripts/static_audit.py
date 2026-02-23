
import os
import re

FILES_TO_AUDIT = [
    "cart_prim_11_helix.py",
    "cart_prim_12_truss.py",
    "cart_prim_13_shard.py",
    "cart_prim_14_y_joint.py",
    "cart_prim_15_scale.py",
    "cart_prim_16_lathe.py",
    "cart_prim_17_canvas.py",
    "cart_prim_18_tank.py",
    "cart_prim_19_tray.py",
    "cart_prim_20_bundle.py",
    "cart_prim_21_column.py",
    "cart_prim_22_duct.py",
    "cart_prim_23_cable_tray.py",
    "cart_prim_24_gutter.py"
]

BASE_PATH = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\MASSA_BMESH_CONSOLE-main\modules\cartridges"

def audit_file(filename):
    filepath = os.path.join(BASE_PATH, filename)
    if not os.path.exists(filepath):
        return f"MISSING: {filename}"

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    errors = []

    # 1. Check Class Def
    if not re.search(r"class MASSA_OT_.*\(Massa_OT_Base\):", content):
        errors.append("Missing 'MASSA_OT_... (Massa_OT_Base)' class definition.")

    # 2. Check build_shape
    if "def build_shape(self, bm" not in content and "def build_shape(self," not in content:
        errors.append("Missing 'def build_shape(self, ...)' method.")

    # 3. Check for forbidden bpy.ops inside build_shape (heuristic)
    # We look for bpy.ops.* appearing after define build_shape
    parts = content.split("def build_shape")
    if len(parts) > 1:
        body = parts[1]
        # stop at next def or class
        body = re.split(r"\n\s*(def|class) ", body)[0]
        
        matches = re.findall(r"bpy\.ops\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+", body)
        # Filter allowed ops if any (none usually allowed in build_shape for cartridges)
        if matches:
            errors.append(f"Forbidden bpy.ops calls in build_shape: {matches}")

    # 4. Check CARTRIDGE_META
    if "CARTRIDGE_META = {" not in content:
        errors.append("Missing CARTRIDGE_META dict.")

    # 5. Check imports
    if "import bmesh" not in content:
        errors.append("Missing 'import bmesh'.")

    if not errors:
        return "PASS"
    else:
        return "FAIL: " + "; ".join(errors)

print(f"{'CARTRIDGE':<35} | {'STATUS'}")
print("-" * 50)
for f in FILES_TO_AUDIT:
    result = audit_file(f)
    print(f"{f:<35} | {result}")
