# Fixes: cart_arc_01_wall.py

## Fix 1 — CRITICAL: Stale BMFace reference crash in tag_socket

### Problem
After `builder.clean()`, some BMFace Python objects in `self.active_faces` can become
invalid C pointers (removed faces from remove_doubles). Accessing `f[layer]` on a removed
face raises `ReferenceError: BMesh data of type BMFace has been removed`.

### Fix Location
`massa/modules/massa_builder.py` — `tag_socket` method (line 464-475)

### Before
```python
def tag_socket(self, socket_id: int):
    """
    Tags selected faces as Socket Locations using 'MASSA_SOCKETS' layer.
    """
    layer = self.bm.faces.layers.int.get("MASSA_SOCKETS")
    if not layer:
        layer = self.bm.faces.layers.int.new("MASSA_SOCKETS")

    if self.active_faces:
        for f in self.active_faces:
            f[layer] = socket_id
    return self
```

### After
```python
def tag_socket(self, socket_id: int):
    """
    Tags selected faces as Socket Locations using 'MASSA_SOCKETS' layer.
    """
    layer = self.bm.faces.layers.int.get("MASSA_SOCKETS")
    if not layer:
        layer = self.bm.faces.layers.int.new("MASSA_SOCKETS")

    if self.active_faces:
        # Guard: BMFace objects become invalid after remove_doubles (clean()).
        # Check is_valid before accessing any layer data to prevent ReferenceError.
        live_faces = [f for f in self.active_faces if f.is_valid]
        for f in live_faces:
            f[layer] = socket_id
    return self
```

### Why this works
`BMFace.is_valid` returns `False` for faces that have been removed/freed by BMesh ops
(including `remove_doubles`). Filtering before the layer access prevents the
`ReferenceError` on the freed C pointer.

---

## Fix 2 — CRITICAL: Re-select faces after clean() in build_shape

### Problem
Even with Fix 1, the socket tagging will silently produce **no sockets** if all
selected faces happen to be invalid (i.e. the wall side faces were merged away).
The real fix is to **not rely on pre-clean selections** — always re-query after clean.

The current code in `build_shape` already does this correctly (calls
`select_faces_by_normal` AFTER `clean()`), so the selection itself is fresh.
Fix 1 is sufficient to prevent the crash.

However, as an additional defense-in-depth measure, `clean()` should also clear
`self.active_faces` so no stale references linger from before the clean call.

### Fix Location
`massa/modules/massa_builder.py` — `clean` method (line 563-568)

### Before
```python
def clean(self):
    """Runs remove_doubles and recalc_normals."""
    bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=0.0001)
    bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
    self._update()
    return self
```

### After
```python
def clean(self):
    """Runs remove_doubles and recalc_normals. Clears active selection (stale after merge)."""
    bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=0.0001)
    bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
    self._update()
    # Invalidate selection: remove_doubles may have freed faces in active_faces.
    self.active_faces = []
    self.active_edges = []
    return self
```

### Why this works
Clears `active_faces` and `active_edges` immediately after any geometry-destructive op,
so any subsequent fluent chain that skips an explicit select call will operate on an
empty set rather than crashing on freed face pointers.

---

## Fix 3 — MEDIUM: UV stretching on BRICK rail cap faces

### Problem
The BRICK style creates a rail box with `t * 1.2` depth and `rail_h = 0.1` height.
The top/bottom cap faces (normals +Z/-Z) have dimensions `wall_width × (t*1.2)`.
With `uv="BOX"` in slot meta, the engine BOX-maps these with `u=v.x, v=v.y`,
producing an extremely wide and flat UV island (smeared band, nearly zero V extent).

### Fix Location
`massa/modules/cartridges/cart_arc_01_wall.py` — `get_slot_meta` method (line 58-64)

Change slot 2 from `"uv": "BOX"` to `"uv": "UNWRAP"` so the engine uses LSCM/conformal
unwrap for the Trim/baseboard geometry. This correctly handles the thin rail geometry
by letting Blender's conformal solver determine UV islands from seam boundaries.

### Before
```python
def get_slot_meta(self):
    return {
        0: {"name": "Wall Surface", "uv": "BOX",  "phys": "MASSA_DEBUG_1"},
        1: {"name": "Detail",       "uv": "BOX",  "phys": "MASSA_DEBUG_2"},
        2: {"name": "Trim",         "uv": "BOX",  "phys": "MASSA_DEBUG_3"},
        9: {"name": "Socket Anchor","sock": True,  "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
    }
```

### After
```python
def get_slot_meta(self):
    return {
        0: {"name": "Wall Surface", "uv": "BOX",    "phys": "MASSA_DEBUG_1"},
        1: {"name": "Detail",       "uv": "BOX",    "phys": "MASSA_DEBUG_2"},
        2: {"name": "Trim",         "uv": "UNWRAP", "phys": "MASSA_DEBUG_3"},
        9: {"name": "Socket Anchor","sock": True,   "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
    }
```

### Why this works
UNWRAP (LSCM/conformal) respects seam edges (tagged via `tag_edge_role(1/2)`) and
unfolds the rail/baseboard geometry properly, avoiding the degenerate aspect ratio
that BOX projection produces on thin cross-section geometry.

---

## Implementation Order

1. Apply Fix 1 to `massa/modules/massa_builder.py` — stops the crash immediately.
2. Apply Fix 2 to `massa/modules/massa_builder.py` — defense-in-depth, prevents future similar bugs.
3. Apply Fix 3 to `massa/modules/cartridges/cart_arc_01_wall.py` — fixes UV stretching.

Fixes 1 and 2 are both in `massa_builder.py`. Make both edits in one pass.
