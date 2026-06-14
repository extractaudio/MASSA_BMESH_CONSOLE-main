# Massa Blender MCP — Setup Guide

A fork of the official [Blender Lab MCP server](https://projects.blender.org/lab/blender_mcp)
extended with Massa-specific tools for selection-driven geometry tagging, mesh operations,
Geometry Node authoring, node graph inspection, and scene utilities.

---

## Architecture

```
Claude Code / Claude Desktop / custom agent harness
        │  MCP protocol (stdio or HTTP)
        ▼
  _MCP/blmcp  ← THIS server (FastMCP, Python)
        │
        ├── TCP socket (port 9876) ──► Blender MCP addon
        │                                    │
        │                               bpy runtime  →  Massa addon
        │
        └── blender --background ──────────► background Blender process
                  (CLI tools only; no GUI required)
```

The server does **not** embed Blender — it either sends Python code to a running
Blender instance (most tools), or launches a background Blender process against a
`.blend` file path (CLI tools). The Massa addon must be installed for Massa-specific
operations; general Blender inspection tools work without it.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python ≥ 3.10 | Bundled with most systems; use `python --version` to check |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Fast Python package manager — `pip install uv` or see link |
| Blender 4.x / 5.x | With the MCP addon enabled (see below) |
| Massa addon | Required only for Massa-specific tools; install and enable in Blender |

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

> **Alias:** `blender-mcp` is provided as a backwards-compatible command name that
> points to the same entry point. Both names launch the identical server.

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
# Local-only (default; safe)
uv run --project /path/to/_MCP massa-blender-mcp --transport http --port 8100

# Expose to the network (requires --allow-unsafe-http)
uv run --project /path/to/_MCP massa-blender-mcp \
  --transport http --host 0.0.0.0 --port 8100 \
  --allow-unsafe-http --cors-origin "http://my-agent-host:3000"
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

See [HTTP Transport Security](#http-transport-security) for flag details.

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

### 4a — Server health (no Blender required)

Ask your agent:

```
Call get_mcp_server_health
```

Expected response: a JSON object with `"status": "ok"`, the count of registered tools,
and any tool-registration errors. This confirms the MCP server process is running and
all tool modules loaded successfully. If `status` is `"degraded"`, check
`tool_registration_errors` for the failing module.

### 4b — Live Blender connection

With Blender running and the MCP addon active, ask your agent:

```
What objects are in the current scene?
```

Expected response: the scene object hierarchy. If you get a connection error, check:
1. Blender is open and the MCP addon server is started
2. Port `9876` is not blocked by a firewall
3. The `BLENDER_MCP_PORT` env var matches what the addon is using

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `BLENDER_MCP_HOST` | `localhost` | Hostname of the Blender addon socket |
| `BLENDER_MCP_PORT` | `9876` | Port of the Blender addon socket |
| `BLENDER_PATH` | `blender` | Path to Blender executable used by background CLI tools |

> **Connection timeout:** The socket client uses a 300 s read timeout. Long-running
> operations (heavy renders, large mesh ops) must complete within this window.

---

## HTTP Transport Security

The `--transport http` mode supports these flags:

| Flag | Default | Purpose |
|---|---|---|
| `--host HOST` | `127.0.0.1` | Interface to bind to |
| `--port PORT` | `8000` | Port to listen on |
| `--allow-unsafe-http` | off | Required to bind non-loopback hosts or use wildcard CORS |
| `--cors-origin ORIGIN` | (loopback regex) | Exact CORS origin to allow; may be repeated; `*` requires `--allow-unsafe-http` |

By default HTTP binds to `127.0.0.1` only, which is safe for local agents.
Binding `0.0.0.0` or enabling wildcard CORS **exposes Blender Python execution to your
network** — only use `--allow-unsafe-http` in a trusted, isolated environment.

---

## Tool Reference

Tools are grouped by execution mode. **Live socket tools** require a running Blender
instance with the MCP addon active. **Background CLI tools** launch `blender --background`
and do not require the Blender GUI. **Local reference tools** read bundled files and
need no Blender at all.

---

### Server / Diagnostic

| Tool | Description |
|---|---|
| `get_mcp_server_health` | Startup health: status, registered tool count, loaded modules, registration errors |

---

### Live Blender Tools — Code Execution

| Tool | Description |
|---|---|
| `execute_blender_code` | Run arbitrary Python in the connected Blender instance; code must assign `result` |

---

### Live Blender Tools — Scene Inspection

| Tool | Description |
|---|---|
| `get_objects_summary` | Scene collection + object hierarchy |
| `get_object_detail_summary` | Detailed single-object info |
| `get_blendfile_summary_datablocks` | Data-block counts, render engine, workspaces for the live file |
| `get_blendfile_summary_missing_files` | Missing linked file paths and asset references |
| `get_blendfile_summary_of_linked_libraries` | Linked Blender library summary |
| `get_blendfile_summary_path_info` | Path, save, backup, and file-location details |
| `get_blendfile_summary_usage_guess` | Scores likely file usage: animation, modeling, compositing, GeoNodes, etc. |

---

### Live Blender Tools — Screenshots, Renders, Navigation

| Tool | Description |
|---|---|
| `get_screenshot_of_window_as_image` | Screenshot the Blender window as image bytes |
| `get_screenshot_of_area_as_image` | Screenshot a specific editor area type as image bytes |
| `get_screenshot_of_window_as_json` | Window screenshot as JSON data |
| `render_viewport_to_path` | Render viewport to file (deferred completion) |
| `render_thumbnail_to_path` | Render thumbnail to file (uses temporary render settings) |
| `jump_to_tab_by_name` | Switch Blender workspace by name |
| `jump_to_tab_by_space_type` | Switch to a workspace containing a matching editor type |
| `jump_to_view3d_object_by_name` | Focus 3D View on a named object |
| `jump_to_view3d_object_data_by_name` | Focus 3D View on the object that owns a named datablock |

---

### Live Blender Tools — Massa Selection & Geometry Tagging (`massa_seams.py`)

Selection-driven tools. The intended workflow is:

1. Enter Edit Mode on a mesh in Blender and select geometry with native tools
   (Alt+click for loops, Ctrl+click for shortest path, box-select, lasso, etc.)
2. Call `get_selected_geometry` to read and confirm what is highlighted
3. Call a write tool to tag the selection or create sockets

| Tool | Description |
|---|---|
| `get_selected_geometry` | Return vertex/edge/face data for every selected element — indices, local + world-space coordinates, normals, edge marks, material indices, MASSA_EDGE_SLOTS layer, and mesh stats |
| `assign_edge_slot_to_selection` | Write edge slot values (0–5) to selected edges and apply live actions: `SEAM`, `SHARP`, `BOTH`, `CREASE`, `BEVEL`, or `IGNORE` |
| `assign_face_material_slot_to_selection` | Assign selected faces to a material slot index (drives Massa slot semantics) |
| `create_socket_at_selected_face` | Create one or more face-centred Empty objects, optionally parented to the mesh and aligned to selected face normals |

---

### Live Blender Tools — Massa Mesh Ops (`massa_mesh_ops.py`)

| Tool | Description |
|---|---|
| `mesh_boolean` | Add DIFFERENCE, UNION, INTERSECT, SLASH, INSET, or KNIFE boolean-style operations; prefers HardOps operators, falls back to native Boolean modifiers |
| `mesh_clean` | Clean mesh topology with configurable merge, dissolve, degenerate, and interior-face settings; prefers HardOps `view3d.clean_mesh` |
| `apply_modifiers` | Deterministically apply native Blender modifiers, with option to keep the last Bevel and Weighted Normal modifiers |
| `apply_transform` | Apply object location, rotation, and/or scale transforms |

HardOps is detected from the **running Blender instance**, not from the vendored source tree.
When unavailable, tools fall back to native operators and report `used_hardops=False`.
The vendored `_MCP/vendor/HOps/` copy is source reference only.

---

### Live Blender Tools — Node Graphs / NodeToPython (`ntp_graphs.py`)

| Tool | Description |
|---|---|
| `ntp_list_graphs` | List material, Geometry Nodes, shader, compositor, world, light, and line-style node graphs |
| `ntp_snapshot_graph` | Export one graph to NodeToPython Python code; registers the vendored NodeToPython addon in Blender on first use |
| `ntp_analyze_graph` | Structural stats, orphan/dead-end nodes, broken links, outputs, and group dependencies |
| `ntp_inspect_node` | Inspect one node's sockets, links, default values, dimensions, and readable RNA properties |

Supported graph types: `MATERIAL`, `GEOMETRY`, `SHADER`, `COMPOSITOR`, `WORLD`, `LIGHT`, `LINESTYLE`

NodeToPython v4.1.0 is vendored under `_MCP/vendor/NodeToPython/` — no extra install needed.
To refresh the vendored source:

```bash
uv run --project _MCP python _Scripts/vendor_nodetopython.py
```

---

### Live Blender Tools — geonodes Script Execution (`geonodes_tools.py`)

| Tool | Description |
|---|---|
| `geonodes_execute_script` | Execute a geonodes Python script inside Blender and report newly created node groups/materials, stdout, and traceback |

---

### Background CLI Tools (no GUI required)

These tools launch `blender --background` against a `.blend` file path.
Set `BLENDER_PATH` if Blender is not on your system `PATH`.

| Tool | Description |
|---|---|
| `execute_blender_code_for_cli` | Open a `.blend` in background Blender and run arbitrary Python; code must assign a dict to `result` |
| `get_blendfile_summary_datablocks_for_cli` | Data-block counts and scene info for a `.blend` file path |
| `get_blendfile_summary_missing_files_for_cli` | Missing linked file paths for a `.blend` file path |
| `get_blendfile_summary_of_linked_libraries_for_cli` | Linked library summary for a `.blend` file path |
| `get_blendfile_summary_path_info_for_cli` | Path and save details for a `.blend` file path |
| `get_blendfile_summary_usage_guess_for_cli` | Usage scoring for a `.blend` file path |

> **Stale-file protection:** If the target `.blend` file is currently open in the live
> Blender session with unsaved edits, the server saves a numbered copy and runs CLI
> work against the copy, then deletes it.

---

### Local Reference Tools (no Blender required)

These tools read bundled files and work even when Blender is not running.

#### Blender API & Manual Docs

| Tool | Description |
|---|---|
| `search_api_docs` | Full-text search over bundled Blender Python API RST docs |
| `search_manual_docs` | Full-text search over bundled Blender user manual RST docs |
| `get_python_api_docs` | Fetch exact Blender Python API docs, namespace listings, definition blocks, and examples |

> Files larger than 32 KB are returned as a top-level definition list — query a narrower
> identifier to get the full doc.

#### geonodes Design Library Reference (`geonodes_tools.py`)

| Tool | Description |
|---|---|
| `geonodes_list_demos` | List vendored geonodes demo scripts with descriptions, sizes, line counts, and inferred tags |
| `geonodes_get_demo` | Read a full demo source file, its module docstring, metadata, and related demos |
| `geonodes_list_types` | Enumerate public geonodes classes grouped by geometry, socket, domain, and control-flow roles |
| `geonodes_get_type_doc` | Read the markdown reference for a geonodes type such as `Float`, `Mesh`, or `Vector` |
| `geonodes_search` | Search demos, docs, and core source with line context and enclosing function/class hints |

geonodes is vendored under `_MCP/vendor/geonodes/`, with the pinned upstream
commit recorded in `_MCP/vendor/geonodes/.vendored_commit`. To refresh it:

```bash
uv run --project _MCP python _Scripts/vendor_geonodes.py
```

##### Learning Patterns for Node Creation

1. `geonodes_search` — find a matching demo or doc pattern
2. `geonodes_get_demo` — read the most relevant demo in full
3. `geonodes_get_type_doc` — check type specifics (`Float`, `Mesh`, `Vector`, …)
4. Adapt the script
5. `geonodes_execute_script` — run it inside Blender

---

### Planned Tools (not yet implemented)

The following tool families are designed and documented but not yet present in the live
`blmcp/tools/` package. They will appear automatically once their modules are added.

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
| `rerun_massa_cartridge` | Re-execute a cartridge on an existing object (live edit) |

#### Geometry Nodes Modifiers (`massa_geonode.py`)
| Tool | Description |
|---|---|
| `list_geonode_groups` | All GN groups in the blend with input schemas |
| `apply_geonode_modifier` | Add a GN modifier with named input values |
| `set_geonode_input` | Update a single input on an existing modifier |
| `get_geonode_modifier_state` | Read current input values from a GN modifier |

#### Slot Manifest (`massa_slots.py`)
| Tool | Description |
|---|---|
| `get_slot_manifest` | Material + UV + physics slot info for a Massa object |
| `tag_faces_to_slot` | Assign faces to a slot by index or normal direction |
| `set_edge_slot_action` | Set SEAM/SHARP/CREASE/BEVEL on an edge slot |

#### Scene Utilities (`massa_scene.py`)
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
The server **auto-discovers** any file with a `register(mcp)` function — no
registration table to update. Files whose names end with `_toolcode.py` or start
with `_template_` are intentionally skipped by the loader.

**Read-only tool (inspects Blender, no modifications):**

```python
# blmcp/tools/my_inspect_tool.py
__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="My Inspect Tool", readOnlyHint=True))
    def my_inspect_tool(object_name: str) -> dict[str, object]:
        """Return the active scene name and a named object's vertex count."""
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
result = {{
    "status": "ok",
    "scene": bpy.context.scene.name,
    "vertex_count": len(obj.data.vertices) if obj and obj.type == "MESH" else None,
}}
"""
        return send_code(code, strict_json=True)
```

**Destructive tool (modifies Blender state):**

```python
# blmcp/tools/my_modify_tool.py
__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="My Modify Tool", destructiveHint=True))
    def my_modify_tool(object_name: str, new_name: str) -> dict[str, object]:
        """Rename a Blender object."""
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj is None:
    result = {{"status": "error", "message": "Object not found: {object_name}"}}
else:
    obj.name = "{new_name}"
    result = {{"status": "ok", "old_name": "{object_name}", "new_name": obj.name}}
"""
        return send_code(code, strict_json=True)
```

Restart the MCP server process after adding a file — the new tool appears immediately.

---

## Updating from Upstream

The upstream source lives at:
`https://projects.blender.org/lab/blender_mcp`

To pull upstream fixes without losing Massa tools:

```bash
# In _MCP/ — overwrite only the non-Massa tool files
# (massa_*.py files are not in upstream and are safe)
git diff --name-only HEAD origin/main | grep -v "massa_" | xargs git checkout origin/main --
uv sync
```

Or simply re-run the fork script (`_Scripts/` directory) when a new upstream version ships.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `get_mcp_server_health` shows `"degraded"` | Inspect `tool_registration_errors` in the response; fix the failing module or check imports |
| `ConnectionRefusedError` on port 9876 | Start the MCP addon server in Blender (addon preferences → **Start Server**) |
| `Massa addon not found` | Enable the Massa addon in Blender Preferences → Add-ons |
| `Operator massa.gen_X not found` | Ensure the cartridge `.py` is in `massa/modules/cartridges/` and Blender was reloaded |
| CLI tool fails with `blender: command not found` | Set `BLENDER_PATH` env var to the full path of the Blender executable |
| Tool not appearing in the agent | Restart the MCP server process; verify `uv run massa-blender-mcp` starts without errors |
| Port conflict with official Blender extension | Disable the official extension in Claude Desktop → Extensions panel before enabling this fork |
| Blender connection times out | The socket timeout is 300 s; heavy operations (large renders, complex meshes) must finish within that window |
| HTTP binds but agent can't connect cross-machine | Ensure `--allow-unsafe-http` was passed when binding a non-loopback host, and that your firewall allows the port |
