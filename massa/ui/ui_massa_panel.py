import bpy
from ..modules.cartridges import MODULES
# We import ui_shared locally inside draw to avoid circular dependencies during registration


class MASSA_PT_Main(bpy.types.Panel):
    bl_label = "Massa Console"
    bl_idname = "MASSA_PT_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Massa"

    def draw(self, context):
        layout = self.layout
        console = context.scene.massa_console  # Access state properties
        obj = context.active_object
        
        # Helper to draw buttons safely
        def draw_safe_button(col_layout, mod_data):
            meta = mod_data.CARTRIDGE_META
            op_name = f"massa.gen_{meta['id']}"
            icon_name = meta.get("icon", "MESH_CUBE")

            try:
                # Attempt to draw with the requested icon
                col_layout.operator(
                    op_name,
                    text=meta["name"],
                    icon=icon_name,
                )
            except TypeError:
                # Fallback if icon is invalid (prevents UI crash)
                print(f"MASSA WARNING: Invalid icon '{icon_name}' in {meta['id']}")
                col_layout.operator(
                    op_name,
                    text=f"{meta['name']} (Icon Error)",
                    icon="QUESTION",
                )

        # --- MODE TOGGLE ---
        row = layout.row()
        row.prop(console, "massa_op_mode", expand=True)
        layout.separator()

        # [ARCHITECT UI UPDATE] High-Priority Actions (Resurrect/Condemn)
        # Always drawn — poll() on each operator handles the disabled/greyed state
        # when no Massa object is active.
        # Resurrect uses DYNAMIC DISPATCH: at draw time we read the active object's
        # stored bl_idname (`massa_op_id`) and wire the button directly to that
        # cartridge operator with `rerun_mode=True`. This makes the cartridge the
        # top-level invocation, which (a) actually fires its invoke() in a real
        # UI context and (b) registers it as the Redo Panel (F9) last operator.
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 1.2

        # Resurrect — dynamic per-object dispatch
        row = col.row()
        row.alert = True
        row.scale_y = 1.2

        op_id = obj.get("massa_op_id") if obj else None
        if op_id:
            try:
                op_props = row.operator(op_id, text="Resurrect Selected", icon="FILE_REFRESH")
                op_props.rerun_mode = True
            except Exception:
                # op_id refers to an uninstalled/renamed cartridge — show disabled placeholder
                sub = row.row()
                sub.enabled = False
                sub.label(text="Resurrect (invalid id)", icon="ERROR")
        else:
            # No Massa object active — greyed-out placeholder
            sub = row.row()
            sub.enabled = False
            sub.label(text="Resurrect Selected", icon="FILE_REFRESH")

        # Condemn — unchanged (works via standard operator dispatch)
        col.separator(factor=0.5)
        col.operator("massa.condemn", text="Condemn (Finalize)", icon="CHECKMARK")
        col.operator("massa.uv_preview", text="UV Preview", icon="UV")
        layout.separator()

        if console.massa_op_mode == 'ACTIVE':
            # --- 1. PRIMITIVES GROUP ---
            box = layout.box()
            row = box.row()
            icon = "TRIA_DOWN" if console.ui_expand_prims else "TRIA_RIGHT"
            row.prop(console, "ui_expand_prims", icon=icon, text="Primitives", emboss=False)

            if console.ui_expand_prims:
                # [ARCHITECT] align=False decouples buttons so they don't share borders (prevents glitching)
                col = box.column(align=False)
                col.scale_y = 1.4  # Good height for clicking
                for mod in MODULES:
                    meta = mod.CARTRIDGE_META
                    if meta["id"].startswith("prim_") and not meta["id"].startswith("prim_con"):
                        draw_safe_button(col, mod)
                        # [ARCHITECT] Non-destructive bottom padding between buttons
                        col.separator(factor=0.1)

            layout.separator()

            # --- 1.5 PRIMITIVES : CONSTRUCTION GROUP ---
            box = layout.box()
            row = box.row()
            icon = "TRIA_DOWN" if console.ui_expand_prim_con else "TRIA_RIGHT"
            row.prop(
                console,
                "ui_expand_prim_con",
                icon=icon,
                text="Primitives : Construction",
                emboss=False,
            )

            if console.ui_expand_prim_con:
                col = box.column(align=False)
                col.scale_y = 1.4
                for mod in MODULES:
                    meta = mod.CARTRIDGE_META
                    if meta["id"].startswith("prim_con"):
                        draw_safe_button(col, mod)
                        col.separator(factor=0.1)

            layout.separator()

            # --- 2. ARCHITECTURE GROUP ---
            box = layout.box()
            row = box.row()
            icon = "TRIA_DOWN" if console.ui_expand_arch else "TRIA_RIGHT"
            row.prop(
                console, "ui_expand_arch", icon=icon, text="Architecture", emboss=False
            )

            if console.ui_expand_arch:
                col = box.column(align=False)
                col.scale_y = 1.4
                for mod in MODULES:
                    meta = mod.CARTRIDGE_META
                    if meta["id"].startswith("arch_"):
                        draw_safe_button(col, mod)
                col.separator(factor=0.1)

            layout.separator()

            # --- 3. BUILDINGS/MISC GROUP ---
            box = layout.box()
            row = box.row()
            icon = "TRIA_DOWN" if console.ui_expand_builds else "TRIA_RIGHT"
            row.prop(
                console,
                "ui_expand_builds",
                icon=icon,
                text="Buildings / Other",
                emboss=False,
            )

            if console.ui_expand_builds:
                col = box.column(align=False)
                col.scale_y = 1.4
                for mod in MODULES:
                    meta = mod.CARTRIDGE_META
                    # Logic: Anything that is NOT prim_ and NOT arch_
                    if not meta["id"].startswith("prim_") and not meta["id"].startswith(
                        "arch_"
                    ):
                        draw_safe_button(col, mod)
                        col.separator(factor=0.1)

            layout.separator()

            # --- 4. REGENERATE BUTTON (The Shadow Panel) ---
            # [ARCHITECT] (Moved to Top)
            pass

        elif console.massa_op_mode == 'POINT_SHOOT':
            # --- POINT & SHOOT UI ---
            box = layout.box()
            box.label(text="Targeting", icon="VIEW3D")

            # Cartridge Selector
            box.prop(console, "massa_staged_cartridge")

            # Target Coordinate
            row = box.row(align=True)
            row.prop(console, "massa_target_coord", text="Target")
            row.operator("massa.pick_coordinate", icon="EYEDROPPER", text="")
            # [ARCHITECT NEW] Spawn Target Button
            row.operator("massa.spawn_target", icon="EMPTY_AXIS", text="")

            layout.separator()

        # --- 5. REDO PANEL LOGIC LINK ---
        # Allows configuring global defaults (Edge Slots, etc.) without running an operator.
        # We import ui_shared here to access the draw functions
        from . import ui_shared

        # Draw the Nav Bar using the Console properties
        # This will update the 'ui_tab' on the Scene object
        col = ui_shared.draw_nav_bar(layout, console)

        # Draw content based on Console's active tab
        # Note: We rely on 'ui_tab' being present in Massa_Console_Props
        if console.ui_tab == "EDGES":
            ui_shared.draw_edge_slots_tab(col, console)

        elif console.ui_tab == "SHAPE":
            if console.massa_op_mode == 'ACTIVE':
                col.label(text="Shape parameters are specific to", icon="INFO")
                col.label(text="the active operator.", icon="BLANK1")
            else:
                 # In Point & Shoot, show global transform params from mixin
                 col.label(text="Global Transform", icon="OBJECT_ORIGIN")
                 col.prop(console, "global_scale")
                 col.prop(console, "pivot_mode")
                 col.prop(console, "ui_use_rot", toggle=True)
                 if console.ui_use_rot:
                     col.prop(console, "rotation")

                 # [ARCHITECT NEW] Render Staged Cartridge Parameters
                 cart_id = console.massa_staged_cartridge
                 if cart_id:
                     safe_id = cart_id.replace(".", "_").replace("-", "_")
                     prop_name = f"props_{safe_id}"
                     pg = getattr(console, prop_name, None)

                     if pg:
                         found_mod = None
                         for mod in MODULES:
                              if mod.CARTRIDGE_META["id"] == cart_id:
                                  found_mod = mod
                                  break

                         if found_mod:
                             col.separator()
                             col.label(text=found_mod.CARTRIDGE_META.get("name", "Parameters"), icon="MODIFIER")

                             from ..operators.massa_base import Massa_OT_Base
                             op_class = None
                             for name, obj in found_mod.__dict__.items():
                                if isinstance(obj, type) and issubclass(obj, Massa_OT_Base) and obj != Massa_OT_Base:
                                    op_class = obj
                                    break

                             if op_class and hasattr(op_class, "draw_shape_ui"):
                                 try:
                                     op_class.draw_shape_ui(pg, col)
                                 except Exception as e:
                                     col.label(text=f"UI Error: {e}", icon="ERROR")

        elif console.ui_tab == "POLISH":
            ui_shared.draw_polish_tab(col, console)

        elif console.ui_tab == "DATA":
            # Pass empty slot names as we aren't in an operator context
            ui_shared.draw_data_tab(col, console, slot_names={})

        elif console.ui_tab == "UVS":
            ui_shared.draw_uvs_tab(col, console, slot_names={}, stats=None)

        elif console.ui_tab == "SLOTS":
            ui_shared.draw_slots_tab(col, console, slot_names={}, stats=None)

        elif console.ui_tab == "COLLISION":
            ui_shared.draw_collision_tab(col, console, slot_names={})

        elif console.ui_tab == "SOCKETS":
            ui_shared.draw_sockets_ui(col, console)

        layout.separator()

        if console.massa_op_mode == 'POINT_SHOOT':
             # SHOOT BUTTON
             row = layout.row()
             row.scale_y = 2.0
             row.operator("massa.shoot_dispatcher", text="SHOOT", icon="PLAY")
        else:
            row = layout.row()
            row.alignment = "CENTER"
            row.label(text="Parameters also available in F9", icon="INFO")
