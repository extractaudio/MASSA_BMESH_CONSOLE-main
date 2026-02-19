import ast
import os

target_dir = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\MASSA_BMESH_CONSOLE-main\modules\cartridges"

for root, dirs, files in os.walk(target_dir):
    for file in files:
        if not file.endswith(".py"):
            continue
            
        full_path = os.path.join(root, file)
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name) and target.id == "bl_idname":
                                    # Check value
                                    value = item.value
                                    if isinstance(value, ast.Tuple):
                                        print(f"FOUND ERROR IN: {file} :: Class {node.name}")
                                        print(f"  Line {item.lineno}: bl_idname is a TUPLE")
        except Exception as e:
            print(f"Failed to parse {file}: {e}")
