import bpy
import sys
import os
import argparse
import json
import importlib

# 1. Setup Path to import your attached 'auditors' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 2. Import your attached files
# NOTE: Ensure your attached files are in the 'auditors' folder
try:
    import auditors
    # If you need specific submodules, import them here:
    # from auditors import my_topology_check, my_uv_check
except ImportError:
    pass 

def run_checks(obj):
    errors = []
    
    # --- DYNAMICALLY RUN ATTACHED AUDITORS ---
    if 'auditors' in sys.modules:
        import auditors
        try:
            errors.extend(auditors.run_all_auditors(obj))
        except Exception as e:
            errors.append(f"Auditor Loader Failed: {str(e)}")

    
    # --- CONNECT YOUR ATTACHED SCRIPTS HERE ---
    # Assuming your attached scripts have a function like `audit_mesh(obj)`
    # Example:
    # errors.extend(auditors.my_topology_check.audit_mesh(obj))
    
    # [FALLBACK LOGIC]: If attached files aren't linked, we run a basic check
    # to ensure the system works out of the box.
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    
    # Check A: Zero Faces
    zero_faces = [f.index for f in bm.faces if f.calc_area() < 0.000001]
    if zero_faces:
        errors.append(f"Found {len(zero_faces)} Zero-Area Faces. Indices: {zero_faces[:5]}...")

    # Check B: Pinched UVs
    uv_layer = bm.loops.layers.uv.verify()
    pinched = []
    for f in bm.faces:
        uvs = [l[uv_layer].uv for l in f.loops]
        # Shoelace formula for UV area
        area = 0.5 * abs(sum(x0*y1 - x1*y0 for ((x0, y0), (x1, y1)) in zip(uvs, uvs[1:] + [uvs[0]])))
        if area < 0.000001 and f.calc_area() > 0.000001:
            pinched.append(f.index)
    if pinched:
        errors.append(f"Found {len(pinched)} Pinched UV Faces.")

    bm.free()
    return errors

def main():
    # Parse Args
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--cartridge", required=True)
    args, _ = parser.parse_known_args(argv)

    # Clean Scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Execute Agent's Cartridge
    try:
        with open(args.cartridge) as f:
            exec(f.read(), globals())
    except Exception as e:
        print("---AUDIT_START---")
        print(json.dumps({"status": "FAIL", "errors": [f"Syntax/Runtime Error: {str(e)}"]}))
        print("---AUDIT_END---")
        return

    # Find Mesh
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        if meshes: obj = meshes[0]

    if not obj:
        print("---AUDIT_START---")
        print(json.dumps({"status": "FAIL", "errors": ["No Mesh Created by Cartridge"]}))
        print("---AUDIT_END---")
        return

    # Run Audit
    error_list = run_checks(obj)
    
    result = {
        "status": "PASS" if not error_list else "FAIL",
        "object": obj.name,
        "errors": error_list
    }

    print("---AUDIT_START---")
    print(json.dumps(result))
    print("---AUDIT_END---")

if __name__ == "__main__":
    main()