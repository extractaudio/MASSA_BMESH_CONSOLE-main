---
description: Workflow for cartridge-authored UV seams, edge slots, and spatial seam audits.
---

# UV Unwrap Workflow

Use this workflow when creating or repairing Massa cartridge UV logic. The goal is to make each cartridge responsible for its own seam and edge-slot intent instead of relying on console auto-detected boundaries.

## Core Policy

The cartridge is the source of truth for UV seams and edge roles.

For UV-critical cartridge work, do not depend on `edge_auto_detect` or automatic boundary detection to invent the unwrap structure. In cartridge UV sessions, turn Auto-Detect Boundaries off before judging seam placement. Automatic detection may be useful as a visualization or emergency fallback, but it must not be the design source for final cartridge seams.

Manual cartridge logic must:

1. Create or retrieve the `MASSA_EDGE_SLOTS` layer.
2. Assign edge roles spatially inside `build_shape`.
3. Mark required UV seams with `e.seam = True`.
4. Use local orientation, occlusion, and topology evidence instead of global-axis assumptions.
5. Protect intentional manual seams with `massa_force_seam`.
6. Verify that the result passes the geometry and surface auditors.

## Engine Facts To Respect

The pipeline currently runs in this order:

1. `op.build_shape(bm)` creates the cartridge BMesh.
2. Cleanup may remove degenerate geometry.
3. The engine ensures `MASSA_EDGE_SLOTS` exists.
4. `auto_detect_edge_slots(bm)` runs only when `edge_auto_detect` is true.
5. `process_edge_slots(bm, op)` converts edge slots into seam, sharp, crease, or bevel actions.
6. `auto_detect_sharp_edges(bm, op)` adds sharp edges after slot processing.
7. Seam solvers and flat-seam cleanup may run later.

Important consequence: if a seam matters, do not leave it as an unprotected guess. Mark it manually and set `massa_force_seam`.

## Required Agent Stance

You are the Massa UV Engineer. Your job is to replace manual edge-index selection with semantic spatial logic.

Never guess edge indices. Never say "edge 14 is the seam" unless that edge was selected by spatial criteria such as face normal, axis position, cap membership, material boundary, or hidden-side bias.

Every seam must answer:

1. What surface is being unfolded?
2. What local frame describes this component after rotation or deformation?
3. Where can the texture cut be hidden by occlusion or assembly contact?
4. Does this cut produce islands that can flatten without stretching?
5. Does the seam connect to another seam loop, boundary, or cap loop?
6. Is the seam protected if cleanup might remove it?

## Edge Slot Standard

Use the existing `MASSA_EDGE_SLOTS` integer layer.

| ID | Name | Default Meaning | Use For |
| :--- | :--- | :--- | :--- |
| 0 | None | No special treatment | Interior smooth edges |
| 1 | Perimeter | Seam + sharp by default | Silhouettes, end caps, outer borders |
| 2 | Contour | Sharp by default | Major hard-surface form breaks |
| 3 | Guide | Seam by default | Zippers, unwrap guide cuts, hidden UV cuts |
| 4 | Detail | Ignored by default | Small decorative lines or optional bevel guides |
| 5 | Fold | Ignored by default | Subdivision crease or cloth-style fold intent |

For UV seams, prefer:

- Slot 1 for cap loops, outer borders, and silhouette seams that are also hard edges.
- Slot 3 for a hidden zipper or flow cut that should be a seam but not a visible hard edge.
- Direct `e.seam = True` plus `massa_force_seam` for intentional seams that should survive cleanup even if the slot action is changed later.

## Boilerplate Layer Setup

Put this near the seam logic in `build_shape`:

```python
edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
if not edge_slots:
    edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

force_seam = bm.edges.layers.int.get("massa_force_seam")
if not force_seam:
    force_seam = bm.edges.layers.int.new("massa_force_seam")

def mark_edge(e, slot=None, seam=False, sharp=False, protect=False):
    if slot is not None:
        e[edge_slots] = slot
    if seam:
        e.seam = True
    if sharp:
        e.smooth = False
    if protect:
        e[force_seam] = 1
```

Use this helper only as a local convenience. Keep the spatial selection logic readable next to the geometry it marks.

## Orientation And Visibility Helpers

Do not assume a component is aligned to global X, Y, or Z. Use global axes only when the cartridge explicitly creates an axis-aligned primitive and marks seams before any rotation, path placement, or deformation.

For general procedural work, derive a local frame first:

- Prefer known construction vectors from the generator, such as the path direction, extrusion vector, rail tangent, or cap-loop normal.
- If construction vectors are not available, estimate an oriented frame with PCA or an oriented bounding box over the component vertices.
- For tubes, prefer cap-loop normals and side-edge direction over a global axis.
- For planks, prefer the dominant local length vector and cap face clusters over AABB dimensions.

Minimal PCA-style helper:

```python
def component_centroid(verts):
    total = sum((v.co for v in verts), Vector())
    return total / max(1, len(verts))

def principal_axis(verts, iterations=8):
    center = component_centroid(verts)
    direction = Vector((1.0, 0.37, 0.19)).normalized()
    points = [v.co - center for v in verts]

    for _ in range(iterations):
        projected = Vector()
        for p in points:
            projected += p * p.dot(direction)
        if projected.length < 0.0001:
            break
        direction = projected.normalized()

    return direction
```

Use the returned direction as the local longitudinal axis. Cap faces are the face clusters whose normals align most strongly with that local axis. Side or zipper candidates are edges whose direction aligns with the local axis and are not part of the cap loops.

Visibility must also be dynamic. Negative Y is only a fallback for simple preview assets. In procedural assemblies, choose the zipper by occlusion:

1. Calculate the component centroid.
2. If a parent or assembly centroid is known, score edges closer to that core mass as more hidden.
3. If no parent centroid exists, prefer inward-facing, underside, concave, or least camera-facing edges.
4. If ray casting is available, prefer the edge with the highest occlusion count from short outward rays.
5. Fall back to the local-frame hidden axis only after the above evidence is unavailable.

Example scoring helper:

```python
def occlusion_score(edge, component_center, parent_center=None):
    edge_center = (edge.verts[0].co + edge.verts[1].co) * 0.5
    score = 0.0

    if parent_center is not None:
        # Edges facing or sitting closer to the assembly core are better hidden cuts.
        to_core = parent_center - edge_center
        score += max(0.0, 1.0 / max(0.001, to_core.length))

    linked_normal = Vector()
    for f in edge.link_faces:
        linked_normal += f.normal
    if linked_normal.length > 0.0001:
        linked_normal.normalize()
        inward = component_center - edge_center
        if inward.length > 0.0001:
            score += max(0.0, linked_normal.dot(inward.normalized()))

    if edge.is_manifold and len(edge.link_faces) == 2:
        try:
            # Concave edges are often visually protected by contact shadow.
            if edge.calc_face_angle(0.0) > math.radians(45):
                score += 0.25
        except ValueError:
            pass

    return score
```

## Phase 1: Classify The Geometry

Before writing seam logic, classify every generated component into a UV archetype.

| Archetype | Shape Examples | Seam Strategy |
| :--- | :--- | :--- |
| `UV_PRIM_PLANK` | beams, steps, rectangular bars, rails | Cut both caps and one hidden longitudinal edge |
| `UV_PRIM_TUBE` | cylinders, posts, pipes, cones | Decap both end loops and add one hidden zipper |
| `UV_PRIM_SHEET` | panels, glass panes, signs | Seam only the perimeter if needed; prefer fit or box mapping |
| `UV_PRIM_STRIP` | path extrusions, rails, hoses | Cut one underside or backside edge along the full path |
| `UV_PRIM_BOX_DETAIL` | hard-surface modules with insets | Separate material islands and mark contour edges sharp |
| `UV_PRIM_SOCKET` | hidden socket or snap faces | Isolate from visible UVs and assign slot 9 material |
| `UV_PRIM_INTERSECTION` | boolean joins, cut-ins, fused modules | Add tension-relief guide seams from concave junctions to perimeters |

State the classification in your reasoning before editing:

```text
Classifying main hull as UV_PRIM_PLANK.
Classifying side pipes as UV_PRIM_TUBE.
Classifying inset panels as UV_PRIM_BOX_DETAIL.
```

## Phase 2: Capture Geometry At Birth

Prefer marking seams immediately after creating each component. Use returned `bmesh.ops` geometry or the builder's active face/edge groups when available.

Good:

```python
ret = bmesh.ops.create_cube(bm, size=1.0)
new_faces = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMFace)]
# Mark seams using these new faces before later operations mix them with the rest of the mesh.
```

Avoid:

```python
# Bad: depends on final edge order after many operations.
bm.edges[14].seam = True
```

## Phase 3: Spatial Seam Patterns

### Pattern A: Plank, Beam, Tread

Goal: caps become separate islands and the long body unwraps as a single strip.

Spatial rules:

1. Find the local longitudinal axis from the generator vector, cap-loop normals, PCA, or an OBB.
2. Find the two cap face clusters whose normals align most strongly with that local axis.
3. Mark cap perimeters as slot 1, seam, sharp, protected.
4. Pick one longitudinal edge with the strongest occlusion score for the zipper.
5. Mark the zipper as slot 3, seam, protected.

```python
def mark_plank_uv(new_faces, parent_center=None, local_axis=None):
    verts = {v for f in new_faces for v in f.verts}
    component_center = component_centroid(list(verts))
    long_axis = (local_axis or principal_axis(list(verts))).normalized()

    cap_faces = sorted(
        new_faces,
        key=lambda f: abs(f.normal.dot(long_axis)),
        reverse=True,
    )[:2]

    for f in cap_faces:
        for e in f.edges:
            mark_edge(e, slot=1, seam=True, sharp=True, protect=True)

    cap_edges = {e for f in cap_faces for e in f.edges}
    long_edges = [
        e for f in new_faces for e in f.edges
        if e not in cap_edges and len(e.verts) == 2
    ]

    zipper_candidates = [
        e for e in set(long_edges)
        if (e.verts[1].co - e.verts[0].co).normalized().dot(long_axis) > 0.75
    ] or list(set(long_edges))

    zipper = max(
        zipper_candidates,
        key=lambda e: occlusion_score(e, component_center, parent_center),
    )
    mark_edge(zipper, slot=3, seam=True, protect=True)
```

Audit the result spatially:

- Cap loops should be complete.
- Exactly one zipper should run the length of the body.
- The zipper should sit on the most occluded side, not a hard-coded global side.
- No zipper should stop in the middle of a face group.

### Pattern B: Tube, Pipe, Post, Cone

Goal: top and bottom caps become islands and the side wall opens into a rectangle.

Spatial rules:

1. Identify cap faces by local tube axis, cap-loop normals, generator tangent, PCA, or an OBB.
2. Mark cap loops as slot 1, seam, sharp, protected.
3. Find side edges that connect the cap loops.
4. Choose one side edge with the strongest dynamic occlusion score.
5. Mark the zipper as slot 3, seam, protected.

```python
def mark_tube_uv(new_verts, parent_center=None, local_axis=None):
    faces = {f for v in new_verts for f in v.link_faces}
    component_center = component_centroid(list(new_verts))
    tube_axis = (local_axis or principal_axis(list(new_verts))).normalized()

    cap_faces = [
        f for f in faces
        if abs(f.normal.dot(tube_axis)) > 0.85
    ]

    cap_edges = set()
    for f in cap_faces:
        for e in f.edges:
            cap_edges.add(e)
            mark_edge(e, slot=1, seam=True, sharp=True, protect=True)

    side_edges = {
        e for v in new_verts for e in v.link_edges
        if e not in cap_edges and e.is_manifold
    }

    axis_like = [
        e for e in side_edges
        if abs((e.verts[1].co - e.verts[0].co).normalized().dot(tube_axis)) > 0.65
    ]

    if axis_like:
        zipper = max(
            axis_like,
            key=lambda e: occlusion_score(e, component_center, parent_center),
        )
        mark_edge(zipper, slot=3, seam=True, protect=True)
```

Audit the result spatially:

- There must be one continuous zipper from one cap loop to the other.
- Cap loops must be fully cut.
- Do not create multiple random zippers around the cylinder.
- Prefer the most occluded side: assembly-facing, underside, inner wall, concave contact, or least visible quadrant.

### Pattern C: Sheet, Pane, Plate

Goal: keep the visible face clean and prevent socket, glass, or thin-panel faces from distorting the main unwrap.

Spatial rules:

1. Treat large front and back faces as primary surfaces.
2. Mark only outer perimeter edges when the sheet needs isolation.
3. Use slot 2 for hard contours that should be sharp but not UV cuts.
4. Use `get_slot_meta` with `uv: "FIT"` or `uv: "BOX"` when full unwrap is unnecessary.

```python
def mark_sheet_uv(sheet_faces):
    boundary_edges = {
        e for f in sheet_faces for e in f.edges
        if e.is_boundary or len(e.link_faces) < 2
    }
    for e in boundary_edges:
        mark_edge(e, slot=1, seam=True, sharp=True, protect=True)
```

Audit the result spatially:

- The front face should not have unnecessary cuts through visible detail.
- Thin side strips should not collapse into zero-area UVs.
- If using `FIT`, verify the slot metadata matches the intended material slot.

### Pattern D: Hard-Surface Box Detail

Goal: keep major mechanical form breaks sharp while only cutting seams where islands need to unfold.

Spatial rules:

1. Use slot 2 for major non-flat contour edges.
2. Use slot 1 for outer borders and cap loops.
3. Use slot 3 for hidden unwrap guides.
4. Do not make every sharp edge a seam. Sharp shading and UV cuts are related but not identical.

```python
for e in component_edges:
    if e.is_manifold and len(e.link_faces) == 2:
        angle = e.calc_face_angle(0.0)
        if angle > math.radians(60):
            mark_edge(e, slot=2, sharp=True)
```

Then add only the seams required to flatten the island:

```python
for e in hidden_guide_edges:
    mark_edge(e, slot=3, seam=True, protect=True)
```

Audit the result spatially:

- Major silhouette edges should read as clean hard edges.
- UV seams should be hidden where possible.
- Large closed volumes with more than 12 faces must have role 1 or role 3 seam edges.

### Pattern E: Socket And Meta Faces

Goal: sockets must not distort visible UV islands.

Spatial rules:

1. Assign socket faces to material slot 9.
2. Mark socket perimeter edges as seams and protected.
3. Keep socket UV strategy as `SKIP` in `get_slot_meta`.

```python
socket_face.material_index = 9
for e in socket_face.edges:
    mark_edge(e, seam=True, sharp=True, protect=True)
```

### Pattern F: Boolean Intersection And Tension Relief

Goal: relieve UV tension around boolean cut-ins, fused modules, drilled holes, inset mechanical details, and any geometry where a sharp concave junction would otherwise create stretched islands.

Spatial rules:

1. Find concave manifold edges around the intersection boundary.
2. Group those edges into junction clusters by shared vertices.
3. Find the deepest concave vertex in each cluster.
4. Find the nearest existing perimeter or cap seam, usually slot 1.
5. Plot the shortest edge-walk from the deep concave vertex to that perimeter.
6. Mark that path as slot 3, seam, protected.

This is a tension-relief seam, not a decorative contour. It should be short, purposeful, and connected to an existing seam or boundary.

```python
def mark_intersection_relief(component_edges):
    concave_edges = []
    for e in component_edges:
        if not e.is_manifold or len(e.link_faces) != 2:
            continue
        try:
            angle = e.calc_face_angle(0.0)
        except ValueError:
            continue

        if angle < math.radians(35):
            continue

        center_delta = e.link_faces[1].calc_center_median() - e.link_faces[0].calc_center_median()
        if center_delta.dot(e.link_faces[0].normal) < -0.001:
            concave_edges.append(e)
            mark_edge(e, slot=2, sharp=True)

    perimeter_edges = [
        e for e in component_edges
        if e[edge_slots] == 1 or e.is_boundary
    ]

    for e in concave_edges:
        deepest = min(
            e.verts,
            key=lambda v: sum((v.co - f.calc_center_median()).dot(f.normal) for f in v.link_faces),
        )
        target = min(
            perimeter_edges,
            key=lambda p: min((deepest.co - v.co).length for v in p.verts),
            default=None,
        )
        if target:
            # In production cartridge code, shortest_edge_path walks v.link_edges.
            for relief_edge in shortest_edge_path(deepest, target):
                mark_edge(relief_edge, slot=3, seam=True, protect=True)
```

Audit the result spatially:

- Relief seams must connect a concave junction to a perimeter, cap loop, or existing seam.
- Do not scatter isolated guide edges inside the boolean scar.
- Relief cuts should reduce `CRITICAL_UV_SPIKES_N`, not create visible random cuts across hero surfaces.
- If no shortest-path helper exists, write one over `v.link_edges`; do not guess edge indices.

## Phase 4: Slot Metadata Must Agree

Update `get_slot_meta` so the UV mode matches the component strategy.

General mapping:

| Component | Suggested UV Mode |
| :--- | :--- |
| Planks, beams, simple bars | `BOX` or `UNWRAP` |
| Tubes, posts, cones, pipes | `UNWRAP` |
| Sheets, panels, glass | `FIT` or `BOX` |
| Hard-surface detail | `BOX` for simple detail, `UNWRAP` for closed complex pieces |
| Sockets | `SKIP` |
| Boolean intersections | `UNWRAP` plus protected relief seams |

Example:

```python
def get_slot_meta(self):
    return {
        0: {"name": "Body", "uv": "UNWRAP", "phys": "METAL_STEEL"},
        1: {"name": "Trim", "uv": "BOX", "phys": "METAL_DARK"},
        3: {"name": "Glass", "uv": "FIT", "phys": "GLASS"},
        9: {"name": "Socket", "uv": "SKIP", "phys": "NONE", "sock": True},
    }
```

## Phase 5: Island Scale And Texel Density

Cutting seams is not enough. The output UVs must also have stable island scale so small detail cartridges and large hull cartridges render with coherent texel density.

After the engine has generated and named the active UV layer `UVMap`, run or require a UV island normalizer that:

1. Excludes slots whose metadata uses `uv: "SKIP"`.
2. Computes island area in 3D and UV space.
3. Scales islands toward a unified texel density.
4. Uses `CARTRIDGE_META` scale class, if present, to choose the density target.
5. Packs islands with a non-zero margin after normalization.

Recommended scale-class policy:

| `CARTRIDGE_META` Scale Class | Texel Density Intent |
| :--- | :--- |
| `SMALL` / `DETAIL` / `PROP` | Higher density for readable small features |
| `MEDIUM` / unset | Baseline density |
| `LARGE` / `HULL` / `STRUCTURE` | Lower density unless the cartridge has hero-facing detail |

If the current engine has no normalizer hook for a cartridge, document that gap in the agent output instead of pretending seam placement solved scale.

## Phase 6: Spatial Review Checklist

Before running Blender, inspect the seam logic like a modeler would.

Answer these questions:

1. Are caps cut off from cylindrical or plank bodies?
2. Does each tube have one hidden zipper from cap to cap?
3. Does each plank have one hidden long seam and two cap loops?
4. Are visible hero faces free of random cuts?
5. Are role 2 contour edges sharp without becoming unwanted seams?
6. Are sockets isolated from visible material islands?
7. Are seams selected by local frame, cap-loop normals, material boundaries, occlusion score, or concave junction depth?
8. Are all important manual seams protected with `massa_force_seam`?
9. Could cleanup remove any flat seam that the unwrap still needs?
10. Would `WARNING_ISOLATED_SEAM_EDGES_N` indicate a real broken seam path?
11. Are rotated or diagonal components using local PCA/OBB/generator axes instead of AABB math?
12. Do boolean intersections have relief seams from concave depth to the nearest perimeter?
13. Will islands be normalized to the expected texel density after unwrap?

## Phase 7: Audit Loop

Use the smallest targeted audit that proves the UV seam change.

Recommended first pass:

```powershell
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode AUDIT
```

Use UV-specific modes only when the edit directly affects UVs or the audit leaves uncertainty:

```powershell
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode UV_INSPECT
python _Scripts/test_run_cartridge.py massa/modules/cartridges/<cartridge>.py --mode UV_HEATMAP
```

Interpret common flags:

| Flag | Meaning | Fix |
| :--- | :--- | :--- |
| `CRITICAL_MISSING_SLOT_LAYER` | `MASSA_EDGE_SLOTS` was not created | Add the layer setup in `build_shape` |
| `CRITICAL_NO_PERIMETER_DEFINED` | No role 1 edges exist | Mark cap loops, silhouettes, or outer borders |
| `CRITICAL_NO_SEAMS_ON_COMPLEX_MESH` | Closed complex mesh has no role 1 or role 3 seam edges | Add cap loops and guide zippers |
| `WARNING_ISOLATED_SEAM_EDGES_N` | Seam edges do not connect to boundaries or other seams | Continue the seam path to a loop or boundary |
| `CRITICAL_MISSING_UV_LAYER` | Output mesh has no UV layer | Fix `get_slot_meta` UV modes or manual UV creation |
| `CRITICAL_ZERO_UV_DATA` | UVs exist but all coordinates collapsed | Verify unwrap mode and avoid `SKIP` on visible slots |
| `CRITICAL_UV_SPIKES_N` | Severe island distortion | Add better guide seams or fix sliver topology |
| `CRITICAL_COLLAPSED_UVS_N` | UV island collapsed to a point | Fix zero-area faces or unwrap strategy |

## Phase 8: Agent Output Requirements

When finishing a cartridge UV change, report:

1. Which archetypes were used.
2. Which slots were marked manually.
3. What local orientation source was used: generator vector, cap-loop normals, PCA, or OBB.
4. Where hidden zippers were placed and why they scored as occluded.
5. Whether `massa_force_seam` protects the manual seams.
6. Which audit command was run and whether it passed.
7. Whether UV islands were normalized for texel density, or which engine gap prevents it.

Example final note:

```text
UV seams are cartridge-authored now. The main body uses PLANK logic with protected cap loops from its PCA local axis and an assembly-facing guide zipper chosen by occlusion score. The posts use TUBE logic with protected cap loops and one core-facing zipper each. Boolean cut-ins have protected relief seams from concave depth to perimeter loops. AUDIT passed with no seam or UV critical flags; texel normalization used the cartridge scale class.
```

## Hard Rules

- Do not rely on `edge_auto_detect` as the final seam author.
- Do not select seams by raw edge index.
- Do not use AABB/global-axis math for rotated, diagonal, path-based, or deformed components.
- Do not assume negative Y is hidden unless no local visibility evidence exists.
- Do not mark every sharp edge as a UV seam.
- Do not leave boolean intersections without tension-relief analysis.
- Do not leave intentional flat seams unprotected.
- Do not allow socket or meta faces to share visible UV islands.
- Do not use `bpy.ops.project_from_view` in background audit workflows.
- Do not use zero UV margins for packed islands.
- Do not claim render-ready UVs until island texel density has been normalized or explicitly reported as an engine gap.
- Do not deliver a complex closed mesh with no slot 1 or slot 3 seams.

## Quick Prompt For Agents

Use this prompt when handing off a UV repair task:

```text
Act as the Massa UV Engineer. Read the cartridge geometry and classify each component as PLANK, TUBE, SHEET, STRIP, BOX_DETAIL, SOCKET, or INTERSECTION. Do not rely on console auto-detected boundaries. In build_shape, create or retrieve MASSA_EDGE_SLOTS and massa_force_seam, then mark seams spatially at geometry birth. Use slot 1 for protected cap/perimeter seams, slot 2 for hard contours, and slot 3 for hidden guide zippers and intersection relief seams. Choose seams by generator vectors, cap-loop normals, PCA/OBB local frames, material boundaries, occlusion score, and concave junction depth, never by raw edge index or fixed negative-Y bias. Update get_slot_meta so UV modes match the geometry. Normalize UV islands to the CARTRIDGE_META scale class after UVMap generation when the engine supports it. Run a targeted audit and fix missing perimeter, missing seam, isolated seam, collapsed UV, UV spike, and texel-density issues before delivery.
```
