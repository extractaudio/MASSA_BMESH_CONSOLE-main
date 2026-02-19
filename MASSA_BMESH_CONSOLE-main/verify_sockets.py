
import bpy
import mathutils

def verify():
    # 1. Clear Scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # 2. Run Operator
    # We need to ensure the operator is registered.
    # In a full addon environment, it should be.
    # Here we assume the addon is loaded or we can access the class.
    
    # Check if operator exists
    if not hasattr(bpy.ops.massa, "gen_prim_03_sheet"):
        print("Operator 'massa.gen_prim_03_sheet' not found. Is the addon loaded?")
        return

    # Create sheet with Sockets Enabled for Slot 0
    bpy.ops.massa.gen_prim_03_sheet(
        sock_enable=True,
        sock_0=True,  # Enable socket for Slot 0 (Surface)
        sock_visual_size=0.5
    )

    obj = bpy.context.active_object
    if not obj:
        print("FAILED: No object created.")
        return

    print(f"Created Object: {obj.name}")

    # 3. Analyze Children (Sockets)
    surface_sockets = []
    for child in obj.children:
        print(f"Child: {child.name} | Loc: {child.location}")
        if "SOCKET_Surface" in child.name:
            surface_sockets.append(child)

    # 4. Assertions
    if len(surface_sockets) != 1:
        print(f"FAILED: Expected 1 Surface socket, found {len(surface_sockets)}")
        for s in surface_sockets:
            print(f" - {s.name}")
    else:
        print("SUCCESS: Only 1 Surface socket found.")
        sock = surface_sockets[0]
        
        # Check Orientation
        # Rotation should be (0,0,0) as we forced it.
        rot = sock.rotation_euler
        print(f"Socket Rotation: {rot}")
        if rot.x == 0 and rot.y == 0 and rot.z == 0:
            print("SUCCESS: Socket is pointing Up (Identity Rotation).")
        else:
            print("WARNING: Socket rotation is not exactly zero. Check logic.")

    # Cleanup
    # bpy.ops.object.delete()

if __name__ == "__main__":
    verify()
