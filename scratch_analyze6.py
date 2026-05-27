import json
from collections import defaultdict

filepath = r'C:\Users\thinktank\.gemini\antigravity-ide\brain\244b33ca-1a21-4b86-894c-add254d46c73\.system_generated\steps\6\output.txt'
with open(filepath, 'r') as f:
    data = json.load(f)

edges = data.get('result', {}).get('selected', {}).get('edges', [])
adj = defaultdict(list)
for e in edges:
    v0, v1 = e.get('vert_indices')
    adj[v0].append(v1)
    adj[v1].append(v0)

endpoints = [v for v, n in adj.items() if len(n) == 1]
visited = set()

paths = []
for ep in endpoints:
    if ep in visited: continue
    curr = ep
    path = [curr]
    prev = None
    while True:
        visited.add(curr)
        next_v = None
        for n in adj[curr]:
            if n != prev:
                next_v = n
                break
        if next_v is None:
            break
        path.append(next_v)
        prev = curr
        curr = next_v
    paths.append(path)

for i, p in enumerate(paths):
    print(f"Path {i+1}: length {len(p)-1}, from {p[0]} to {p[-1]}")
