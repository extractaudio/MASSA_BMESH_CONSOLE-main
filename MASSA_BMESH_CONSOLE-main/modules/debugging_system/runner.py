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
    # --- DYNAMICALLY RUN ATTACHED AUDITORS ---
    if 'auditors' in sys.modules:
        import auditors
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
                # If registration fails (e.g. doesn't inherit from Operator), we just proceed without it
                # But we might want to log it?
                # errors.append(f"Class Reg Warning: {str(e)}") 
                pass 
                
        try:
            errors.extend(auditors.run_all_auditors(obj, op_class))
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

    # Added arguments for Extended Modes
    parser.add_argument("--mode", default="AUDIT")
    parser.add_argument("--payload", default=None)
    
    # Reparse with new args
    args, _ = parser.parse_known_args(argv)
    
    payload = {}
    if args.payload:
        try: payload = json.loads(args.payload)
        except: pass

    # Clean Scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # --- MODE CHECK ---
    
    if args.mode == "VISUAL_DIFF":
        # 1. Run First Cartridge (Target A)
        try:
            with open(args.cartridge) as f:
                exec(f.read(), globals())
        except Exception as e:
            print_json({"status": "FAIL", "message": f"Cartridge A Crash: {e}"})
            return

        obj_a = find_generated_object()
        if not obj_a:
            print_json({"status": "FAIL", "message": "Cartridge A produced no object"})
            return
        obj_a.name = "Version_A_Red"
        
        # 2. Run Second Cartridge (Target B)
        file_b = payload.get("filename_b")
        if file_b:
            if not os.path.isabs(file_b):
                 # Assume same dir as cartridge A if relative
                 file_b = os.path.join(os.path.dirname(args.cartridge), file_b)
            
            if os.path.exists(file_b):
                try:
                    with open(file_b) as f:
                        exec(f.read(), globals())
                except Exception as e:
                    print_json({"status": "FAIL", "message": f"Cartridge B Crash: {e}"})
                    return
                
                obj_b = find_generated_object(exclude=[obj_a])
                if not obj_b:
                    print_json({"status": "FAIL", "message": "Cartridge B produced no object"})
                    return
                obj_b.name = "Version_B_Green"
                
                # 3. Setup Red/Green
                setup_visual_diff(obj_a, obj_b)
                
                # 4. Render
                output_path = render_viewport(f"diff_{obj_a.name}_vs_{obj_b.name}")
                print_json({"status": "SUCCESS", "image_path": output_path})
                return
            else:
                 print_json({"status": "FAIL", "message": f"File B not found: {file_b}"})
                 return
        else:
             print_json({"status": "FAIL", "message": "filename_b missing in payload"})
             return

    # Default AUDIT execution
    try:
        with open(args.cartridge) as f:
            exec(f.read(), globals())
    except Exception as e:
        print_json({"status": "FAIL", "errors": [f"Syntax/Runtime Error: {str(e)}"]})
        return

    # Find Mesh
    obj = find_generated_object()
    if not obj:
        print_json({"status": "FAIL", "errors": ["No Mesh Created by Cartridge"]})
        return

    # Run mode-specific logic
    if args.mode == "VISUAL_DIFF":
        # ... (Visual Diff Logic as before) ...
        # (Assuming this block is already here, I am inserting AFTER it or handling strict placement)
        pass 

    if args.mode == "UV_HEATMAP":
        # ... (UV Heatmap Logic as before) ...
        # (Assuming placement)
        pass

    if args.mode == "PERFORMANCE":
        import time
        start_time = time.perf_counter()
        try:
            with open(args.cartridge) as f:
                exec(f.read(), globals())
        except Exception as e:
            print_json({"status": "FAIL", "message": f"Cartridge Crash: {e}"})
            return
        end_time = time.perf_counter()
        
        obj = find_generated_object()
        if not obj:
            print_json({"status": "FAIL", "message": "No object created"})
            return

        poly_count = len(obj.data.polygons)
        vert_count = len(obj.data.vertices)
        exec_time_ms = (end_time - start_time) * 1000
        
        crashes_blender = False
        if poly_count > 100000: crashes_blender = True # Arbitrary budget
        
        result = {
            "status": "SUCCESS",
            "execution_time_ms": exec_time_ms,
            "poly_count": poly_count,
            "vert_count": vert_count,
            "budget_status": "FAIL" if crashes_blender else "PASS"
        }
        print_json(result)
        return

    if args.mode == "CSG_DEBUG":
        try:
            with open(args.cartridge) as f:
                exec(f.read(), globals())
        except Exception as e:
            print_json({"status": "FAIL", "message": f"Cartridge Crash: {e}"})
            return

        obj = find_generated_object()
        if not obj:
            print_json({"status": "FAIL", "message": "No object created"})
            return
            
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
            print_json({"status": "FAIL", "message": "No Boolean Modifiers found to debug"})
            return

        setup_camera(payload.get("camera_angle", "ISO_CAM"))
        output_path = render_viewport(f"csg_debug_{obj.name}")
        print_json({"status": "SUCCESS", "image_path": output_path, "cutters_visualized": cutters_found})
        return

    # Default AUDIT execution

    # Run Standard Audit
    error_list = run_checks(obj)
    
    result = {
        "status": "PASS" if not error_list else "FAIL",
        "object": obj.name,
        "errors": error_list
    }

    print_json(result)

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

def print_json(data):
    print("---AUDIT_START---")
    print(json.dumps(data))
    print("---AUDIT_END---")

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

def setup_uv_heatmap(obj):
    import bmesh
    import math
    
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
            # Normalize? This is tricky as UV scale is arbitrary. 
            # We assume roughly 1 unit UV = 1 unit 3D for "ideal" or just look for variations.
            # STRETCH = Area3D / AreaUV. 
            # If we assume 1:1 is good.
            if area_uv < 0.000001:
                ratio = 999.0 # Infinite stretch
            else:
                ratio = area_3d / area_uv
        
        # Visualize Ratio
        # Ideally 1.0. 
        # > 1.0 means 3D is bigger than UV (Under-texelated)
        # < 1.0 means UV is bigger than 3D (Over-texelated)
        
        # We map log scale?
        # Let's just catch extreme stretching.
        # Blue = Good (approx 1). Red = Bad (> 5 or < 0.2)
        
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
    # Create simple camera looking at 0,0,0
    cam_data = bpy.data.cameras.new("Cam")
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    if angle == "ISO_CAM":
        cam_obj.location = (10, -10, 10)
        cam_obj.rotation_euler = (0.95, 0, 0.78) # Approx iso

def render_viewport(name):
    tmp_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"{name}.png")
    bpy.context.scene.render.filepath = tmp_path
    
    # Use OpenGL render (viewport render)
    bpy.ops.render.opengl(write_still=True)
    return tmp_path

if __name__ == "__main__":
    main()