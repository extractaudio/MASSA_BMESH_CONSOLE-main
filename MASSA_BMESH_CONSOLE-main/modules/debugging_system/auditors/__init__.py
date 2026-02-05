import pkgutil
import importlib
import inspect

def run_all_auditors(obj):
    """
    Dynamically finds all scripts in this 'auditors' folder,
    imports them, and looks for a function called 'audit_mesh(obj)'.
    """
    errors = []
    package_path = __path__
    prefix = __name__ + "."

    # 1. Iterate over all files in the /auditors/ folder
    for _, name, _ in pkgutil.iter_modules(package_path):
        try:
            # 2. Import the module (e.g., massa_ui_auditor)
            module = importlib.import_module(prefix + name)

            # 3. Check for the standardized entry point 'audit_mesh(obj)'
            if hasattr(module, 'audit_mesh') and inspect.isfunction(module.audit_mesh):
                
                # 4. Run the Audit
                # Expectation: audit_mesh(obj) returns a list of error strings
                result = module.audit_mesh(obj)
                
                if result and isinstance(result, list):
                    errors.extend(result)
            
        except Exception as e:
            errors.append(f"Auditor '{name}' crashed: {str(e)}")

    return errors