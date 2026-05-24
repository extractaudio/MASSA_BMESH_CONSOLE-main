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

if __name__ == "__main__":
    main()
