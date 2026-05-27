import json

filepath = r'C:\Users\thinktank\.gemini\antigravity-ide\brain\244b33ca-1a21-4b86-894c-add254d46c73\.system_generated\steps\6\output.txt'
with open(filepath, 'r') as f:
    data = json.load(f)

edges = data.get('result', {}).get('selected', {}).get('edges', [])

print(f"Total selected edges: {len(edges)}")
for e in edges:
    v_co = e.get('v_co_local')
    dx = abs(v_co[0][0] - v_co[1][0])
    dy = abs(v_co[0][1] - v_co[1][1])
    dz = abs(v_co[0][2] - v_co[1][2])
    print(f"Edge {e.get('index')}: dx={dx:.4f}, dy={dy:.4f}, dz={dz:.4f}, Y mid={e.get('midpoint_local')[1]:.4f}")
