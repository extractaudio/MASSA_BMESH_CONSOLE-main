import bpy
import sys
import os
import argparse
import json
import importlib
import time

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
        with open(cartridge_path) as f:
            exec(f.read(), globals())
        end_time = time.perf_counter()
        exec_time_ms = (end_time - start_time) * 1000
    except Exception as e:
        return {"status": "FAIL", "errors": [f"Syntax/Runtime Error: {str(e)}"]}

    # Find Mesh
    obj = find_generated_object()
    if not obj:
        return {"status": "FAIL", "errors": ["No Mesh Created by Cartridge"]}

    if mode == "VISUAL_DIFF":
         # Fallthrough if logic above was different? Original code had pass.
         pass

    if mode == "UV_HEATMAP":
        # Logic was missing or incomplete in original file dump, but implied setup_uv_heatmap
        # Assuming setup_uv_heatmap(obj) is intended.
        # But setup_uv_heatmap is not fully defined in my context (missing from original dump or implicit)
        # I'll try to execute it if defined.
        # Original dump had setup_uv_heatmap defined at end.
        try:
             setup_uv_heatmap(obj)
             # Render?
             # setup_uv_heatmap sets up camera but doesn't render.
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
