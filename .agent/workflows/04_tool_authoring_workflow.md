# MCP Tool Authoring Workflow

Use when adding, debugging, or reviewing tools under `_MCP/blmcp/tools`.

---

## Discovery Rules

The server auto-discovers any module in `blmcp/tools` with a `register(mcp)` function.

Skipped automatically:
- Files ending with `_toolcode.py` — Blender-side execution payloads.
- Files starting with `_template_` — shared code snippets, not tools.

Every tool module must include `__all__ = ("register",)`.

---

## Choose An Implementation Style

**Inline** — use when Blender-side logic is short (< ~40 lines):

```python
__all__ = ("register",)

from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Tool Name", readOnlyHint=True))
    def tool_name(param: str) -> dict[str, object]:
        """One-line description shown to the agent."""
        code = f"""
import bpy
result = {{"status": "ok", "value": {param!r}}}
"""
        return send_code(code, strict_json=True)
```

`strict_json=True` — response must be JSON-safe. Use for all structured tools.
`strict_json=False` — allows `repr()` fallback for non-serialisable Blender objects. Use only for arbitrary code execution tools.

Use `destructiveHint=True` instead of `readOnlyHint=True` for anything that mutates Blender state.

**Split (`my_tool.py` + `my_tool_toolcode.py`)** — use when Blender-side logic is long, reusable, or testable independently:

```python
# my_tool.py  (MCP wrapper)
_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))

def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Tool Name", readOnlyHint=True))
    def tool_name() -> dict[str, object]:
        return send_code(toolcode_format_call(_TOOL_CALL, None), strict_json=True)
```

```python
# my_tool_toolcode.py  (Blender-side code)
from typing import NamedTuple

class Result(NamedTuple):
    status: str
    message: str

def main(params: None) -> Result:
    import bpy
    return Result(status="ok", message=bpy.context.scene.name)
```

To share helper code between tool-code files, put it in `_template_name.py` and include it with:
```python
# @include_begin: _template_name.py
# @include_end
```

**CLI variant** — use when the tool should inspect a `.blend` without a live Blender session:

```python
from blmcp.tools_helpers.blender_cli import run_blender_cli, synced_blend_for_cli

with synced_blend_for_cli(blend_file) as synced_path:
    return run_blender_cli(synced_path, toolcode_format_call(_TOOL_CALL, params))
```

The executed code must assign a **dict** to `result` — the CLI wrapper rejects all other return types.

---

## Error Handling

Return structured dicts from Blender-side code:
```python
result = {"status": "error", "message": str(exc)}
```

For optional Blender add-ons (HardOps, NodeToPython, etc.):
- Detect availability inside Blender, not at import time.
- Use native fallback where possible.
- Always report `used_<addon>: false` and populate `warnings` when falling back.

Raise Python exceptions in the MCP wrapper only for invalid wrapper state, malformed Blender responses, or programming errors — not for expected Blender-side failures.

---

## Verification After Adding A Tool

1. `get_mcp_server_health` — confirm the new module name appears in `registered_tool_modules`.
2. If `degraded`: inspect `tool_registration_errors` for the module; fix the import or registration error.
3. Call the new tool on a small, safe input.
4. Verify the response shape includes `status`, expected data fields, and (if applicable) `warnings`.
5. Add or update tests in `_MCP/tests/` for any behaviour that can be exercised without a live Blender session.

---

## Prompt Frame

```
Add or review this Massa Blender MCP tool.

Follow the auto-registration pattern in _MCP/blmcp/tools.
Choose inline code for short Blender logic; use a *_toolcode.py split for longer/testable logic.
Set ToolAnnotations (readOnlyHint or destructiveHint) accurately.
Return structured dict data, handle optional Blender dependencies gracefully, and verify with get_mcp_server_health after adding.

Task:
<task>
```
