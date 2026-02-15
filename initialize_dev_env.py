import os
import sys
import subprocess
import json
from pathlib import Path

"""
MASSA CONSOLE - DEVELOPMENT ENVIRONMENT INITIALIZER
---------------------------------------------------
This script prepares the workspace for:
1. Cartridge Development (Auto-completion, Linting)
2. MCP Server Execution (Dependencies)
3. Addon Architecture Integrity Checks
"""

def print_step(msg):
    print(f"\n[MASSA INIT] >>> {msg}")

def print_success(msg):
    print(f"[SUCCESS] {msg}")

def print_warn(msg):
    print(f"[WARNING] {msg}")

def find_addon_root(start_path):
    """Locates the folder containing the Blender Addon (__init__.py with bl_info)."""
    print_step("Locating Addon Core...")
    for path in start_path.rglob("__init__.py"):
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            if "bl_info" in content and "name" in content:
                print_success(f"Found Addon Core at: {path.parent}")
                return path.parent
        except Exception as e:
            continue
    return None

def install_dependencies(addon_root):
    """Installs requirements for MCP and Dev environment."""
    print_step("Installing Dependencies...")
    
    # 1. Install fake-bpy-module for Intellisense
    print("... Installing fake-bpy-module-latest (for code completion)")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fake-bpy-module-latest"])
    
    # 2. Install MCP Server Requirements
    mcp_reqs = addon_root / "MCP" / "requirements.txt"
    if mcp_reqs.exists():
        print(f"... Installing MCP requirements from {mcp_reqs.name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(mcp_reqs)])
        print_success("Dependencies installed.")
    else:
        print_warn(f"MCP requirements.txt not found at {mcp_reqs}")

def setup_vscode(root_path, addon_root):
    """Configures VS Code settings for Blender development."""
    print_step("Configuring VS Code Workspace...")
    
    vscode_dir = root_path / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    settings_path = vscode_dir / "settings.json"
    
    # Default settings for Blender Dev
    settings = {
        "python.analysis.extraPaths": [
            str(addon_root.resolve()),
            str((addon_root / "modules").resolve()),
            str((addon_root / "operators").resolve())
        ],
        "python.autoComplete.extraPaths": [
            str(addon_root.resolve())
        ],
        "files.exclude": {
            "**/*.pyc": True,
            "**/__pycache__": True
        },
        "python.analysis.typeCheckingMode": "basic"
    }
    
    # Update existing settings if they exist, otherwise create new
    if settings_path.exists():
        try:
            with open(settings_path, 'r') as f:
                current_settings = json.load(f)
                current_settings.update(settings)
                settings = current_settings
        except:
            pass
            
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=4)
        
    print_success(f"VS Code settings updated at {settings_path}")

def verify_structure(addon_root):
    """Verifies the folder structure supports Cartridge generation."""
    print_step("Verifying Architecture...")
    
    required_paths = [
        addon_root / "modules" / "cartridges",
        addon_root / "modules" / "cartridges" / "__init__.py",
        addon_root / "MCP" / "server.py",
        addon_root / "operators" / "massa_base.py"
    ]
    
    all_good = True
    for p in required_paths:
        if not p.exists():
            print_warn(f"Missing critical component: {p.name}")
            all_good = False
    
    if all_good:
        print_success("Architecture Integrity: 100%. Ready for Cartridge Forging.")
    else:
        print_warn("Some components are missing. Check the repository structure.")

def main():
    root_path = Path(__file__).parent
    addon_root = find_addon_root(root_path)
    
    if not addon_root:
        print("[ERROR] Could not find the MASSA Addon folder (looking for __init__.py with bl_info).")
        return

    install_dependencies(addon_root)
    setup_vscode(root_path, addon_root)
    verify_structure(addon_root)
    
    print("\n[MASSA INIT] >>> Initialization Complete.")
    print("You can now open this folder in VS Code and begin forging cartridges.")

if __name__ == "__main__":
    main()