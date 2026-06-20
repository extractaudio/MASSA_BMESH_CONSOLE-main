import bpy
import importlib

# --- IMPORTS ---
from .utils import mat_utils
from .modules import massa_console  # 1. BRAIN
from .modules import massa_engine  # 2. CORE
from .operators import massa_base, massa_tools, massa_console_op, massa_point_tool, massa_shooter, massa_uv_preview  # 3. LOGIC
from .modules import cartridges  # 4. CONTENT
from .modules import advanced_analytics # 4.5 ANALYTICS
from .ui import ui_massa_panel, ui_massa_pie, gizmo_massa  # 5. INTERFACE
from .modules import mcp_bridge  # 6. MCP BRIDGE (Blender-side socket server)

# --- MANUAL OVERRIDE / HOT RELOAD LOGIC ---
if "massa_console" in locals():
    print("Massa: Detected existing instance. Reloading...")
    try:
        # 1. UTILS & SHARED DNA (Must reload first!)
        importlib.reload(mat_utils)
        from .modules import massa_properties

        importlib.reload(massa_properties)  # <--- CRITICAL: Reload the Mixin Base

        # 2. ENGINE SUB-SYSTEMS (Leaf nodes of the Engine)
        from .modules import (
            massa_polish,
            massa_surface,
            massa_sockets,
            seam_solvers,
            advanced_analytics,
            massa_collision,
        )

        importlib.reload(massa_polish)
        importlib.reload(massa_surface)
        importlib.reload(massa_sockets)
        importlib.reload(seam_solvers)
        importlib.reload(advanced_analytics)
        importlib.reload(massa_collision)

        # 3. CORE SYSTEMS
        importlib.reload(massa_console)  # The Brain
        importlib.reload(massa_engine)  # The Engine (aggregates sub-systems)
        importlib.reload(massa_base)  # The Muscle (inherits props + uses engine)
        importlib.reload(massa_tools)
        importlib.reload(massa_console_op)
        importlib.reload(massa_point_tool)
        importlib.reload(massa_shooter)
        importlib.reload(massa_uv_preview)

        # 4. CONTENT & UI
        # Reload individual cartridge modules before re-discovery
        if hasattr(cartridges, "MODULES"):
            for mod in cartridges.MODULES:
                importlib.reload(mod)

        importlib.reload(cartridges)
        # Re-discover after reload to pick up new/changed cartridges
        cartridges._discover()

        importlib.reload(ui_massa_panel)  # The Face
        importlib.reload(ui_massa_pie)
        importlib.reload(gizmo_massa)

        # 5. MCP BRIDGE (stop any running server before swapping the code)
        try:
            mcp_bridge.server.stop_server()
        except Exception:
            pass
        importlib.reload(mcp_bridge.server)
        importlib.reload(mcp_bridge)

        print("Massa: Reload Complete.")
    except Exception as e:
        print(f"Massa: Reload Error: {e}")


addon_keymaps = []


def register():
    # 1. Register Console (Shared Properties)
    massa_console.register()

    # Register Collision Viz
    from .modules import massa_collision

    massa_collision.register()

    # 2. Register Operators
    bpy.utils.register_class(massa_base.Massa_OT_Base)
    bpy.utils.register_class(massa_tools.MASSA_OT_Condemn)
    bpy.utils.register_class(massa_tools.MASSA_OT_Finalize_And_Inspect)
    bpy.utils.register_class(massa_point_tool.MASSA_OT_PickCoordinate)
    bpy.utils.register_class(massa_shooter.MASSA_OT_ShootDispatcher)
    bpy.utils.register_class(massa_shooter.MASSA_OT_SpawnTarget)
    bpy.utils.register_class(massa_uv_preview.MASSA_OT_UV_Preview)
    bpy.utils.register_class(massa_uv_preview.MASSA_OT_UV_Preview_Exit)

    # 3. Register Cartridges
    cartridges.register()

    # 4. Register UI
    bpy.utils.register_class(ui_massa_panel.MASSA_PT_Main)
    bpy.utils.register_class(ui_massa_pie.MASSA_MT_category_primitives)
    bpy.utils.register_class(ui_massa_pie.MASSA_MT_category_construction)
    bpy.utils.register_class(ui_massa_pie.MASSA_MT_category_architecture)
    bpy.utils.register_class(ui_massa_pie.MASSA_MT_category_buildings)
    bpy.utils.register_class(ui_massa_pie.MASSA_MT_pie_add)
    bpy.utils.register_class(gizmo_massa.MASSA_GGT_GizmoGroup)

    # 4.6 MCP Bridge operators (server itself is started explicitly by the user)
    mcp_bridge.register()

    # 5. Keymaps
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new("wm.call_menu_pie", "I", "PRESS", ctrl=True)
        kmi.properties.name = "MASSA_MT_pie_add"
        addon_keymaps.append((km, kmi))


def unregister():
    # Unregister Collision Viz
    from .modules import massa_collision

    massa_collision.unregister()

    # 0. Stop + unregister the MCP bridge (closes socket and main-thread timer)
    mcp_bridge.unregister()

    # 1. Unregister Keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # 2. Unregister UI
    bpy.utils.unregister_class(gizmo_massa.MASSA_GGT_GizmoGroup)
    bpy.utils.unregister_class(ui_massa_pie.MASSA_MT_pie_add)
    bpy.utils.unregister_class(ui_massa_pie.MASSA_MT_category_buildings)
    bpy.utils.unregister_class(ui_massa_pie.MASSA_MT_category_architecture)
    bpy.utils.unregister_class(ui_massa_pie.MASSA_MT_category_construction)
    bpy.utils.unregister_class(ui_massa_pie.MASSA_MT_category_primitives)
    bpy.utils.unregister_class(ui_massa_panel.MASSA_PT_Main)

    # 2. Unregister Cartridges
    cartridges.unregister()

    # 3. Unregister Operators
    bpy.utils.unregister_class(massa_shooter.MASSA_OT_SpawnTarget)
    bpy.utils.unregister_class(massa_shooter.MASSA_OT_ShootDispatcher)
    bpy.utils.unregister_class(massa_uv_preview.MASSA_OT_UV_Preview_Exit)
    bpy.utils.unregister_class(massa_uv_preview.MASSA_OT_UV_Preview)
    bpy.utils.unregister_class(massa_point_tool.MASSA_OT_PickCoordinate)
    bpy.utils.unregister_class(massa_tools.MASSA_OT_Finalize_And_Inspect)
    bpy.utils.unregister_class(massa_tools.MASSA_OT_Condemn)
    bpy.utils.unregister_class(massa_base.Massa_OT_Base)

    # 4. Unregister Console
    massa_console.unregister()
