import socket
import json
import os

BRIDGE_PORT = 5555

def send_bridge(skill: str, params: dict = None) -> dict:
    """
    Sends a command to the Blender MCP Bridge via socket.
    Used for tools that need to interact with the LIVE Blender session.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', BRIDGE_PORT))
            payload = json.dumps({"skill": skill, "params": params or {}})
            s.sendall(payload.encode('utf-8'))
            
            # Read response
            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                chunks.append(chunk)
            
            if not chunks:
                 return {"status": "error", "msg": "Empty response from bridge"}

            return json.loads(b"".join(chunks).decode('utf-8'))
    except ConnectionRefusedError:
        return {"status": "error", "msg": "Bridge unreachable. Is Blender running and MCP Bridge Active?"}
    except Exception as e:
        return {"status": "error", "msg": f"Bridge Communication Error: {str(e)}"}
