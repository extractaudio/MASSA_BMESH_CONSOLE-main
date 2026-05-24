# Massa Blender MCP — Setup Guide

A fork of the official [Blender Lab MCP server](https://projects.blender.org/lab/blender_mcp)
extended with Massa-specific tools for materials, cartridges, Geometry Nodes, slot tagging,
mesh operations, and scene management.

---

## Architecture

```
Claude Code / Claude Desktop / Antigravity
        │  MCP protocol (stdio or HTTP)
        ▼
  _MCP/blmcp  ← THIS server (FastMCP, Python)
        │  TCP socket — port 9876
        ▼
  Blender addon  (lab_blender_org/mcp)
        │
        ▼
  bpy runtime  →  Massa addon
```

The server does **not** embed Blender — it only sends Python code to a running
Blender instance that has the MCP addon enabled. The Massa addon must also be
installed in that Blender.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python ≥ 3.10 | Bundled with most systems; use `python --version` to check |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Fast Python package manager — `pip install uv` or see link |
| Blender 4.x / 5.x | With the MCP addon enabled (see below) |
| Massa addon | Installed and enabled in Blender |

---

## Step 1 — Enable the Blender MCP Addon

1. Open Blender → **Edit → Preferences → Add-ons**
2. Search for **"MCP"** or **"Blender Lab MCP"**
3. Enable it ✓
4. In the addon preferences, click **Start Server** (or it auto-starts on launch)
5. Confirm the server is running on `localhost:9876`

> The addon is installed from the Blender Extensions platform:
> `Edit → Preferences → Get Extensions → search "MCP"`

---

## Step 2 — Install the MCP Server Package

From this directory (`_MCP/`):

```bash
# Recommended: use uv (creates an isolated .venv automatically)
uv sync

# Or with plain pip into a venv
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -e .
```

Verify it works:

```bash
uv run massa-blender-mcp --help
# Should print: "MCP server for Blender."
```

---

## Step 3 — Register as an MCP Server

### Claude Code (CLI)

Add to `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "C:/Users/extra/OneDrive/Documents/vscode projects/Massa_Mesh/MASSA_BMESH_CONSOLE-main/_MCP",
        "massa-blender-mcp"
      ],
      "env": {
        "BLENDER_MCP_HOST": "localhost",
        "BLENDER_MCP_PORT": "9876"
      }
    }
  }
}
```

> **Tip:** If you already have the official Blender extension installed in Claude Desktop,
> disable it (Extensions panel) before enabling this fork — they both claim the same
> `mcp__blender__*` namespace and will conflict.

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "C:/Users/extra/OneDrive/Documents/vscode projects/Massa_Mesh/MASSA_BMESH_CONSOLE-main/_MCP",
        "massa-blender-mcp"
      ]
    }
  }
}
```

Config file locations:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:**   `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:**   `~/.config/Claude/claude_desktop_config.json`

### Antigravity / Custom Agent Harness

If your harness reads an MCP config file, add the same block as above.
For HTTP transport (e.g. llama.cpp web UI or a remote agent):

```bash
uv run --project /path/to/_MCP massa-blender-mcp --transport http --host 0.0.0.0 --port 8100
```

Then register as:
```json
{
  "mcpServers": {
    "blender": {
      "type": "http",
      "url": "http://localhost:8100/"
    }
  }
}
```

### VS Code / Cursor / Windsurf

Add to `.vscode/mcp.json` in your workspace (or user `settings.json`):

```json
{
  "mcp": {
    "servers": {
      "blender": {
        "type": "stdio",
        "command": "uv",
        "args": [
          "run",
          "--project",
          "${workspaceFolder}/_MCP",
          "massa-blender-mcp"
        ]
      }
    }
  }
}
```

---

## Step 4 — Verify Connection

With Blender running and the MCP addon active, ask your agent:

```
List all Massa cartridges
```

Expected response: a JSON list of cartridge names, ids, and flags.

If you get a connection error, check:
1. Blender is open and the MCP addon server is started
2. Port `9876` is not blocked by a firewall
3. The `BLENDER_MCP_PORT` env var matches what the addon is using

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `BLENDER_MCP_HOST` | `localhost` | Hostname of the Blender addon socket |
| `BLENDER_MCP_PORT` | `9876` | Port of the Blender addon socket |
| `BLENDER_PATH` | `blender` | Path to Blender executable (CLI tools only) |

---

## Tool Reference

### Original Blender Tools (upstream)

| Tool | Description |
|---|---|
| `execute_blender_code` | Run arbitrary Python in Blender |
| `get_objects_summary` | Scene collection + object hierarchy |
| `get_object_detail_summary` | Detailed single-object info |
| `get_screenshot_of_window_as_image` | Screenshot the Blender window |
| `get_screenshot_of_area_as_image` | Screenshot a specific area |
| `get_screenshot_of_window_as_json` | Window screenshot as JSON data |
| `render_viewport_to_path` | Render viewport to file |
| `render_thumbnail_to_path` | Render thumbnail to file |
| `jump_to_tab_by_name` | Switch UI tab by name |
| `jump_to_tab_by_space_type` | Switch UI tab by space type |
| `jump_to_view3d_object_by_name` | Focus viewport on object |
| `jump_to_view3d_object_data_by_name` | Focus on object data |
| `search_api_docs` | Search Blender Python API docs |
| `search_manual_docs` | Search Blender user manual |
| `get_python_api_docs` | Fetch specific API docs |
| `get_blendfile_summary_*` | Various .blend file summaries |

### Massa Tools (this fork)

#### Materials (`massa_materials.py`)
| Tool | Description |
|---|---|
| `list_massa_material_presets` | List all MASTER_MAT_DB preset names |
| `assign_massa_material` | Assign a preset to an object slot |
| `get_object_materials` | Inspect an object's material slots |

#### Cartridges (`massa_cartridges.py`)
| Tool | Description |
|---|---|
| `list_massa_cartridges` | Discover all registered cartridges |
| `get_cartridge_parameters` | List operator properties for a cartridge |
| `run_massa_cartridge` | Generate a parametric mesh from a cartridge |
| `rerun_massa_cartridge` | Re-execute cartridge on existing object (live edit) |

#### Geometry Nodes (`massa_geonode.py`)
| Tool | Description |
|---|---|
| `list_geonode_groups` | All GN groups in the blend with input schemas |
| `apply_geonode_modifier` | Add a GN modifier with named input values |
| `set_geonode_input` | Update a single input on an existing modifier |
| `get_geonode_modifier_state` | Read current input values from a GN modifier |

#### Node Graphs / NodeToPython (`ntp_graphs.py`)
| Tool | Description |
|---|---|
| `ntp_list_graphs` | List material, Geometry Nodes, shader, compositor, world, light, and line-style node graphs |
| `ntp_snapshot_graph` | Export one graph to NodeToPython Python code; registers vendored NodeToPython on first use |
| `ntp_analyze_graph` | Read structural stats, orphan/dead-end nodes, broken links, outputs, and group dependencies |
| `ntp_inspect_node` | Inspect one node's sockets, links, default values, and readable RNA properties |

NodeToPython v4.1.0 is vendored under `_MCP/vendor/NodeToPython/`, so no extra
install step is required. To refresh the vendored source, run:

```bash
uv run --project _MCP python _Scripts/vendor_nodetopython.py
```

#### geonodes Design Material + Runtime (`geonodes_tools.py`)
| Tool | Description |
|---|---|
| `geonodes_list_demos` | List vendored geonodes demo scripts with descriptions, sizes, line counts, and inferred tags |
| `geonodes_get_demo` | Read a full demo source file, its module docstring, and related demos |
| `geonodes_list_types` | Enumerate public geonodes classes grouped by geometry, socket, domain, and control-flow roles |
| `geonodes_get_type_doc` | Read the markdown reference for a geonodes type such as `Float`, `Mesh`, or `Vector` |
| `geonodes_search` | Search demos, docs, and core source with line context and enclosing function/class hints |
| `geonodes_execute_script` | Execute a geonodes script inside Blender and report newly created node groups/materials |

geonodes is vendored under `_MCP/vendor/geonodes/`, with the pinned upstream
commit recorded in `_MCP/vendor/geonodes/.vendored_commit`. To refresh it, run:

```bash
uv run --project _MCP python _Scripts/vendor_geonodes.py
```

##### Learning Patterns

For node creation work, start with `geonodes_search` to find a matching pattern,
read the most relevant demo with `geonodes_get_demo`, check type specifics with
`geonodes_get_type_doc`, adapt the script, then call `geonodes_execute_script`.

#### Mesh Ops (`massa_mesh_ops.py`)
| Tool | Description |
|---|---|
| `mesh_boolean` | Add DIFFERENCE, UNION, INTERSECT, SLASH, INSET, or KNIFE boolean-style operations; prefers live HardOps operators and falls back to native Boolean modifiers where Blender supports them |
| `mesh_clean` | Clean mesh topology with per-call merge, dissolve, degenerate, and interior-face settings; prefers HardOps `view3d.clean_mesh` and restores HardOps preferences after the call |
| `apply_modifiers` | Deterministically apply native Blender modifiers, with an option to keep the last Bevel and Weighted Normal modifiers |
| `apply_transform` | Apply object location, rotation, and scale transforms |

HardOps is detected from the **running Blender instance**, not from the vendored
source tree. If `bpy.ops.hops.slash` or `bpy.ops.view3d.clean_mesh` is unavailable,
the tools automatically use the native fallback and report `used_hardops=False`.
The vendored `_MCP/vendor/HOps/` copy is source reference only.

#### Slots (`massa_slots.py`)
| Tool | Description |
|---|---|
| `get_slot_manifest` | Material + UV + physics slot info for a Massa object |
| `tag_faces_to_slot` | Assign faces to a slot (by index or normal direction) |
| `set_edge_slot_action` | Set SEAM/SHARP/CREASE/BEVEL on an edge slot |

#### Scene (`massa_scene.py`)
| Tool | Description |
|---|---|
| `list_massa_objects` | All Massa-generated objects with op_id + params |
| `get_massa_console_state` | Read the Massa console property bag |
| `set_massa_console_property` | Write a Massa console property |
| `get_object_massa_params` | Full MASSA_PARAMS snapshot for an object |
| `align_massa_objects_to_grid` | Space objects evenly along an axis |

---

## Adding New Tools

Each tool is a single Python file in `_MCP/blmcp/tools/`.
The server **auto-discovers** any file with a `register(mcp)` function — no registration
table to update.

Minimal template:

```python
# blmcp/tools/my_tool.py
__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="My Tool", destructiveHint=True))
    def my_tool(param: str) -> dict[str, object]:
        """One-line description shown to the agent."""
        code = f"""
import bpy
# ... your bpy code here ...
result = {{"status": "ok", "param": "{param}"}}
"""
        return send_code(code, strict_json=True)
```

Then restart the MCP server process — the new tool appears immediately.

---

## Updating from Upstream

The upstream source lives at:
`https://projects.blender.org/lab/blender_mcp`

To pull upstream fixes without losing Massa tools:

```bash
# In _MCP/ — overwrite only the non-Massa tool files
# (massa_*.py files are safe; they are not in upstream)
git diff --name-only HEAD origin/main | grep -v "massa_" | xargs git checkout origin/main --
uv sync
```

Or simply re-run the fork script (`_Scripts/` directory) when a new upstream version ships.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ConnectionRefusedError` on port 9876 | Start the MCP server in Blender (addon preferences) |
| `Massa addon not found` | Enable the Massa addon in Blender Preferences |
| `Operator massa.gen_X not found` | Ensure the cartridge `.py` file is in `massa/modules/cartridges/` and Blender was reloaded |
| Tool not appearing in Claude | Restart the MCP server process; check `uv run massa-blender-mcp` starts without errors |
| Port conflict with official extension | Disable the official Blender Claude Extension in Claude Desktop Extensions panel |
