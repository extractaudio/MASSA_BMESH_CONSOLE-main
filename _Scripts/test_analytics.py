import bpy
import sys
import os
import json

# Add project root to path
project_root = r"D:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\MASSA_BMESH_CONSOLE-main"
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from modules import advanced_analytics
    
    # Create Test Object
    bpy.ops.mesh.primitive_cube_add(size=2)
    obj = bpy.context.active_object
    obj.name = "Test_Cube"
    
    # Test 1: Audit Evaluated
    print("\n--- TEST: audit_evaluated ---")
    stats = advanced_analytics.audit_evaluated("Test_Cube")
    print(json.dumps(stats, indent=2))
    
    # Test 2: Trace Dependencies (Add a parent to test)
    print("\n--- TEST: trace_dependencies ---")
    bpy.ops.object.empty_add()
    parent = bpy.context.active_object
    parent.name = "Parent_Empty"
    obj.parent = parent
    
    deps = advanced_analytics.trace_dependencies("Test_Cube")
    print(json.dumps(deps, indent=2))
    
    print("\n--- TEST COMPLETE ---")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
