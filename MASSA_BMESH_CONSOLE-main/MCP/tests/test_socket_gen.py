import socket
import json

HOST = '127.0.0.1'
PORT = 5555

payload = {
    "skill": "test_generator_ui",
    "params": {
        "cartridge_id": "prim_04_panel",
        "creation_params": {"cuts_x": 2, "cuts_y": 2},
        "modification_params": {"cuts_x": 6, "cuts_y": 6}
    }
}

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(json.dumps(payload).encode('utf-8'))
        
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk: break
            data += chunk
            
        print("Response:", data.decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
