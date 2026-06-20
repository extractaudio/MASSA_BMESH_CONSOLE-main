# Fixes: cart_arc_01_wall.py

## Fix 1 (CRITICAL) — Guard tag_socket against removed BMFace references

**File:** `massa/modules/massa_builder.py`
**Lines:** 473–474

### Before
```python
        if self.active_faces:
            for f in self.active_faces:
                f[layer] = socket_id
```

### After
```python
        if self.active_faces:
            for f in self.active_faces:
                if not f.is_valid:
                    continue
                f[layer] = socket_id
```

**Why this is the minimum fix:** `BMFace.is_valid` is the canonical BMesh check for whether a face reference is still alive after cleanup ops. Adding it as a guard before the write eliminates all 5 FUZZ_CRASH events without changing geometry behavior. The socket simply won't be tagged on a face that no longer exists (which is correct — it was cleaned away for a reason).

---

## Fix 2 (UV/Seam) — Move seam tagging to AFTER baseboards are built

**File:** `massa/modules/cartridges/cart_arc_01_wall.py`

The perimeter seam pass currently fires before baseboards are added, so baseboard boundary edges are never marked as seams.

### Before (current order in build_shape)
```python
        # Merge Segments before tagging seams to ensure continuous mesh
        builder.clean()

        # Tag Perimeter Edges as Seams (1)
        builder.select_all_faces().select_boundary().tag_edge_role(1)

        # Build Baseboards
        bh = self.baseboard_height
        bd = self.baseboard_depth

        if bh > 0.001:
            # ... baseboard geometry creation ...
            for r in bb_rects:
                # Front Baseboard
                builder.create_box(r['w'], bd, bh) \
                       .translate(cx, -bd/2, cz) \
                       .tag_slot(2) \
                       .select_boundary().tag_edge_role(2)

                builder.select_boundary().tag_edge_role(1)   # BUG: wrong selection context

                # Back Baseboard
                builder.create_box(r['w'], bd, bh) \
                       .translate(cx, t + bd/2, cz) \
                       .tag_slot(2) \
                       .select_boundary().tag_edge_role(1)

        # Sockets (Tagging existing faces)
        builder.clean() # Final cleanup
```

### After (move seam pass to after baseboards, fix selection context)
```python
        # Merge Segments before building baseboards
        builder.clean()

        # Build Baseboards
        bh = self.baseboard_height
        bd = self.baseboard_depth

        if bh > 0.001:
            # ... (same baseboard rect computation, unchanged) ...
            for r in bb_rects:
                if r['w'] <= 0.001: continue

                cx = r['x'] + r['w']/2
                cz = bh/2

                # Front Baseboard (Y = -bd/2)
                builder.create_box(r['w'], bd, bh) \
                       .translate(cx, -bd/2, cz) \
                       .tag_slot(2) \
                       .select_boundary().tag_edge_role(2)   # contour only

                # Back Baseboard (Y = t + bd/2)
                builder.create_box(r['w'], bd, bh) \
                       .translate(cx, t + bd/2, cz) \
                       .tag_slot(2) \
                       .select_boundary().tag_edge_role(2)   # contour only

        # Final cleanup before socket tagging
        builder.clean()

        # Tag Perimeter Edges as Seams (1) — NOW covers wall + baseboards
        builder.select_all_faces().select_boundary().tag_edge_role(1)
```

**Key changes:**
1. Seam pass moved to after both the wall geometry AND the baseboard geometry are complete
2. The duplicate/ambiguous `builder.select_boundary().tag_edge_role(1)` call inside the baseboard loop is removed — it was firing on an undefined active_faces context
3. Back baseboard changes from edge_role(1) to edge_role(2) for consistency (contour, not seam); the unified seam pass at the end handles all perimeters correctly

---

## Fix 3 (UV) — Use "BOX" in get_slot_meta instead of "SKIP"

**File:** `massa/modules/cartridges/cart_arc_01_wall.py`

The current `get_slot_meta` declares `"uv": "SKIP"` for all slots, then manually calls `tag_uvs` in `build_shape`. This is a fragile dual-path approach. The cleaner fix is to declare the correct UV method in `get_slot_meta` and remove the manual tag_uvs calls.

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

### And remove from build_shape (delete these 3 lines at end of build_shape)
```python
        # REMOVE these lines:
        uv_sc   = 1.0 if self.fit_uvs else self.uv_scale
        uv_proj = 'FIT' if self.fit_uvs else 'BOX'
        builder.select_faces_by_slot(0).tag_uvs(scale=uv_sc, projection=uv_proj)
        builder.select_faces_by_slot(1).tag_uvs(scale=uv_sc, projection=uv_proj)
        builder.select_faces_by_slot(2).tag_uvs(scale=uv_sc, projection=uv_proj)
```

**Note:** If `uv_scale` and `fit_uvs` operator properties need to be honored, keep the manual `tag_uvs` calls but change `get_slot_meta` to `"uv": "KEEP"` so the pipeline doesn't overwrite the manually-assigned UVs. Do not use `"SKIP"` in both places — that leaves faces with uninitialized UV coordinates.

---

## Priority Order

1. **Fix 1** (massa_builder.py tag_socket guard) — eliminates all 5 FUZZ_CRASH events
2. **Fix 2** (seam pass ordering + selection context) — fixes smeared seam band at baseboard junction
3. **Fix 3** (get_slot_meta uv values) — fixes stretched UV on wall surface
