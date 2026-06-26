---
name: cart-skill
description: >
  Diagnose and fix MASSA Blender cartridges in massa/modules/cartridges/.
  ALWAYS trigger immediately when the user's message begins with "Cart_skill" — this is a hard keyword trigger, no exceptions.
  Also use when the user reports: broken UV unwrap, seam errors, edge slot problems, wrong material slots (0-9), geometry shape errors,
  wrong object placement, parameter behavior regressions, viewport/render mismatches, CRITICAL audit flags, FUZZ_CRASH in test output,
  or any request to "fix", "repair", "audit", or "clean up" a cartridge.
  Covers three issue families: (1) UV / seam / edge-slot errors, (2) geometry / topology / shape errors, (3) material slot assignment errors.
---

# Cart-Skill — MASSA Cartridge Diagnosis & Repair

When a user message starts with **Cart_skill**, execute this skill in full.
Three issue families are handled. Gather evidence first, classify second, then follow the matching path.

**Core rule:** Do not edit a cartridge until you have a baseline audit, a short shape contract, and a repair hypothesis backed by runtime or visual evidence. For simple issues the evidence packet can be short, but it must exist.

All paths below are relative to the repo root `MASSA_BMESH_CONSOLE-main/`.

---

## Step 0 — Identify the Cartridge

Extract the cartridge filename or path from the user's message.
If not given, list available cartridges:
```
mcp__blender__massa_list_cartridges
```
Or glob for the file:
```
massa/modules/cartridges/cart_*.py
```
Confirm the target before proceeding.

---

## Step 1 — Baseline Audit (mandatory, do this before anything else)

The headless audit is the only way to surface runtime crashes. Do not read source code or classify issues until you have the audit output in hand.

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
```

Parse the JSON between `---AUDIT_START---` / `---AUDIT_END---`. The runner emits a **structured, severity-aware** result — read the structured fields, not just the flat `errors` list.

### Audit Output Reference (current schema)

```jsonc
{
  "status": "PASS" | "FAIL",          // FAIL iff there is >=1 CRITICAL issue
  "mode": "AUDIT",
  "object": "<generated object name>",
  "operator": "massa.gen_<id>",
  "summary": { "critical": N, "warning": N, "info": N, "total": N },
  "issues": {
    "critical": [ ... ],              // these FAIL the audit — primary repair targets
    "warning":  [ ... ],              // advisory; see severity note below
    "info":     [ ... ]              // informational only
  },
  "auditors": {
    "ran":     ["massa_auditor","massa_edge_auditor","massa_fuzz_auditor",
                "massa_surface_auditor","massa_topology_extra","massa_ui_auditor"],
    "skipped": [],                    // an auditor with no audit_mesh() entry point
    "by_auditor": { "<auditor>": [ "<flag>", ... ] }   // attribution per source
  },
  "telemetry": { ... },               // full mesh data — see Step 2C
  "execution_time_ms": 12.3,
  "errors": [ ... ]                  // backward-compat flat list = critical+warning+info
}
```

A SYSTEM_FAILURE result (Blender crash / launch / registration failure) instead carries
`{status:"SYSTEM_FAILURE", message, returncode, stdout_tail, stderr_tail}`. **Read `stderr_tail`** — Blender writes Python tracebacks there. A timeout reports `"Blender timed out after Ns."`.

### How to read it

- **`status` / `summary.critical` is the pass/fail gate.** Anything in `issues.critical` is a real repair target. `FUZZ_CRASH` (cartridge crashes on randomized params) is always critical — **fix it first**.
- **Severity is already classified — do NOT key off the literal `CRITICAL_` string prefix.** Some `CRITICAL_*`-named flags are intentionally downgraded into `issues.warning` because they are valid for this addon's parts (open shells, flat panels, thin strips). Trust the bucket the flag is in: `CRITICAL_NON_MANIFOLD_*`, `CRITICAL_FLAT_Z_AXIS`, `CRITICAL_NO_PERIMETER_DEFINED`, `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH`, `WARNING_THIN_FACES_*`, and isolated-seam flags land in **warning**. Treat warnings as advisory unless one of them directly explains the user's reported defect.
- **Use `auditors.by_auditor` to attribute findings.** `massa_surface_auditor` → UV/normals/self-intersection; `massa_edge_auditor` → seams/edge slots; `massa_auditor` → dimensions/slot-layer/integrity; `massa_topology_extra` → loose verts/wire edges; `massa_fuzz_auditor` → parameter-fuzz crashes; `massa_ui_auditor` → operator/panel metadata.
- **`auditors.skipped` should be empty.** If an auditor name appears there, that auditor has no `audit_mesh()` entry point and its checks are NOT running — note it as a tooling gap.
- **`telemetry` usually replaces temporary geometry harnesses** (see Step 2C).

If Bash is unavailable (permissions blocked), note the limitation clearly, then proceed with static source analysis — but flag that runtime crashes may be present that static analysis cannot detect.

Also take a visual baseline if Blender MCP is connected:
```
mcp__blender__massa_spawn_cartridge   (spawn it)
mcp__blender__get_screenshot_of_window_as_image
```

---

## Step 2 - Build the Evidence Packet (mandatory before editing)

After the baseline audit, build a compact evidence packet. This is where the agent converts source and runtime output into understanding.

### 2A - Static Shape Contract

Read the target cartridge after the audit. Extract:

- `CARTRIDGE_META` name, id, flags, and intended category.
- All `bpy.props`: enums, booleans, dimensions, segment counts, min/max/default values.
- `get_slot_meta()` slot names, UV strategies, phys keys, sockets.
- `build_shape()` phases: profile creation, extrusion/spin/boolean/inset steps, slot assignment, edge-slot assignment, UV assignment.

Write a 5-10 line contract before editing:

```
Shape contract:
- Modes:
- Expected orientation/axis:
- Expected bounds/proportions:
- Material slots:
- Edge-slot/seam roles:
- Sockets:
- Parameter risks:
```

If the user named a reference cartridge, build the same contract for the reference and compare:

- prop names and mode semantics
- slot ids and slot meanings
- edge-slot writes (`MASSA_EDGE_SLOTS`) and seam/sharp behavior
- UV strategy and manual UV math
- object orientation, bounds, sockets, and optional parts

### 2B - Parameter Matrix Simulation

Simulate meaningful parameter variants, not just defaults. At minimum include:

- default values
- every enum mode
- every boolean feature both on and off when relevant
- minimum legal segment counts
- small dimensions near property minima
- thin and thick wall/profile cases
- user-reported values, if provided
- reference-matching values, if comparing to another cartridge

Use the smallest available runtime path:

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode PERFORMANCE
```

Note: `--mode AUDIT` runs `massa_fuzz_auditor`, which already fuzzes the cartridge's own properties (5 randomized iterations, vector-aware, ranges clamped to soft limits) and reports any `FUZZ_CRASH` with the exact failing `PARAMS`. Treat that as automatic coverage of the random-parameter space, then add the targeted variants above for the specific cases you care about.

If the cartridge exposes enum modes, prefer the bundled matrix helper before writing a one-off harness:

```
python .agents/skills/cart-skill/scripts/run_cartridge_matrix.py massa/modules/cartridges/<name>.py --enum <enum_prop> --set fit_uvs=true
```

Use `--set name=value` for additional operator overrides. The helper runs Blender directly from `massa/modules/debugging_system/config.py::BLENDER_PATH`, executes each enum value in a clean scene, prints JSON telemetry, and deletes its temporary harness.

If the current runner cannot set operator parameters directly and the helper does not cover the case, use Blender MCP, `SKILL_EXEC`, or a temporary targeted harness to instantiate the operator, set properties, run the pipeline, and print JSON summaries. On Windows, shell quoting often mangles `--payload` JSON; if two quoting attempts fail, stop fighting the shell and use the matrix helper or a temporary Blender script instead. Put temporary harnesses under `_Scripts/__cart_matrix_tmp.py` or `C:\tmp`, remove them before final delivery, and state if parameter simulation was blocked.

For each variant, record the fields below. Most come straight from the AUDIT `telemetry` block — no harness needed:

```
case          -> the variant you ran
status        -> result.status + summary.critical
bbox / dims   -> telemetry.bounds_local / telemetry.dimensions
verts/edges/faces -> telemetry.geometry.{verts,edges,faces} (+ ngon_faces, tris_equiv)
material_slots    -> telemetry.materials
edge_slot_counts  -> telemetry.edge_slots.histogram   (slot id -> tagged edge count)
uv_state          -> telemetry.uv.{layer_count, bounds, collapsed_faces}
watertight        -> telemetry.geometry.is_watertight (+ non_manifold_edges, loose_verts)
new_flags         -> issues.critical / issues.warning that this variant introduced
```

### 2C - Runtime Geometry Summary

For shape/topology/material/edge-slot work, inspect the generated geometry in addition to raw audit status.

**Primary source: the AUDIT `telemetry` block** (also present on `--mode PERFORMANCE`). It answers most geometry questions with no extra tooling:

```jsonc
telemetry: {
  geometry: { verts, edges, faces, tris_equiv, tri_faces, quad_faces, ngon_faces,
              open_edges, non_manifold_edges, wire_edges, loose_verts, is_watertight },
  bounds_local: { min:[x,y,z], max:[x,y,z] },
  dimensions: [x,y,z],                 // world-space (accounts for scale)
  edge_slots: { layer_present, tagged_edges, histogram:{ "1":N, "3":N, ... } },
  uv: { layers:[...], layer_count, bounds:{min:[u,v],max:[u,v]}, collapsed_faces },
  materials: ["Metal Iron", ...],      // final compressed material list
  modifiers: [{name,type}, ...],
  transform: { location, rotation_euler, scale },
  massa_op_id, has_massa_params, custom_prop_keys
}
```

Read it against the shape contract: expected bounds/proportions (`dimensions`, `bounds_local`), slot coverage (`materials`, `edge_slots.histogram`), seam roles (`edge_slots.histogram` keys 1/3/5), UV health (`uv.bounds` inside 0–1, `uv.collapsed_faces == 0`), and manifold/closed state (`is_watertight`, `open_edges`, `non_manifold_edges`).

For UV work, separate **default tiling** from **fitted UVs**:
- `fit_uvs=False` may intentionally produce UV bounds outside 0–1 to preserve texel density. Do not call that a failure by itself.
- `fit_uvs=True` must normalize the relevant UVs into 0–1 with `telemetry.uv.collapsed_faces == 0`.
- If a full AUDIT fails only because of unrelated geometry flags, still report the UV-only result separately from the overall cartridge status.

**Deeper inspection (only when telemetry is insufficient):** prefer Blender MCP when connected —
```
mcp__blender__massa_spawn_cartridge
mcp__blender__get_objects_summary
mcp__blender__get_object_detail_summary
mcp__blender__massa_get_selected_geometry   (per-edge MASSA_EDGE_SLOTS / seam / sharp, per-face material_index)
```
If MCP is unavailable and you need per-element data the telemetry doesn't expose (e.g. *which* edges carry a slot), use a temporary summary harness under `_Scripts/__cart_*_tmp.py` and remove it before delivery.

### 2D - Visual Viewport Analysis

For wrong shape, placement, UV, edge marking, reference comparison, or material bleed, create images and inspect them before editing and after editing:

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode RENDER --payload "{\"camera_angle\":\"ISO_CAM\"}"
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode RENDER --payload "{\"camera_angle\":\"ISO_CAM\",\"shading\":\"WIREFRAME\"}"
```

For UV or seam-slot work, also capture a console-equivalent evidence render that turns on **Preview: UV Check** and **Edge Viz: Slots** before generation:

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode RENDER --payload '{"camera_angle":"ISO_CAM","operator_props":{"debug_view":"UV","viz_edge_mode":"SLOTS","show_wireframe":true}}'
```

This render should show the UV checker material plus colored edge-slot lines. Confirm the JSON includes `operator_props.applied.debug_view == "UV"`, `operator_props.applied.viz_edge_mode == "SLOTS"`, and non-empty `render_overlays.edge_slots.counts` when the shape has tagged edge slots. If shell JSON quoting fails on Windows, use the payload-env path instead of hand-escaping JSON:

```powershell
$env:MASSA_RENDER_PAYLOAD = ConvertTo-Json -InputObject @{camera_angle='ISO_CAM'; operator_props=@{debug_view='UV'; viz_edge_mode='SLOTS'; show_wireframe=$true}} -Compress
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode RENDER --payload-env MASSA_RENDER_PAYLOAD
```

Use `UV_INSPECT` / `UV_HEATMAP` for UV or seam issues. Use `VISUAL_DIFF` when comparing against a backup or reference:

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode VISUAL_DIFF --payload "{\"filename_b\":\"<reference_or_backup>.py\"}"
```

Open generated images with the available image-viewing tool. Parse the image against the shape contract: orientation, proportions, openings, optional parts, sockets, material regions, visible seams/edge slots, and whether the viewport result matches the code change. Do not rely on "render succeeded" alone.

`UV_INSPECT` is camera-bound to the 0–1 UV square. If default tiling puts islands outside 0–1, the image may look blank or unhelpful even when UV data is valid. In that case, verify `fit_uvs=True` with telemetry or the matrix helper before declaring the unwrap broken.

### 2E - Hypothesis Gate

Before editing, state:

```
Observed evidence:
Root cause hypothesis:
Targeted edit:
Expected verification change:
```

If the evidence does not support a specific hypothesis, gather more data instead of patching.

---

## Step 3 - Classify the Issue

Classify each entry by which `auditors.by_auditor` source produced it and which token it carries — not by the raw `CRITICAL_`/`WARNING_` prefix (severity is already bucketed for you).

| Signal | Family |
|---|---|
| `FUZZ_CRASH` (any traceback from `build_shape`, with failing `PARAMS`) | **B — Geometry / Topology** — fix this first, always |
| `CRITICAL_ZERO_AREA_FACES`, `CRITICAL_EMPTY_MESH`, `CRITICAL_LOOSE_VERTS`, `CRITICAL_WIRE_EDGES`, `CRITICAL_SELF_INTERSECTION`, `CRITICAL_INVERTED_NORMALS`, wrong shape/proportions/placement | **B — Geometry / Topology** |
| `CRITICAL_MISSING_UV_LAYER`, `CRITICAL_ZERO_UV_DATA`, `CRITICAL_COLLAPSED_UVS`, `CRITICAL_UV_SPIKES`, `WARNING_PINCHED_UV_FACES`, `WARNING_ISOLATED_SEAM_EDGES`, `telemetry.uv.bounds` outside 0–1, `telemetry.uv.collapsed_faces > 0`, seam lines visible in render, red heatmap | **A — UV / Seam / Edge Slot** |
| `CRITICAL_MISSING_SLOT_LAYER`, wrong material on faces, faces missing material, slot indices in `build_shape` not in `get_slot_meta`, invalid `phys` values, material bleed between parts | **C — Material Slot** |

**Warnings (advisory):** `CRITICAL_NON_MANIFOLD_*`, `CRITICAL_FLAT_Z_AXIS`, `CRITICAL_NO_PERIMETER_DEFINED`, `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH`, `WARNING_THIN_FACES_*` arrive in `issues.warning` because they are valid for many parts. Act on them **only** when they explain the user's reported defect (e.g. a part that should be a closed volume showing `NON_MANIFOLD`, or a seam-less complex mesh that genuinely needs seams). Otherwise note and move on.

A cartridge can have issues in more than one family. Fix order: **B first** (a crashing cartridge can't be UV-debugged), then C (slots drive UV strategies), then A (UVs last).

Classify only after completing the Step 2 evidence packet. If the evidence packet reveals multiple issue families, keep the fix order above and re-run the relevant matrix/render checks after each family.

### Mixed Audit / UV-Only Status

Sometimes full `AUDIT` fails on geometry while UVs are healthy. In that case:

1. Do **not** claim the cartridge fully passes.
2. Do report whether the requested UV concern is resolved using `telemetry.uv`, UV modes, heatmap/inspect output, and edge-slot histograms.
3. State the remaining non-UV criticals separately with their auditor source.
4. If the remaining geometry critical blocks trustworthy UV assessment (for example degenerate faces or self-intersection that corrupts UVs), fix geometry first or report that UV verification is blocked.

---

## Family A — UV / Seam / Edge Slot Fix

**Reference workflow:** `.agents/workflows/UV_unwrap.md`

### A1 — Inspect Current State

If Blender MCP is connected and the object is in the scene:
1. `mcp__blender__massa_get_selected_geometry` (enter Edit Mode first) — check `MASSA_EDGE_SLOTS` values, `is_seam`, `is_sharp` on all edges.
2. Run UV modes headlessly:
```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode UV_INSPECT
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode UV_HEATMAP
```
UV_INSPECT shows island layout and seam placement.
UV_HEATMAP shows distortion (blue/green = good, red = stretched).

Cross-reference the AUDIT `telemetry.uv` block (`layers`, `bounds`, `collapsed_faces`) and the `massa_surface_auditor` / `massa_edge_auditor` entries in `by_auditor` — they pinpoint the failure without needing a render.

### A2 — Diagnose from Output

| Signal (audit flag / telemetry) | Root Cause | Fix |
|---|---|---|
| `CRITICAL_MISSING_UV_LAYER` / `telemetry.uv.layer_count == 0` | `build_shape` never created/wrote a UV layer | Add manual UV math, or set a slot `uv` strategy (`"BOX"`/`"UNWRAP"`) so the pipeline unwraps |
| `CRITICAL_ZERO_UV_DATA` (all UVs at 0,0) | `get_slot_meta` is `"SKIP"` but `build_shape` never writes UVs | Add manual UV math or change strategy to `"BOX"` / `"UNWRAP"` |
| `telemetry.uv.bounds` outside 0–1 / islands outside space | Manual UV math overflows | Normalize with `uv_scale` / `fit_uvs` logic |
| `CRITICAL_COLLAPSED_UVS_N` / `telemetry.uv.collapsed_faces > 0` | Faces have 3D area but zero UV area (lazy planar projection on sides) | Give those faces real UVs (box-map or per-face unwrap) |
| Smeared band on one face of a closed loop | Missing wrapping fix | Apply the cylindrical seam wrapping fix (see below) |
| Overlapping islands (no surface flag, visible in UV_INSPECT) | No seams cut | Tag edges: slot 1 for perimeter, slot 3 for hidden guide zippers |
| `WARNING_ISOLATED_SEAM_EDGES_N` | Seam not forming a continuous loop | Extend the seam path to close the loop |
| `CRITICAL_UV_SPIKES_N` / extreme distortion | Thin or degenerate face | Fix topology first (Family B), then re-audit |

### A3 — Edge Slot Assignment in Code

Read `build_shape` in the cartridge. Retrieve/create layers at the top of the function:
```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
force_seam = bm.edges.layers.int.get("massa_force_seam") or bm.edges.layers.int.new("massa_force_seam")
```

| Slot | Role | When to use |
|---|---|---|
| 1 | Perimeter / cap | Open borders, cap loops, visible silhouettes that must be protected as seam+sharp |
| 2 | Contour / material boundary | Hard internal form breaks and material-transition edges; do not overwrite protected slot 1 or slot 3 seams |
| 3 | Protected guide / zipper | Longitudinal unwrap cuts, hidden zippers, segment cut rings, relief seams |
| 4 | Detail | Small chamfers, soft feature lines |
| 5 | Fold | Subdivision crease |

Use `e.seam = True` and `force_seam = 1` for slots 1 and 3 when the seam must survive downstream processing. Avoid broad "all hard angles are slot 1" passes; they make perimeter intent unreadable and can bury the one guide seam UV unwrap needs.

### A4 — Wrapping Fix (closed-loop surfaces)

For any extruded profile (beam, pipe, wall, column): the face that spans the seam will smear without this fix.
```python
for f in bm.faces:
    if f.material_index != 0:
        continue
    loop_uvs = [[l, get_u(l.vert.co.x, l.vert.co.z), l.vert.co.y] for l in f.loops]
    us = [item[1] for item in loop_uvs]
    if (max(us) - min(us)) > (perim * 0.5):
        for item in loop_uvs:
            if item[1] < (perim * 0.5):
                item[1] += perim
    for l, u, v in loop_uvs:
        l[uv_layer].uv = (u * su_s, v * sv_s)
```

### A5 — Live Edge Slot Fix via MCP (optional, when Blender is connected)

Workflow from `.agents/workflows/02_massa_mesh_and_slots_workflow.md`:
1. Ensure Edit Mode, select target edges.
2. `mcp__blender__massa_get_selected_geometry` — confirm current slot values.
3. `mcp__blender__massa_assign_edge_slot_to_selection` with `slot` (1–5) and `action` (`SEAM`/`SHARP`/`BOTH`/`CREASE`/`BEVEL`/`IGNORE`).
4. Re-check with `mcp__blender__massa_get_selected_geometry`.

The MCP tool also returns a **procedural cartridge snippet** — inject it into `build_shape` so the fix is permanent.

### A6 — Verify

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode UV_INSPECT
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode UV_HEATMAP
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode RENDER --payload '{"camera_angle":"ISO_CAM","operator_props":{"debug_view":"UV","viz_edge_mode":"SLOTS","show_wireframe":true}}'
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
```
Pass criteria: no UV flags in `issues.critical` (`MISSING_UV_LAYER`, `ZERO_UV_DATA`, `COLLAPSED_UVS`, `UV_SPIKES`), `telemetry.uv.collapsed_faces == 0`, fitted-mode `telemetry.uv.bounds` within 0–1, readable UV_INSPECT when fitted, heatmap mostly blue/green, the evidence render was exported with UV Check + Edge Viz Slots applied, and `edge_slots.histogram` / `render_overlays.edge_slots.counts` contain the expected perimeter/guide slots for the shape contract.

---

## Family B — Geometry / Topology Fix

**Reference docs:** `docs/blender-addon-docs/CARTRIDGE_MANDATE.md` (§5, §6), `.agents/workflows/WF_CARTRIDGE_MODIFY.md`

### B1 — Inspect Shape

If Blender MCP is connected:
```
mcp__blender__massa_spawn_cartridge
mcp__blender__get_objects_summary
mcp__blender__get_object_detail_summary   (target object)
mcp__blender__get_screenshot_of_window_as_image
```
Check: vertex count, face count, non-manifold edges, normals, overall proportions match intent.

For shape, placement, or proportion issues, also use the Step 2 runtime geometry summary and parameter matrix. A clean AUDIT result is not enough when the reported problem is visual or behavioral.

For headless inspection: the AUDIT output already surfaces topology flags AND a `telemetry.geometry` block (`verts/edges/faces`, `non_manifold_edges`, `wire_edges`, `loose_verts`, `is_watertight`, `ngon_faces`). Parse those before reaching for MCP.

### B2 — Fix by Flag

Critical flags (in `issues.critical`) — fix these:

| Flag | Source auditor | Fix |
|---|---|---|
| `FUZZ_CRASH` | `massa_fuzz_auditor` | Read the traceback **and the failing `PARAMS`** in the flag; reproduce with those values, then protect the crashing op (`if not f.is_valid: continue`, size guard, or handle the degenerate param). Fix this first. |
| `CRITICAL_ZERO_AREA_FACES_N` | `massa_auditor` / `massa_surface_auditor` | Add a size guard: `if self.length < 0.001: return`. Or `bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges[:])` |
| `CRITICAL_EMPTY_MESH` | `massa_auditor` | `build_shape` produced no geometry for some params — add a guard / ensure the profile builds |
| `CRITICAL_LOOSE_VERTS_N` | `massa_auditor` / `massa_topology_extra` | `bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')` |
| `CRITICAL_WIRE_EDGES_N` | `massa_topology_extra` | Edges with no faces — remove them or build the missing face |
| `CRITICAL_SELF_INTERSECTION` | `massa_surface_auditor` | Geometry overlaps itself (non-neighbor faces) — usually an inset/boolean/extrude overshoot; clamp the offending offset. Confirm visually (RENDER) before treating as a hard defect — extreme params can trip the BVH heuristic. |
| `CRITICAL_INVERTED_NORMALS` | `massa_surface_auditor` | >50% of faces point inward — call `bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])` or fix winding order |
| `CRITICAL_MISSING_SLOT_LAYER` | `massa_auditor` | Add `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")` at top of `build_shape` (Family C / A overlap) |

Advisory flags (in `issues.warning`) — act only if they explain the reported defect:

| Flag | Fix if relevant |
|---|---|
| `CRITICAL_NON_MANIFOLD_N` | Valid for open shells. If the part *should* be a closed volume: find T-junctions/open holes, use `bmesh.ops.fill` or fix bridge logic |
| `CRITICAL_NO_PERIMETER_DEFINED` | If silhouette needs bevels/seams: tag silhouette edges with slot 1 on `MASSA_EDGE_SLOTS` |
| `WARNING_THIN_FACES_N` | If slivers cause UV/bevel artifacts: rebuild the affected loops — usually a profile point is nearly collinear |
| `CRITICAL_FLAT_Z_AXIS` | Expected for flat panels; investigate only if the part should have Z thickness |

### B3 — Shape / Placement Issues (no audit flag)

When the shape looks wrong visually:
1. Read `build_shape` top-to-bottom using jCodemunch (`get_symbol_source`).
2. Identify which phase produces the wrong geometry (profile definition, extrusion, segmentation, cap normal forcing).
3. Make the targeted fix — smallest possible change.
4. Run VISUAL_DIFF against a backup:
```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode VISUAL_DIFF \
  --payload '{"filename_b": "massa/modules/cartridges/<name>_backup.py"}'
```

Before editing, compare the visible result to the Step 2 shape contract and parameter matrix. After editing, inspect the rendered image again and state whether the object now matches the contract.

### B4 — Headless Safety Rules (non-negotiable)

- No `bpy.ops` inside `build_shape` — use `bmesh.ops` only.
- No `bpy.context` reads inside `build_shape`.
- No `bpy.data` creation inside `build_shape`.
- Call `bm.verts.ensure_lookup_table()` (and `.edges`, `.faces`) after any `bm.verts.new()` call.
- Wrap `bm.faces.new(verts)` in `try/except ValueError`.

### B5 — Verify

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
```
`summary.critical` same or lower than baseline; no new entries in `issues.critical`; no new `FUZZ_CRASH`; `telemetry.geometry.is_watertight` / counts consistent with the shape contract.
If geometry was changed, also screenshot from Blender MCP and confirm visually.

---

## Family C — Material Slot Fix

**Reference:** `.agents/workflows/02_massa_mesh_and_slots_workflow.md`

### C1 — Read Current Slot State

Three things to check — all matter:

**1. Index coverage:** Read `get_slot_meta()` and note every slot index defined. Read `build_shape` and note every `f.material_index = N` assignment. Every index used in `build_shape` must appear in `get_slot_meta`, and every slot in `get_slot_meta` should be used by at least one face.

**2. Phys value validity:** For every slot in `get_slot_meta`, verify the `phys` value is a real key in `MASTER_MAT_DB` (defined in `massa/utils/mat_utils.py` — read it to get the authoritative current key list rather than trusting this doc). Invalid phys values (`"METAL_CHECKERPLATE"`, `"METAL_PAINTED"`, `"DEBUG_9"`, etc.) silently fall back to a default material at runtime. Known-valid keys include: `METAL_IRON`, `METAL_STEEL`, `CONCRETE_RAW`, `RUBBER`, `GLASS_CLEAR`, `FABRIC_ROUGH`, `WOOD_OAK`, `PLASTIC_HARD`, `GENERIC`, `MASSA_DEBUG_1` through `MASSA_DEBUG_9`.

**3. Final material list:** Check `telemetry.materials` from the AUDIT output — this is the compressed material list actually applied to the object. A slot resolving to an unexpected/duplicate/`Generic` material here is a symptom of an invalid `phys` key or a slot that no face uses.

If Blender MCP is connected (Edit Mode, faces selected):
```
mcp__blender__massa_get_selected_geometry   → check material_index per face
```

### C2 — Fix Mismatches

| Problem | Fix |
|---|---|
| `build_shape` uses slot index not in `get_slot_meta` | Add the missing slot to `get_slot_meta` with correct `name`, `uv`, `phys` |
| `get_slot_meta` defines a slot but no faces use it | Either remove the unused slot or assign the correct faces to it |
| Invalid `phys` value (not in `MASTER_MAT_DB`) | Replace with the closest valid key (e.g. `METAL_CHECKERPLATE` → `METAL_IRON`) |
| Socket slot not on index 9 | Move socket faces to `material_index = 9`, set `"sock": True` and `"uv": "SKIP"` in `get_slot_meta[9]` |

Valid `uv` strategies: `"SKIP"`, `"BOX"`, `"FIT"`, `"TUBE_Z"`, `"TUBE_Y"`, `"TUBE_X"`, `"UNWRAP"`.
Use `"SKIP"` for any slot where `build_shape` writes UVs manually.

### C3 — Live MCP Face Slot Assignment

If fixing face assignments interactively (Blender connected, Edit Mode, faces selected):
1. `mcp__blender__massa_get_selected_geometry` — confirm current `material_index`.
2. `mcp__blender__massa_assign_face_material_slot_to_selection` with target slot index.
3. `mcp__blender__massa_get_selected_geometry` — verify.

Then mirror the fix back into `build_shape` (`f.material_index = N` on the correct faces).

### C4 — Verify

```
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<name>.py --mode AUDIT
```
Confirm `get_slot_meta` covers all indices used in `build_shape`. No new flags.

---

## Step 4 - Final Delivery Checklist

Before reporting done:

- [ ] `summary.critical == 0` (or same/fewer than baseline) — no entries in `issues.critical`
- [ ] No `FUZZ_CRASH` events
- [ ] `auditors.skipped` is empty (all six auditors ran)
- [ ] Any remaining `issues.warning` entries are understood and judged not to be the reported defect
- [ ] If full AUDIT still fails, UV-only status is reported separately and not presented as a full cartridge pass
- [ ] Shape contract written and used to justify the edit
- [ ] Parameter matrix run, or limitation stated with a fallback static/runtime check
- [ ] `telemetry` checked against the shape contract (bounds/dimensions, geometry counts, `is_watertight`, `edge_slots.histogram`, `materials`)
- [ ] Relevant viewport/UV/render images inspected, not merely generated
- [ ] Reference cartridge comparison performed when a reference was named
- [ ] No existing `bpy.props` renamed or removed
- [ ] `get_slot_meta()` covers all face slot indices used in `build_shape`
- [ ] `draw_shape_ui` reflects any newly added properties
- [ ] Default tiling and `fit_uvs=True` are checked separately when UV bounds are part of the task
- [ ] `telemetry.uv.bounds` within 0–1 and `telemetry.uv.collapsed_faces == 0` when `fit_uvs = True`
- [ ] Backup file removed (or noted if kept for versioning)

Report: shape contract summary, evidence found (cite `summary` counts + key `issues`/`telemetry` fields), root cause, what changed, parameter/visual checks, and the before/after audit `summary` (critical/warning/info).
