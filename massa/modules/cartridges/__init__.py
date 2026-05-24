import bpy
import importlib
import pkgutil
import pathlib
import inspect

# -------------------------------------------------------------------
# AUTO-DISCOVERY CARTRIDGE LOADER
# -------------------------------------------------------------------
# Scans this directory for .py files containing CARTRIDGE_META and
# a Massa_OT_Base subclass. No manual registration needed - just
# drop a cartridge file in this folder and reload.
# -------------------------------------------------------------------

MODULES = []
CLASSES = []

# Required keys in CARTRIDGE_META for validation
_REQUIRED_META_KEYS = {"name", "id", "icon", "flags"}


def _discover():
    """
    Auto-discovers all cartridge modules in this package directory.
    Validates each cartridge against the Cartridge Mandate.
    """
    global MODULES, CLASSES
    MODULES = []
    CLASSES = []

    from ...operators.massa_base import Massa_OT_Base

    pkg_dir = pathlib.Path(__file__).parent

    for finder, name, is_pkg in pkgutil.iter_modules([str(pkg_dir)]):
        if name.startswith("__"):
            continue

        try:
            mod = importlib.import_module(f".{name}", __package__)
        except Exception as e:
            file_path = pkg_dir / f"{name}.py"
            raise RuntimeError(
                f"Massa Cartridge: Failed to import '{file_path}': {e}"
            ) from e

        # Must have CARTRIDGE_META
        if not hasattr(mod, "CARTRIDGE_META"):
            continue

        meta = mod.CARTRIDGE_META

        # Validate required keys
        missing = _REQUIRED_META_KEYS - set(meta.keys())
        if missing:
            print(
                f"Massa Cartridge Warning: '{pkg_dir / (name + '.py')}' missing meta keys: {missing}"
            )

        # Find the operator class (subclass of Massa_OT_Base, not Base itself)
        op_cls = None
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (
                inspect.isclass(attr)
                and issubclass(attr, Massa_OT_Base)
                and attr is not Massa_OT_Base
                and hasattr(attr, "bl_idname")
            ):
                op_cls = attr
                break

        if op_cls is None:
            print(f"Massa Cartridge Warning: '{name}' has CARTRIDGE_META but no operator class")
            continue

        # Validate mandate requirements
        if not hasattr(op_cls, "build_shape"):
            raise RuntimeError(
                f"Massa Cartridge: '{pkg_dir / (name + '.py')}' missing build_shape()"
            )
        if not hasattr(op_cls, "get_slot_meta"):
            raise RuntimeError(
                f"Massa Cartridge: '{pkg_dir / (name + '.py')}' missing get_slot_meta()"
            )

        MODULES.append(mod)
        CLASSES.append(op_cls)

    print(f"Massa: Discovered {len(MODULES)} cartridges")


# Run discovery on import
_discover()


# -------------------------------------------------------------------
# REGISTRATION HANDLERS
# -------------------------------------------------------------------

def register():
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass  # Already registered
        except RuntimeError as e:
            print(f"Massa Error: Could not register {cls.__name__}: {e}")


def unregister():
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
