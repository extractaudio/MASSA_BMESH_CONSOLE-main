import bpy
import bmesh
import sys
import os
import traceback

# Add to path to resolve absolute imports if needed
sys.path.append("d:\\AntiGravity_google\\MASSA_BMESH_CONSOLE-main\\MASSA_BMESH_CONSOLE-main")

cartridge_dir = "d:\\AntiGravity_google\\MASSA_BMESH_CONSOLE-main\\MASSA_BMESH_CONSOLE-main\\modules\\cartridges"
carts = [
    "cart_asm_09_checkpoint.py",
    "cart_asm_10_tower.py",
    "cart_asm_11_spiral_staircase.py",
    "cart_asm_12_fire_escape.py",
    "cart_asm_13_cloister.py",
    "cart_asm_14_loading_dock.py",
    "cart_asm_15_elevator_shaft.py",
    "cart_asm_16_quantum_server.py",
    "cart_asm_17_iris_door.py",
    "cart_asm_18_radar_array.py",
    "cart_asm_19_cryo_pod.py",
    "cart_asm_20_robotic_arm.py"
]

results = {}

for cart_file in carts:
    cart_path = os.path.join(cartridge_dir, cart_file)
    print(f"\n--- Testing {cart_file} ---")
    
    try:
        # Load module
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_module", cart_path)
        module = importlib.util.module_from_spec(spec)
        
        # Need to mock relative imports 'from ...operators.massa_base import Massa_OT_Base'
        # Easiest way in Blender background without the addon installed is to inject the class
        class MockMassaBase:
            pass
        import sys
        
        # Mock massa__base if it doesn't exist
        try:
            from modules.operators.massa_base import Massa_OT_Base
        except ImportError:
            class Massa_OT_Base: pass
            import types
            mock_module = types.ModuleType("massa_base")
            mock_module.Massa_OT_Base = Massa_OT_Base
            sys.modules["...operators.massa_base"] = mock_module
            sys.modules["..operators.massa_base"] = mock_module
            
        spec.loader.exec_module(module)
        
        # Find class
        cart_class = None
        for name, obj in module.__dict__.items():
            if isinstance(obj, type) and name.startswith("MASSA_OT_"):
                cart_class = obj
                break
                
        if not cart_class:
            print(f"Skipping {cart_file}: No MASSA_OT_ class found")
            continue
            
        # Instantiate
        instance = cart_class()
        
        # Set default properties if needed
        # (bpy.props might not be initialized as instance attributes outside Blender's class registration,
        # but we can try to rely on their defaults or set manually)
        for name, prop in cart_class.__annotations__.items() if hasattr(cart_class, '__annotations__') else []:
             pass # Not needed if we use the properties natively, but since we didn't register the class, bpy.props might fail.
        
        # Actually blender's bpy classes need registration to use properties.
        # If we just test the math, we can spoof the properties.
        
    except Exception as e:
        pass
        
    # Better yet, let's use the actual Runner script logic!
    try:
        from modules.debugging_system.runner import import_cartridge_class, setup_initial_bmesh, CartridgeAuditError
        cls = import_cartridge_class(cart_path)
        if not cls: raise Exception("No class found")
        
        # Need to register it so properties work
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            # Already registered or other issue
            pass
            
        # Create a new bmesh
        bm = setup_initial_bmesh()
        
        # Instantiate through window manager or standard class hack
        # The runner.py uses:
        # op_instance = cls()
        # and then populates it from cls.__annotations__ defaults.
        op_instance = cls()
        
        # Populate defaults
        for prop_name, prop_tuple in getattr(cls, '__annotations__', {}).items():
            if type(prop_tuple) == tuple and len(prop_tuple) >= 2:
                prop_meta = prop_tuple[1]
                if 'default' in prop_meta:
                    setattr(op_instance, prop_name, prop_meta['default'])
                    
        # Apply the layout and see if build_shape fails
        op_instance.build_shape(bm)
        
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        print(f"SUCCESS: {cart_file} generated {len(bm.verts)} verts, {len(bm.faces)} faces")
        bm.free()
        results[cart_file] = "PASS"
        
    except Exception as e:
        print(f"FAILED: {cart_file}")
        traceback.print_exc()
        results[cart_file] = "FAIL"

print("\n\nSUMMARY:")
for k, v in results.items():
    print(f"{k}: {v}")

fails = [k for k, v in results.items() if v == 'FAIL']
if fails:
    sys.exit(1)
sys.exit(0)
