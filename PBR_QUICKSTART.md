# PBR Materials Implementation - Quick Reference

## What Was Implemented

### 1. HDRI Environment Lighting
- **Location**: `app/templates/defects/visualization.html` lines ~455-465
- **HDRI Source**: Babylon.js playground environment.env (free, CC0)
- **Features**: 
  - Image-Based Lighting (IBL) for realistic ambient lighting
  - Environment reflections on metallic surfaces
  - Optional skybox with 30% blur

### 2. PBR Material System
- **Location**: `app/templates/defects/visualization.html` lines ~468-640
- **10 Material Recipes**: Wall, Floor, Ceiling, Door, Window, Sink, Table, Furniture, Roof, Default
- **Properties**: baseColor, metallic (0-1), roughness (0-1), alpha (transparency)
- **Auto-Assignment**: Function detects IFC element types and applies appropriate materials

### 3. Optimized Lighting
- **Location**: `app/templates/defects/visualization.html` lines ~678-691
- **Changes**: Reduced light intensities to complement IBL (0.6→0.3, 0.8→0.5, 0.4→0.2)

## Key Material Properties

| Element | Metallic | Roughness | Visual Result |
|---------|----------|-----------|---------------|
| Walls (plaster) | 0.0 | 0.95 | Matte, no reflections |
| Floors (wood) | 0.0 | 0.7 | Semi-matte wood |
| Windows (glass) | 0.9 | 0.05 | Clear, reflective, 40% transparent |
| Sink (steel) | 1.0 | 0.2 | Mirror-like metal reflections |
| Tables (wood) | 0.0 | 0.65 | Natural matte wood |

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

**Too dark?** → Increase `scene.environmentIntensity` to 1.5-2.0  
**No reflections?** → Check `metallic` values (must be > 0.0 for reflections)  
**Windows not transparent?** → Verify `alpha: 0.4` in window recipe  
**Performance issues?** → Reduce environment intensity or disable skybox

## Documentation
- Full technical details: `/usr/src/app/PBR_IMPLEMENTATION.md`
- Material theory: https://learnopengl.com/PBR/Theory
- Babylon.js PBR docs: https://doc.babylonjs.com/features/featuresDeepDive/materials/using/introToPBR
- Free HDRIs: https://polyhaven.com/hdris

## X-Ray Mode Compatibility
✓ PBR materials fully support X-ray mode (stored `originalAlpha` preserved)
