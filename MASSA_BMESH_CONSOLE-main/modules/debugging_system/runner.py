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

# 1. Setup Path to import your attached 'auditors' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 2. Import your attached files
# NOTE: Ensure your attached files are in the 'auditors' folder
try:
    from . import auditors
except ImportError:
    try:
        import auditors
    except ImportError:
        pass

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

def skill_execute_code(params):
    code = params.get("code", "")
    output_capture = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(output_capture):
            exec(code, globals())
        return {
            "status": "SUCCESS",
            "output": output_capture.getvalue()
        }
    except Exception as e:
        return {
            "status": "error",
            "msg": str(e),
            "output": output_capture.getvalue()
        }

def skill_create_bmesh(params):
    name = params.get("name", "New_Object")
    script = params.get("script_content", "")
    
    try:
        bm = bmesh.new()
        # Env for script
        env = {
            "bm": bm,
            "bmesh": bmesh,
            "bpy": bpy,
            "mathutils": importlib.import_module("mathutils")
        }
        
        exec(script, env)
        
        # Finish
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        
        # Ensure 10 slots (Hard 10)
        while len(obj.data.materials) < 10:
            obj.data.materials.append(None)
            
        return {"status": "SUCCESS", "object_name": obj.name}
        
    except Exception as e:
        return {"status": "FAIL", "msg": str(e)}

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
    elif skill == "execute_code":
        return skill_execute_code(params)
    elif skill == "create_bmesh":
        return skill_create_bmesh(params)
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
        if os.path.exists(cartridge_path) and cartridge_path != "global_skill_placeholder.py":
            with open(cartridge_path) as f:
                exec(f.read(), globals())
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
        if mode in ["AUDIT", "PERFORMANCE", "UV_HEATMAP", "CSG_DEBUG"]:
             return {"status": "FAIL", "errors": ["No Mesh Created by Cartridge or Found in Scene"]}

    if mode == "UV_HEATMAP":
        try:
             setup_uv_heatmap(obj)
             output_path = render_viewport(f"heatmap_{obj.name}")
             return {"status": "SUCCESS", "image_path": output_path}
        except Exception as e:
             return {"status": "FAIL", "message": f"Heatmap Error: {str(e)}"}

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
        
        score = 0.0
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
