---
description: Workflow for cartridge-authored UV seams, edge slots, and spatial seam audits.
---

# UV Unwrap Workflow

Goal: Cartridges author their own seam/edge intent, avoiding `edge_auto_detect` reliance. Disable Auto-Detect Boundaries during UV design.

## Core Policy & Facts

Execution order: `build_shape` -> cleanup -> slot auto-detect (if enabled) -> `process_edge_slots` -> `auto_detect_sharp_edges` -> seam solvers.
Manual logic in `build_shape` must:

1. Manage `MASSA_EDGE_SLOTS` layer.
2. Spatially assign edge roles (via orientation, occlusion, topology; not global axes). Never guess indices.
3. Mark UV seams (`e.seam = True`) and protect them (`e[massa_force_seam] = 1`).
4. Address: surface unfolding, stretch-free islands, and loop connectivity.
5. Pass geometry/surface auditors.

## Edge Slots (`MASSA_EDGE_SLOTS`)

| ID | Name | Default Meaning | Use For |
| :--- | :--- | :--- | :--- |
| 0 | None | No special treatment | Interior smooth edges |
| 1 | Perimeter (Seam+Sharp) | Silhouettes, end caps, outer borders |
| 2 | Contour (Sharp) | Major hard-surface form breaks |
| 3 | Guide (Seam) | Hidden zippers, unwrap guides |
| 4 | Detail | Minor decors / optional bevel guides |
| 5 | Fold | SubD crease / cloth fold |

Prefer 1 for visible boundaries, 3 for hidden cuts, and explicit `e.seam=True` + `massa_force_seam=1` for custom protected cuts.

## Boilerplate & Helpers

```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
force_seam = bm.edges.layers.int.get("massa_force_seam") or bm.edges.layers.int.new("massa_force_seam")

def mark_edge(e, slot=None, seam=False, sharp=False, protect=False):
    if slot is not None: e[edge_slots] = slot
    if seam: e.seam = True
    if sharp: e.smooth = False
    if protect: e[force_seam] = 1

def component_centroid(verts):
    return sum((v.co for v in verts), Vector()) / max(1, len(verts))

def principal_axis(verts, iters=8):
    ctr = component_centroid(verts)
    dir = Vector((1.0, 0.37, 0.19)).normalized()
    pts = [v.co - ctr for v in verts]
    for _ in range(iters):
        proj = sum((p * p.dot(dir) for p in pts), Vector())
        if proj.length < 0.0001: break
        dir = proj.normalized()
    return dir

def occlusion_score(edge, comp_ctr, parent_ctr=None):
    edge_ctr = (edge.verts[0].co + edge.verts[1].co) * 0.5
    score = max(0.0, 1.0 / max(0.001, (parent_ctr - edge_ctr).length)) if parent_ctr else 0.0
    nrm = sum((f.normal for f in edge.link_faces), Vector())
    if nrm.length > 0.0001:
        inward = comp_ctr - edge_ctr
        if inward.length > 0.0001: score += max(0.0, nrm.normalized().dot(inward.normalized()))
    if edge.is_manifold and len(edge.link_faces) == 2:
        try:
            if edge.calc_face_angle(0.0) > 0.785: score += 0.25 # 45deg
        except ValueError: pass
    return score
```

## Archetypes & Spatial Patterns

Capture geometry right after creation (e.g., `ret["geom"]`), avoid global edge indices later.

- **PLANK** (beams): Cut both caps + 1 hidden longitudinal edge.
- **TUBE** (pipes): Cut both caps + 1 hidden zipper.
- **SHEET** (panels): Perimeter seams; `FIT`/`BOX` map.
- **STRIP** (paths): 1 hidden underside edge along path.
- **BOX_DETAIL**: Separate materials, sharp contours.
- **SOCKET** (hidden): Isolate UVs, use slot 9.
- **INTERSECTION** (booleans): Guide seams from concave junctions to perimeters.

```python
def mark_plank_uv(faces, parent_ctr=None, local_axis=None):
    verts = list({v for f in faces for v in f.verts})
    ctr, axis = component_centroid(verts), (local_axis or principal_axis(verts)).normalized()
    caps = sorted(faces, key=lambda f: abs(f.normal.dot(axis)), reverse=True)[:2]
    for f in caps:
        for e in f.edges: mark_edge(e, 1, True, True, True)
    cap_e = {e for f in caps for e in f.edges}
    long_e = [e for f in faces for e in f.edges if e not in cap_e and len(e.verts)==2]
    zips = [e for e in set(long_e) if abs((e.verts[1].co-e.verts[0].co).normalized().dot(axis))>0.75] or list(set(long_e))
    mark_edge(max(zips, key=lambda e: occlusion_score(e, ctr, parent_ctr)), 3, True, False, True)

def mark_tube_uv(verts, parent_ctr=None, local_axis=None):
    faces = {f for v in verts for f in v.link_faces}
    ctr, axis = component_centroid(list(verts)), (local_axis or principal_axis(list(verts))).normalized()
    caps = [f for f in faces if abs(f.normal.dot(axis)) > 0.85]
    cap_e = set()
    for f in caps:
        for e in f.edges: cap_e.add(e); mark_edge(e, 1, True, True, True)
    side_e = {e for v in verts for e in v.link_edges if e not in cap_e and e.is_manifold}
    axis_e = [e for e in side_e if abs((e.verts[1].co-e.verts[0].co).normalized().dot(axis))>0.65]
    if axis_e: mark_edge(max(axis_e, key=lambda e: occlusion_score(e, ctr, parent_ctr)), 3, True, False, True)

def mark_sheet_uv(sheet_faces):
    for e in {e for f in sheet_faces for e in f.edges if e.is_boundary or len(e.link_faces)<2}:
        mark_edge(e, 1, True, True, True)

def mark_intersection_relief(edges):
    concave = [e for e in edges if e.is_manifold and len(e.link_faces)==2 and e.calc_face_angle(0.0) >= 0.61 and (e.link_faces[1].calc_center_median() - e.link_faces[0].calc_center_median()).dot(e.link_faces[0].normal) < -0.001]
    for e in concave: mark_edge(e, slot=2, sharp=True)
    perim = [e for e in edges if e[edge_slots]==1 or e.is_boundary]
    for e in concave:
        deepest = min(e.verts, key=lambda v: sum((v.co-f.calc_center_median()).dot(f.normal) for f in v.link_faces))
        target = min(perim, key=lambda p: min((deepest.co-v.co).length for v in p.verts), default=None)
        if target:
            for r_edge in shortest_edge_path(deepest, target): mark_edge(r_edge, 3, True, False, True)

# Box Detail (Major contours vs guides)
for e in comp_edges:
    if e.is_manifold and len(e.link_faces)==2 and e.calc_face_angle(0.0) > 1.047: mark_edge(e, slot=2, sharp=True)
for e in hidden_guides: mark_edge(e, slot=3, seam=True, protect=True)

# Sockets (slot 9)
socket_face.material_index = 9
for e in socket_face.edges: mark_edge(e, seam=True, sharp=True, protect=True)
```

## Mathematical UVs & Dual-Mode Scaling

Golden Cartridges prefer explicit, mathematical UV control (`"SKIP"` mode in slot meta). Every cartridge that writes manual UVs must support two scaling modes via operator properties (`uv_scale` and `fit_uvs`):

- `fit_uvs = False` (default): UVs are calculated in world units and multiplied by `uv_scale`. A 1m wall with scale 1.0 produces UVs from 0 to 1. A 2m wall produces 0 to 2 (tiling the texture). This ensures consistent texel density.
- `fit_uvs = True`: UVs are normalized so the entire surface geometry fits within the 0–1 square exactly. Used for decals, displays, or single-instance baked textures.

```python
uv_layer = bm.loops.layers.uv.verify() # Always verify layer first

# Example setup for structural walls vs caps:
su_s = (1.0 / perim)       if (self.fit_uvs and perim > 0) else self.uv_scale
sv_s = (1.0 / self.length) if self.fit_uvs                  else self.uv_scale

su_c = (1.0 / self.width)  if self.fit_uvs else self.uv_scale
sv_c = (1.0 / self.height) if self.fit_uvs else self.uv_scale
```

### Arc-Length U Calculation

For walls of an extruded profile, the U coordinate is commonly the arc length walked along the 2D profile from the designated seam corner. Compute the perimeter and use a helper to query the distance:

```python
perim = sum(
    math.hypot(pts[(i+1) % len(pts)][0] - pts[i][0],
               pts[(i+1) % len(pts)][1] - pts[i][1])
    for i in range(len(pts))
)

def get_u(x, z):
    """Returns arc length from pts[0] along the profile to the point (x, z)."""
    cu = 0.0
    for i in range(len(pts)):
        p1 = pts[i]
        if math.hypot(p1[0] - x, p1[1] - z) < 0.002:
            return cu
        pn  = pts[(i+1) % len(pts)]
        cu += math.hypot(pn[0] - p1[0], pn[1] - p1[1])
    return 0.0
```

## The Wrapping Fix (Cylindrical Seam)

**This is the most critical pattern for closed-loop UVs.** For any closed-loop surface (extruded profile, cylinder, sphere, pipes), one face will inevitably span the seam — its loops have U coordinates at both `~0` and `~perimeter`. Without a fix, that face renders as a highly stretched, smeared band across the entire texture.

To fix this, detect the spanning faces and shift the small U values up by the perimeter distance before scaling:

```python
for f in bm.faces:
    if f.material_index != 0: continue # Only apply to surfaces, skip caps

    # Compute all loop UVs first
    loop_uvs = []
    for l in f.loops:
        ua = get_u(l.vert.co.x, l.vert.co.z)
        va = l.vert.co.y
        loop_uvs.append([l, ua, va])

    # Detect wrapping: if U range exceeds 50% of perimeter, this is the closing face
    us = [item[1] for item in loop_uvs]
    if (max(us) - min(us)) > (perim * 0.5):
        # Shift small U values up by perimeter so all loops land near max
        for item in loop_uvs:
            if item[1] < (perim * 0.5):
                item[1] += perim

    # Now apply scale and write to the actual BMesh layer
    for l, u, v in loop_uvs:
        l[uv_layer].uv = (u * su_s, v * sv_s)
```

## Advanced Seam Selection Algorithms

### The Longitudinal Seam Algorithm

For closed-loop walls, provide a coherent seam path running with the surface flow so UV unwrapping has a clean cut. Straight extrusions usually need one longitudinal seam.

```python
if pts:
    seam_x, seam_z = pts[0][0], pts[0][1]

    bm.edges.ensure_lookup_table()
    for e in bm.edges:
        v1, v2 = e.verts[0], e.verts[1]

        # Both vertices must lie on the (seam_x, seam_z) line (any Y)
        on_seam_1 = (abs(v1.co.x - seam_x) < 0.005) and (abs(v1.co.z - seam_z) < 0.005)
        on_seam_2 = (abs(v2.co.x - seam_x) < 0.005) and (abs(v2.co.z - seam_z) < 0.005)

        if on_seam_1 and on_seam_2:
            e.seam            = True
            e[edge_slots]     = 3                # Slot 3: Guide
```

### Segment Cut Seams

When segmenting geometry (e.g. length subdivision cuts), tag the resulting ring edges as Guide lines (Slot 3) to break up the UV islands logically:

```python
if hasattr(self, "segments_y") and self.segments_y > 0:
    for e in bm.edges:
        # Segment cuts are perpendicular to Y → both verts share Y coordinate
        if abs(e.verts[0].co.y - e.verts[1].co.y) < 0.001:
            # Filter out cap edges (Y ≈ 0 and Y ≈ length)
            if 0.01 < e.verts[0].co.y < (self.length - 0.01):
                e[edge_slots] = 3                # Slot 3: Guide
```

## UV Strategies via `get_slot_meta`

Different parts of the geometry should use different UV strategies defined in the cartridge's metadata:

| Value | When to Use |
|:---|:---|
| `"SKIP"` | **Golden Standard for manual UVs.** Use for main walls/surfaces mapped mathematically in `build_shape`. |
| `"BOX"` | Tri-planar cube projection. Use for flat-ish caps where analytic mapping is sufficient and manual mapping is overkill. |
| `"FIT"` | Stretch UVs to fill the 0–1 space. Good for simple decals if manual math isn't required. |
| `"TUBE_Z"` / `"Y"` / `"X"` | Cylindrical projection along an axis. Use for radial trim if manual computation is skipped. |
| `"UNWRAP"` | LSCM/Angle-Based unwrap. Fallback for highly organic or complex forms. Requires explicit seams (`e.seam=True`). |

## Final Polish & Output

1. **Metadata:** Ensure `get_slot_meta` matches strategy (e.g., `UNWRAP` for tubes, `FIT`/`BOX` for sheets, `SKIP` for sockets).
2. **Texel Density:** Normalize UV islands using `CARTRIDGE_META` scale class (`SMALL`/`MEDIUM`/`LARGE`).
3. **Audit:** Verify visually and via tests: `python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode AUDIT`.
4. **Agent Output:** State archetypes used, slot decisions, local orientation method, and normalization status.

## Hard Rules

- **NO `bpy.ops` or `bpy.context` reads inside `build_shape`**: This is non-negotiable for headless safety. Use only BMesh and Mathutils for UV and seam calculation.
- **Index Lookup Preservation**: Call `bm.verts.ensure_lookup_table()` (and `.edges`, `.faces`) after any geometry mutation before querying indices for seam marking or UV application.
- **Protect Normal Flow**: `recalc_face_normals` alone can fail on concave profiles. Force cap normals explicitly before using their bounds for UV calculations.
- Do not rely on `edge_auto_detect` or guess raw edge indices.
- Do not use global-axis math for deformed/rotated components.
- Do not leave flat seams unprotected or intersections without relief seams.

## Quick Prompt For Agents

Act as the Massa UV Engineer. Read the cartridge geometry and classify each component as PLANK, TUBE, SHEET, STRIP, BOX_DETAIL, SOCKET, or INTERSECTION. Do not rely on console auto-detected boundaries. In build_shape, create or retrieve MASSA_EDGE_SLOTS and massa_force_seam, then mark seams spatially at geometry birth. Use slot 1 for protected cap/perimeter seams, slot 2 for hard contours, and slot 3 for hidden guide zippers and intersection relief seams. Choose seams by generator vectors, cap-loop normals, PCA/OBB local frames, material boundaries, occlusion score, and concave junction depth, never by raw edge index or fixed negative-Y bias. Update get_slot_meta so UV modes match the geometry. Normalize UV islands to the CARTRIDGE_META scale class after UVMap generation when the engine supports it. Run a targeted audit and fix missing perimeter, missing seam, isolated seam, collapsed UV, UV spike, and texel-density issues before delivery.
