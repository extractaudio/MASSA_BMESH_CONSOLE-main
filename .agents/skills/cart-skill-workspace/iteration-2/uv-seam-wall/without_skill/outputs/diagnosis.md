# Diagnosis: cart_arc_01_wall.py

## Crash: FUZZ_CRASH — BMesh data of type BMFace has been removed

### Root Cause

`build_shape` calls `builder.clean()` at line 208 (the "Final cleanup" comment) immediately before calling `select_faces_by_normal` to select faces for socket tagging.

`clean()` internally calls `bmesh.ops.remove_doubles(...)`, which **merges coincident vertices and deletes the resulting duplicate faces**. When remove_doubles runs, it invalidates existing BMFace Python objects that refer to geometry that was merged away.

`select_faces_by_normal` (massa_builder.py line 199) collects live `BMFace` references from `self.bm.faces` into `self.active_faces`. Because this runs **after** `clean()`, the faces themselves are valid at selection time.

**However**, the issue is that `clean()` calls `_update()` which refreshes lookup tables, but does NOT clear `self.active_faces`. If any previous operation (e.g. `select_boundary().tag_edge_role(1)` before clean) left stale references in `active_faces`, those would be dangling pointers into deallocated BMFace memory.

More critically: `clean()` is the "Final cleanup" that consolidates all geometry. After `clean()`, the face population can change. The subsequent `select_faces_by_normal` does a fresh query against `self.bm.faces`, so the selections themselves should be fresh. **The actual crash location is `tag_socket` at line 474 of massa_builder.py**:

```python
for f in self.active_faces:
    f[layer] = socket_id   # <-- ReferenceError here
```

The crash happens because `select_faces_by_normal` iterates `self.bm.faces` which returns a snapshot, but BMesh face objects become invalid **if the BMesh is modified between selection and use**. In the crash scenario, the faces collected by `select_faces_by_normal` at line 211 are valid, but the issue arises on fuzz params where the wall geometry produces coincident/degenerate faces that `clean()` removes — meaning `select_faces_by_normal` can select a face at the end of the BMesh list that is actually already flagged for deletion by an in-progress remove_doubles operation, or the BMesh internal compaction happens lazily after `_update()`.

### Precise Mechanism

1. `builder.clean()` is called at line 208
2. `bmesh.ops.remove_doubles` runs — this **deletes** some BMFace objects (merged faces). The faces are freed in C.
3. `_update()` refreshes lookup tables, but Python references to deleted faces are now dangling
4. `select_faces_by_normal` at line 211 iterates `self.bm.faces` — this should return only live faces, BUT...
5. Under certain fuzz parameters (e.g. degenerate wall where panels collapse to zero area), `remove_doubles` may not fully compact the BMesh face list before Python iterates it. Alternatively, with certain `wall_style` + hole combos, the baseboard geometry produces faces exactly coincident with wall faces, meaning `remove_doubles` invalidates face references that the builder's fluent chain already holds internally.

**The core bug**: `select_faces_by_normal` does not guard against stale/removed faces. After any `clean()` call, the BMesh can contain garbage-collected face slots. The `tag_socket` method must validate each face before accessing it.

### UV / Seam Issues

The current code at lines 218-222 has a comment explaining that manual `tag_uvs` calls were removed in favor of the engine's post-weld UV pass. This is correct behavior.

However, there is a **UV stretching issue** for the wall body when `wall_style == 'REINFORCED'` or `wall_style == 'BRICK'`:

1. `get_slot_meta` returns `"uv": "BOX"` for all three slots (0, 1, 2)
2. The engine's BOX-map runs after weld/merge using world-space vertex coordinates
3. For the REINFORCED style, the inset faces (slot 1) on the front face (normal +Y) get BOX-projected using the `abs(n.x) >= 0.5` branch (`u=v.y, v_coord=v.z`). Since the inset face normals are `(0, 1, 0)`, BOX correctly routes to the `else` branch (`u=v.x, v_coord=v.z`).
4. **The smeared band issue**: The BRICK rail (slot 2) is a thin box (`rail_h=0.1`) that straddles the wall. The top and bottom cap faces of the rail have normals `(0,0,1)` and `(0,0,-1)` — these get BOX-projected with `u=v.x, v=v.y`. Since `v.y` spans `[0, t*1.2]` (thickness ~0.24), and `v.x` spans the full wall width, the UV island is extremely wide and nearly zero height. This produces a smeared/stretched single-pixel-height band in the UV layout.
5. Additionally, `select_boundary().tag_edge_role(2)` is called without a preceding `select_all_faces()` or explicit face re-select after `create_box(...).translate(...).tag_slot(2)`. The `tag_slot` method assigns slot to `self.active_faces`, but `select_boundary` operates on `active_faces`. This chain is valid **only if** `create_box` sets `active_faces`. Looking at `create_box`, it does append to `active_faces`, so this is correct. No bug here.

### Summary of Issues

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | CRITICAL | build_shape line 211-212 | `select_faces_by_normal` after `clean()` produces face refs that crash in `tag_socket` when BMesh has removed/compacted faces from degenerate geometry |
| 2 | MEDIUM | tag_socket in massa_builder.py line 473 | No validity check on face before accessing layer — any stale face ref crashes |
| 3 | MEDIUM | BRICK style, slot 2 rail cap faces | BOX projection on thin horizontal cap faces produces severely stretched UV island (smeared band) |
| 4 | LOW | get_slot_meta uv="SKIP" vs "BOX" discrepancy | The indexed/stale version shows `"uv": "SKIP"` for all slots, but the live file shows `"uv": "BOX"`. The live file is correct; index is stale. |
