# Massa Cartridge Audit Standards

This section defines the strict geometric and behavioral contracts for the core architectural cartridges. The auditing system parses these JSON blocks to validate generated meshes.

## ARC_01: Wall
```json
{
  "id": "arc_01_wall",
  "behavior": "Volumetric Panels",
  "slots": [0, 2, 9],
  "default_params": {
      "wall_length": 4.0,
      "wall_height": 3.0,
      "wall_thick": 0.2
  },
  "expected_dimensions": [4.0, 0.2, 3.0],
  "tolerance": 0.2
}
```

## ARC_02: Stairs
```json
{
  "id": "arc_02_stairs",
  "behavior": "Stacked Treads & Risers",
  "slots": [0, 1, 2, 9],
  "default_params": {
      "stair_width": 1.2,
      "total_height": 3.0,
      "step_count": 12,
      "tread_depth": 0.28
  },
  "expected_dimensions": [1.3, 3.95, 3.6],
  "tolerance": 0.5
}
```

## ARC_03: Window
```json
{
  "id": "arc_03_window",
  "behavior": "Volumetric Frame & Glass",
  "slots": [0, 3, 9],
  "default_params": {
      "win_width": 2.0,
      "win_height": 2.5,
      "frame_width": 0.1
  },
  "expected_dimensions": [2.0, 0.1, 2.5],
  "tolerance": 0.2
}
```

## ARC_04: Doorway
```json
{
  "id": "arc_04_doorway",
  "behavior": "Volumetric Jambs & Header",
  "slots": [0, 1, 7, 9],
  "default_params": {
      "door_width": 1.0,
      "door_height": 2.1,
      "frame_width": 0.1,
      "frame_depth": 0.15
  },
  "expected_dimensions": [1.2, 0.15, 2.2],
  "tolerance": 0.2
}
```

## ARC_05: Column
```json
{
  "id": "arc_05_column",
  "behavior": "Stacked Rings",
  "slots": [0, 9],
  "default_params": {
      "total_height": 4.0,
      "radius_base": 0.4
  },
  "expected_dimensions": [0.96, 0.96, 4.2],
  "tolerance": 0.3
}
```
