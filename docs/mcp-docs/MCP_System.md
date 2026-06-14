# MCP System Summary

This document summarizes the `_MCP` system in this repository: how it starts, how it loads tools, how it talks to Blender, what tool families are currently implemented, and how the support code is organized.

## Purpose

`_MCP` is a Python MCP server package named `massa-blender-mcp`. It is a Massa-focused fork of Blender's Lab MCP server. Its job is to expose Blender and Massa workflows to an agent through MCP tools.

The server does not embed Blender. It runs as a separate Python process, accepts MCP calls through `stdio` or HTTP, and forwards most Blender work to a running Blender instance over a TCP socket. Blender must have the Blender MCP add-on enabled and listening on the configured host and port. For some tools, the server can also launch a background Blender process with `blender --background` and run code against a specific `.blend` file.

The runtime shape is:

```text
Agent / MCP client
    |
    | MCP protocol, stdio or HTTP
    v
_MCP/blmcp FastMCP server
    |
    | JSON-over-TCP execute request, default localhost:9876
    v
Blender MCP add-on
    |
    v
Blender bpy runtime, with optional Massa add-on, HardOps, NodeToPython, and geonodes support
```

## Package Layout

> Note: this document and the MCP setup guide now live in `docs/mcp-docs/`
> (moved out of `_MCP/` during the docs reorganization).

```text
_MCP/
  pyproject.toml
  blmcp/
    __init__.py
    __main__.py
    data/
      prompts.yml
      api/
      manual/
    tools/
      *.py
      *_toolcode.py
      _template_*.py
    tools_helpers/
      __init__.py
      blender_cli.py
      connection.py
      geonodes_paths.py
      rst_doc_search.py
      rst_parse_docs.py
  tests/
    test_server_startup.py
    test_response_validation.py
    test_render_paths.py
```

### `pyproject.toml`

`_MCP/pyproject.toml` declares the package:

- Project name: `massa-blender-mcp`
- Version: `1.0.0`
- Python requirement: `>=3.10`
- Dependencies: `docutils`, `mcp[cli]>=1.2.0`, and `pyyaml`
- Console scripts:
  - `massa-blender-mcp = "blmcp:main"`
  - `blender-mcp = "blmcp:main"`

The second script keeps compatibility with existing configs that still call the original upstream-style command.

Package data includes:

- `blmcp/data/prompts.yml`
- bundled Blender Python API RST docs under `blmcp/data/api`
- bundled Blender manual RST docs under `blmcp/data/manual`
- vendored NodeToPython source under `vendor/NodeToPython`
- vendored geonodes source, demos, docs, and license under `vendor/geonodes`

### `SETUP.md`

[`docs/mcp-docs/SETUP.md`](SETUP.md) is the user-facing setup guide. It explains installing with `uv`, configuring Claude/agent MCP clients, running over stdio or HTTP, connecting to the Blender add-on, and troubleshooting common connection problems.

One important maintenance note: `SETUP.md` contains a broader tool reference than the current indexed `blmcp/tools` package. The live code currently contains the tool modules listed in this document below. Treat `blmcp/tools` as authoritative for what will be registered at startup.

## Server Startup

The server entry point is `blmcp.main()` in `_MCP/blmcp/__init__.py`.

Startup flow:

1. Build and parse command-line arguments.
2. Validate HTTP security settings if HTTP transport was requested.
3. Load `blmcp/data/prompts.yml`.
4. Create `FastMCP("blender-mcp", instructions=...)`.
5. Auto-discover and register every valid tool module in `blmcp.tools`.
6. Add a server health tool.
7. Configure HTTP transport if requested.
8. Run the MCP server.

The default transport is `stdio`.

HTTP is optional and is configured with:

```text
--transport http
--host 127.0.0.1
--port 8000
--cors-origin <origin>
--allow-unsafe-http
```

By default, HTTP binding is limited to loopback hosts. Non-loopback hosts, such as `0.0.0.0`, require `--allow-unsafe-http`. Wildcard CORS also requires `--allow-unsafe-http`. When HTTP is enabled, the server uses FastMCP's streamable HTTP transport at `/`, enables stateless HTTP mode, and wraps the Starlette app with CORS middleware.

## Initial Instructions

The MCP server reads `blmcp/data/prompts.yml` and passes `initial_instructions` to `FastMCP`. These instructions tell the agent:

- Blender must be running with the MCP add-on enabled.
- Inspect the scene before modifying it.
- Prefer specialized tools over arbitrary code execution.
- Use `bpy.ops` where operator context is appropriate and `bpy.data` where direct precision is needed.
- Manage Blender mode, selection, active object, and dependency graph updates explicitly.
- Use bmesh for edit-mode geometry.
- Return structured data rather than relying on printed output.
- Be careful with datablocks, shared data, orphan data, visibility states, units, transforms, and coordinate spaces.

## Tool Loading

Tool loading is automatic. `_register_tools(mcp, tools_pkg)` walks `blmcp.tools.__path__` with `pkgutil.iter_modules`.

For each discovered module:

- Modules whose names end with `_toolcode` are skipped.
- Modules whose names start with `_template_` are skipped.
- Every other module is imported as `blmcp.tools.<module_name>`.
- If the module has a `register(mcp)` function, the server calls it.
- Successful module names are recorded.
- Import or registration failures are caught and recorded instead of crashing the whole server.

After discovery, `_register_health_tool` adds `get_mcp_server_health`. This tool reports:

- `status`: `ok` or `degraded`
- `registered_tool_count`
- `registered_tool_modules`
- `tool_registration_errors`

That design means a broken optional tool can degrade the server without preventing other tools from loading.

## How Tools Are Written

Each live tool module follows the same broad pattern:

```python
__all__ = ("register",)

def register(mcp: FastMCP) -> None:
    @mcp.tool(...)
    def some_tool(...) -> dict[str, object]:
        ...
```

Tool metadata uses `mcp.types.ToolAnnotations`. Read-only tools set `readOnlyHint=True`; tools that modify Blender state use `destructiveHint=True`.

There are two implementation styles:

1. Inline-code tools build a Python string directly inside the tool function and send it to Blender with `send_code`.
2. Tool-code modules split the MCP wrapper and Blender-executed code into separate files. For example:
   - `get_blendfile_summary_datablocks.py`
   - `get_blendfile_summary_datablocks_toolcode.py`

The wrapper registers the MCP tool. The `_toolcode.py` file defines `Params`, `Result`, and `main(params)`. The helper layer loads the tool-code file, inserts parameters, appends the common calling footer, and ensures the returned `NamedTuple` becomes a dict.

## Blender Connection Runtime

The main interactive connection helper is `_MCP/blmcp/tools_helpers/connection.py`.

Defaults:

```text
BLENDER_MCP_HOST=localhost
BLENDER_MCP_PORT=9876
```

`get_connection_params()` reads those env vars.

`send_code(code, strict_json)`:

- Opens a TCP socket to the configured Blender MCP add-on.
- Sends a null-terminated JSON request:
  - `type: "execute"`
  - `code: <python code>`
  - `strict_json: <bool>`
- Reads until the null-byte response delimiter.
- Parses the returned JSON.
- Raises `ConnectionError` for unreachable Blender, timeouts, socket errors, empty responses, or invalid JSON.

The Blender-side add-on is expected to run the code in Blender's Python environment and return a response dict with fields such as:

- `status`
- `result`
- `message`
- optional `stdout`
- optional `stderr`

`strict_json=True` is used for tools whose results should be JSON-safe. `strict_json=False` is used by the arbitrary code execution tool so Blender objects and other non-JSON values can fall back to `repr`.

## Background Blender CLI Runtime

`_MCP/blmcp/tools_helpers/blender_cli.py` supports command-line operation for tools that can inspect or render a `.blend` file without using the live socket.

`BLENDER_PATH` controls the Blender executable and defaults to `blender`.

`run_blender_cli(blend_file, code, timeout=120.0)`:

- Runs `[BLENDER_PATH, "--background", blend_file, "--python-expr", wrapper]`.
- Executes the supplied code.
- Requires the executed code to assign a dict to `result`.
- Prints a special result marker and parses it from stdout.
- Raises a clear error when Blender is missing, times out, returns non-dict data, or fails to print the result marker.

`synced_blend_for_cli(blend_file)` protects against stale on-disk state. It checks the running Blender instance, and if that same file is open with unsaved edits, it saves a numbered copy and runs CLI work against the copy. The copy is deleted afterward.

## Tool-Code Helpers

`_MCP/blmcp/tools_helpers/__init__.py` provides the shared mini-framework for split tool-code modules.

Key functions:

- `toolcode_load_from_filepath(filepath)` maps a wrapper file to its sibling `*_toolcode.py` file.
- `_toolcode_expand_includes(toolcode_path)` expands include blocks:
  - `# @include_begin: _template_name.py`
  - `# @include_end`
- `toolcode_wrap_with_calling_convention(toolcode, use_result=True)` appends code that calls `main(__BLMCP_PARAMS__)`.
- `toolcode_format_call(toolcode_template, params)` replaces `__BLMCP_PARAMS__` with `repr(params)`.

If `main()` returns a callable, the footer stores it as `check_is_finished` and returns an empty result. This supports Blender add-on deferred completion for long-running jobs such as renders.

## Current Live Tool Inventory

The current `blmcp/tools` package contains 44 registered MCP tools plus the startup health tool.

### Server Health

| Tool | Module | Purpose |
|---|---|---|
| `get_mcp_server_health` | `blmcp/__init__.py` | Reports startup status, registered modules, and any tool-registration errors. |

### Code Execution

| Tool | Module | Purpose |
|---|---|---|
| `execute_blender_code` | `execute_blender_code.py` | Runs arbitrary Python in the connected Blender instance with access to `bpy`; expects the code to assign `result`. |
| `execute_blender_code_for_cli` | `execute_blender_code.py` | Opens a `.blend` in background Blender and runs arbitrary Python there; expects a dict `result`. |

Use these as escape hatches. The prompt instructions explicitly prefer specialized tools when available.

### Scene And Object Inspection

| Tool | Module | Purpose |
|---|---|---|
| `get_objects_summary` | `get_objects_summary.py` | Returns object and collection hierarchy information for the live scene. |
| `get_object_detail_summary` | `get_object_detail_summary.py` | Returns detailed information for a named object. |
| `get_blendfile_summary_datablocks` | `get_blendfile_summary_datablocks.py` | Reports data-block counts, render engine, scene name, workspaces, and active workspace for the live file. |
| `get_blendfile_summary_datablocks_for_cli` | same | Runs the same summary against a `.blend` through background Blender. |
| `get_blendfile_summary_missing_files` | `get_blendfile_summary_missing_files.py` | Reports missing linked file paths and asset references for the live file. |
| `get_blendfile_summary_missing_files_for_cli` | same | CLI version for a `.blend` file. |
| `get_blendfile_summary_of_linked_libraries` | `get_blendfile_summary_of_linked_libraries.py` | Summarizes linked Blender libraries in the live file. |
| `get_blendfile_summary_of_linked_libraries_for_cli` | same | CLI version for a `.blend` file. |
| `get_blendfile_summary_path_info` | `get_blendfile_summary_path_info.py` | Reports path, save, backup, and file-location details. |
| `get_blendfile_summary_path_info_for_cli` | same | CLI version for a `.blend` file. |
| `get_blendfile_summary_usage_guess` | `get_blendfile_summary_usage_guess.py` | Scores likely file usage, such as animation, rendering, modeling, video editing, compositing, geometry nodes, and UV work. |
| `get_blendfile_summary_usage_guess_for_cli` | same | CLI version for a `.blend` file. |

### Screenshots, Renders, And Navigation

| Tool | Module | Purpose |
|---|---|---|
| `get_screenshot_of_window_as_image` | `get_screenshot_of_window_as_image.py` | Captures the Blender window as downscaled image bytes. |
| `get_screenshot_of_area_as_image` | `get_screenshot_of_area_as_image.py` | Captures a specific Blender area type as image bytes. |
| `get_screenshot_of_window_as_json` | `get_screenshot_of_window_as_json.py` | Captures window screenshot data as JSON. |
| `render_viewport_to_path` | `render_viewport_to_path.py` | Renders the current viewport to a file path, with deferred completion support. |
| `render_thumbnail_to_path` | `render_thumbnail_to_path.py` | Renders a thumbnail to a file path, using temporary render settings and deferred output checks. |
| `jump_to_tab_by_name` | `jump_to_tab_by_name.py` | Switches Blender to a workspace by name. |
| `jump_to_tab_by_space_type` | `jump_to_tab_by_space_type.py` | Switches to a workspace containing a matching editor space type. |
| `jump_to_view3d_object_by_name` | `jump_to_view3d_object_by_name.py` | Focuses a 3D View on a named object, optionally changing UI/visibility state. |
| `jump_to_view3d_object_data_by_name` | `jump_to_view3d_object_data_by_name.py` | Focuses a 3D View on the object that owns a named datablock. |

### Bundled Documentation Tools

| Tool | Module | Purpose |
|---|---|---|
| `search_api_docs` | `search_api_docs.py` | Full-text search over bundled Blender Python API RST documentation. |
| `search_manual_docs` | `search_manual_docs.py` | Full-text search over bundled Blender manual RST documentation. |
| `get_python_api_docs` | `get_python_api_docs.py` | Fetches exact Blender Python API docs, namespace listings, definition blocks, examples, suggestions, and missing/partial responses. |

`get_python_api_docs` has a size guard. Exact RST files larger than 32 KB are summarized as a list of top-level definitions so the caller can query a narrower identifier.

The RST helpers live in:

- `tools_helpers/rst_doc_search.py`
- `tools_helpers/rst_parse_docs.py`

These helpers parse RST, preserve useful directives, collect examples from `literalinclude`, and expose searchable doc content.

### Massa Mesh Operations

| Tool | Module | Purpose |
|---|---|---|
| `mesh_boolean` | `massa_mesh_ops.py` | Adds boolean-style operations to a target mesh. Uses HardOps when available, otherwise falls back to native Blender Boolean modifiers for `DIFFERENCE`, `UNION`, and `INTERSECT`. |
| `mesh_clean` | `massa_mesh_ops.py` | Cleans mesh topology. Uses HardOps `view3d.clean_mesh` when available, otherwise runs native merge-by-distance, limited dissolve, degenerate dissolve, and optional interior-face deletion. |
| `apply_modifiers` | `massa_mesh_ops.py` | Applies native Blender modifiers deterministically, with options to keep the last Bevel and Weighted Normal modifiers and to avoid shape-key-risky application. |
| `apply_transform` | `massa_mesh_ops.py` | Applies object location, rotation, and/or scale using Blender's native transform application. |

HardOps is detected in the running Blender instance. The tools do not assume a vendored HardOps install is active. When HardOps is unavailable, the response reports fallback behavior and warnings.

### Massa Selection, Edge Slots, Material Slots, And Sockets

| Tool | Module | Purpose |
|---|---|---|
| `get_selected_geometry` | `massa_seams.py` | Reads selected vertices, edges, faces, active element, coordinates, normals, edge marks, material indices, and the `MASSA_EDGE_SLOTS` layer from the current mesh selection. |
| `assign_edge_slot_to_selection` | `massa_seams.py` | Writes edge slot values `0-5` to selected edges and can apply live actions: `SEAM`, `SHARP`, `BOTH`, `CREASE`, `BEVEL`, or `IGNORE`. |
| `assign_face_material_slot_to_selection` | `massa_seams.py` | Assigns selected faces to a material slot index. This drives Massa slot semantics through face material indices. |
| `create_socket_at_selected_face` | `massa_seams.py` | Creates one or more face-centered Empty objects, optionally parented to the mesh and aligned to selected face normals. |

These tools are selection-driven. The intended workflow is:

1. The user selects geometry in Blender.
2. The agent calls `get_selected_geometry` to inspect and confirm the selection.
3. The agent calls a write tool to tag the selected geometry or create sockets.

### Node Graph And NodeToPython Tools

| Tool | Module | Purpose |
|---|---|---|
| `ntp_list_graphs` | `ntp_graphs.py` | Lists material, geometry-node, shader, compositor, world, light, and line-style node graphs. |
| `ntp_snapshot_graph` | `ntp_graphs.py` | Exports one node graph to Python code using the vendored NodeToPython add-on. |
| `ntp_analyze_graph` | `ntp_graphs.py` | Reports structural statistics, categories, output nodes, orphan/dead-end nodes, broken links, linked groups, dependency chains, and complexity. |
| `ntp_inspect_node` | `ntp_graphs.py` | Inspects one node's inputs, outputs, links, defaults, location, dimensions, and readable RNA properties. |

Supported graph types are:

```text
MATERIAL
GEOMETRY
SHADER
COMPOSITOR
WORLD
LIGHT
LINESTYLE
```

`ntp_snapshot_graph` resolves vendored NodeToPython paths from both package layout and legacy repository layout. It imports and registers NodeToPython inside Blender on first use if it is not already registered. Snapshot output is collected from Blender's clipboard after `bpy.ops.ntp.export()`.

### Vendored geonodes Tools

| Tool | Module | Purpose |
|---|---|---|
| `geonodes_list_demos` | `geonodes_tools.py` | Lists vendored geonodes demo scripts with descriptions, sizes, line counts, and inferred tags. |
| `geonodes_get_demo` | `geonodes_tools.py` | Returns one demo source file, module docstring, metadata, and related demos. |
| `geonodes_list_types` | `geonodes_tools.py` | Lists public geonodes classes grouped by broad categories such as geometry, socket, domain, and control-flow. |
| `geonodes_get_type_doc` | `geonodes_tools.py` | Reads markdown reference documentation for a geonodes type. |
| `geonodes_search` | `geonodes_tools.py` | Searches vendored demos, docs, and core source with context lines and enclosing function/class hints. |
| `geonodes_execute_script` | `geonodes_tools.py` | Executes a geonodes Python script inside Blender and reports newly created node groups/materials, stdout, and traceback. |

`tools_helpers/geonodes_paths.py` resolves geonodes vendor roots and searchable scopes. The tool code supports both package-installed and repository-local vendor layouts.

## Tool Families By Execution Mode

### Live Blender Socket Tools

Most tools use `send_code` and require a running Blender instance:

- arbitrary execution
- object and scene summaries
- screenshots
- viewport navigation
- docs-independent Blender actions
- Massa mesh operations
- selected geometry and slot tagging
- NodeToPython graph inspection/export
- geonodes script execution

### Background Blender CLI Tools

CLI variants open a `.blend` path in `blender --background`:

- `execute_blender_code_for_cli`
- `get_blendfile_summary_*_for_cli`

They use `synced_blend_for_cli` to avoid stale reads when the same file is open and dirty in the live Blender session.

### Local-Only Reference Tools

These tools mostly read files bundled with the package and do not need Blender:

- `search_api_docs`
- `search_manual_docs`
- `get_python_api_docs`
- `geonodes_list_demos`
- `geonodes_get_demo`
- `geonodes_list_types`
- `geonodes_get_type_doc`
- `geonodes_search`

Some geonodes tools become live Blender tools only when they execute scripts.

## Response And Validation Behavior

The code distinguishes three response layers:

1. MCP tool function return values, always Python dict-like objects.
2. Blender add-on socket responses, with `status`, `result`, `message`, and optional captured output.
3. Tool-code `NamedTuple` results, converted to dict by the calling convention footer.

Tests cover several important guardrails:

- The default transport is `stdio`.
- Loopback HTTP is allowed by default.
- Non-loopback HTTP requires `--allow-unsafe-http`.
- Wildcard CORS requires `--allow-unsafe-http`.
- Registration failures are surfaced by `get_mcp_server_health`.
- CLI arbitrary execution rejects non-dict return values.
- Screenshot tools reject malformed non-dict tool results.
- Render path logic restores Blender render file paths after success or failure.

## Security Model

This server exposes Blender Python execution. That is inherently powerful. The code reduces accidental exposure in several ways:

- `stdio` is the default transport.
- HTTP binds to `127.0.0.1` by default.
- Non-loopback HTTP requires an explicit unsafe flag.
- Wildcard CORS requires the same explicit unsafe flag.
- DNS rebinding protection remains enabled unless unsafe HTTP is requested.
- Tool annotations mark destructive tools.
- Prompt instructions tell agents to inspect before modifying and to avoid destructive changes without confirmation.

These are guardrails, not a sandbox. Any tool that executes Python in Blender can affect the open scene and the local Blender environment.

## Adding A New Tool

Add a Python module under `_MCP/blmcp/tools`.

Requirements:

1. The file name must not end with `_toolcode.py`.
2. The file name must not start with `_template_`.
3. The module must define `register(mcp)`.
4. Inside `register`, decorate one or more functions with `@mcp.tool(...)`.
5. Restart the MCP server so auto-discovery imports the new module.

Minimal live-Blender example:

```python
__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Example Tool", readOnlyHint=True))
    def example_tool() -> dict[str, object]:
        code = """
import bpy
result = {"status": "ok", "scene": bpy.context.scene.name}
"""
        return send_code(code, strict_json=True)
```

For larger tools, prefer a split module:

```text
my_tool.py
my_tool_toolcode.py
```

The wrapper registers MCP-facing functions. The tool-code file defines the Blender-side `main(params)` and returns a `NamedTuple`.

## Maintenance Notes

- `blmcp/tools` is the source of truth for live tool registration.
- `*_toolcode.py` files are execution payloads and are intentionally skipped during auto-registration.
- `_template_*.py` files are include snippets used by tool-code modules and are intentionally skipped during auto-registration.
- `get_mcp_server_health` should be the first diagnostic when tools do not appear.
- If Blender connection calls fail, check `BLENDER_MCP_HOST`, `BLENDER_MCP_PORT`, and whether the Blender MCP add-on server is running.
- If CLI tools fail to find Blender, set `BLENDER_PATH`.
- If NodeToPython snapshotting fails, verify the vendored NodeToPython files are present and Blender can register the add-on.
- If geonodes reference tools return missing vendor errors, verify package data includes `vendor/geonodes` or that the repository vendor path exists.

