import bpy
from ..modules.cartridges import MODULES


def draw_safe_button(layout, mod_data):
    meta = mod_data.CARTRIDGE_META
    op_name = f"massa.gen_{meta['id']}"
    icon_name = meta.get("icon", "MESH_CUBE")

    try:
        # Attempt to draw with the requested icon
        layout.operator(
            op_name,
            text=meta["name"],
            icon=icon_name,
        )
    except TypeError:
        # Fallback if icon is invalid (prevents UI crash)
        layout.operator(
            op_name,
            text=f"{meta['name']} (Icon Error)",
            icon="QUESTION",
        )


class MASSA_MT_category_primitives(bpy.types.Menu):
    bl_label = "Primitives"
    bl_idname = "MASSA_MT_category_primitives"

    def draw(self, context):
        layout = self.layout
        for mod in MODULES:
            meta = mod.CARTRIDGE_META
            if meta["id"].startswith("prim_") and not meta["id"].startswith("prim_con"):
                draw_safe_button(layout, mod)


class MASSA_MT_category_construction(bpy.types.Menu):
    bl_label = "Primitives : Construction"
    bl_idname = "MASSA_MT_category_construction"

    def draw(self, context):
        layout = self.layout
        for mod in MODULES:
            meta = mod.CARTRIDGE_META
            if meta["id"].startswith("prim_con"):
                draw_safe_button(layout, mod)


class MASSA_MT_category_architecture(bpy.types.Menu):
    bl_label = "Architecture"
    bl_idname = "MASSA_MT_category_architecture"

    def draw(self, context):
        layout = self.layout
        for mod in MODULES:
            meta = mod.CARTRIDGE_META
            if meta["id"].startswith("arch_"):
                draw_safe_button(layout, mod)


class MASSA_MT_category_buildings(bpy.types.Menu):
    bl_label = "Buildings / Other"
    bl_idname = "MASSA_MT_category_buildings"

    def draw(self, context):
        layout = self.layout
        for mod in MODULES:
            meta = mod.CARTRIDGE_META
            # Logic: Anything that is NOT prim_ and NOT arch_
            if not meta["id"].startswith("prim_") and not meta["id"].startswith("arch_"):
                draw_safe_button(layout, mod)


class MASSA_MT_pie_add(bpy.types.Menu):
    bl_label = "Massa Pie"
    bl_idname = "MASSA_MT_pie_add"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # West: Primitives
        pie.menu("MASSA_MT_category_primitives", icon="MESH_CUBE")

        # East: Construction
        pie.menu("MASSA_MT_category_construction", icon="MOD_BUILD")

        # South: Buildings/Other
        pie.menu("MASSA_MT_category_buildings", icon="COMMUNITY")

        # North: Architecture
        pie.menu("MASSA_MT_category_architecture", icon="ARCH_VIS")
