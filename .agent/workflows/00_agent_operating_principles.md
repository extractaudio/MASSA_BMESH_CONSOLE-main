# Agent Operating Principles — Massa Blender MCP

Use before any task that touches Blender through the Massa MCP server.

---

## Opening Protocol (every session)

1. Call `get_mcp_server_health`.
   - If `degraded`: read `tool_registration_errors` and avoid any failing module's tools.
2. Establish work mode — this determines which tool set to use:
   - **Live scene**: user has Blender open; use live socket tools.
   - **File path**: user gave a `.blend` path; use `_for_cli` variants, no GUI needed.
   - **Reference only**: no Blender needed; use bundled doc and geonodes reference tools.
3. If live scene + object task: call `get_objects_summary` before touching anything.

---

## Tool Decision Tree

```
Task involves a .blend file path?
  └─ YES → use _for_cli tools only
Task modifies geometry / materials / nodes?
  └─ YES → confirm target object + mode first, then use purpose-built write tool
Task inspects something?
  └─ use purpose-built read tool
No existing tool covers it?
  └─ execute_blender_code (last resort; justify the choice)
Need API or node graph reference?
  └─ search_api_docs / search_manual_docs / geonodes_search (no Blender required)
```

**Purpose-built read tools (prefer first):**
`get_objects_summary` · `get_object_detail_summary` · `get_blendfile_summary_*`
`get_selected_geometry` · `ntp_list_graphs` · `ntp_analyze_graph` · `ntp_inspect_node`

**Purpose-built write tools (prefer over arbitrary code):**
`mesh_boolean` · `mesh_clean` · `apply_modifiers` · `apply_transform`
`assign_edge_slot_to_selection` · `assign_face_material_slot_to_selection` · `create_socket_at_selected_face`
`geonodes_execute_script` · `ntp_snapshot_graph`

**Arbitrary code (escape hatches):**
`execute_blender_code` · `execute_blender_code_for_cli`

---

## Before Any Write

- Name the exact target object. If uncertain, call `get_objects_summary`.
- Confirm object type is `MESH` when edit-mode tools are involved.
- State what will change and what side effects to expect.
- Prefer non-destructive modifiers. Flag destructive changes explicitly.
- Preserve user selection and mode unless changing them is the task.

---

## Response Contract

Every completed task must include:

- Tools used (names, not descriptions).
- Objects changed (by name).
- Any warnings, fallbacks, or skipped steps.
- At least one read-back verification after any write.

---

## Prompt Frame

```
Use the Massa Blender MCP tools.

1. Check server health. Establish work mode (live / file path / reference).
2. Inspect before acting. Use purpose-built tools over arbitrary Python.
3. Name targets before writing. State what changes.
4. After any write, verify with a read-back tool and report tools used,
   objects changed, warnings, and fallbacks.

Task:
<task>
```
