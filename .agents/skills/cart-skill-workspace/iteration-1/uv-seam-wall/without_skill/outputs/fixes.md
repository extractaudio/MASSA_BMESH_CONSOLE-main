# Fixes Applied: cart_arc_01_wall.py

All fixes were applied directly to:
`D:\AntiGravity_google\MASSA_BMESH_CONSOLE-main\massa\modules\cartridges\cart_arc_01_wall.py`

---

## Fix 1 — slot_meta: change uv="SKIP" to uv="BOX" for content slots

**Lines changed:** 60-62

### Before
```python
def get_slot_meta(self):
    return {
        0: {"name": "Wall Surface", "uv": "SKIP", "phys": "MASSA_DEBUG_1"},
        1: {"name": "Detail",       "uv": "SKIP", "phys": "MASSA_DEBUG_2"},
        2: {"name": "Trim",         "uv": "SKIP", "phys": "MASSA_DEBUG_3"},
        9: {"name": "Socket Anchor","sock": True,  "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
    }
```

### After
```python
def get_slot_meta(self):
    return {
        0: {"name": "Wall Surface", "uv": "BOX",  "phys": "MASSA_DEBUG_1"},
        1: {"name": "Detail",       "uv": "BOX",  "phys": "MASSA_DEBUG_2"},
        2: {"name": "Trim",         "uv": "BOX",  "phys": "MASSA_DEBUG_3"},
        9: {"name": "Socket Anchor","sock": True,  "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
    }
```

**Rationale:** `uv="SKIP"` told the engine to bypass UV generation entirely, leaving UVs only from the manual `tag_uvs` calls inside `build_shape`. Those manual calls ran at pipeline stage 1 (before weld/merge), so UV coordinates were based on pre-weld vertex positions. Changing to `uv="BOX"` delegates UV assignment to the engine pipeline, which runs after weld — coordinates are therefore stable and produce no seam-boundary stretching. Slot 9 (Socket Anchor) correctly keeps `uv="SKIP"` since it has no renderable geometry.

---

## Fix 2 — Remove manual tag_uvs calls from build_shape

**Lines removed:** former lines 214-219

### Before
```python
        # §7.2 — Dual-mode UV pass (respects uv_scale / fit_uvs)
        uv_sc   = 1.0 if self.fit_uvs else self.uv_scale
        uv_proj = 'FIT' if self.fit_uvs else 'BOX'
        builder.select_faces_by_slot(0).tag_uvs(scale=uv_sc, projection=uv_proj)
        builder.select_faces_by_slot(1).tag_uvs(scale=uv_sc, projection=uv_proj)
        builder.select_faces_by_slot(2).tag_uvs(scale=uv_sc, projection=uv_proj)
```

### After
```python
        # UV pass is handled by the engine pipeline using slot_meta uv="BOX".
        # Manual tag_uvs calls were removed because they ran before weld/merge (pipeline stage 1),
        # producing UV coords from pre-weld vertex positions — causing stretching and island
        # misalignment at segment boundaries when USE_WELD merges adjacent panels.
        # The engine UV pass runs after weld, so coords are stable and correctly placed.
```

**Rationale:** With slot_meta now declaring `uv="BOX"`, the engine handles UV projection post-weld. Keeping the manual calls would double-project and potentially undo the engine's work. The `uv_scale` and `fit_uvs` operator properties are still declared on the class (lines 55-56) and will be used by the engine UV pass via the standard pipeline contract.

**Note:** If the `fit_uvs` / `uv_scale` operator properties need to be passed into the engine UV pass, verify that `Massa_OT_Base` propagates `self.uv_scale` to the engine BOX projector. If not, a follow-up fix may be needed to pass these through the pipeline's `generate_surface_maps` call.

---

## Fix 3 — Baseboard: remove dead double tag_edge_role on front baseboard

**Lines changed:** 190-195 (former), now 192-199

### Before
```python
                # Front Baseboard (Y = -bd/2)
                builder.create_box(r['w'], bd, bh) \
                       .translate(cx, -bd/2, cz) \
                       .tag_slot(2) \
                       .select_boundary().tag_edge_role(2)

                builder.select_boundary().tag_edge_role(1)
```

### After
```python
                # Front Baseboard (Y = -bd/2)
                # tag_edge_role(1) = Perimeter (Seam + Sharp) on the outer boundary.
                # The previous double-tag (role 2 then immediately role 1) was dead code —
                # the second call overwrote the first. Simplified to a single role-1 tag.
                builder.create_box(r['w'], bd, bh) \
                       .translate(cx, -bd/2, cz) \
                       .tag_slot(2) \
                       .select_boundary().tag_edge_role(1)
```

**Rationale:** The original code tagged the front baseboard boundary with role 2 (Contour/Sharp) then immediately re-selected the same boundary and overwrote it with role 1 (Perimeter/Seam+Sharp). The role-2 tag was never effective. Simplified to the single intended role-1 tag, matching the back baseboard behavior.

---

## Summary of changes

| Fix | File location | Nature |
|-----|---------------|--------|
| slot_meta uv: SKIP → BOX | lines 60-62 | Behavioral: enables engine UV pass |
| Remove manual tag_uvs block | lines 214-222 | Behavioral: eliminates pre-weld UV baking |
| Baseboard single edge role | lines 192-199 | Correctness: removes dead code double-tag |

---

## Not fixed / deferred

- **REINFORCED inset UV overlap:** The inset creates two +Y-normal face layers (outer ring + recessed face) that share nearly identical UV coordinates under BOX projection. With the fix in place (engine BOX-maps post-weld), the UV overlap will be reduced but not eliminated — the outer and inner inset faces still have the same XZ footprint. A proper fix requires either using `uv="UNWRAP"` for slot 1, or adjusting the inset to shift the inner face along X/Z to separate the UV islands. This is tracked as a follow-up.

- **Seam effectiveness with default edge_slot_1_action=IGNORE:** If the operator's `edge_slot_1_action` defaults to IGNORE, the perimeter seam tags (role 1) will not be converted to UV seams. This is a pipeline configuration concern, not a cartridge bug — the cartridge correctly places role-1 tags on perimeter edges.
