
import bpy
import os
import sys
import importlib
import importlib.abc
import importlib.util

# 1. Define Root Path (Inner 'MASSA_BMESH_CONSOLE-main' folder)
# File is in: ROOT/MCP/skills/generate_back_alley.py
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. Custom Finder to Alias the directory as 'massa_console' package
class AddonFinder(importlib.abc.MetaPathFinder):
    def __init__(self, path_map):
        self.path_map = path_map

    def find_spec(self, fullname, path, target=None):
        if fullname in self.path_map:
            root_path = self.path_map[fullname]
            return importlib.util.spec_from_file_location(
                fullname, 
                os.path.join(root_path, "__init__.py"),
                submodule_search_locations=[root_path]
            )
        return None

# Register Finder
sys.meta_path.insert(0, AddonFinder({"massa_console": root_dir}))

def build_layout():
    # 3. Import and Register Addon via alias
    try:
        # Ensure root_dir is in sys.path for standard import fallback
        if root_dir not in sys.path:
            sys.path.append(root_dir)
            
        if "massa_console" in sys.modules:
             # Reload if needed or just use
             pass
        else:
             import massa_console
             # Manually trigger register if not auto-run by __init__ (Blender addons usually don't auto-register on import)
             if hasattr(massa_console, "register"):
                 massa_console.register()
                 print("Registered 'massa_console' addon.")
    except Exception as e:
        print(f"Failed to register addon: {e}")
        return

    # 4. Clean Scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 5. Define Layout
    layout = [
        # Ground
        {
            "type": "PRIMITIVE", 
            "id": "plane", 
            "name": "Ground_Asphalt", 
            "transforms": {"scale": [5, 10, 1]},
            "parameters": {"size": 10}
        },
        # Buildings
        {
            "type": "PRIMITIVE",
            "id": "cube",
            "name": "Building_Left",
            "transforms": {"location": [-6, 0, 5], "scale": [1, 10, 5]}
        },
        {
            "type": "PRIMITIVE",
            "id": "cube",
            "name": "Building_Right",
            "transforms": {"location": [6, 0, 5], "scale": [1, 10, 5]}
        },
        # Door
        {
            "type": "CARTRIDGE",
            "id": "prim_con_doorway",
            "name": "Door_Back_Entry",
            "transforms": {"location": [-5, -2, 0], "rotation": [0, 0, 90]},
            "parameters": {"standard_type": "STD_EXT", "use_trim": True}
        },
        # Pipes
        {
            "type": "CARTRIDGE",
            "id": "prim_02_pipe",
            "name": "Pipe_Main_Gas",
            "transforms": {"location": [-4.8, 2, 3], "rotation": [0, 0, 0]},
            "parameters": {"length": 6.0, "radius": 0.15, "shape_mode": "STRAIGHT"}
        },
        {
            "type": "CARTRIDGE",
            "id": "prim_02_pipe",
            "name": "Pipe_Elbow_Top",
            "transforms": {"location": [-4.8, 2, 9], "rotation": [90, 0, 0]},
            "parameters": {"shape_mode": "ELBOW", "radius": 0.15}
        },
        # Crates
        {
            "type": "CARTRIDGE",
            "id": "cart_crate",
            "name": "Crate_Ammo_01",
            "transforms": {"location": [-3, -4, 0.5], "rotation": [0, 0, 15]},
            "parameters": {"width": 1.0, "height": 1.0, "depth": 1.0}
        },
        {
            "type": "CARTRIDGE",
            "id": "cart_crate",
            "name": "Crate_Supply_02",
            "transforms": {"location": [-3.5, -3.2, 0.5], "rotation": [0, 0, -5]},
            "parameters": {"width": 0.8, "height": 0.8, "depth": 0.8}
        }
    ]

    # 6. Generator Loop
    for item in layout:
        try:
            obj_type = item.get('type', 'PRIMITIVE')
            item_id = item.get('id')
            name = item.get('name', f"New_{item_id}")
            p_cre = item.get('parameters', {})
            trans = item.get('transforms', {})
            
            obj = None
            
            if obj_type == 'CARTRIDGE':
                # Op Name: massa.gen_{id}
                op_name = f"gen_{item_id}"
                if hasattr(bpy.ops.massa, op_name):
                    print(f"Generating {name} via massa.{op_name}...")
                    func = getattr(bpy.ops.massa, op_name)
                    func('EXEC_DEFAULT', **p_cre)
                    obj = bpy.context.active_object
                else:
                    print(f"Error: Operator massa.{op_name} not found.")

            elif obj_type == 'PRIMITIVE':
                if item_id == 'cube':
                     bpy.ops.mesh.primitive_cube_add(size=1)
                elif item_id == 'plane':
                     bpy.ops.mesh.primitive_plane_add(size=2)
                obj = bpy.context.active_object

            # Transforms
            if obj:
                obj.name = name
                if 'location' in trans:
                    obj.location = trans['location']
                if 'rotation' in trans:
                    import math
                    deg = trans['rotation']
                    obj.rotation_euler = (math.radians(deg[0]), math.radians(deg[1]), math.radians(deg[2]))
                if 'scale' in trans:
                    obj.scale = trans['scale']
                    
        except Exception as e:
            print(f"Failed to create {item.get('name')}: {e}")

    # 7. Organization (Simple)
    for obj in bpy.context.scene.objects:
        try:
            col_name = "Misc"
            if obj.type == 'MESH': col_name = "Geometry"
            elif obj.type == 'LIGHT': col_name = "Lights"
            
            if "Ground" in obj.name: col_name = "Environment"
            if "Building" in obj.name: col_name = "Buildings"
            
            if col_name not in bpy.data.collections:
                c = bpy.data.collections.new(col_name)
                bpy.context.scene.collection.children.link(c)
                
            col = bpy.data.collections[col_name]
            if col.name not in [x.name for x in obj.users_collection]:
                col.objects.link(obj)
                for old in obj.users_collection:
                    if old.name != col_name:
                        old.objects.unlink(obj)
        except:
            pass

    # 8. Save
    out_path = os.path.join(root_dir, "Back_Alley_Scene.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
    print(f"Success! Scene saved to {out_path}")

if __name__ == "__main__":
    build_layout()
