import json
import os
import sys

def update_json_file(file_path, new_config):
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Read existing config or create empty
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {file_path} contains invalid JSON. Overwriting.")
            config = {}
    else:
        config = {}

    # Update mcpServers
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    config["mcpServers"]["blender"] = new_config

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    print(f"Updated {file_path}")

def main():
    mcp_dir = r"d:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\_MCP"
    
    new_config = {
        "command": "uv",
        "args": [
            "run",
            "--project",
            mcp_dir,
            "massa-blender-mcp"
        ],
        "env": {
            "BLENDER_MCP_HOST": "localhost",
            "BLENDER_MCP_PORT": "9876"
        }
    }

    # Claude Code (Codex) config
    claude_code_path = os.path.expanduser("~/.claude.json")
    update_json_file(claude_code_path, new_config)

    # Claude Desktop config
    appdata = os.environ.get('APPDATA', '')
    if appdata:
        claude_desktop_path = os.path.join(appdata, "Claude", "claude_desktop_config.json")
        update_json_file(claude_desktop_path, new_config)
    else:
        print("Warning: APPDATA environment variable not found. Skipping Claude Desktop config.")

    _check_bridge()
    _print_next_steps()


def _check_bridge():
    """Best-effort liveness check against the Blender-side MCP bridge."""
    host = os.environ.get("BLENDER_MCP_HOST", "localhost")
    port = int(os.environ.get("BLENDER_MCP_PORT", "9876"))
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2.0)
            sock.connect((host, port))
            sock.sendall((json.dumps({"type": "ping"}) + "\0").encode("utf-8"))
            buf = bytearray()
            while b"\0" not in buf:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf.extend(chunk)
        line, _sep, _rest = buf.partition(b"\0")
        resp = json.loads(line.decode("utf-8")) if line else {}
        result = resp.get("result", {}) if isinstance(resp, dict) else {}
        print(f"MCP bridge: REACHABLE at {host}:{port} "
              f"(Blender {result.get('blender_version')}, "
              f"MASSA loaded: {result.get('massa_loaded')})")
    except OSError:
        print(f"MCP bridge: NOT reachable at {host}:{port} (this is expected if "
              f"Blender isn't running yet).")


def _print_next_steps():
    print()
    print("Next steps (one-step bridge — no separate upstream addon needed):")
    print("  1. Launch Blender 5.x with the MASSA addon enabled.")
    print("  2. In the 3D View 'Massa' side panel, click 'Start' next to 'MCP Server'")
    print("     (or run the operator bpy.ops.massa.mcp_bridge_start()).")
    print("  3. Re-run this check or call the 'blender_ping' MCP tool to confirm.")


if __name__ == "__main__":
    main()
