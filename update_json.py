import json
import os
import sys

def append_objects(new_objects):
    file_path = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\object_logic.json"
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Check for duplicates by name
    existing_names = {obj.get('name') for obj in data}
    
    added_count = 0
    for obj in new_objects:
        if obj.get('name') not in existing_names:
            data.append(obj)
            existing_names.add(obj.get('name'))
            added_count += 1
            
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Successfully added {added_count} new objects. Total count: {len(data)}")

if __name__ == "__main__":
    # Expecting a temp file path with the new json data as the first argument
    # because passing huge json string in command line is risky
    if len(sys.argv) > 1:
        temp_file = sys.argv[1]
        with open(temp_file, 'r') as f:
            new_items = json.load(f)
        append_objects(new_items)
