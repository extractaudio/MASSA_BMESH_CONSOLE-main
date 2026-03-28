---
description: Flash Workflow Router — Start Here
---

# WF_FLASH_INDEX — Task Router

Read the task. Pick **one** row. Follow that workflow only.

| Task | Workflow |
| :--- | :--- |
| Create a new cartridge file that does not exist yet | `WF_FLASH_BUILD.md` |
| Fix bugs, flags, or crashes in an existing cartridge | `WF_FLASH_MODIFY.md` |
| Add parameters or UI to an existing cartridge | `WF_FLASH_MODIFY.md` |
| Run an audit and interpret results | `WF_FLASH_AUDIT.md` |
| Change the engine, base operator, or global properties | `WF_FLASH_CONSOLE.md` |

---

## Absolute Rules — Enforced Across All Workflows

These apply everywhere. No exceptions.

1. **READ before WRITE.** Never write to a file you have not read in this session.
2. **No `bpy.ops` inside `build_shape`.** Use `bmesh.ops` only.
3. **No `bpy.context` at module level.** Only valid inside `execute()` / `invoke()` / `draw()`.
4. **Never rename or delete an existing `bpy.props`.** Resurrection breaks silently.
5. **Zero `CRITICAL_` flags before delivery.** No exceptions.
6. **Run AUDIT after every code change.** Do not skip.
7. **Never guess a file path.** Use only paths confirmed by reading or directory listing.

---

## Key Paths (Copy-Paste Ready)

| What | Path |
| :--- | :--- |
| Cartridge folder | `massa/modules/cartridges/` |
| Audit runner | `modules/debugging_system/runner.py` |
| Debug agent | `modules/debugging_system/debug_agent.py` |
| Config (Blender path) | `modules/debugging_system/config.py` |
| Base operator | `massa/operators/massa_base.py` |

## Audit Command Template

```bash
python modules/debugging_system/runner.py --cartridge massa/modules/cartridges/<CARTRIDGE>.py --mode AUDIT
```

Parse JSON between `---AUDIT_START---` and `---AUDIT_END---`.
`CRITICAL_` prefix = must fix. `WARNING_` prefix = should fix.
