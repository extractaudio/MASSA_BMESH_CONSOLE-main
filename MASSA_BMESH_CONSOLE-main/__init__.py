import bpy
import importlib

bl_info = {
    "name": "Massa Container",
    "category": "3D View",
    "author": "ThinkTank",
    "version": (1, 0, 2),
    "blender": (5, 0, 0),
    "location": "Sidebar > Massa",
    "description": "Procedural Geometry Engine",
}

# --- IMPORTS ---
from .utils import mat_utils
from .modules import massa_console  # 1. BRAIN
from .modules import massa_engine  # 2. CORE
from .operators import massa_base, massa_tools  # 3. LOGIC
from .modules import cartridges  # 4. CONTENT
from .ui import ui_massa_panel, gizmo_massa  # 5. INTERFACE

# --- MANUAL OVERRIDE / HOT RELOAD LOGIC ---
if "massa_console" in locals():
    print("Massa: Detected existing instance. Reloading...")
    try:
        # 1. UTILS & SHARED DNA (Must reload first!)
        importlib.reload(mat_utils)
        from .modules import massa_properties

        importlib.reload(massa_properties)  # <--- CRITICAL: Reload the Mixin Base

        # 2. ENGINE SUB-SYSTEMS (Leaf nodes of the Engine)
        from .modules import massa_polish, massa_surface, massa_sockets, seam_solvers

        importlib.reload(massa_polish)
        importlib.reload(massa_surface)
        importlib.reload(massa_sockets)
        importlib.reload(seam_solvers)

        # 3. CORE SYSTEMS
        importlib.reload(massa_console)  # The Brain
        importlib.reload(massa_engine)  # The Engine (aggregates sub-systems)
        importlib.reload(massa_base)  # The Muscle (inherits props + uses engine)
        importlib.reload(massa_tools)

        # 4. CONTENT & UI
        importlib.reload(cartridges)

        # RELOAD INDIVIDUAL CARTRIDGES
        if hasattr(cartridges, "MODULES"):
            for mod in cartridges.MODULES:
                importlib.reload(mod)

        importlib.reload(ui_massa_panel)  # The Face
        importlib.reload(gizmo_massa)

        print("Massa: Reload Complete.")
    except Exception as e:
        print(f"Massa: Reload Error: {e}")


def register():
    # 1. Register Console (Shared Properties)
    massa_console.register()

    # 2. Register Operators
    bpy.utils.register_class(massa_base.Massa_OT_Base)
    bpy.utils.register_class(massa_base.MASSA_OT_ReRun_Active)
    bpy.utils.register_class(massa_tools.MASSA_OT_Condemn)
    bpy.utils.register_class(massa_tools.MASSA_OT_Resurrect_Wrapper)

    # 3. Register Cartridges
    cartridges.register()

    # 4. Register UI
    bpy.utils.register_class(ui_massa_panel.MASSA_PT_Main)
    bpy.utils.register_class(gizmo_massa.MASSA_GGT_GizmoGroup)


def unregister():
    # 1. Unregister UI
    bpy.utils.unregister_class(gizmo_massa.MASSA_GGT_GizmoGroup)
    bpy.utils.unregister_class(ui_massa_panel.MASSA_PT_Main)

    # 2. Unregister Cartridges
    cartridges.unregister()

    # 3. Unregister Operators
    bpy.utils.unregister_class(massa_tools.MASSA_OT_Condemn)
    bpy.utils.unregister_class(massa_tools.MASSA_OT_Resurrect_Wrapper)
    bpy.utils.unregister_class(massa_base.Massa_OT_Base)
    bpy.utils.unregister_class(massa_base.MASSA_OT_ReRun_Active)

    # 4. Unregister Console
    massa_console.unregister()
