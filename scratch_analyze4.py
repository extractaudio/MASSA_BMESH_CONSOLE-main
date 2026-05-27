import json

filepath = r'C:\Users\thinktank\.gemini\antigravity-ide\brain\244b33ca-1a21-4b86-894c-add254d46c73\.system_generated\steps\6\output.txt'
with open(filepath, 'r') as f:
    data = json.load(f)

edges = data.get('result', {}).get('selected', {}).get('edges', [])

print("Checking if edges lie on X = ±(Z - 0.5) planes...")
all_match = True
for e in edges:
    v_co = e.get('v_co_local')
    for p in v_co:
        x = p[0]
        z_rel = p[2] - 0.5
        # is |X| ≈ |Z_rel| ?
        diff = abs(abs(x) - abs(z_rel))
        if diff > 0.001:
            print(f"Mismatch! Edge {e.get('index')}: x={x}, z_rel={z_rel}, diff={diff}")
            all_match = False
            break

if all_match:
    print("YES! All selected edges lie on the X = ±(Z - 0.5) diagonal planes!")
