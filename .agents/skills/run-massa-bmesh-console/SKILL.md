---
name: run-massa-bmesh-console
description: Run, build, audit, and test the MASSA BMESH CONSOLE Blender addon. Use when asked to run massa, audit a cartridge, package the addon, screenshot Blender, build and launch massa, or verify a cartridge change.
---

# MASSA BMESH CONSOLE — Run Skill

MASSA is a Blender 5.x addon. The agent path is **headless cartridge audits** via Blender's background mode — no display needed, returns structured JSON. For live interaction with a running Blender, use the `mcp__blender__massa_*` MCP tools.

All paths below are relative to the repo root (`MASSA_BMESH_CONSOLE-main/`).

## Prerequisites

- **Blender 5.1** installed at `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe` (configured in `massa/modules/debugging_system/config.py`)
- **Python 3.x** (standard library only — no `pip install` needed)

If Blender is at a different path, edit `massa/modules/debugging_system/config.py` and change `BLENDER_PATH`.

## Build — Package the Addon

```
python _Scripts/package_massa_addon.py
```

Output: `_EXPORT/massa.zip` — Blender 5.0 Extension format with `blender_manifest.toml` at ZIP root. The `debugging_system/` folder is excluded. Deletes and recreates the zip on each run.

## Run (Agent Path) — Headless Cartridge Audit

The primary agent interaction is the **headless auditor**. It launches Blender in background mode, runs a cartridge through the full pipeline, and returns structured JSON.

```
python _Scripts/test_run_cartridge.py <path/to/cartridge.py> [--mode MODE]
```

Output is bracketed by `---AUDIT_START---` / `---AUDIT_END---` markers and parsed to JSON:

```json
{"status": "PASS", "object": "ARC Mezzanine", "errors": []}
```

or on failure:

```json
{"status": "FAIL", "object": "ARC Wall", "errors": ["FUZZ_CRASH: BMesh data of type BMFace has been removed\n..."]}
```

### Audit Modes

| Mode | What it checks |
|---|---|
| `AUDIT` (default) | Geometry validity + fuzz test with random params |
| `VISUAL_DIFF` | Renders the mesh for visual comparison |
| `UV_HEATMAP` | UV coverage / stretching heatmap |
| `UV_INSPECT` | Raw UV layout inspection |
| `PERFORMANCE` | Timing of the build pipeline |
| `CSG_DEBUG` | Boolean / CSG operation diagnostics |
| `RENDER` | Full render output |
| `SKILL_EXEC` | Runs the cartridge as a skill script |
| `CONSOLE_AUDIT` | Audits the console property system |

### Examples — verified working

Audit the mezzanine (PASS):
```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/cart_arc_07_mezzanine.py --mode AUDIT
```

Audit a pipe primitive (PASS):
```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/cart_prim_02_pipe.py --mode AUDIT
```

Audit the wall (reveals fuzz-crash bug in `tag_socket` with hole params):
```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/cart_arc_01_wall.py --mode AUDIT
```

### Bulk Audit

To audit every cartridge in one pass (pipe through Python):

```bash
for f in massa/modules/cartridges/cart_*.py; do
  echo "=== $f ===" 
  python _Scripts/test_run_cartridge.py "$f" --mode AUDIT 2>&1 | tail -6
done
```

## Run (Agent Path) — Live Blender via MCP

When Blender is running with the MCP add-on enabled and connected, use the `mcp__blender__massa_*` MCP tools:

- `mcp__blender__massa_list_cartridges` — list installed cartridges
- `mcp__blender__massa_spawn_cartridge` — spawn a cartridge into the scene
- `mcp__blender__massa_get_selected_geometry` — inspect active object geometry
- `mcp__blender__massa_mesh_boolean` / `massa_mesh_clean` — pipeline ops
- `mcp__blender__get_screenshot_of_window_as_image` — screenshot current Blender window
- `mcp__blender__execute_blender_code` — run arbitrary `bpy` code

MCP tools are the right path when you need to verify live UI behavior, inspect scene state, or screenshot the Blender viewport.

## Run (Human Path)

1. Run `python _Scripts/package_massa_addon.py` → produces `_EXPORT/massa.zip`
2. In Blender: Edit → Preferences → Add-ons → Install → select `_EXPORT/massa.zip`
3. Enable the "MASSA" addon
4. The MASSA panel appears in the 3D Viewport N-panel

This path requires a display; it is not usable headless.

## Gotchas

- **Fuzz crashes in AUDIT mode are real bugs.** The fuzz auditor randomizes parameters widely including negative dimensions and edge-case values. `FUZZ_CRASH` errors in the output are genuine cartridge bugs, not test noise. `cart_arc_01_wall.py` has a known crash when `hole_enable` is used with certain param combos.
- **`BLENDER_PATH` must exist before any script runs.** `config.py` calls `sys.exit(1)` if the exe is missing. Check the path if you see `CRITICAL ERROR: Blender not found at ...`.
- **`sys.exit(1)` in config.py is conditional but loud.** If Blender is not at the configured path, all test scripts will abort immediately with a clear error — not a Python import error.
- **Audit output is JSON inside Blender's stdout.** Blender prints a lot of startup noise to stdout. The script strips it; only the JSON between `---AUDIT_START---` / `---AUDIT_END---` is returned. If you run Blender directly, you'll see the raw noise.
- **The `debugging_system/` directory is excluded from the addon ZIP.** Never reference it from cartridge code — it won't be present in a user install.
- **130+ cartridges, most are untested on every commit.** `AUDIT` mode is the CI equivalent. Run it on every cartridge you touch.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `CRITICAL ERROR: Blender not found at C:\Program Files\...` | Edit `massa/modules/debugging_system/config.py` and set `BLENDER_PATH` to the actual Blender 5.1 exe path |
| `SYSTEM_FAILURE: Blender crashed or returned no data.` | Blender itself crashed — check the `log` field in the JSON for a Python traceback |
| `FUZZ_CRASH: BMesh data of type BMFace has been removed` | Cartridge calls `tag_socket` on a face after the face has been deleted (e.g., by an inset or cut operation). Guard with a validity check before `tag_socket`. |
| Package script says `Warning: Could not remove old package` | The old `massa.zip` is open (Blender may have it locked). Close Blender and retry. |
| MCP tools return `connection refused` | Blender is not running, or the MCP add-on is not enabled/connected in Blender preferences |
