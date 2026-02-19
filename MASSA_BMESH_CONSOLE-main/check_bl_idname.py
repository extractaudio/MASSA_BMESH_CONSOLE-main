import os
import ast

def check_file(filepath):
    print(f"Scanning {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == 'bl_idname':
                            # Check if value is a string (Constant/Str)
                            value = item.value
                            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                                # Correct
                                pass
                            elif isinstance(value, ast.Str): # Start form python 3.8
                                # Correct
                                pass
                            else:
                                print(f"POTENTIAL ISSUE in {filepath}: bl_idname is {type(value)}")
                                if isinstance(value, ast.Tuple):
                                    print(f"  -> Found Tuple at line {item.lineno}")

scan_dir = 'modules/cartridges'
for root, dirs, files in os.walk(scan_dir):
    for file in files:
        if file.endswith('.py'):
            check_file(os.path.join(root, file))
