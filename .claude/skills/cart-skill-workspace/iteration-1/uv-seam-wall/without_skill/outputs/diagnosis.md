# UV / Seam Diagnosis: cart_arc_01_wall.py

## Summary

Three bugs work together to produce the reported UV stretching and smeared-band artifact. The root cause is a **slot-meta / manual-UV conflict** combined with **wrong edge-role tagging order for baseboards**.

---

## Bug 1 — CRITICAL: slot_meta `uv="SKIP"` conflicts with manual `tag_uvs` calls

**File:** `massa/modules/cartridges/cart_arc_01_wall.py`
**Lines:** 60-63 (slot_meta), 217-219 (UV pass)

### What is happening

`get_slot_meta()` declares `uv="SKIP"` for all three content slots (0, 1, 2). Per the MASSA architecture, `uv="SKIP"` instructs the engine pipeline to skip UV generation for those slots entirely.

At the same time, `build_shape()` calls `tag_uvs()` manually at lines 217-219 — a BOX or FIT projection applied directly inside the shape-building phase.

### Why it causes problems

The engine pipeline runs in this order:
1. `build_shape(bm)` — cartridge fills BMesh **← tag_uvs runs here**
2. Weld / merge (`USE_WELD=True`) — vertices merged, geometry moves
3. Seam solving / `apply_base_drivers`
4. Engine UV pass — **skipped** because `uv="SKIP"`

The manual `tag_uvs` call inside step 1 assigns UV coordinates based on **pre-weld vertex positions**. After step 2, welded vertices may shift slightly, and UV islands that were computed from absolute world X coordinates of separate wall segments may end up misaligned at the weld seam. Additionally, because the engine UV pass is skipped, there is no opportunity for the pipeline to re-pack or correct the UVs.

### Symptom
- UV stretching at the boundaries between wall segments (visible when `hole_enable=True` creates multiple panels that are then welded).
- No engine-level UV correction or packing occurs.

---

## Bug 2 — CRITICAL: BOX projection smears UVs at the REINFORCED inset ridge

**File:** `massa/modules/cartridges/cart_arc_01_wall.py`
**Lines:** 128-131

### What is happening

The REINFORCED style creates an inset face via:
```python
builder.select_faces_by_normal(Vector((0, 1, 0))) \
       .inset(0.1, depth=0.05) \
       .tag_slot(1) \
       .select_boundary().tag_edge_role(2)
```

The inset operation creates:
- The **outer ring** of the inset (still on the +Y face plane, normal ≈ (0,1,0))
- The **inner recessed face** (inset into the wall, also normal ≈ (0,1,0))
- The **inset side walls** (normals facing ±X/±Z depending on geometry)

Both the outer ring and the inner recessed face share the `+Y` normal, so the BOX projector maps them with `u=v.x, v=v.z`. Since the recessed face occupies the same XZ position range as the outer face (it is inset inward in Y only), **both faces receive nearly identical UV coordinates**. This produces UV overlap between the two polygons — the "smeared band" effect where two overlapping UV islands share texel space, causing a blurry stripe when rendered.

### Symptom
- Smeared / blurry band on the front face of the wall when `wall_style='REINFORCED'`.
- Two face layers at different depths share the same UV island.

---

## Bug 3 — MAJOR: Double edge-role tagging destroys role-2 assignment on front baseboard

**File:** `massa/modules/cartridges/cart_arc_01_wall.py`
**Lines:** 190-195

### What is happening

```python
# Front Baseboard (Y = -bd/2)
builder.create_box(r['w'], bd, bh) \
       .translate(cx, -bd/2, cz) \
       .tag_slot(2) \
       .select_boundary().tag_edge_role(2)   # Line 193: assigns role 2 (Sharp/Contour)

builder.select_boundary().tag_edge_role(1)   # Line 195: RE-SELECTS same boundary, overwrites with role 1
```

The `select_boundary()` at line 195 re-selects the same boundary edges of the last-active builder selection (the front baseboard), and overwrites the role-2 assignment with role-1 (Perimeter = Seam+Sharp).

This means:
- The `tag_edge_role(2)` at line 193 is dead code — its effect is immediately erased.
- The front baseboard boundary ends up as role 1 (identical to the back baseboard at line 201).
- The intent was likely: outer perimeter = role 1 (seam), inner detail edges = role 2 (sharp). But both end up as role 1.

### Symptom
- Baseboard edges all tagged as Seam+Sharp instead of the expected detail/contour sharp.
- Minor visual difference but incorrect seam placement on the baseboard interior edges.

---

## Supporting Evidence

### MassaBuilder.tag_uvs BOX projection (massa/modules/massa_builder.py lines 493-502)
The projection uses **raw vertex coordinates** (`v.x`, `v.z`), not normalized per-face UVs. For a wall segment translated to world position (cx, cy, cz), the U coordinate of the front face is the world X position of each vertex. Adjacent segments that share an X boundary will produce UV coordinates that start/end at the same U value — but this is only correct if the weld merges those vertices cleanly. Any floating-point imprecision in the weld can leave a hairline seam artifact.

### Edge slot pipeline (massa/modules/massa_engine.py lines 75-116)
Edge slots are translated to mesh seam/sharp/crease/bevel marks by `process_edge_slots`. The default `edge_slot_1_action` is configurable but defaults to `"IGNORE"` unless the user has set it. If the slot action is `IGNORE`, the perimeter seam tags from `tag_edge_role(1)` have no effect on the UV unwrap. This means the seams the cartridge places are only meaningful if the operator's `edge_slot_1_action` is set to `"SEAM"` or `"BOTH"`.

---

## Impact Summary

| Issue | Severity | Trigger condition |
|-------|----------|-------------------|
| slot_meta uv="SKIP" vs manual tag_uvs | CRITICAL | Always — every wall spawn |
| REINFORCED inset UV overlap / smeared band | CRITICAL | wall_style='REINFORCED' |
| Baseboard double tag_edge_role overwrite | MAJOR | baseboard_height > 0 |
| Seams inactive when edge_slot_1_action=IGNORE | MODERATE | Default config |
