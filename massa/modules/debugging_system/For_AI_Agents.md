# MASSA Debugging System — Reference for AI Agents

This folder contains the headless debugging suite for the MASSA addon. All tools run outside Blender's GUI by spawning a background Blender process and communicating via stdin/stdout.

---

## 0. Setup

Edit `config.py` and set `BLENDER_PATH` to your local Blender executable before using any tool:

```python
# config.py
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
```

Platform examples:

- **Windows**: `r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"`
- **macOS**: `"/Applications/Blender.app/Contents/MacOS/Blender"`
- **Linux**: `"/usr/bin/blender"`

---

## 1. `debug_agent.py` — Live State Inspection

Executes arbitrary Python inside an active headless Blender instance. Use this to inspect the live Blender data model.

**Inline code:**

```bash
python modules/debugging_system/debug_agent.py --code "import bpy; print(bpy.data.objects.keys())"
```

**File execution** (recommended for complex logic):

```bash
# 1. Write your inspection logic to a file:
#    temp_inspect.py → your bpy logic here
# 2. Execute it:
python modules/debugging_system/debug_agent.py --file temp_inspect.py
```

---

## 2. `runner.py` — Cartridge Audit Runner

The primary audit tool. Runs a cartridge through the generation pipeline headlessly and validates the result.

**Base syntax:**

```bash
python modules/debugging_system/runner.py --cartridge <path_to_cartridge.py> --mode <MODE>
```

### Modes

| Mode | Command | What It Does |
| :--- | :--- | :--- |
| **AUDIT** | `--mode AUDIT` | Full geometry checks: topology, slots, UVs, normals, seams. Fuzz testing runs automatically. |
| **VISUAL_DIFF** | `--mode VISUAL_DIFF --payload '{"filename_b": "<path_b>"}'` | Renders a red/green wireframe overlay comparing two cartridge versions. |
| **UV_HEATMAP** | `--mode UV_HEATMAP` | Renders a UV distortion heatmap. Red = bad stretching, Blue = good. |
| **UV_INSPECT** | `--mode UV_INSPECT` | Renders the 2D UV layout (0–1 space). Check for overlaps and out-of-bounds islands. |
| **PERFORMANCE** | `--mode PERFORMANCE` | Reports execution time (ms) and polycount against budget thresholds. |

**Examples:**

```bash
# Standard geometry audit
python modules/debugging_system/runner.py --cartridge modules/cartridges/cart_prim_01_beam.py --mode AUDIT

# Compare two versions
python modules/debugging_system/runner.py \
  --cartridge modules/cartridges/cart_prim_01_beam.py \
  --mode VISUAL_DIFF \
  --payload '{"filename_b": "modules/cartridges/cart_prim_01_beam_v2.py"}'

# UV distortion heatmap
python modules/debugging_system/runner.py --cartridge modules/cartridges/cart_prim_01_beam.py --mode UV_HEATMAP
```

**Output format:** JSON wrapped in `---AUDIT_START---` / `---AUDIT_END---` markers.

---

## 3. Auditors — What They Check

The `auditors/` sub-package runs automatically during AUDIT mode. Each auditor targets a specific concern:

| Auditor | File | Checks |
| :--- | :--- | :--- |
| **Topology** | `massa_auditor.py` | Empty mesh, flat Z axis, missing slot layer, loose verts, non-manifold edges, zero-area faces, thin sliver faces. |
| **Edge Slots** | `massa_edge_auditor.py` | Missing `MASSA_EDGE_SLOTS` layer, no seams on complex meshes (>12 faces), isolated seam edges. |
| **Surface** | `massa_surface_auditor.py` | Missing UV layer, zero UV data, inverted normals, zero-area faces, self-intersections, UV spikes, collapsed UVs. |
| **Fuzz** | `massa_fuzz_auditor.py` | Randomizes parameters and re-runs generation to catch crashes on edge-case inputs. |
| **UI** | `massa_ui_auditor.py` | Validates operator properties and UI draw calls. |
| **Topology Extra** | `massa_topology_extra.py` | Extended topology checks beyond the base auditor. |

---

## 4. Audit Flags Reference

Flags are returned in the `"flags"` list of the JSON output. Anything prefixed `CRITICAL_` must be fixed before a cartridge is considered stable.

### Topology Flags (`massa_auditor.py`)

| Flag | Meaning | Fix |
| :--- | :--- | :--- |
| `CRITICAL_EMPTY_MESH` | No geometry was created. | Check `build_shape` logic. |
| `CRITICAL_FLAT_Z_AXIS` | Geometry has zero height. | Check `bmesh.ops.scale` or extrusion logic. |
| `CRITICAL_MISSING_SLOT_LAYER` | No `MASSA_EDGE_SLOTS` layer found. | Create layer: `bm.edges.layers.int.new("MASSA_EDGE_SLOTS")`. |
| `CRITICAL_NO_PERIMETER_DEFINED` | No edges tagged as role 1 (Perimeter). | Tag silhouette edges with `e[edge_slots] = 1`. |
| `CRITICAL_LOOSE_VERTS_N` | N vertices not connected to any edge. | Run `bmesh.ops.remove_doubles` or delete orphans. |
| `CRITICAL_NON_MANIFOLD_N` | N non-manifold edges (holes or T-junctions). | Check bridge and fill logic; run `recalc_face_normals`. |
| `CRITICAL_ZERO_AREA_FACES_N` | N faces with 0.0 area. | Check extrusion and bridge operations for collapsed faces. |
| `WARNING_THIN_FACES_N` | N sliver faces (Perimeter² / Area > 1000). | Causes UV distortion and bevel artifacts. Rebuild those faces. |

### Edge Slot Flags (`massa_edge_auditor.py`)

| Flag | Meaning | Fix |
| :--- | :--- | :--- |
| `WARNING_MISSING_EDGE_SLOTS_LAYER` | Layer exists but has no assigned edges. | Assign edge roles in `build_shape`. |
| `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` | Complex mesh (>12 faces) with zero seam edges. | Tag edges with role 1 (Perimeter) or role 3 (Guide). |
| `WARNING_ISOLATED_SEAM_EDGES_N` | N seam edges not connected to others. | Ensure seam loops are continuous. |

### Surface / UV Flags (`massa_surface_auditor.py`)

| Flag | Meaning | Fix |
| :--- | :--- | :--- |
| `CRITICAL_MISSING_UV_LAYER` | No UV layer on the mesh. | Set UV strategy in `get_slot_meta` or write UVs manually. |
| `CRITICAL_ZERO_UV_DATA` | UV layer exists but all UVs are at (0, 0). | Check UV assignment logic in `build_shape`. |
| `CRITICAL_INVERTED_NORMALS` | Faces pointing inward. | Run `bmesh.ops.recalc_face_normals`. |
| `CRITICAL_SELF_INTERSECTION` | Geometry overlaps itself. | Check boolean and extrusion logic. |
| `CRITICAL_UV_SPIKES_N` | N UV islands with extreme distortion. | Improve seam placement or UV math. |
| `CRITICAL_COLLAPSED_UVS_N` | N UV islands collapsed to a point. | Check for zero-area faces in UV space. |

---

## 5. Tool Map

```text
debugging_system/
├── config.py              ← Set BLENDER_PATH here before using any tool
├── debug_agent.py         ← Execute arbitrary Python in Blender (--code / --file)
├── runner.py              ← Cartridge audit runner (--cartridge / --mode / --payload)
├── headless_launcher.py   ← Spawns the background Blender process
├── launcher.py            ← Internal launcher helper
├── runner_console.py      ← Interactive console interface for runner
├── visual_inspector.py    ← Viewport rendering helpers (used by runner)
└── auditors/
    ├── massa_auditor.py        ← Core topology checks
    ├── massa_edge_auditor.py   ← Edge slot and seam checks
    ├── massa_surface_auditor.py ← UV and normal checks
    ├── massa_fuzz_auditor.py   ← Parameter randomization / crash testing
    ├── massa_ui_auditor.py     ← Operator and UI validation
    └── massa_topology_extra.py ← Extended topology checks
```
