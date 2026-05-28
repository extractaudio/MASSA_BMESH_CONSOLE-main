# Diagnosis: cart_arc_01_wall.py

## Classification

**Primary: Family B — Geometry / Topology (FUZZ_CRASH)**
5 FUZZ_CRASH events. Fix this before any UV work.

**Secondary: Family A — UV / Seam issues (incidental, noted below)**

---

## Family B: FUZZ_CRASH Root Cause

**File:** `massa/modules/cartridges/cart_arc_01_wall.py`
**Crash site:** `build_shape` around line 212 → `massa_builder.py:474` in `tag_socket`

### Call sequence in build_shape (end of method):

```
builder.clean()   # "Final cleanup" — line ~196

# Then immediately:
builder.select_faces_by_normal(Vector((-1, 0, 0)), tolerance=0.1) \
       .tag_socket(1)                                              # line ~212

builder.select_faces_by_normal(Vector((1, 0, 0)), tolerance=0.1) \
       .tag_socket(2)
```

### Why faces become invalid

`builder.clean()` calls bmesh cleanup operations (remove doubles, degenerate faces, loose geometry). After `clean()` returns, **all previously cached BMFace pointer objects are potentially invalidated** by BMesh's internal compaction.

`select_faces_by_normal` runs *after* `clean()` and correctly populates `self.active_faces` with fresh face references at that moment. However, under certain fuzz parameter combinations (very small/clamped holes, zero-area panels generated when hole dimensions equal wall dimensions, REINFORCED/BRICK styles with small wall segments), `clean()` may remove faces that are *re-queried* by `select_faces_by_normal` via the BMesh face iterator — including degenerate faces that appear valid during iteration but are flagged for removal by a pending compaction.

The BMFace object survives the Python reference check but BMesh raises `ReferenceError: BMesh data of type BMFace has been removed` when you try to write `f[layer] = socket_id`.

### Exact crash line

`massa/modules/massa_builder.py`, line 474:
```python
f[layer] = socket_id   # f is a removed/invalid BMFace
```

### Reproduces across all 5 fuzz variants because:
- `hole_enable=False` + STANDARD: single-panel wall; `clean()` can compact if any degenerate faces sneak in from inset ops
- `hole_enable=True` + various: multiple panels; corner cases where hole nearly fills wall leave near-zero-area panels that clean() removes
- BRICK/REINFORCED: extra geometry (rails, ridges) adds more faces that get merged by clean(), invalidating iterator snapshot

---

## Family A: UV / Seam Issues (secondary)

### Issue 1 — Slot 0 uses `"uv": "SKIP"` in get_slot_meta, but build_shape manually calls tag_uvs on slot 0

`get_slot_meta` declares all slots as `"uv": "SKIP"`, which tells the pipeline's auto-unwrap to skip them. Then at the end of `build_shape`, the cartridge manually calls:
```python
builder.select_faces_by_slot(0).tag_uvs(scale=uv_sc, projection=uv_proj)
builder.select_faces_by_slot(1).tag_uvs(scale=uv_sc, projection=uv_proj)
builder.select_faces_by_slot(2).tag_uvs(scale=uv_sc, projection=uv_proj)
```
This is a dual-path UV approach. It is not inherently wrong, but it means the pipeline never runs its own UV logic and the cartridge is entirely responsible. If `tag_uvs` uses BOX projection with default world-scale, wide walls will have stretched UVs because the box projection is isotropic — a 4m x 3m wall face maps to a 4:3 UV island, not a 1:1 tile.

### Issue 2 — Seam tagging happens before baseboards are built

The perimeter seam pass runs immediately after the main wall segments are merged:
```python
builder.clean()
builder.select_all_faces().select_boundary().tag_edge_role(1)   # seam pass
# ... then baseboards are added AFTER this ...
builder.create_box(...)   # front baseboard
builder.create_box(...)   # back baseboard
```
Baseboards are added after the seam tagging pass, so their boundary edges are never marked as seams (edge role 1). This means the baseboard faces share UV space incorrectly with the wall surface — no seam boundary isolates them, causing the UV unwrap to bleed across the slot 0/slot 2 boundary and create the "smeared band" artifact on the baseboard/wall junction face.

### Issue 3 — Front baseboard has a duplicate/conflicting tag_edge_role call

In the front baseboard block:
```python
builder.create_box(r['w'], bd, bh) \
       .translate(cx, -bd/2, cz) \
       .tag_slot(2) \
       .select_boundary().tag_edge_role(2)   # contour

builder.select_boundary().tag_edge_role(1)   # seam — BUT active_faces is the boundary selection, not baseboard faces
```
The second `select_boundary()` call operates on whatever `active_faces` is at that point (the boundary edges of the previous op), not on the baseboard box faces. This means the seam is applied to an ambiguous selection rather than the intended baseboard perimeter.
