# Procedural Node Recipes (Blender 5.0 Edition)

A comprehensive database of **130** procedural node setups, expanded with detailed logic and parameters.

---
### 1. Procedural Cracks
- **Category:** Grunge
- **Difficulty:** Intermediate
- **Goal:** Surface cracks based on Voronoi cells
- **Node Tree:**
  1. `Voronoi Texture (Distance to Edge)`
  2. `ColorRamp (Crush Black/White)`
  3. `Math (Invert)`
  4. `Mix Color (Multiply with Base Color)`
  5. `Bump Node (Height)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Grunge styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 2. Weathered Rust
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Realistic rust patches on metal
- **Node Tree:**
  1. `Noise Texture (High Detail)`
  2. `ColorRamp (Rust Colors)`
  3. `Mix Shader (Factor: Noise)`
  4. `Principled BSDF (Metal vs Rust Diffuse)`
  5. `Bump Node`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 3. Moss Growth
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Moss growing on top surfaces
- **Node Tree:**
  1. `Geometry Node (Normal)`
  2. `Vector Math (Dot Product with Z Axis)`
  3. `ColorRamp (Threshold)`
  4. `Mix Shader (Moss BSDF vs Rock BSDF)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 4. Still Water
- **Category:** Liquid
- **Difficulty:** Intermediate
- **Goal:** Calm water surface
- **Node Tree:**
  1. `Principled BSDF (Trans: 1, Rough: 0, IOR: 1.33)`
  2. `Noise Texture (Scale large)`
  3. `Bump Node (Height)`
  4. `Normal`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Liquid styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 5. Volumetric Fire
- **Category:** FX
- **Difficulty:** Intermediate
- **Goal:** Fire simulation density
- **Node Tree:**
  1. `Gradient Texture (Spherical)`
  2. `Math (Multiply with Noise)`
  3. `ColorRamp (Black/Red/Yellow)`
  4. `Emission Strength & Color`
  5. `Principled Volume`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* FX styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 6. Object Scattering
- **Category:** GeoNodes
- **Difficulty:** Intermediate
- **Goal:** Scatter objects on surface
- **Node Tree:**
  1. `Distribute Points on Faces (Density Map)`
  2. `Instance on Points (Collection Info)`
  3. `Random Value (Rotation/Scale)`
  4. `Set Material`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* GeoNodes styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 7. Hanging Cables
- **Category:** GeoNodes
- **Difficulty:** Intermediate
- **Goal:** Catenary curves between points
- **Node Tree:**
  1. `Mesh Line (End Points)`
  2. `Subdivide Mesh`
  3. `Set Position (Offset Z based on Factor curve)`
  4. `Mesh to Curve`
  5. `Curve Circle (Profile)`
  6. `Curve to Mesh`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* GeoNodes styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 8. Surface Dust
- **Category:** Grunge
- **Difficulty:** Intermediate
- **Goal:** Dust accumulation on top
- **Node Tree:**
  1. `Texture Coordinate (Object)`
  2. `Noise Texture`
  3. `Separate XYZ (Normal Z)`
  4. `Math (Multiply)`
  5. `Mix Color (Base Texture vs Grey)`
  6. `Roughness (Increase)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Grunge styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 9. Micro Scratches
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Fine surface scratches
- **Node Tree:**
  1. `Voronoi Texture (Minkowski) or Wave Texture`
  2. `Mapping (Scale Y > 50)`
  3. `Bump Node (Invert)`
  4. `Normal Input`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 10. Fingerprints
- **Category:** Surface
- **Difficulty:** Intermediate
- **Goal:** Smudges on glossy surface
- **Node Tree:**
  1. `Image Texture (Roughness Map)`
  2. `ColorRamp (Adjust Contrast)`
  3. `Mix Color (Mix with Base Roughness)`
  4. `Principled BSDF (Roughness)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Surface styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 11. Wood Grain
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Procedural wood texture
- **Node Tree:**
  1. `Wave Texture (Rings)`
  2. `Vector Math (Add Noise to Coordinates)`
  3. `ColorRamp (Wood Tones)`
  4. `Bump Node`
  5. `Principled BSDF`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 12. Procedural Bricks
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Brick wall pattern
- **Node Tree:**
  1. `Brick Texture`
  2. `Mix Color (Mortar vs Brick Color)`
  3. `Brick Texture (Use as Factor)`
  4. `Bump Node`
  5. `Displacement`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 13. Hologram
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Sci-fi hologram shader
- **Node Tree:**
  1. `Layer Weight (Facing/Fresnel)`
  2. `ColorRamp (Blue/Cyan/Alpha)`
  3. `Emission Strength`
  4. `Mix Shader (Transparent vs Emission)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 14. Dispersion Glass
- **Category:** Glass
- **Difficulty:** Intermediate
- **Goal:** Glass with chromatic aberration
- **Node Tree:**
  1. `Principled BSDF (Trans: 1, Rough: 0)`
  2. `Noise Texture`
  3. `Math (Add to IOR per loop for R/G/B channels separate)`
  4. `Combine Color`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Glass styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 15. Snow Coverage
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Snow on top of geometry
- **Node Tree:**
  1. `Texture Coordinate (Normal Z)`
  2. `Math (Greater Than)`
  3. `Mix Shader (Snow SSS vs Ground Material)`
  4. `Displacement (Upwards masked by Z)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 16. Velvet Sheen
- **Category:** Fabric
- **Difficulty:** Intermediate
- **Goal:** Soft fabric sheen
- **Node Tree:**
  1. `Principled BSDF (Sheen Weight: 1.0)`
  2. `Wave Texture (High Scale)`
  3. `Bump (Weave Pattern)`
  4. `ColorRamp (Falloff)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Fabric styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 17. Molten Magma
- **Category:** FX
- **Difficulty:** Intermediate
- **Goal:** Glowing lava cracks
- **Node Tree:**
  1. `Noise Texture (Distorted)`
  2. `Map Range`
  3. `ColorRamp (Black/Red/Yellow/White)`
  4. `Emission Strength (High)`
  5. `Displacement`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* FX styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 18. Rain Ripples
- **Category:** FX
- **Difficulty:** Intermediate
- **Goal:** Animated water ripples
- **Node Tree:**
  1. `Voronoi Texture (Classic, 4D animated)`
  2. `ColorRamp (Constant rings)`
  3. `Bump Node`
  4. `Normal`
  5. `Mix Shader (Water)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* FX styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 19. Volumetric Clouds
- **Category:** FX
- **Difficulty:** Intermediate
- **Goal:** Fluffy clouds
- **Node Tree:**
  1. `Principled Volume`
  2. `Density connected to: Noise Texture`
  3. `Math (Multiply)`
  4. `Gradient Texture (Fade height)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* FX styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 20. Cobwebs
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Spidery web patterns
- **Node Tree:**
  1. `Voronoi Texture (Distance to Edge)`
  2. `Math (Less Than small value)`
  3. `Mix Shader (Transparent vs Diffuse White)`
  4. `Geometry (Alpha)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 21. Brushed Metal
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Anisotropic metal finish
- **Node Tree:**
  1. `Noise Texture (Scale Y >> X)`
  2. `Bump Node`
  3. `Principled BSDF (Anisotropic: 0.8, Metallic: 1.0)`
  4. `Normal`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 22. Carbon Fiber
- **Category:** Tech
- **Difficulty:** Intermediate
- **Goal:** Woven carbon pattern
- **Node Tree:**
  1. `Voronoi Texture (Chebyshev, 45deg rotation)`
  2. `ColorRamp (Black/Grey bands)`
  3. `Bump Node`
  4. `Principled BSDF (Metallic 0, Roughness 0.4)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Tech styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 23. Ceramic Tiles
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Smooth tiles with grout
- **Node Tree:**
  1. `Voronoi Texture (Manhattan)`
  2. `ColorRamp (Constant)`
  3. `Bump (Invert for Grout)`
  4. `Principled BSDF (Roughness Low)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 24. Leather
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Organic leather grain
- **Node Tree:**
  1. `Voronoi Texture (Smooth F1)`
  2. `Math (Multiply with Noise)`
  3. `Bump Node (Low Strength)`
  4. `Principled BSDF (Roughness 0.6)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 25. Skin (SSS)
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Fake subsurface scattering skin
- **Node Tree:**
  1. `Texture Coordinate (Object)`
  2. `Noise Texture (Cloudy)`
  3. `Mix Color (Skin Tones)`
  4. `Principled BSDF (Subsurface Weight 1.0, Radius Red)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 26. Soap Bubbles
- **Category:** FX
- **Difficulty:** Intermediate
- **Goal:** Thin film interference
- **Node Tree:**
  1. `Layer Weight (Facing)`
  2. `ColorRamp (Rainbow Spectrum)`
  3. `Principled BSDF (Base Color / Emission)`
  4. `Mix Shader (Transparent)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* FX styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 27. Solar Panels
- **Category:** Tech
- **Difficulty:** Intermediate
- **Goal:** Photovoltaic grid
- **Node Tree:**
  1. `Brick Texture (Frequency 2, Offset 0.5)`
  2. `ColorRamp (Dark Blue/Black)`
  3. `Roughness (High on grid lines)`
  4. `Principled BSDF`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Tech styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 28. Chainmail
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Interlocking rings (Alpha)
- **Node Tree:**
  1. `Voronoi Texture (Euclidean)`
  2. `Math (Distance check for rings)`
  3. `Mix Shader (Transparent vs Glossy Metal)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 29. Wicker Weave
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Basket weaving pattern
- **Node Tree:**
  1. `Wave Texture (Bands, 45deg)`
  2. `Math (Ping Pong)`
  3. `Bump Node`
  4. `Principled BSDF (Wood Color)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 30. Car Paint
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Metallic flake paint
- **Node Tree:**
  1. `Layer Weight (Fresnel)`
  2. `Mix Color (Base vs Flakes)`
  3. `Voronoi (Flakes Normal)`
  4. `Principled BSDF (Clearcoat 1.0)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 31. Cooling Lava Rock
- **Category:** FX
- **Difficulty:** Intermediate
- **Goal:** Black rock with glowing cracks
- **Node Tree:**
  1. `Voronoi Texture (Crackle)`
  2. `ColorRamp (Invert)`
  3. `Emission (Red/Orange)`
  4. `Mix Shader (Diffuse Rock vs Emission)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* FX styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 32. Cracked Ice
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Deep ice fractures
- **Node Tree:**
  1. `Voronoi Texture (Distance to Edge)`
  2. `ColorRamp (Sharp transition)`
  3. `Transmission Roughness`
  4. `Bump Node`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 33. Muddy Ground
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Wet mud surface
- **Node Tree:**
  1. `Noise Texture (Low Detail)`
  2. `ColorRamp (Browns)`
  3. `Map Range (To Roughness)`
  4. `Bump Node`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 34. Puddle Mapping
- **Category:** Grunge
- **Difficulty:** Intermediate
- **Goal:** Puddles on uneven surface
- **Node Tree:**
  1. `Noise Texture`
  2. `ColorRamp (Threshold)`
  3. `Mix Shader (Roughness 0, IOR 1.33 vs Ground Roughness)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Grunge styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 35. Sand Dunes
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Wavy sand patterns
- **Node Tree:**
  1. `Wave Texture (Distorted with Noise)`
  2. `Bump Node`
  3. `Displacement`
  4. `Principled BSDF (Sand Color)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 36. Starfield
- **Category:** Space
- **Difficulty:** Intermediate
- **Goal:** Space background
- **Node Tree:**
  1. `Voronoi Texture (F1)`
  2. `Math (Greater Than 0.99)`
  3. `Emission (White)`
  4. `Add Shader (Black Background)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Space styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 37. Neon Sign
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Glowing tube light
- **Node Tree:**
  1. `Geometry (Backfacing)`
  2. `Mix Shader (Emission vs Glass)`
  3. `Volume Scatter (Glow Bloom)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 38. CRT Screen
- **Category:** Tech
- **Difficulty:** Intermediate
- **Goal:** Pixel grid phosphor effect
- **Node Tree:**
  1. `Wave Texture (Bands) * Brick Texture (Cells)`
  2. `Math (Multiply)`
  3. `Emission Color (Image Texture input)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Tech styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 39. Glitch Effect
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Digital noise distortion
- **Node Tree:**
  1. `Noise Texture (4D, W=Time)`
  2. `Mapping Vector (Distort X)`
  3. `Image Texture Vector`
  4. `Emission`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 40. Wireframe Overlay
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Glowing edges
- **Node Tree:**
  1. `Wireframe Node`
  2. `Mix Shader (Emission Color vs Transparent)`
  3. `Add Shader (Base Material)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 41. Toon Shader
- **Category:** Style
- **Difficulty:** Intermediate
- **Goal:** Cel shaded look
- **Node Tree:**
  1. `Diffuse BSDF`
  2. `Shader to RGB`
  3. `ColorRamp (Constant Steps)`
  4. `Emission (To keep colors flat)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Style styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 42. X-Ray
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** See-through rim effect
- **Node Tree:**
  1. `Layer Weight (Fresnel)`
  2. `Math (Power)`
  3. `Emission (Cyan)`
  4. `Add Shader (Transparent)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 43. Ghost / Spirit
- **Category:** FX
- **Difficulty:** Intermediate
- **Goal:** Ethereal transparency
- **Node Tree:**
  1. `Layer Weight (Facing)`
  2. `ColorRamp (Alpha gradient)`
  3. `Emission (Blue)`
  4. `Mix Shader (Transparent)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* FX styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 44. Hex Force Field
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Hexagon shield pattern
- **Node Tree:**
  1. `Voronoi Texture (Manhattan, smooth)`
  2. `Math (Less Than)`
  3. `Emission (Color)`
  4. `Mix Shader (Transparent)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 45. Scanline Hologram
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Horizontal scanlines
- **Node Tree:**
  1. `Wave Texture (Bands Z)`
  2. `Math (Multiply)`
  3. `Emission (Holo Color)`
  4. `Mix Shader (Transparent)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 46. Gradient Heat Map
- **Category:** Data
- **Difficulty:** Intermediate
- **Goal:** Temperature visualization
- **Node Tree:**
  1. `Texture Coordinate (Generated Z)`
  2. `ColorRamp (Inferno/Magma)`
  3. `Emission`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Data styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 47. Edge Wear
- **Category:** Grunge
- **Difficulty:** Intermediate
- **Goal:** Metal edges on paint
- **Node Tree:**
  1. `Geometry Node (Pointiness or Bevel)`
  2. `ColorRamp (Contrast)`
  3. `Mix Shader (Painted Base vs Shiny Metal)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Grunge styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 48. Dirt in Crevices
- **Category:** Grunge
- **Difficulty:** Intermediate
- **Goal:** Ambient Occlusion dirt
- **Node Tree:**
  1. `Ambient Occlusion Node`
  2. `ColorRamp (High Contrast)`
  3. `Mix Color (Multiply Dark Brown)`
  4. `Base Color`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Grunge styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 49. Dust Layer
- **Category:** Grunge
- **Difficulty:** Intermediate
- **Goal:** Top-down dust
- **Node Tree:**
  1. `Geometry (Normal)`
  2. `Separate XYZ (Z)`
  3. `Math (Dot Product)`
  4. `Mix Shader (Dust Matt vs Base Material)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Grunge styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 50. Parallax Occlusion
- **Category:** Tech
- **Difficulty:** Intermediate
- **Goal:** Fake depth on flat plane
- **Node Tree:**
  1. `UV Map`
  2. `Vector Math (Subtract View Vector * Height Map)`
  3. `Texture Vector Input`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Tech styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 51. Cast Iron
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Rough, dark iron
- **Node Tree:**
  1. `Noise Texture (High Scale)`
  2. `Bump Node (Low Strength)`
  3. `Principled BSDF (Metallic 1, Roughness 0.7, Color Black/Grey)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 52. Galvanized Steel
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Spangled zinc finish
- **Node Tree:**
  1. `Voronoi Texture (Cells)`
  2. `ColorRamp (Grey variations)`
  3. `Principled BSDF (Metallic 1, Roughness 0.3)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 53. Anodized Aluminum
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Colored metal with sheen
- **Node Tree:**
  1. `Principled BSDF (Metallic 1, Roughness 0.4, Color: Deep Blue/Red)`
  2. `Layer Weight (Facing)`
  3. `Mix Color (Lighter Edge)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 54. Hammered Copper
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Dented metal surface
- **Node Tree:**
  1. `Voronoi Texture (Smooth F1)`
  2. `Bump Node (Invert)`
  3. `Principled BSDF (Metallic 1, Color Copper)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 55. Gold Foil
- **Category:** Metal
- **Difficulty:** Intermediate
- **Goal:** Crinkled gold logic
- **Node Tree:**
  1. `Noise Texture (Detail 16)`
  2. `Bump Node (High Strength)`
  3. `Principled BSDF (Metallic 1, Color Gold)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Metal styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 56. Polished Marble
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Veined stone surface
- **Node Tree:**
  1. `Wave Texture (Distorted)`
  2. `Mix Color (White/Grey)`
  3. `Principled BSDF (Roughness 0.05, Subsurface Weight 0.1)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 57. Rough Granite
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Speckled stone
- **Node Tree:**
  1. `Noise Texture (High Scale)`
  2. `ColorRamp (Black/White/Grey specks)`
  3. `Bump Node`
  4. `Principled BSDF`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 58. Asphalt/Tarmac
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Road surface
- **Node Tree:**
  1. `Noise Texture (High Scale)`
  2. `Bump Node`
  3. `Principled BSDF (Color Dark Grey, Roughness 0.9)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 59. Concrete (Pitted)
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Industrial wall
- **Node Tree:**
  1. `Voronoi (Distance to Edge)`
  2. `ColorRamp (Invert small dots)`
  3. `Bump Node (Invert)`
  4. `Principled BSDF (Grey)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 60. Plaster Wall
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Uneven wall finish
- **Node Tree:**
  1. `Noise Texture`
  2. `Bump Node (Very low strength)`
  3. `Principled BSDF (Roughness 1.0)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 61. Stucco
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Rough exterior wall
- **Node Tree:**
  1. `Noise Texture`
  2. `Displacement (Mid level)`
  3. `Principled BSDF (White, Rough loops)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 62. Herringbone Floor
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Wood pattern
- **Node Tree:**
  1. `Brick Texture (Frequency 2, Width/Height ratio)`
  2. `Rotate 45deg`
  3. `Principled BSDF (Wood Color)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 63. Subway Tiles
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Glossy white tiles
- **Node Tree:**
  1. `Brick Texture (Offset 0.5)`
  2. `Principled BSDF (Roughness 0.1, Color White)`
  3. `Bump (Mortar invert)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 64. Roof Shingles
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Overlapping tiles
- **Node Tree:**
  1. `Brick Texture`
  2. `Vector Math (Staircase Mapping)`
  3. `Gradient Texture (Linear)`
  4. `Displacement`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 65. Grid Floor (Sci-Fi)
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Glowing floor grid
- **Node Tree:**
  1. `Brick Texture`
  2. `Math (Greater Than)`
  3. `Mix Shader (Glossy Black vs Emission Blue)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 66. Rubber Floor
- **Category:** Arch
- **Difficulty:** Intermediate
- **Goal:** Dot pattern flooring
- **Node Tree:**
  1. `Voronoi Texture (Dots)`
  2. `ColorRamp (Circle mask)`
  3. `Bump Node (Height)`
  4. `Principled BSDF (Black Rubber)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Arch styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 67. Denim Fabric
- **Category:** Fabric
- **Difficulty:** Intermediate
- **Goal:** Blue jeans weave
- **Node Tree:**
  1. `Wave Texture (Diagonal)`
  2. `Noise Texture (Overlay)`
  3. `Principled BSDF (Blue, Sheen Weight 0.5)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Fabric styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 68. Silk
- **Category:** Fabric
- **Difficulty:** Intermediate
- **Goal:** Shinier fabric
- **Node Tree:**
  1. `Principled BSDF (Roughness 0.3, Anisotropic 0.5, Sheen Weight 1.0, Color Purple)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Fabric styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 69. Wool Knit
- **Category:** Fabric
- **Difficulty:** Intermediate
- **Goal:** Cozy sweater
- **Node Tree:**
  1. `Wave Texture (Zig Zag)`
  2. `Displacement`
  3. `Principled BSDF (Sheen Weight 1.0)`
  4. `Hair Particle (Fuzz)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Fabric styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 70. Nylon/Synthetic
- **Category:** Fabric
- **Difficulty:** Intermediate
- **Goal:** Sportswear
- **Node Tree:**
  1. `Brick Texture (Tiny scale for weave)`
  2. `Principled BSDF (Roughness 0.4, Sheen Tint)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Fabric styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 71. Linen
- **Category:** Fabric
- **Difficulty:** Intermediate
- **Goal:** Natural rough cloth
- **Node Tree:**
  1. `Wave Texture (Crosshatch)`
  2. `Bump Node`
  3. `Principled BSDF (Roughness 0.8)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Fabric styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 72. Tattered Cloth
- **Category:** Fabric
- **Difficulty:** Intermediate
- **Goal:** Alpha transparency holes
- **Node Tree:**
  1. `Noise Texture`
  2. `ColorRamp (Hard Step)`
  3. `Mix Shader (Transparent vs Fabric)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Fabric styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 73. Sequin
- **Category:** Fabric
- **Difficulty:** Intermediate
- **Goal:** Glittering discs
- **Node Tree:**
  1. `Voronoi Texture (Cells)`
  2. `Normal Map (Random tilts)`
  3. `Principled BSDF (Metallic 1)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Fabric styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 74. Cardboard
- **Category:** Paper
- **Difficulty:** Intermediate
- **Goal:** Corrugated internal
- **Node Tree:**
  1. `Wave Texture (Sine)`
  2. `Bump Node`
  3. `Principled BSDF (Brown Paper)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Paper styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 75. Paper (Crumpled)
- **Category:** Paper
- **Difficulty:** Intermediate
- **Goal:** Wrinkled sheet
- **Node Tree:**
  1. `Voronoi Texture`
  2. `Bump Node`
  3. `Principled BSDF (Roughness 1.0, Transmission 0.2)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Paper styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 76. Styrofoam
- **Category:** Synthetic
- **Difficulty:** Intermediate
- **Goal:** White packaging
- **Node Tree:**
  1. `Voronoi Texture (Cells)`
  2. `Bump Node (Outwards)`
  3. `Principled BSDF (Subsurface Weight 0.5)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Synthetic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 77. Dragon Scales
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Reptilian armor
- **Node Tree:**
  1. `Voronoi Texture`
  2. `Mapping (Scale Y)`
  3. `Bump Node`
  4. `Principled BSDF (Metallic 0.5)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 78. Alien Skin
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Slimy texture
- **Node Tree:**
  1. `Voronoi Texture`
  2. `ColorRamp (Green/Purple)`
  3. `Principled BSDF (Subsurface Weight 1.0, Roughness 0.1)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 79. Eyeball (Iris)
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Radial muscle fibers
- **Node Tree:**
  1. `Gradient Texture (Radial)`
  2. `Noise Texture (Distortion)`
  3. `ColorRamp (Eye Colors)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 80. Blood Splatter
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Liquid decals
- **Node Tree:**
  1. `Noise Texture (Distorted)`
  2. `ColorRamp (Red/Transparent)`
  3. `Principled BSDF (Roughness 0.0, Transmission 0.2)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 81. Orange Peel
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Citrus pore texture
- **Node Tree:**
  1. `Noise Texture (Tiny scale)`
  2. `Bump Node (Invert)`
  3. `Principled BSDF (Orange, Subsurface Weight 0.2)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 82. Honeycomb
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Beeswax structure
- **Node Tree:**
  1. `Voronoi Texture (F1, Distance)`
  2. `Math (Modulo)`
  3. `Principled BSDF (Yellow, Subsurface, Transmission)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 83. Sponge
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Porous material
- **Node Tree:**
  1. `Voronoi Texture (Distance to Edge)`
  2. `Volume Scatter (Destiny)`
  3. `Displacement (Invert)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 84. Meat (Raw)
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Muscle and Fat
- **Node Tree:**
  1. `Wave Texture (Distorted)`
  2. `ColorRamp (Red/White)`
  3. `Principled BSDF (Subsurface Weight 0.8)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 85. Bone
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Porous white calc
- **Node Tree:**
  1. `Noise Texture (Detail)`
  2. `Bump Node`
  3. `Principled BSDF (Off-White, Subsurface Weight 0.1)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 86. Feather (Alpha)
- **Category:** Organic
- **Difficulty:** Intermediate
- **Goal:** Barbs struct
- **Node Tree:**
  1. `Gradient Texture (Linear)`
  2. `Wave Texture (Fine lines)`
  3. `Mix Shader (Alpha)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Organic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 87. Plasma Shield
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Energy barrier
- **Node Tree:**
  1. `Layer Weight (Fresnel)`
  2. `Before Math (Sine)`
  3. `Emission (Purple)`
  4. `Mix Shader (Transparent)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 88. Warp Speed
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Streaking stars
- **Node Tree:**
  1. `Voronoi Texture (Stars)`
  2. `Mapping (Scale Z Stretch)`
  3. `Emission (White/Blue)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 89. Digital Rain
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Matrix code style
- **Node Tree:**
  1. `Principled BSDF`
  2. `Image Sequence (Characters)`
  3. `Mapping (Scroll Y)`
  4. `Emission (Green)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 90. Nanobots
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Swarming black particles
- **Node Tree:**
  1. `Voronoi Texture (Cells)`
  2. `Bump Node`
  3. `Principled BSDF (Metallic, Anisotropic)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 91. Invisibility Cloak
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Refractive distortion
- **Node Tree:**
  1. `Refraction BSDF`
  2. `Noise Texture`
  3. `Normal Map (Distort Background)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 92. Laser Beam
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Solid light core
- **Node Tree:**
  1. `Gradient Texture (Quadratic Sphere)`
  2. `ColorRamp (White Core`
  3. `Red Edge)`
  4. `Emission Strength 100`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 93. Force Field (Hit)
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Impact ripple
- **Node Tree:**
  1. `Gradient Texture (Spherical)`
  2. `Wave Texture (Ripple)`
  3. `Mix Shader (Add to shield)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 94. Holo-Map
- **Category:** Sci-Fi
- **Difficulty:** Intermediate
- **Goal:** Topo lines
- **Node Tree:**
  1. `Texture Coordinate (Z)`
  2. `Math (Modulo)`
  3. `Emission (Blue)`
  4. `Mix Shader (Transparent)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Sci-Fi styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 95. Circuit Board
- **Category:** Tech
- **Difficulty:** Intermediate
- **Goal:** PCB traces
- **Node Tree:**
  1. `Voronoi (Manhattan)`
  2. `ColorRamp (Green/Copper)`
  3. `Bump Node`
  4. `Principled BSDF`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Tech styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 96. LED Array
- **Category:** Tech
- **Difficulty:** Intermediate
- **Goal:** Dot matrix screen
- **Node Tree:**
  1. `Brick Texture (Dots)`
  2. `Emission (RGB input)`
  3. `Principled BSDF (Black Plastic background)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Tech styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 97. Milk
- **Category:** Liquid
- **Difficulty:** Intermediate
- **Goal:** SSS liquid
- **Node Tree:**
  1. `Principled BSDF (Base Color White)`
  2. `Subsurface Weight 1.0`
  3. `Subsurface Radius (Red/Green/Blue equal)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Liquid styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 98. Honey
- **Category:** Liquid
- **Difficulty:** Intermediate
- **Goal:** Viscous amber
- **Node Tree:**
  1. `Principled BSDF (Transmission 1.0)`
  2. `IOR 1.5`
  3. `Color (Amber)`
  4. `Volume Absorption (Yellow)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Liquid styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 99. Oil Slick
- **Category:** Liquid
- **Difficulty:** Intermediate
- **Goal:** Rainbow surface
- **Node Tree:**
  1. `Layer Weight (Fresnel)`
  2. `ColorRamp (Spectrum)`
  3. `Principled BSDF (Metallic 0.5, Roughness 0.1)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Liquid styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 100. Coffee
- **Category:** Liquid
- **Difficulty:** Intermediate
- **Goal:** Dark opaque liquid
- **Node Tree:**
  1. `Principled BSDF (Transmission 0.8)`
  2. `Volume Absorption (Dark Brown, High Density)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Liquid styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 101. Wine (Red)
- **Category:** Liquid
- **Difficulty:** Intermediate
- **Goal:** Deep red transparent
- **Node Tree:**
  1. `Principled BSDF (Transmission 1.0)`
  2. `IOR 1.34`
  3. `Volume Absorption (Red)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Liquid styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 102. Slime
- **Category:** Liquid
- **Difficulty:** Intermediate
- **Goal:** Green goo
- **Node Tree:**
  1. `Principled BSDF (Transmission 0.8, Roughness 0.1)`
  2. `Volume Scatter (Green)`
  3. `Noise (Bump)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Liquid styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 103. Ocean Foam
- **Category:** Liquid
- **Difficulty:** Intermediate
- **Goal:** White caps
- **Node Tree:**
  1. `Ocean Modifier (Foam Data)`
  2. `Attribute Node (Foam)`
  3. `Mix Color (Water Color vs White)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Liquid styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 104. Caustics (Fake)
- **Category:** Light
- **Difficulty:** Intermediate
- **Goal:** Underwater light pattern
- **Node Tree:**
  1. `Voronoi Texture (Smooth F1)`
  2. `Math (Power)`
  3. `Emission (Light Blue)`
  4. `Mix Shader (Add)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Light styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 105. Displacement Map
- **Category:** Geo
- **Difficulty:** Intermediate
- **Goal:** Height map logic
- **Node Tree:**
  1. `Image Texture (Non-Color)`
  2. `Displacement Node`
  3. `Material Output (Displacement)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Geo styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 106. Pointiness Wear
- **Category:** Geometry
- **Difficulty:** Intermediate
- **Goal:** Edge detection
- **Node Tree:**
  1. `Geometry Node (Pointiness)`
  2. `ColorRamp`
  3. `Mix (Edge Wear)`
  4. `Base Color`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Geometry styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 107. Ambient Occlusion
- **Category:** Geometry
- **Difficulty:** Intermediate
- **Goal:** Corner darkening
- **Node Tree:**
  1. `Ambient Occlusion Node`
  2. `ColorRamp (Black/White)`
  3. `Mix Color (Multiply)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Geometry styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 108. Object Info Random
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Variation per object
- **Node Tree:**
  1. `Object Info (Random)`
  2. `ColorRamp (Gradient)`
  3. `Base Color`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 109. Particle Info
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Age based color
- **Node Tree:**
  1. `Particle Info (Age / Lifetime)`
  2. `ColorRamp`
  3. `Emission`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 110. Camera Ray
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Only visible to camera
- **Node Tree:**
  1. `Light Path (Is Camera Ray)`
  2. `Mix Shader (Transparent vs Material)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 111. Backface Culling
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Hide backfaces
- **Node Tree:**
  1. `Geometry (Backfacing)`
  2. `Mix Shader (Transparent vs Material)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 112. Fresnel Glow
- **Category:** FX
- **Difficulty:** Intermediate
- **Goal:** Rim lighting
- **Node Tree:**
  1. `Layer Weight (Fresnel)`
  2. `ColorRamp`
  3. `Emission`
  4. `Add Shader`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* FX styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 113. Top Mask
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Snow/Dust mask
- **Node Tree:**
  1. `Geometry (Normal)`
  2. `Separate XYZ (Z)`
  3. `Math (Greater Than)`
  4. `Mix Factor`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 114. Slope Mask
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Cliff rock logic
- **Node Tree:**
  1. `Normal Vector`
  2. `Dot Product (Z Axis)`
  3. `ColorRamp`
  4. `Mix Shader (Grass vs Rock)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 115. Proximity Light
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Glow near object
- **Node Tree:**
  1. `Geometry (Position)`
  2. `Vector Math (Distance to Object)`
  3. `Math (Less Than)`
  4. `Emission`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 116. Radial Gradient
- **Category:** Pattern
- **Difficulty:** Intermediate
- **Goal:** Circular sweep
- **Node Tree:**
  1. `Gradient Texture (Radial)`
  2. `Map Range`
  3. `ColorRamp`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Pattern styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 117. Checkerboard
- **Category:** Pattern
- **Difficulty:** Intermediate
- **Goal:** Tiling check
- **Node Tree:**
  1. `Checker Texture`
  2. `Mapping (Scale)`
  3. `Principled BSDF`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Pattern styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 118. Polka Dots
- **Category:** Pattern
- **Difficulty:** Intermediate
- **Goal:** Grid of circles
- **Node Tree:**
  1. `Voronoi Texture (Smooth F1)`
  2. `Math (Less Than radius)`
  3. `Mix Color`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Pattern styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 119. Stripes
- **Category:** Pattern
- **Difficulty:** Intermediate
- **Goal:** Banding
- **Node Tree:**
  1. `Wave Texture (Bands)`
  2. `ColorRamp (Constant)`
  3. `Principled BSDF`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Pattern styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 120. ZigZag
- **Category:** Pattern
- **Difficulty:** Intermediate
- **Goal:** Sawtooth pattern
- **Node Tree:**
  1. `Wave Texture (Triangle)`
  2. `Vector Math (Add X+Y)`
  3. `ColorRamp`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Pattern styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 121. Spiral
- **Category:** Pattern
- **Difficulty:** Intermediate
- **Goal:** Archimedean spiral
- **Node Tree:**
  1. `Gradient Texture (Radial)`
  2. `Math (Add Z Rotation)`
  3. `Math (Sine)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Pattern styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 122. Tartan/Plaid
- **Category:** Pattern
- **Difficulty:** Intermediate
- **Goal:** Scottish cloth
- **Node Tree:**
  1. `Wave Texture (Bands X) + Wave Texture (Bands Y)`
  2. `Mix Color (Overlay)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Pattern styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 123. Camouflage
- **Category:** Pattern
- **Difficulty:** Intermediate
- **Goal:** Army camo
- **Node Tree:**
  1. `Noise Texture`
  2. `Voronoi Texture (Distorted)`
  3. `ColorRamp (Green/Brown/Black)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Pattern styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 124. Halftone
- **Category:** Style
- **Difficulty:** Intermediate
- **Goal:** Comic book dots
- **Node Tree:**
  1. `Texture Coordinate (Window)`
  2. `Voronoi Texture`
  3. `Math (Compare Brightness)`
  4. `Mix Color (Black/White)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Style styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 125. Pixelate
- **Category:** Style
- **Difficulty:** Intermediate
- **Goal:** Low res look
- **Node Tree:**
  1. `Texture Coordinate`
  2. `Vector Math (Snap)`
  3. `Image Texture`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Style styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 126. Normal Map Mixing
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Combine normals
- **Node Tree:**
  1. `Bump Node 1`
  2. `Bump Node 2 (Normal Input)`
  3. `Principled BSDF`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 127. Alpha Clip
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Leaf cutout
- **Node Tree:**
  1. `Image Texture (Alpha)`
  2. `Principled BSDF (Alpha)`
  3. `Material Settings (Blend Mode: Alpha Clip)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 128. Shadow Catcher
- **Category:** Render
- **Difficulty:** Intermediate
- **Goal:** Composite shadow only
- **Node Tree:**
  1. `Principled BSDF`
  2. `Object Settings (Visibility: Shadow Catcher)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Render styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 129. Vertex Color
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Paint mask
- **Node Tree:**
  1. `Attribute Node (Col)`
  2. `Mix Shader (Factor)`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes


---
### 130. UV Warp
- **Category:** Logic
- **Difficulty:** Intermediate
- **Goal:** Flowing water UVs
- **Node Tree:**
  1. `UV Map`
  2. `Vector Math (Add Noise * Time)`
  3. `Image Texture`
- **Key Parameters:**
  - `Scale`: Controls texture frequency
  - `Detail`: Adjusts fractal depth
  - `Color`: Base material tint
- **Semantic Context:**
  - *Typical Use:* Logic styling
  - *Material Pairings:* Standard Principled BSDF
- **Performance Notes:**
  - *Impact:* Low to Medium
  - *Real-time:* Yes

