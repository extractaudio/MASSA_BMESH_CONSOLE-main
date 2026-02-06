import bpy
import sys
import os
import json
import importlib.util

def setup_massa_env():
    """
    Sets up the 'massa' package environment by aliasing the addon directory 
    (which might have dashes) to a clean 'massa' package name in sys.modules.
    """
    # 1. Calculate Addon Root (Repo/MASSA_BMESH_CONSOLE-main)
    # runner.py is in modules/debugging_system/
    # root is ../../
    current_dir = os.path.dirname(os.path.abspath(__file__))
    addon_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    
    # 2. Register top-level package 'massa' pointing to __init__.py
    init_path = os.path.join(addon_root, "__init__.py")
    if not os.path.exists(init_path):
        return False, f"__init__.py not found at {init_path}"
        
    try:
        spec = importlib.util.spec_from_file_location("massa", init_path)
        massa_mod = importlib.util.module_from_spec(spec)
        sys.modules["massa"] = massa_mod
        
        # Let's execute the __init__ module.
        spec.loader.exec_module(massa_mod)
        
        # If that worked, we can try running the register function
        if hasattr(massa_mod, "register"):
            massa_mod.register()
            return True, "Massa Registered Successfully"
        else:
            return False, "No register function in massa module"
            
    except Exception as e:
        import traceback
        return False, f"Setup Error: {str(e)}\n{traceback.format_exc()}"

def execute_console_audit(is_direct=False):
    report = {"status": "PASS", "errors": [], "logs": []}
    
    # 1. Setup Environment
    if not is_direct:
        ok, msg = setup_massa_env()
        report["logs"].append(msg)
        if not ok:
            report["status"] = "FAIL"
            report["errors"].append(msg)
            return report
        
        # 2. Create Test Context
        bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # 3. Test: Operator Registration
    # Check if a known operator is registered
    # The actual bl_idname is "massa.gen_prim_con_beam"
    
    if not hasattr(bpy.ops.massa, "gen_prim_con_beam"):
         report["status"] = "FAIL"
         report["errors"].append("Operator massa.gen_prim_con_beam not found in bpy.ops")
         return report
         
    # 4. Test: Execution (Beam)
    try:
        # Run the operator
        bpy.ops.massa.gen_prim_con_beam()
        
        # Verify Object Creation
        obj = bpy.context.active_object
        if not obj:
            report["status"] = "FAIL"
            report["errors"].append("Operator ran but no active object found.")
            return report
            
        report["logs"].append(f"Created Object: {obj.name}")
        
        # 5. Test: Console Data Presence (Slots, Edge Layers)
        # Check for 'MASSA_EDGE_SLOTS' layer
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
             report["status"] = "FAIL"
             report["errors"].append("MASSA_EDGE_SLOTS layer missing from generated mesh.")
        else:
            report["logs"].append("confirmed: MASSA_EDGE_SLOTS present")
            
        bm.free()
        
        # 6. Test: Redo Panel Simulation (Resurrection)
        # But we can check if the object has the resurrection ID
        if "massa_op_id" not in obj:
             report["status"] = "FAIL"
             report["errors"].append("Object missing 'massa_op_id' custom property.")
        
        if obj["massa_op_id"] != "massa.gen_prim_con_beam":
             report["status"] = "FAIL"
             report["errors"].append(f"Incorrect massa_op_id: {obj.get('massa_op_id')}")

    except Exception as e:
        import traceback
        report["status"] = "FAIL"
        report["errors"].append(f"Runtime Error: {str(e)}\n{traceback.format_exc()}")
        
    return report

if __name__ == "__main__":
    final_report = execute_console_audit(is_direct=False)
    print("---AUDIT_START---")
    print(json.dumps(final_report, indent=4))
    print("---AUDIT_END---")
