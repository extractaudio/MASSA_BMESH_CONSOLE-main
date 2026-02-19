import ast
import os

target_dir = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\_Scripts"

print(f"Scanning directory: {target_dir}")
found_classes = 0
found_issues = 0

for root, dirs, files in os.walk(target_dir):
    for file in files:
        if not file.endswith(".py"):
            continue
            
        full_path = os.path.join(root, file)
        
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                tree = ast.parse(content)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check inheritance (simplified)
                    is_operator = False
                    for base in node.bases:
                        if isinstance(base, ast.Name) and (base.id == "Operator" or base.id == "Massa_OT_Base"):
                            is_operator = True
                        elif isinstance(base, ast.Attribute) and base.attr == "Operator":
                             is_operator = True
                    
                    if is_operator:
                        found_classes += 1
                        has_idname = False
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name) and target.id == "bl_idname":
                                        has_idname = True
                                        value = item.value
                                        if isinstance(value, ast.Tuple):
                                            found_issues += 1
                                            print(f"!!! ERROR: {file} :: Class {node.name}")
                                            print(f"    Line {item.lineno}: bl_idname is a TUPLE")
                                        elif isinstance(value, ast.Constant):
                                            pass
                                            # print(f"OK: {file} :: {node.name} -> {value.value}")
                                        else:
                                            print(f"WARNING: {file} :: {node.name} -> {type(value)}")
                        
                        if not has_idname:
                            print(f"WARNING: {file} :: {node.name} has NO bl_idname")

        except Exception as e:
            print(f"Failed to parse {file}: {e}")

print(f"Scan complete. Found {found_classes} Operator classes. Found {found_issues} issues.")
