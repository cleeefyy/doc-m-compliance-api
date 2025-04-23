import ezdxf
import os
import json

# Load DXF
dxf_path = os.path.join("floorplans", "example_wc.dxf")
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

# Layers to extract
target_layers = {
    "SECTION_FLOOR": [],
    "SECTION_TOILET": [],
    "SECTION_BASIN": [],
    "SECTION_GRAB_RAIL_REAR": [],
    "SECTION_GRAB_RAIL_SIDE": [],
    "SECTION_SHELF": [],
    "SECTION_DOOR_GRAB_RAIL": []
}

# Collect Y positions and print what we find
for e in msp:
    layer = e.dxf.layer
    if layer in target_layers and hasattr(e.dxf, "insert"):
        y = e.dxf.insert[1]
        target_layers[layer].append(y)
        print(f"📐 {layer}: insert Y = {y}")
    elif layer in target_layers and hasattr(e.dxf, "center"):
        y = e.dxf.center[1]
        target_layers[layer].append(y)
        print(f"📐 {layer}: center Y = {y}")
    elif layer in target_layers and hasattr(e.dxf, "start"):
        y = e.dxf.start[1]
        target_layers[layer].append(y)
        print(f"📐 {layer}: start Y = {y}")

# Print all collected values
print("\n📂 Collected Y-values for each layer:")
for layer, values in target_layers.items():
    print(f"  {layer}: {values}")

# Optional scale factor (set to 1.0 if working in mm)
SCALE = 1.0

# Use lowest floor Y as baseline
floor_y = min(target_layers["SECTION_FLOOR"]) if target_layers["SECTION_FLOOR"] else 0
print(f"\n🏗️  Floor Y baseline: {floor_y}")

# Compute height from floor
heights = {}
for layer, y_values in target_layers.items():
    if y_values and layer != "SECTION_FLOOR":
        avg_y = sum(y_values) / len(y_values)
        height = round((avg_y - floor_y) * SCALE, 2)
        key = layer.replace("SECTION_", "").lower()
        heights[key] = height
        print(f"📏 {key} height from floor: {height} mm")

# Load and update JSON
with open("outputs/example_wc_data.json", "r") as f:
    data = json.load(f)

data["section_heights_mm"] = heights

with open("outputs/example_wc_data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"\n✅ Extracted and saved section heights to example_wc_data.json")


