
import sys
import os
import json
import io
from unittest.mock import MagicMock

# 1. Setup Path to find 'core' & 'skills'
# Current: MCP/tests/verify_scene_file_gen.py
# Root:    MCP/
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# 2. Mock core.bridge_client
# We need to mock this BEFORE importing scene_creator
sys.modules['core'] = MagicMock()
sys.modules['core.bridge_client'] = MagicMock()
mock_send = MagicMock(return_value={"status": "sent"})
sys.modules['core.bridge_client'].send_bridge = mock_send

# 3. Import scene_creator
from skills.scene_creator import create_scene

def test_file_generation():
    print("Testing create_scene file generation...")
    
    layout = [
        {"type": "PRIMITIVE", "id": "cube", "name": "Test_Cube"}
    ]
    
    # Run Function
    result = create_scene(layout, audit=False)
    
    # 4. Verification
    # Check if send_bridge was called with 'filepath'
    if not mock_send.called:
        print("FAIL: send_bridge was not called")
        return
        
    call_args = mock_send.call_args
    skill_name = call_args[0][0]
    payload = call_args[0][1]
    
    print(f"Skill Called: {skill_name}")
    print(f"Payload Keys: {payload.keys()}")
    
    if "filepath" not in payload:
        print("FAIL: 'filepath' missing from payload")
        return
        
    filepath = payload["filepath"]
    print(f"Filepath generated: {filepath}")
    
    if not os.path.exists(filepath):
        print("FAIL: File does not exist on disk")
        return
        
    # Read Content
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    if "layout" in data and len(data["layout"]) == 1:
        print("SUCCESS: JSON content verified.")
    else:
        print(f"FAIL: JSON content mismatch: {data}")

    # Cleanup
    try:
        os.remove(filepath)
        print("Cleanup: File removed.")
    except:
        pass

if __name__ == "__main__":
    test_file_generation()
