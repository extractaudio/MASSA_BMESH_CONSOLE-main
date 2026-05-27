import json
from collections import defaultdict
import math

filepath = r'C:\Users\thinktank\.gemini\antigravity-ide\brain\244b33ca-1a21-4b86-894c-add254d46c73\.system_generated\steps\6\output.txt'
with open(filepath, 'r') as f:
    data = json.load(f)

edges = data.get('result', {}).get('selected', {}).get('edges', [])
verts = {}

# Build adjacency list
adj = defaultdict(list)
edge_coords = []
for e in edges:
    idx = e.get('index')
    v_indices = e.get('vert_indices')
    v_co = e.get('v_co_local')
    adj[v_indices[0]].append(v_indices[1])
    adj[v_indices[1]].append(v_indices[0])
    verts[v_indices[0]] = v_co[0]
    verts[v_indices[1]] = v_co[1]

# Find endpoints (degree 1)
endpoints = [v for v, neighbors in adj.items() if len(neighbors) == 1]
print(f"Number of endpoints: {len(endpoints)}")

for ep in endpoints:
    co = verts[ep]
    print(f"Endpoint {ep}: {co}")

# Let's see if these edges follow a specific rule (e.g. they form a cross on the cap, or they are along the XZ planes, etc.)
# Let's check the absolute coordinates of the vertices in these edges.
print("\nUnique vertex coordinates (abs values) rounded to 2 decimals:")
coords = set()
for v_co in verts.values():
    coords.add((round(abs(v_co[0]), 2), round(abs(v_co[1]), 2), round(abs(v_co[2]), 2)))
for c in sorted(coords):
    print(c)
