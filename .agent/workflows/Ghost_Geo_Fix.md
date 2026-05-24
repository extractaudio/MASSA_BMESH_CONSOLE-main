---
description: Workflow for finding and repairing loose, broken, duplicate, and hidden ghost geometry in Massa cartridges.
---

# Ghost Geo Fix Workflow

Use this workflow when a Massa cartridge generates geometry that looks correct in the viewport but damages UV unwrap, produces doubles, creates invisible faces, leaves orphan topology, or fails the audit suite with loose, non-manifold, zero-area, thin-face, self-intersection, UV spike, or collapsed-UV flags.

The cartridge is responsible for clean BMesh output. The engine cleanup passes are safety nets, not permission to ship messy topology.

## Core Mission

Ghost geometry is any generated topology that is not part of the visible, intended asset contract.

It usually appears as:

1. Loose vertices with no edges.
2. Wire edges with no faces.
3. Duplicate faces occupying the same space.
4. Internal faces hidden inside closed volumes.
5. Zero-area or near-zero-area faces.
6. Sliver faces with extreme aspect ratios.
7. Doubled vertices that look welded but are separate.
8. Non-manifold edges from bad bridging, duplicate caps, or partial shells.
9. Self-intersecting faces from boolean-like construction or overlapping components.
10. Socket/helper faces accidentally left as visible geometry.
11. UV-only damage caused by tiny, hidden, or collapsed geometry.

The goal is not to delete blindly. The goal is to prove what each piece of geometry is, classify whether it is intentional, then remove, rebuild, or quarantine it before UVs and slots are assigned.

## Required Agent Stance

You are the Massa Ghost Geometry Mechanic.

Never fix by adding a broad cleanup pass first. First identify where the unwanted topology is born in `build_shape()`. The best repair changes the construction step so the bad geometry never exists.

Always answer:

1. What geometry family is this cartridge building?
2. Which faces, edges, or verts are supposed to survive?
3. Which geometry is only scaffolding or temporary construction?
4. Which operation first creates the ghost topology?
5. Is this a source-construction bug or only a missing final cleanup?
6. Would the proposed fix preserve slots, edge slots, seams, sockets, normals, UVs, and resurrection properties?

## Hard Rules

- Do not use `bpy.ops` inside `build_shape`.
- Do not inspect or select geometry by raw final index as the repair strategy.
- Do not hide broken topology with material slots, transparent materials, or socket slots.
- Do not rely on `FIX_DEGENERATE` or `REMOVE_LOOSE` as the primary fix.
- Do not remove socket faces unless they are helper duplicates instead of the intended socket anchors.
- Do not call `bmesh.ops.recalc_face_normals` as a cure for non-manifold geometry.
- Do not delete every internal face blindly; cavities, vents, sockets, and open-shell cartridges can be intentional.
- Do not ship a cartridge that only passes visual render but fails `AUDIT`.
- Do not claim UVs are fixed until topology flags are clean first.

## Phase 0: Read The Contract

Before editing a cartridge, refresh the relevant local instructions:

1. `CARTRIDGE_MANDATE.md`
2. `README.md`
3. `.agent/workflows/UV_unwrap.md`
4. `CLAUDE.md` or `AGENTS.md`

Confirm the cartridge still obeys:

- `CARTRIDGE_META` exists and `id` matches `bl_idname`.
- The class inherits `Massa_OT_Base`.
- `build_shape(self, bm)` is pure BMesh and mathutils.
- `get_slot_meta()` defines every material slot used by generated faces.
- Edge slots use `MASSA_EDGE_SLOTS`.
- Intentional manual seams use spatial logic and protection where needed.
- Sockets are derived from existing intended faces, not extra loose helper geometry.

## Phase 1: Establish The Baseline

Run the smallest audit that proves the current failure.

```powershell
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode AUDIT
```

Record all flags before editing. The key ghost-geometry flags are:

| Flag | Meaning | First suspicion |
| :--- | :--- | :--- |
| `CRITICAL_LOOSE_VERTS_N` | Vertices are not linked to any edge | Temporary verts, failed face creation, deleted faces leaving orphans |
| `CRITICAL_WIRE_EDGES_N` | Edges have no faces | Construction rails left behind, failed bridge/fill, debug skeletons |
| `CRITICAL_NON_MANIFOLD_N` | Edges are open, doubled, or shared by too many faces | Duplicate caps, bad tube joins, T-junctions, half-built shells |
| `CRITICAL_ZERO_AREA_FACES_N` | Faces have collapsed area | Duplicate verts, zero dimensions, bad profile points, degenerate extrusion |
| `WARNING_THIN_FACES_N` | Slivers with high perimeter-area ratio | Near-overlapping cuts, bevel scraps, tiny panels, bad bisects |
| `CRITICAL_SELF_INTERSECTION` | Faces overlap without sharing vertices | Intersecting components, hidden shells, failed boolean-style joins |
| `CRITICAL_UV_SPIKES_N` | Small geometry creates huge UV jumps | Slivers, wrong seam cuts, collapsed side faces |
| `CRITICAL_COLLAPSED_UVS_N` | Nonzero faces have zero UV area | Degenerate topology or incomplete UV assignment |
| `CRITICAL_INVERTED_NORMALS` | Majority of normals point inward | Winding mistake, duplicate internal shell, blanket normal recalc failure |

If `AUDIT` fails with UV flags, still fix geometry first. Bad topology is the root cause of many UV failures.

## Phase 2: Parse The Cartridge Script

Read the cartridge top-to-bottom and build a source map.

Capture these sections:

| Source section | What to inspect |
| :--- | :--- |
| Imports | `bmesh`, `math`, `mathutils`, `Massa_OT_Base`, optional `MassaBuilder` |
| Properties | Dimensions that can become zero, negative, or incompatible |
| `get_slot_meta()` | Slot indices, UV modes, socket slots, missing `phys` keys |
| `build_shape()` phases | Where verts, edges, faces, rings, caps, bridges, insets, cuts, and cleanup happen |
| Seam logic | Edge-slot layer setup, cap loops, guide seams, force-seam protection |
| UV logic | Whether UVs are assigned before or after cleanup, and whether hidden faces get UVs |
| `execute()` override | Post-generation socket or object changes outside `build_shape` |

While parsing, mark every geometry birth site:

```text
GEOMETRY_BIRTH_MAP
- profile points -> base verts -> start cap
- extrude_face_region -> walls + end cap
- ring creation -> side faces + caps
- inset/extrude -> detail faces
- bridge_loops -> connector faces
- duplicate/mirror/array -> repeated components
- socket tagging -> existing faces only
- cleanup -> remove doubles, delete scaffolding, recalc normals
```

The repair usually belongs at one birth site, not at the bottom of the file.

## Phase 3: Classify Ghost Geometry

Use this taxonomy before editing.

| Class | Definition | Common source | Preferred repair |
| :--- | :--- | :--- | :--- |
| `GHOST_LOOSE_VERT` | Vertex has no linked edges | Failed `faces.new`, temporary point cloud, delete faces only | Delete explicit loose verts or avoid creating them until needed |
| `GHOST_WIRE_EDGE` | Edge has no linked faces | Debug rails, open guide splines, failed face fill | Delete wire edges or convert to real faces/edge slots only if intentional |
| `GHOST_DUP_FACE` | Two faces occupy the same plane with same verts or duplicate verts | Double cap creation, mirrored overlap, repeated loop | Remove duplicate creation; weld verts only after proving face set |
| `GHOST_INTERNAL_FACE` | Face is trapped inside a closed volume and not a cavity/socket | Overlapping boxes, duplicate shell, bad boolean-style union | Do not hide it; rebuild join or delete internal partition |
| `GHOST_ZERO_FACE` | Face area below tolerance | Collinear points, zero thickness, duplicate adjacent vertices | Guard dimensions and skip invalid faces before creation |
| `GHOST_SLIVER` | Face is valid but too thin to unwrap or bevel | Near-miss bisect, bevel scrap, tiny inset | Change construction tolerances or dissolve only connected slivers |
| `GHOST_OPEN_SHELL` | Non-manifold boundary not allowed by cartridge flags | Missing cap, failed bridge, partial loop | Fill caps or complete bridge; only allow if `ALLOW_OPEN_MESH` is intentional |
| `GHOST_SELF_INTERSECTION` | Separate faces overlap in space | Intersecting components not fused, duplicate shell | Rebuild with shared loops, add real cuts, or separate slots intentionally |
| `GHOST_SOCKET_HELPER` | Extra hidden mesh made only to spawn sockets | Old helper-face pattern | Tag an existing intended face or `MASSA_SOCKETS` layer instead |

State the classification before changing code:

```text
Classified failure as GHOST_DUP_FACE at cap creation.
The script creates a start cap manually, then creates another coincident cap after bridge_loops.
Repair: preserve the extrusion cap and remove the second cap creation.
```

## Phase 4: Build A BMesh Evidence Probe

If the script is not obvious, add a temporary local reasoning probe while editing. Do not ship probe code.

Use BMesh relationships, not final object appearance:

```python
def ghost_geo_report(bm):
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    loose_verts = [v for v in bm.verts if not v.link_edges]
    wire_edges = [e for e in bm.edges if not e.link_faces]
    non_manifold = [e for e in bm.edges if not e.is_manifold]
    zero_faces = [f for f in bm.faces if f.calc_area() < 0.000001]
    thin_faces = []

    for f in bm.faces:
        area = f.calc_area()
        if area <= 0.000001:
            continue
        perimeter = sum(e.calc_length() for e in f.edges)
        if perimeter > 0 and ((perimeter * perimeter) / area) > 1000.0:
            thin_faces.append(f)

    return {
        "verts": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "loose_verts": len(loose_verts),
        "wire_edges": len(wire_edges),
        "non_manifold": len(non_manifold),
        "zero_faces": len(zero_faces),
        "thin_faces": len(thin_faces),
    }
```

Use the report after major build phases:

```python
# Temporary only.
print("after ring build", ghost_geo_report(bm))
print("after caps", ghost_geo_report(bm))
print("after bridge", ghost_geo_report(bm))
```

Remove the probe before delivery.

## Phase 5: Repair Patterns

### Pattern A: Guard Dimensions Before Geometry Birth

Zero and near-zero parameters create collapsed faces. Clamp only where it preserves user intent.

```python
width = max(0.001, float(self.width))
height = max(0.001, float(self.height))
length = max(0.001, float(self.length))
thickness = min(max(0.001, float(self.thickness)), min(width, height) * 0.49)
```

For profile points, reject duplicates before face creation:

```python
def dedupe_profile_points(points, eps=0.0001):
    clean = []
    for p in points:
        if not clean or (Vector((p[0], p[1])) - Vector((clean[-1][0], clean[-1][1]))).length > eps:
            clean.append(p)
    if len(clean) > 2:
        first = Vector((clean[0][0], clean[0][1]))
        last = Vector((clean[-1][0], clean[-1][1]))
        if (first - last).length <= eps:
            clean.pop()
    return clean
```

### Pattern B: Create Faces Safely

Never let invalid faces leave their vertices behind.

```python
verts = [bm.verts.new((x, y, z)) for x, y, z in coords]
bm.verts.ensure_lookup_table()

try:
    face = bm.faces.new(verts)
except ValueError:
    bmesh.ops.delete(bm, geom=[v for v in verts if v.is_valid and not v.link_edges], context="VERTS")
    return
```

If face creation is optional, skip it before creating verts when possible.

### Pattern C: Remove Temporary Construction Geometry

If a cartridge creates scaffolding for measurement, path sampling, or bridge setup, keep it in Python lists until it becomes real mesh.

Good:

```python
path_points = [Vector((x, y, z)) for x, y, z in computed_path]
```

Avoid:

```python
# Bad: creates mesh verts that may never receive edges or faces.
path_verts = [bm.verts.new(p) for p in computed_path]
```

If temporary geometry must be created, delete it immediately after use:

```python
temp_geom = temp_verts + temp_edges
# ... use it ...
bmesh.ops.delete(bm, geom=[g for g in temp_geom if g.is_valid], context="VERTS")
```

### Pattern D: Fix Duplicate Caps

Duplicate caps are a classic ghost source. They make the asset look closed while producing internal coincident faces and UV doubles.

Check for these script smells:

- `bm.faces.new(base_verts)` creates a cap.
- `extrude_face_region` preserves that cap and creates the opposite cap.
- Later code creates another face from the same ring verts.
- Ring builders create cap fan faces, then `fill` or `edgeloop_fill` runs on the same boundary.

Repair:

1. Choose one cap owner.
2. Delete the second cap creation path.
3. Force cap normals after all cuts.
4. Assign slots by face role, not by creation order.
5. Mark cap perimeter seams once.

### Pattern E: Fix Ring And Tube Joins

Tube ghosts usually come from a mismatched ring count, wrong wrap index, or duplicate seam column.

Use modulo wrapping:

```python
for i in range(segments):
    v00 = ring_a[i]
    v01 = ring_a[(i + 1) % segments]
    v11 = ring_b[(i + 1) % segments]
    v10 = ring_b[i]
    bm.faces.new((v00, v01, v11, v10))
```

Do not create both a duplicated first vertex at the end of the ring and modulo faces. Pick one. The Massa standard is usually unique ring verts plus modulo indexing.

### Pattern F: Rebuild Bad Bridges

Bridge failures create wire edges, non-manifold edges, and slivers.

Before bridging, prove both loops:

```python
def loop_is_usable(loop):
    if len(loop) < 3:
        return False
    return len(set(loop)) == len(loop)
```

For two loops:

- Same count is ideal.
- Same winding direction must be intentional.
- Vertex order must progress around the same local axis.
- If counts differ, resample one loop or use explicit fan/tri topology.

Do not rely on `bmesh.ops.bridge_loops` when loops are unordered or mixed with unrelated edges.

### Pattern G: Delete Only Proven Orphans

Use this final source-level cleanup at the end of `build_shape()` when appropriate:

```python
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

loose_verts = [v for v in bm.verts if v.is_valid and not v.link_edges]
if loose_verts:
    bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")

wire_edges = [e for e in bm.edges if e.is_valid and not e.link_faces]
if wire_edges:
    bmesh.ops.delete(bm, geom=wire_edges, context="EDGES")

bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=True, faces=True)
bm.normal_update()
```

This is allowed only after the construction bug is understood. It should not be the whole repair.

### Pattern H: Preserve Data Layers Through Repair

When deleting or rebuilding faces, reapply semantic data after geometry is stable:

1. Assign `f.material_index` by role.
2. Recreate or retrieve `MASSA_EDGE_SLOTS`.
3. Re-mark cap/perimeter seams.
4. Re-mark guide zippers.
5. Re-tag socket faces using intended geometry.
6. Verify UV layer creation and manual UV assignment after cleanup.

Do not assign UVs before deleting ghosts unless the topology is already final.

## Phase 6: Internal Face Detection

Internal faces are the hardest ghost geometry because they can be valid topology and still ruin UVs.

Use evidence:

| Evidence | Interpretation |
| :--- | :--- |
| Face normal points into a sealed volume | Possible duplicate/internal shell |
| Face is not boundary and is fully occluded by nearby faces | Possible internal partition |
| Two faces have centers nearly equal and normals opposite or equal | Duplicate or doubled face |
| Slot is hidden/utility but `sock` is false | Possible abandoned helper surface |
| UV island exists for an invisible face | Likely UV-damaging ghost |

Do not delete internal geometry if it is:

- A real cavity wall.
- A vent/interior visible through openings.
- A collision-only or separated slot that is intentionally generated.
- A socket anchor face defined in `get_slot_meta()` or `MASSA_SOCKETS`.
- An allowed open shell declared by the cartridge flags.

When internal faces are accidental, prefer rebuilding the construction so intersecting components share a boundary or are intentionally separated.

## Phase 7: UV Damage Triage

Ghost geometry often appears first as UV failure.

Use this order:

1. Fix `CRITICAL_LOOSE_VERTS_N`, `CRITICAL_WIRE_EDGES_N`, `CRITICAL_NON_MANIFOLD_N`, and `CRITICAL_ZERO_AREA_FACES_N`.
2. Fix `WARNING_THIN_FACES_N`.
3. Fix `CRITICAL_SELF_INTERSECTION`.
4. Rebuild seam and edge-slot logic.
5. Reassign or regenerate UVs.
6. Run UV inspection only after geometry is clean.

UV-specific symptoms:

| Symptom | Likely hidden geometry |
| :--- | :--- |
| One island is a needle or huge streak | Sliver face or UV spike from tiny geometry |
| All UVs collapse to one point | Missing UV assignment or wrong `SKIP` slot |
| Texture smears across a tube | Missing zipper seam or duplicate seam column |
| Many tiny UV islands | Duplicate caps, internal faces, fragmented helper detail |
| Overlap persists after seams | Internal duplicate faces or coincident shells |

## Phase 8: Audit Loop

After each repair pass:

```powershell
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode AUDIT
```

Add UV modes only if the edit touched UVs, seams, edge slots, or face topology that affects unwrap:

```powershell
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode UV_INSPECT
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode UV_HEATMAP
```

Use `VISUAL_DIFF` only when shape appearance or silhouette changed:

```powershell
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode VISUAL_DIFF
```

Pass criteria:

- No new flags compared with baseline.
- No `CRITICAL_*` topology flags.
- No `WARNING_THIN_FACES_N` unless explicitly accepted with reason.
- No UV collapse, spike, or missing UV flags.
- No visible shape regression unless requested.
- No deleted sockets, slots, edge slots, or protected seams.

## Phase 9: Agent Output Requirements

When finishing a ghost-geometry repair, report:

1. Baseline audit flags.
2. Ghost classes found.
3. Birth site that created each ghost.
4. Repair applied at the source.
5. Cleanup performed at the end of `build_shape()`, if any.
6. Slot, edge-slot, seam, socket, and UV preservation notes.
7. Verification command and result.

Example:

```text
Ghost geometry repair complete. Baseline had CRITICAL_LOOSE_VERTS_8 and CRITICAL_ZERO_AREA_FACES_4. The root cause was duplicate profile points creating invalid cap faces in build phase 2. I added profile de-duplication before vertex creation, removed the second cap creation path, then re-applied slot 1 cap seams and slot 3 guide seams after cleanup. AUDIT now passes with no critical topology or UV flags.
```

## Quick Prompt For Agents

Use this prompt when handing off a cartridge ghost-geometry repair:

```text
Act as the Massa Ghost Geometry Mechanic. Read the full cartridge and map every geometry birth site in build_shape. Classify failures as loose verts, wire edges, duplicate faces, internal faces, zero-area faces, slivers, non-manifold shells, self-intersections, or socket/helper ghosts. Do not repair by broad cleanup first. Find where the bad topology is created, fix that source construction, then apply a narrow final cleanup for proven orphans only. Preserve material slots, MASSA_EDGE_SLOTS, protected seams, socket anchors, normals, and UV assignment. Run AUDIT first, then UV_INSPECT or UV_HEATMAP only if geometry or UV logic changed. Report baseline flags, ghost classes, source birth sites, repairs, and final audit status.
```

