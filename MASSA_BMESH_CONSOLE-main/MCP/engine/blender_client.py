import socket
import json
from ..config import settings

def send_bridge(skill, params=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((settings.HOST, settings.BRIDGE_PORT))
            payload = json.dumps({"skill": skill, "params": params or {}})
            s.sendall(payload.encode('utf-8'))
            
            # Read response
            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                chunks.append(chunk)
            
            if not chunks:
                return {"status": "error", "msg": "Empty response from Blender"}
                
            return json.loads(b"".join(chunks).decode('utf-8'))
    except ConnectionRefusedError:
        return {"status": "error", "msg": "Bridge unreachable. Is Blender running?"}
    except Exception as e:
        return {"status": "error", "msg": f"Bridge Communication Error: {str(e)}"}
