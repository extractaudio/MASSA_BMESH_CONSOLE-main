import json

filepath = r'C:\Users\thinktank\.gemini\antigravity-ide\brain\244b33ca-1a21-4b86-894c-add254d46c73\.system_generated\steps\6\output.txt'
with open(filepath, 'r') as f:
    data = json.load(f)

edges = data.get('result', {}).get('selected', {}).get('edges', [])
print(f'Total selected edges: {len(edges)}')
for e in edges:
    v_co = e.get('v_co_local')
    mid = e.get('midpoint_local')
    idx = e.get('index')
    print(f'Edge {idx}: mid={mid}, v0={v_co[0]}, v1={v_co[1]}')
