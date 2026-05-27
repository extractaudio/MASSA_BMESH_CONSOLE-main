import json
from collections import defaultdict

filepath = r'C:\Users\thinktank\.gemini\antigravity-ide\brain\244b33ca-1a21-4b86-894c-add254d46c73\.system_generated\steps\6\output.txt'
with open(filepath, 'r') as f:
    data = json.load(f)

edges = data.get('result', {}).get('selected', {}).get('edges', [])

adj = defaultdict(list)
verts = {}
for e in edges:
    v_co = e.get('v_co_local')
    v0, v1 = e.get('vert_indices')
    adj[v0].append(v1)
    adj[v1].append(v0)
    verts[v0] = v_co[0]
    verts[v1] = v_co[1]

endpoints = [v for v, n in adj.items() if len(n) == 1]
print(f"Number of endpoints: {len(endpoints)}")

for ep in endpoints:
    co = verts[ep]
    print(f"Endpoint {ep}: {co}")

# Let's trace one path
if endpoints:
    curr = endpoints[0]
    path = [curr]
    prev = None
    while True:
        neighbors = adj[curr]
        next_v = None
        for n in neighbors:
            if n != prev:
                next_v = n
                break
        if next_v is None:
            break
        path.append(next_v)
        prev = curr
        curr = next_v
    print(f"Path length: {len(path)-1} edges")
    print("Path coordinates:")
    for v in path:
        print(verts[v])

