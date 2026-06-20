import pkgutil
import importlib
import inspect


def run_all_auditors(obj, op_class=None, detailed=False):
    """
    Dynamically finds all scripts in this 'auditors' folder, imports them,
    and looks for a module-level entry point ``audit_mesh(obj, op_class=None)``.

    Returns:
        - ``detailed=False`` (default): a flat ``list[str]`` of flags (legacy
          contract, preserved for existing callers).
        - ``detailed=True``: ``{"flags": [...], "by_auditor": {name: [...]},
          "ran": [...], "skipped": [...]}`` so the runner can build per-auditor
          telemetry and attribute every flag to its source.
    """
    errors = []
    by_auditor = {}
    ran = []
    skipped = []
    package_path = __path__
    prefix = __name__ + "."

    # 1. Iterate over all files in the /auditors/ folder
    for _, name, _ in pkgutil.iter_modules(package_path):
        mod_flags = []
        try:
            # 2. Import the module (e.g., massa_ui_auditor)
            module = importlib.import_module(prefix + name)

            # 3. Check for the standardized entry point 'audit_mesh(obj)'
            if not (hasattr(module, 'audit_mesh') and inspect.isfunction(module.audit_mesh)):
                # No standard entry point — record it so the gap is visible in
                # telemetry instead of being silently ignored.
                skipped.append(name)
                continue

            # 4. Run the Audit
            # Expectation: audit_mesh(obj, op_class) -> list of error strings
            # We handle both signatures for backward compatibility
            sig = inspect.signature(module.audit_mesh)
            if 'op_class' in sig.parameters:
                result = module.audit_mesh(obj, op_class=op_class)
            else:
                result = module.audit_mesh(obj)

            ran.append(name)
            if result and isinstance(result, list):
                mod_flags.extend(str(r) for r in result)

        except Exception as e:
            # Prefix with CRITICAL_ + auditor name so downstream severity
            # classification flags it and the source is attributable.
            mod_flags.append(f"CRITICAL_AUDITOR_CRASH_{name}: {str(e)}")

        if mod_flags:
            by_auditor[name] = mod_flags
            errors.extend(mod_flags)

    if detailed:
        return {
            "flags": errors,
            "by_auditor": by_auditor,
            "ran": ran,
            "skipped": skipped,
        }
    return errors