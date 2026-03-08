import bpy
import sys
import os
import argparse
import json
import importlib
import time
import math
import base64
import io
import contextlib
import bmesh
import re

# 1. Setup Path to import your attached 'auditors' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(current_dir)) # Up 2 levels: modules/debugging_system -> modules -> root
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Add parent of repo to sys.path so we can import 'massa' as a package
parent_of_repo = os.path.dirname(repo_root)
if parent_of_repo not in sys.path:
    sys.path.append(parent_of_repo)

def is_path_safe(filepath, base_dir=repo_root):
    """
    Validates that the given filepath is within the base_dir to prevent path traversal.
    """
    abs_filepath = os.path.abspath(filepath)
    abs_base_dir = os.path.abspath(base_dir)
    return os.path.commonpath([abs_filepath, abs_base_dir]) == abs_base_dir

# 2. Import your attached files
# NOTE: Ensure your attached files are in the 'auditors' folder
try:
    from . import auditors
except ImportError:
    try:
        import auditors
    except ImportError:
        pass

def prepare_cartridge_env():
    # Import required modules
    try:
        # Import using full package path 'massa.x.y' to support relative imports inside them
        import massa.operators.massa_base as massa_base_mod
        import massa.modules.massa_builder as massa_builder_mod
        import massa.modules.massa_properties as massa_props_mod

        globals()['Massa_OT_Base'] = massa_base_mod.Massa_OT_Base
        globals()['MassaBuilder'] = massa_builder_mod.MassaBuilder
        globals()['MassaPropertiesMixin'] = massa_props_mod.MassaPropertiesMixin
        return True
    except ImportError as e:
        print(f"Failed to import dependencies: {e}")
        return False

def run_checks(obj):
    errors = []
    
    # --- DYNAMICALLY RUN ATTACHED AUDITORS ---
    # Try to find auditors module
    auditors_mod = None
    if 'auditors' in sys.modules:
        auditors_mod = sys.modules['auditors']
    elif 'massa.modules.debugging_system.auditors' in sys.modules:
        auditors_mod = sys.modules['massa.modules.debugging_system.auditors']
    elif 'auditors' in globals():
        auditors_mod = globals()['auditors']

    if auditors_mod:
        # Identify the Operator Class from globals if possible
        op_class = None
        # Look for class starting with MASSA_OT_
        for name, val in globals().items():
            if name.startswith("MASSA_OT_") and isinstance(val, type):
                op_class = val
                break
        
        # Register Class to populate bl_rna
        if op_class:
            try:
                bpy.utils.register_class(op_class)
            except Exception as e:
                pass 
                
        try:
            if hasattr(auditors_mod, 'run_all_auditors'):
                errors.extend(auditors_mod.run_all_auditors(obj, op_class))
        except Exception as e:
            errors.append(f"Auditor Loader Failed: {str(e)}")

    
    # --- CONNECT YOUR ATTACHED SCRIPTS HERE ---
    
    # [FALLBACK LOGIC]: If attached files aren't linked, we run a basic check
    # to ensure the system works out of the box.
    if not obj or obj.type != 'MESH':
       return ["Object not valid for mesh audit"]

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

def find_generated_object(exclude=None):
    if exclude is None: exclude = []
    # Try active
    obj = bpy.context.active_object
    if obj and obj not in exclude and obj.type == 'MESH':
        return obj
    # Try list
    for o in bpy.data.objects:
        if o.type == 'MESH' and o not in exclude:
            return o
    return None

def setup_visual_diff(obj_a, obj_b):
    # Red for A
    mat_a = bpy.data.materials.new(name="Red_Wire")
    mat_a.use_nodes = False
    mat_a.diffuse_color = (1.0, 0.0, 0.0, 1.0) # Red
    # Wireframe display in viewport
    obj_a.show_wire = True
    obj_a.show_all_edges = True
    obj_a.color = (1.0, 0.0, 0.0, 1.0)
    
    # Green for B
    mat_b = bpy.data.materials.new(name="Green_Wire")
    mat_b.use_nodes = False
    mat_b.diffuse_color = (0.0, 1.0, 0.0, 1.0) # Green
    obj_b.show_wire = True
    obj_b.show_all_edges = True
    obj_b.color = (0.0, 1.0, 0.0, 1.0)

    # Offset B slightly to prevent Z-fighting if identical
    obj_b.location.x += 0.01

def setup_camera(angle="ISO_CAM"):
    # Simple camera setup
    cam_data = bpy.data.cameras.new("Cam")
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    if angle == "ISO_CAM":
        cam_obj.location = (10, -10, 10)
        cam_obj.rotation_euler = (0.95, 0, 0.78)

def render_viewport(name):
    tmp_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"{name}.png")
    bpy.context.scene.render.filepath = tmp_path

    if bpy.app.background:
        # Use Workbench for software render
        bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
        # Configure Workbench for clarity
        bpy.context.scene.display.shading.light = 'FLAT'
        bpy.context.scene.display.shading.color_type = 'MATERIAL' # Use Material colors (for Heatmaps/UVs)
        # Ensure we show wireframes if set on objects
        # Workbench X-Ray might be needed for UV overlap checking?
        # Actually wireframe attribute on object works in Workbench.

        bpy.ops.render.render(write_still=True)
    else:
        # Use OpenGL render (viewport render)
        bpy.ops.render.opengl(write_still=True)
    return tmp_path

def image_to_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return None

# --- SKILL HANDLERS ---

def skill_get_scene_info(params):
    limit = params.get("limit", 20)
    offset = params.get("offset", 0)
    obj_type = params.get("object_type")
    
    all_objs = bpy.data.objects
    if obj_type:
        all_objs = [o for o in all_objs if o.type == obj_type]
        
    total_count = len(all_objs)
    subset = all_objs[offset : offset + limit]
    
    obj_list = []
    for o in subset:
        obj_list.append({
            "name": o.name,
            "type": o.type,
            "location": [round(v, 3) for v in o.location],
            "collection": [c.name for c in o.users_collection]
        })
        
    return {
        "status": "SUCCESS",
        "total_objects": total_count,
        "returned": len(obj_list),
        "objects": obj_list
    }

def skill_get_object_info(params):
    name = params.get("object_name")
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "FAIL", "msg": f"Object '{name}' not found"}
        
    # Gather Info
    info = {
        "name": obj.name,
        "type": obj.type,
        "location": [round(v, 4) for v in obj.location],
        "rotation_euler": [round(v, 4) for v in obj.rotation_euler],
        "scale": [round(v, 4) for v in obj.scale],
        "dimensions": [round(v, 4) for v in obj.dimensions],
        "parent": obj.parent.name if obj.parent else None,
        "collections": [c.name for c in obj.users_collection],
        "modifiers": [m.name for m in obj.modifiers],
        "constraints": [c.name for c in obj.constraints],
        "vertex_count": len(obj.data.vertices) if obj.type == 'MESH' else 0,
        "poly_count": len(obj.data.polygons) if obj.type == 'MESH' else 0
    }
    
    # Run Health Check
    health = "PASS"
    issues = []
    if obj.type == 'MESH':
        issues = run_checks(obj)
        if issues: health = "FAIL"
        
    info["health"] = health
    info["audit_issues"] = issues
    
    return {"status": "SUCCESS", "info": info}

def skill_transform_object(params):
    """
    Handles Move, Rotate, Scale
    """
    name = params.get("name")
    obj = bpy.data.objects.get(name)
    if not obj:
        return {"status": "FAIL", "msg": f"Object '{name}' not found"}
        
    mode = params.get("mode", "ABSOLUTE")
    loc = params.get("location")
    rot = params.get("rotation") # Degrees
    scl = params.get("scale")
    
    # Location
    if loc:
        if mode == "RELATIVE":
            obj.location.x += loc[0]
            obj.location.y += loc[1]
            obj.location.z += loc[2]
        else:
            obj.location = loc
            
    # Rotation
    if rot:
        # Convert degrees to radians
        rot_rad = [math.radians(a) for a in rot]
        if mode == "RELATIVE":
            obj.rotation_euler.x += rot_rad[0]
            obj.rotation_euler.y += rot_rad[1]
            obj.rotation_euler.z += rot_rad[2]
        else:
            obj.rotation_euler = rot_rad
            
    # Scale
    if scl:
        if mode == "RELATIVE":
            obj.scale.x *= scl[0]
            obj.scale.y *= scl[1]
            obj.scale.z *= scl[2]
        else:
            obj.scale = scl
            
    # Update dependency graph
    bpy.context.view_layer.update()
    
    return {
        "status": "SUCCESS",
        "new_transforms": {
            "location": [round(v, 3) for v in obj.location],
            "rotation_deg": [round(math.degrees(v), 3) for v in obj.rotation_euler],
            "scale": [round(v, 3) for v in obj.scale]
        }
    }

def skill_get_vision(params):
    mode = params.get("mode", "SOLID")
    # Set view mode if possible (requires view3d context, tricky in background)
    # We'll just render whatever assume setup is okay.
    
    path = render_viewport("vision_dump")
    b64 = image_to_base64(path)
    
    return {
        "status": "SUCCESS",
        "image": b64, # Base64 data
        "path": path
    }

def handle_skill_execution(payload):
    skill = payload.get("skill")
    params = payload.get("params", {})
    
    if skill == "get_scene_info":
        return skill_get_scene_info(params)
    elif skill == "get_object_info":
        return skill_get_object_info(params)
    elif skill == "transform_object":
        return skill_transform_object(params)
    elif skill == "get_vision":
        return skill_get_vision(params)
    else:
        return {"status": "FAIL", "msg": f"Unknown skill: {skill}"}


def execute_audit(cartridge_path, mode="AUDIT", payload=None, is_direct=False):
    """
    Executes the audit logic.
    is_direct: If True, skips scene clearing and uses current context.
    """
    if payload is None: payload = {}

    if not is_direct:
        # Clean Scene
        bpy.ops.wm.read_factory_settings(use_empty=True)

    # --- MODE CHECK ---
    
    if mode == "SKILL_EXEC":
        return handle_skill_execution(payload)
    
    if mode == "VISUAL_DIFF":
        # 1. Run First Cartridge (Target A)
        if not is_path_safe(cartridge_path):
            return {"status": "FAIL", "message": f"Access Denied: Cartridge A path '{cartridge_path}' is outside authorized directory"}

        try:
            with open(cartridge_path) as f:
                exec(f.read(), globals())
        except Exception as e:
            return {"status": "FAIL", "message": f"Cartridge A Crash: {e}"}

        obj_a = find_generated_object()
        if not obj_a:
            return {"status": "FAIL", "message": "Cartridge A produced no object"}
        obj_a.name = "Version_A_Red"
        
        # 2. Run Second Cartridge (Target B)
        file_b = payload.get("filename_b")
        if file_b:
            if not os.path.isabs(file_b):
                 # Assume same dir as cartridge A if relative
                 file_b = os.path.join(os.path.dirname(cartridge_path), file_b)
            
            if not is_path_safe(file_b):
                return {"status": "FAIL", "message": f"Access Denied: Cartridge B path '{file_b}' is outside authorized directory"}

            if os.path.exists(file_b):
                try:
                    with open(file_b) as f:
                        exec(f.read(), globals())
                except Exception as e:
                    return {"status": "FAIL", "message": f"Cartridge B Crash: {e}"}
                
                obj_b = find_generated_object(exclude=[obj_a])
                if not obj_b:
                    return {"status": "FAIL", "message": "Cartridge B produced no object"}
                obj_b.name = "Version_B_Green"
                
                # 3. Setup Red/Green
                setup_visual_diff(obj_a, obj_b)
                
                # 4. Render
                output_path = render_viewport(f"diff_{obj_a.name}_vs_{obj_b.name}")
                return {"status": "SUCCESS", "image_path": output_path}
            else:
                 return {"status": "FAIL", "message": f"File B not found: {file_b}"}
        else:
             return {"status": "FAIL", "message": "filename_b missing in payload"}

    # Default AUDIT execution
    exec_time_ms = 0.0
    try:
        start_time = time.perf_counter()
        print(f"Runner: Checking cartridge {cartridge_path}")
        if os.path.exists(cartridge_path) and cartridge_path != "global_skill_placeholder.py":
            if not is_path_safe(cartridge_path):
                return {"status": "FAIL", "errors": [f"Access Denied: Cartridge path '{cartridge_path}' is outside authorized directory"]}

            print("Runner: File exists, executing...")
            prepare_cartridge_env()
            with open(cartridge_path) as f:
                code = f.read()

                # Replace relative imports using regex to handle variations
                # Use flexible whitespace matching
                code = re.sub(r'from\s+\.+\s*operators\.massa_base\s+import\s+Massa_OT_Base', '# [MOCKED] Massa_OT_Base', code)
                # Allow optional 'modules.' prefix for MassaBuilder
                code = re.sub(r'from\s+\.+\s*(?:modules\.)?massa_builder\s+import\s+MassaBuilder', '# [MOCKED] MassaBuilder', code)
                # Mock MassaPropertiesMixin
                code = re.sub(r'from\s+\.+\s*(?:modules\.)?massa_properties\s+import\s+MassaPropertiesMixin', '# [MOCKED] MassaPropertiesMixin', code)

                # Check for remaining relative imports
                if "from ." in code:
                    print("Runner WARNING: Relative imports found in code!")
                    for line in code.split('\n'):
                        if "from ." in line and not line.strip().startswith("#"):
                            print(f"  > {line}")

                exec(code, globals())

                # [AUTO-EXECUTE] If we just loaded an Operator, run it to generate the mesh
                op_class = None
                print("Runner: Scanning globals for MASSA_OT_...")
                for name, val in globals().items():
                    if name.startswith("MASSA_OT_"):
                         print(f"Runner: Found Global {name}")
                         if isinstance(val, type):
                             # Avoid picking up the Base class itself if imported
                             if name != "Massa_OT_Base":
                                 op_class = val
                                 break

                if op_class:
                    try:
                        # Ensure bpy is real
                        if hasattr(bpy, "utils") and hasattr(bpy, "ops"):
                            try:
                                bpy.utils.register_class(op_class)
                            except ValueError:
                                pass # Already registered

                            # Call Operator
                            idname = op_class.bl_idname
                            print(f"Runner: Found Operator {idname}")
                            if "." in idname:
                                cat, name = idname.split(".")
                                if hasattr(bpy.ops, cat):
                                    func = getattr(getattr(bpy.ops, cat), name)
                                    func() # Run!
                                    print(f"Runner: Executed {idname}")
                                else:
                                    print(f"Runner: Could not find category {cat} in bpy.ops")
                            else:
                                print(f"Runner: Invalid idname {idname}")
                    except Exception as e:
                        print(f"Runner Execution Error: {e}")
                        import traceback
                        traceback.print_exc()

        else:
             # If cartridge doesn't exist (and we aren't in SKILL_EXEC), it's okay if we just want to audit existing?
             # But usually audit runs the cartridge.
             # If placeholder, we skip exec.
             pass
             
        end_time = time.perf_counter()
        exec_time_ms = (end_time - start_time) * 1000
    except Exception as e:
        return {"status": "FAIL", "errors": [f"Syntax/Runtime Error: {str(e)}"]}

    # Find Mesh
    obj = find_generated_object()
    if not obj:
        # If we didn't run a cartridge, and there's no object, fail.
        # But if we are in a mode that expects one, we should error.
        if mode in ["AUDIT", "PERFORMANCE", "UV_HEATMAP", "CSG_DEBUG", "UV_INSPECT"]:
             return {"status": "FAIL", "errors": ["No Mesh Created by Cartridge or Found in Scene"]}

    if mode == "UV_HEATMAP":
        try:
             setup_uv_heatmap(obj)
             output_path = render_viewport(f"heatmap_{obj.name}")
             return {"status": "SUCCESS", "image_path": output_path}
        except Exception as e:
             return {"status": "FAIL", "message": f"Heatmap Error: {str(e)}"}

    if mode == "UV_INSPECT":
        try:
             # Generate a 2D mesh representation of the UV layout
             print(f"DEBUG: UV_INSPECT on {obj} Name:{obj.name} Type:{obj.type} Data:{obj.data}")
             setup_uv_layout_view(obj)
             output_path = render_viewport(f"uv_layout_{obj.name}")
             return {"status": "SUCCESS", "image_path": output_path}
        except Exception as e:
             import traceback
             traceback.print_exc()
             return {"status": "FAIL", "message": f"UV Inspect Error: {str(e)}"}

    if mode == "PERFORMANCE":
        poly_count = len(obj.data.polygons)
        vert_count = len(obj.data.vertices)
        
        crashes_blender = False
        if poly_count > 100000: crashes_blender = True
        
        result = {
            "status": "SUCCESS",
            "execution_time_ms": exec_time_ms,
            "poly_count": poly_count,
            "vert_count": vert_count,
            "budget_status": "FAIL" if crashes_blender else "PASS"
        }
        return result

    if mode == "CSG_DEBUG":
        # Visualize Cutters
        cutters_found = 0
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and mod.object:
                mod.object.hide_viewport = False
                mod.object.hide_render = False
                mod.object.display_type = 'WIRE'
                mod.object.show_wire = True
                cutters_found += 1
                
        if cutters_found == 0:
            return {"status": "FAIL", "message": "No Boolean Modifiers found to debug"}

        setup_camera(payload.get("camera_angle", "ISO_CAM"))
        output_path = render_viewport(f"csg_debug_{obj.name}")
        return {"status": "SUCCESS", "image_path": output_path, "cutters_visualized": cutters_found}

    if mode == "RENDER":
        setup_camera(payload.get("camera_angle", "ISO_CAM"))
        try:
             # Basic View Settings for clear render
             if obj:
                 obj.show_wire = (payload.get("shading") == "WIREFRAME")
                 if obj.show_wire:
                     obj.display_type = 'WIRE'
                 else:
                     obj.display_type = 'SOLID'
                     
             output_path = render_viewport(f"render_{obj.name}")
             return {"status": "SUCCESS", "image_path": output_path}
        except Exception as e:
             return {"status": "FAIL", "message": f"Render Error: {str(e)}"}

    # Default AUDIT execution

    # Run Standard Audit
    error_list = run_checks(obj)
    
    result = {
        "status": "PASS" if not error_list else "FAIL",
        "object": obj.name,
        "errors": error_list
    }

    return result

def setup_uv_heatmap(obj):
    import bmesh
    
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    
    uv_layer = bm.loops.layers.uv.verify()
    
    # Create Vertex Color Layer for Heatmap
    vcol_layer = bm.loops.layers.color.new("Heatmap")
    
    blue = (0.0, 0.0, 1.0, 1.0)
    green = (0.0, 1.0, 0.0, 1.0)
    yellow = (1.0, 1.0, 0.0, 1.0)
    red = (1.0, 0.0, 0.0, 1.0)
    
    for f in bm.faces:
        # Calculate 3D Area
        area_3d = f.calc_area()
        
        # Calculate UV Area
        uvs = [l[uv_layer].uv for l in f.loops]
        # Shoelace formula
        area_uv = 0.5 * abs(sum(x0*y1 - x1*y0 for ((x0, y0), (x1, y1)) in zip(uvs, uvs[1:] + [uvs[0]])))
        
        if area_3d < 0.000001:
            ratio = 1.0
        else:
            if area_uv < 0.000001:
                ratio = 999.0 # Infinite stretch
            else:
                ratio = area_3d / area_uv
        
        # Simple heuristic for "Badness"
        if ratio > 5.0 or ratio < 0.2:
            col = red
        elif ratio > 2.0 or ratio < 0.5:
            col = yellow
        elif ratio > 1.2 or ratio < 0.8:
            col = green
        else:
            col = blue
            
        for l in f.loops:
            l[vcol_layer] = col

    bm.to_mesh(mesh)
    bm.free()
    
    # Setup Material to show Vertex Colors
    mat = bpy.data.materials.new(name="Heatmap_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Shader
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfDiffuse') # Simple diffuse
    
    # Vertex Color
    vcol = nodes.new('ShaderNodeVertexColor')
    vcol.layer_name = "Heatmap"
    
    links.new(vcol.outputs['Color'], bsdf.inputs['Color'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat
        
    # Ensure Render uses it
    obj.active_material = mat
    # Viewport
    obj.show_wire = True
    
    setup_camera()

def setup_uv_layout_view(obj):
    """
    Creates a new mesh where XY coordinates = UV coordinates of the original object.
    Used for visual inspection of packing and overlaps.
    """
    import bmesh

    bm_orig = bmesh.new()
    bm_orig.from_mesh(obj.data)
    bm_orig.faces.ensure_lookup_table()

    uv_layer = bm_orig.loops.layers.uv.verify()

    # Create new BMesh for UVs
    bm_uv = bmesh.new()

    # Iterate faces and recreate them in UV space (2D)
    for f in bm_orig.faces:
        uv_verts = []
        for l in f.loops:
            uv = l[uv_layer].uv
            # Create vert at (u, v, 0)
            # Note: We duplicate verts per face loop to simulate split UVs correctly
            # (UV islands are split in UV space even if connected in 3D)
            v = bm_uv.verts.new((uv.x, uv.y, 0))
            uv_verts.append(v)

        try:
            bm_uv.faces.new(uv_verts)
        except ValueError:
            pass # Degenerate face in UV space

    bm_orig.free()

    # Convert to Mesh Object
    mesh_uv = bpy.data.meshes.new("UV_Layout_Mesh")
    bm_uv.to_mesh(mesh_uv)
    bm_uv.free()

    uv_obj = bpy.data.objects.new("UV_Layout_Obj", mesh_uv)
    bpy.context.collection.objects.link(uv_obj)

    # Hide original
    obj.hide_render = True
    obj.hide_viewport = True

    # Material: Wireframe + Semi-transparent fill
    mat = bpy.data.materials.new(name="UV_Layout_Mat")
    mat.use_nodes = True
    # Wireframe display
    uv_obj.show_wire = True
    uv_obj.show_all_edges = True
    uv_obj.data.materials.append(mat)

    # Setup Orthographic Camera
    setup_camera()
    cam = bpy.context.scene.camera
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 1.2 # Slightly larger than 1.0 to show margins
    cam.location = (0.5, 0.5, 10) # Center of 0-1 space
    cam.rotation_euler = (0, 0, 0) # Look down Z (default camera points down -Z in Blender if rot is 0,0,0? No, default is -Z)
    # Actually standard camera looks down -Z.
    # We want to look at XY plane.
    # Default camera:
    # Location (0,0,10)
    # Rotation (0,0,0) -> Points Down -Z.
    # Top of image is +Y, Right is +X.
    # This matches UV space orientation.

    # Add border for 0-1 bounds
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.5, 0.5, -0.1))
    plane = bpy.context.active_object
    plane.display_type = 'WIRE'
    plane.show_wire = True

def print_json(data):
    print("---AUDIT_START---")
    print(json.dumps(data))
    print("---AUDIT_END---")

def main():
    # Parse Args
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--cartridge", required=True)
    parser.add_argument("--mode", default="AUDIT")
    parser.add_argument("--payload", default=None)
    
    args, _ = parser.parse_known_args(argv)

    payload = {}
    if args.payload:
        try: payload = json.loads(args.payload)
        except: pass

    # Execute
    result = execute_audit(args.cartridge, args.mode, payload, is_direct=False)

    # Print Result
    print_json(result)

if __name__ == "__main__":
    main()
