# MCP Tool Authoring Workflow

Use this workflow when adding, debugging, or reviewing tools under `_MCP/blmcp/tools`.

## Goal

Add tools that auto-register cleanly, return structured data, respect live-vs-CLI execution boundaries, and degrade the server gracefully when optional dependencies are missing.

## Tool Discovery Rules

The server auto-discovers modules in `blmcp.tools`.

Registered:

- Any module under `_MCP/blmcp/tools` that has a `register(mcp)` function.

Skipped:

- Files ending in `_toolcode.py`.
- Files starting with `_template_`.

Every normal tool module should include:

```python
__all__ = ("register",)
```

## Pick An Implementation Pattern

Use inline code when the Blender-side logic is short.

Use split tool-code files when the Blender-side logic is long, reusable, or testable outside the MCP wrapper:

```text
my_tool.py
my_tool_toolcode.py
```

Use templates for repeated helper code:

```text
_template_name.py
```

Then include it inside a tool-code file with:

```python
# @include_begin: _template_name.py
# @include_end
```

## Live Socket Tool Pattern

```python
__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Tool Name", readOnlyHint=True))
    def tool_name(param: str) -> dict[str, object]:
        code = f"""
import bpy

result = {{"status": "ok", "param": {param!r}}}
"""
        return send_code(code, strict_json=True)
```

Use `destructiveHint=True` instead of `readOnlyHint=True` for tools that mutate Blender state.

## Split Tool-Code Pattern

Wrapper file:

```python
__all__ = ("register",)

from blmcp.tools_helpers import (
    toolcode_format_call,
    toolcode_load_from_filepath,
    toolcode_wrap_with_calling_convention,
)
from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Tool Name", readOnlyHint=True))
    def tool_name() -> dict[str, object]:
        return send_code(toolcode_format_call(_TOOL_CALL, None), strict_json=True)
```

Tool-code file:

```python
from typing import NamedTuple


class Result(NamedTuple):
    status: str
    message: str


def main(params: None) -> Result:
    del params
    import bpy

    return Result(status="ok", message=bpy.context.scene.name)
```

## CLI Pattern

Use CLI variants when a tool should inspect a `.blend` file through `blender --background`.

```python
from blmcp.tools_helpers.blender_cli import run_blender_cli, synced_blend_for_cli


with synced_blend_for_cli(blend_file) as synced_path:
    return run_blender_cli(synced_path, toolcode_format_call(_TOOL_CALL, params))
```

The executed code must assign a dict to `result`, or the CLI wrapper will reject it.

## Error Handling

Prefer structured error dicts from Blender-side code:

```python
result = {"status": "error", "message": str(exc)}
```

Raise Python exceptions in the MCP wrapper only for invalid wrapper-level state, malformed responses, or programming errors.

For optional Blender add-ons:

- Detect availability inside the running Blender instance.
- Use native fallback when possible.
- Report `used_<addon>=False` and include `warnings`.

## Verification Workflow

1. Start with `get_mcp_server_health`.
2. Confirm the new module appears in `registered_tool_modules`.
3. If health is `degraded`, inspect `tool_registration_errors`.
4. Run the new tool on a tiny safe input.
5. Verify response shape:
   - `status`
   - names/counts
   - warnings
   - explicit errors
6. Add or update tests when the behavior can be exercised without Blender.

## Prompt Frame

```text
Add or review this Massa Blender MCP tool.

Follow the existing auto-registration pattern in _MCP/blmcp/tools.
Choose inline code for short Blender logic or a *_toolcode.py split for longer/testable logic.
Use ToolAnnotations accurately.
Return structured dict data, handle optional Blender dependencies gracefully, and verify with get_mcp_server_health.

Task:
<task>
```

