# PBR Materials & HDRI Lighting Implementation

## Overview
This document describes the Physically Based Rendering (PBR) materials system implemented for the 3D visualization feature. The system automatically applies realistic materials to IFC building elements based on their type.

## Features Implemented

### 1. **HDRI Environment Setup**
- **Image-Based Lighting (IBL)**: Uses prefiltered HDR environment map for realistic reflections and ambient lighting
- **Environment Texture**: `environment.env` from Babylon.js playground (free, high-quality)
- **Skybox**: Optional reflective skybox with 30% blur for subtle environment reflections
- **Environment Intensity**: 1.0 (adjustable for different lighting scenarios)

**Code Location**: Lines ~455-465 in `app/templates/defects/visualization.html`

```javascript
const hdrTexture = BABYLON.CubeTexture.CreateFromPrefilteredData(
    "https://playground.babylonjs.com/textures/environment.env", 
    scene
);
scene.environmentTexture = hdrTexture;
scene.environmentIntensity = 1.0;
const skybox = scene.createDefaultSkybox(hdrTexture, true, 1000, 0.3);
```

### 2. **PBR Material Recipes**
Each architectural element type has a predefined PBR recipe with:
- **baseColor**: RGB color values
- **metallic**: 0.0 (non-metallic) to 1.0 (pure metal)
- **roughness**: 0.0 (mirror-smooth) to 1.0 (completely rough/matte)
- **alpha**: Optional transparency (for glass)
- **textureNames**: Placeholder for future texture loading

**Supported Element Types**:

| Element Type | Metallic | Roughness | Description |
|--------------|----------|-----------|-------------|
| Wall (plaster) | 0.0 | 0.95 | Matte painted surface |
| Floor (dark wood) | 0.0 | 0.7 | Semi-matte wood finish |
| Ceiling (paint) | 0.0 | 0.9 | Flat white paint |
| Door (painted wood) | 0.0 | 0.4 | Satin finish |
| Window (glass) | 0.9 | 0.05 | Transparent reflective glass |
| Sink (steel) | 1.0 | 0.2 | Polished metal |
| Table (matte wood) | 0.0 | 0.65 | Natural wood finish |
| Furniture (generic) | 0.0 | 0.6 | Standard wood |
| Roof (tiles) | 0.0 | 0.8 | Rough ceramic/tile |
| Default | 0.0 | 0.75 | Generic surface |

**Code Location**: Lines ~468-545 in `app/templates/defects/visualization.html`

### 3. **Automated Material Assignment**
The `applyPBRMaterials(scene)` function:
- Iterates through all scene meshes
- Detects element type from mesh name (e.g., "IfcWall", "IfcSlab", "door", "vindu")
- Applies appropriate PBR recipe
- Handles transparency (glass windows)
- Enables environment reflections
- Preserves X-ray mode compatibility

**Name Matching Logic**:
- Supports IFC naming: `IfcWall`, `IfcSlab`, `IfcFurnishingElement`
- Supports Norwegian terms: `vegg` (wall), `gulv` (floor), `tak` (ceiling/roof), `dør` (door), `vindu` (window)
- Case-insensitive matching
- Falls back to "default" recipe if no match

**Code Location**: Lines ~548-640 in `app/templates/defects/visualization.html`

### 4. **Optimized Lighting for PBR**
Traditional lighting intensities reduced to complement IBL:
- **HemisphericLight**: 0.3 intensity (down from 0.6) - base ambient
- **DirectionalLight (key)**: 0.5 intensity (down from 0.8) - main sun
- **DirectionalLight (fill)**: 0.2 intensity (down from 0.4) - subtle fill

**Rationale**: PBR materials rely heavily on environment lighting from the HDRI. Excessive direct lighting can wash out the realistic PBR appearance.

**Code Location**: Lines ~678-691 in `app/templates/defects/visualization.html`

## Technical Details

### PBRMetallicRoughnessMaterial Properties
Each material instance includes:
```javascript
pbrMaterial.baseColor = recipe.baseColor;           // Base color (albedo)
pbrMaterial.metallic = recipe.metallic;             // Metalness (0-1)
pbrMaterial.roughness = recipe.roughness;           // Surface roughness (0-1)
pbrMaterial.alpha = recipe.alpha;                   // Transparency (optional)
pbrMaterial.useRadianceOverAlpha = true;           // Better transparency
pbrMaterial.useSpecularOverAlpha = true;           // Reflections on transparent
pbrMaterial.backFaceCulling = true;                // Performance optimization
pbrMaterial.twoSidedLighting = false;              // Proper 3D normals
pbrMaterial.originalAlpha = pbrMaterial.alpha;     // X-ray mode support
```

### Future Texture Support
The system includes placeholders for texture loading:
```javascript
textureNames: {
    albedo: 'plaster_albedo.jpg',      // Base color map
    normal: 'plaster_normal.jpg',      // Surface detail
    roughness: 'plaster_roughness.jpg', // Roughness variation
}
```

---

## Quick Testing

1. **Start the app**: `docker-compose up` or `python run.py`
2. **Open visualization**: Navigate to any project and click to visualize
3. **Check console**: Look for "✓ Applied X PBR materials"
4. **Visual test**:
   - Windows should be transparent with reflections
   - Sinks/metal should show clear environment reflections
   - Walls should be matte (no shiny spots)
   - Wood floors should have subtle sheen

## Customization

### Change Environment Intensity
```javascript
// Line ~462 in visualization.html
scene.environmentIntensity = 1.5; // Increase for brighter reflections
```

### Use Custom HDRI
1. Convert your `.hdr` to `.env`: https://sandbox.babylonjs.com/
2. Place in `/static/textures/custom.env`
3. Update line ~459:
```javascript
const hdrTexture = BABYLON.CubeTexture.CreateFromPrefilteredData(
    "/static/textures/custom.env", 
    scene
);
```

### Adjust Material Properties
Edit `PBR_RECIPES` object (line ~468):
```javascript
'wall': {
    baseColor: new BABYLON.Color3(0.9, 0.9, 0.85), // RGB color
    metallic: 0.0,   // 0 = non-metal, 1 = pure metal
    roughness: 0.95  // 0 = mirror, 1 = completely matte
}
```

## Troubleshooting

- **Too dark?** → Increase `scene.environmentIntensity` to 1.5-2.0  
- **No reflections?** → Check `metallic` values (must be > 0.0 for reflections)  
- **Windows not transparent?** → Verify `alpha: 0.4` in window recipe  
- **Performance issues?** → Reduce environment intensity or disable skybox

## X-Ray Mode Compatibility
✓ PBR materials fully support X-ray mode (stored `originalAlpha` preserved)

## References
- Material theory: https://learnopengl.com/PBR/Theory
- Babylon.js PBR docs: https://doc.babylonjs.com/features/featuresDeepDive/materials/using/introToPBR
- Free HDRIs: https://polyhaven.com/hdris
