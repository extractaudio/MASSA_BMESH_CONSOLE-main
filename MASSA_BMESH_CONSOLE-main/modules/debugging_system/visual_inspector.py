import bpy
import sys
import os
import importlib
import math
import json
from mathutils import Vector, Euler

# Ensure we can import the package
repo_root = os.getcwd()
pkg_env = os.path.join(repo_root, "_pkg_env")
if pkg_env not in sys.path:
    sys.path.append(pkg_env)

def setup_scene():
    # Clear existing objects
    bpy.ops.wm.read_homefile(use_empty=True)

    # Create Camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Create Sun Light
    light_data = bpy.data.lights.new("Sun", type='SUN')
    light_obj = bpy.data.objects.new("Sun", light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.rotation_euler = (math.radians(45), math.radians(45), 0)

def set_camera_view(view_type, target_obj):
    cam = bpy.context.scene.camera

    # Calculate bounding box center and size
    bbox = [target_obj.matrix_world @ Vector(corner) for corner in target_obj.bound_box]
    center = sum(bbox, Vector()) / 8.0
    size = max((v - center).length for v in bbox) * 2.5

    if view_type == 'ISO':
        cam.location = center + Vector((size, -size, size))
        # Look at center
        direction = center - cam.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam.rotation_euler = rot_quat.to_euler()

    elif view_type == 'TOP':
        cam.location = center + Vector((0, 0, size))
        cam.rotation_euler = (0, 0, 0)

    elif view_type == 'FRONT':
        cam.location = center + Vector((0, -size, 0))
        cam.rotation_euler = (math.radians(90), 0, 0)

    elif view_type == 'SIDE':
        cam.location = center + Vector((size, 0, 0))
        cam.rotation_euler = (math.radians(90), 0, math.radians(90))

def run_inspection(cartridge_module_name, output_dir):
    try:
        # 1. Import Module
        print(f"Importing {cartridge_module_name}...")
        mod = importlib.import_module(cartridge_module_name)

        # 2. Find Operator Class
        op_class = None
        for name, obj in mod.__dict__.items():
            if isinstance(obj, type) and name.startswith("MASSA_OT_") and "Massa_OT_Base" in [b.__name__ for b in obj.__bases__]:
                op_class = obj
                break

        if not op_class:
            print(f"Error: No MASSA_OT class found in {cartridge_module_name}")
            return

        # 3. Register Classes (Base first)
        # We need Massa_OT_Base. It is imported in the cartridge module.
        base_class = getattr(mod, "Massa_OT_Base", None)
        if base_class:
            try:
                bpy.utils.register_class(base_class)
            except ValueError:
                pass # Already registered

        try:
            bpy.utils.register_class(op_class)
        except ValueError:
            pass

        # 4. Execute Operator
        setup_scene()

        idname = op_class.bl_idname # e.g. "massa.gen_arc_02_stairs"
        op_func_name = idname.split(".")[-1] # gen_arc_02_stairs

        print(f"Executing {idname}...")

        # We need to construct a context override or just call it if it doesn't poll for VIEW_3D
        # Massa_OT_Base doesn't have a poll method, so it should run.
        # But we need to call it via bpy.ops.massa...

        op_call = getattr(bpy.ops.massa, op_func_name)
        op_call()

        # 5. Find Generated Object
        obj = bpy.context.active_object
        if not obj:
            # Try to find by name "Massa_Obj" or similar
            for o in bpy.data.objects:
                if "Massa" in o.name:
                    obj = o
                    break

        if not obj:
            print("Error: No object generated.")
            return

        print(f"Generated Object: {obj.name}")

        # 6. Generate Stats
        stats = {
            "verts": len(obj.data.vertices),
            "edges": len(obj.data.edges),
            "faces": len(obj.data.polygons),
            "dimensions": [d for d in obj.dimensions],
            "slots": {}
        }

        # Analyze Material Slots
        for i, slot in enumerate(obj.material_slots):
            stats["slots"][i] = slot.name

        # Check UV Layers
        stats["uv_layers"] = [l.name for l in obj.data.uv_layers]

        # 7. Render Views
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.resolution_y = 512
        bpy.context.scene.render.filepath = os.path.join(output_dir, "render_")

        for view in ['ISO', 'TOP', 'FRONT', 'SIDE']:
            set_camera_view(view, obj)
            bpy.context.scene.render.filepath = os.path.join(output_dir, f"{view}.png")
            # Use software render engine if possible, or simple workbench
            bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
            bpy.context.scene.display.shading.light = 'MATCAP'
            bpy.context.scene.display.shading.color_type = 'OBJECT'

            try:
                # Redirect output to null to avoid clutter
                # open(os.devnull, 'w')
                bpy.ops.render.render(write_still=True)
            except Exception as e:
                print(f"Render Error ({view}): {e}")

        # Save Stats
        with open(os.path.join(output_dir, "stats.json"), 'w') as f:
            json.dump(stats, f, indent=4)

        print("Inspection Complete.")

    except Exception as e:
        print(f"Inspection Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Parse args: blender -b -P visual_inspector.py -- <module_name> <output_dir>
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        if len(args) >= 2:
            run_inspection(args[0], args[1])
        else:
            print("Usage: blender -b -P visual_inspector.py -- <module_name> <output_dir>")
    else:
        print("Usage: blender -b -P visual_inspector.py -- <module_name> <output_dir>")
