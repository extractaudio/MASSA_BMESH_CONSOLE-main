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
        # [ARCHITECT] This allows re-running the logic on the selected object
        # using the CURRENT settings in the Brain (Sidebar).
        if obj and "massa_op_id" in obj:
            box = layout.box()
            col = box.column(align=True)
            col.scale_y = 1.2

            # [ARCHITECT NEW] Resurrection Logic
            # Directly call the original operator with rerun_mode=True
            # This triggers the specific operator (e.g. Box), allowing the Redo Panel to appear.
            op_id = obj["massa_op_id"]
            try:
                # [ARCHITECT UDPATE] Red Alert Button for Resurrection
                row = col.row()
                row.alert = True
                row.scale_y = 1.2
                op = row.operator(
                    op_id, text="Resurrect Selected", icon="FILE_REFRESH"
                )
                op.rerun_mode = True

                # [ARCHITECT UPDATE] Condemn (Finalize) Button
                col.separator(factor=0.5)
                col.operator("massa.condemn", text="Condemn (Finalize)", icon="CHECKMARK")
            except Exception:
                col.label(text="Unknown Operator", icon="ERROR")

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
            col.label(text="Shape parameters are specific to", icon="INFO")
            col.label(text="the active operator.", icon="BLANK1")

        elif console.ui_tab == "POLISH":
            ui_shared.draw_polish_tab(col, console)

        elif console.ui_tab == "DATA":
            # Pass empty slot names as we aren't in an operator context
            ui_shared.draw_data_tab(col, console, slot_names={})

        elif console.ui_tab == "UVS":
            ui_shared.draw_uvs_tab(col, console, slot_names={}, stats=None)

        elif console.ui_tab == "SLOTS":
            ui_shared.draw_slots_tab(col, console, slot_names={}, stats=None)

        # --- 6. MCP BRIDGE ---
        layout.separator()
        box = layout.box()
        box.label(text="System", icon="PREFERENCES")
        box.operator("massa.start_mcp_server", text="Start MCP Bridge", icon="URL")

        layout.separator()
        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="Parameters also available in F9", icon="INFO")
