# Quick Reference Guide

## Starting the Application

**macOS/Linux:**
```bash
./run.sh
```

**Windows:**
```cmd
run.bat
```

**Or manually:**
```bash
source venv/bin/activate  # or venv\Scripts\activate (Windows)
python main.py
```

## Basic Workflow

1. **Load Image** → Click "Open Image (JPG/SVG)"
2. **Set Dimensions** → Enter width and height in mm
3. **Adjust Settings** → Move sliders until preview looks good
4. **Select Colors** → Pick background and text colors
5. **Process** → Click "Process Image"
6. **Generate SVG** → Click "Generate SVG" and save
7. **Generate STL** → Click "Generate STL", configure, and save

## Slider Settings Guide

| Slider | Purpose | Recommended Range |
|--------|---------|------------------|
| **Contrast** | Make edges sharper | 100-150 |
| **Brightness** | Lighten/darken image | 80-120 |
| **Sharpness** | Edge clarity | 100-150 |
| **Blur** | Reduce noise | 0-3 |
| **Threshold** | Edge detection cutoff | 100-150 |

## Color Selection Tips

- **Yellow background templates**: Pick bright yellow from card
- **White background templates**: Pick white from card
- **Black text**: Pick from the darkest text
- **White text**: Pick from the brightest text

## Typical Dimensions

Based on example templates:

- Small templates: ~100mm × 50mm
- Medium templates: ~240mm × 120mm
- Large templates: ~270mm × 140mm

Always measure your actual template!

## STL Settings

| Setting | Purpose | Recommended |
|---------|---------|-------------|
| **Base Thickness** | Card thickness | 1.5-2.5mm |
| **Raised Text** | Dual-color printing | Enable for multi-color |

## File Formats

### Inputs
- `.jpg`, `.jpeg` - Photos of templates
- `.png` - High-quality images
- `.svg` - Vector graphics

### Outputs
- `.svg` - Vector file (2 layers)
- `.stl` - 3D model for printing

## Keyboard Shortcuts

### In Preview Windows
- **Mouse Wheel** - Zoom in/out
- **Left Click + Drag** - Pan view
- **Reset View** - Double-click

## Common Issues - Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Blurry edges | Increase sharpness, decrease blur |
| Missing holes | Lower threshold value |
| Extra noise | Increase blur slightly |
| Wrong colors | Use color picker on actual image |
| Size incorrect | Double-check dimension input |

## File Locations

```
TracerTemplateMaker/
├── Examples/          ← Sample images here
├── (create these as needed:)
├── output_svg/        ← Save SVG files here
└── output_stl/        ← Save STL files here
```

## Processing Time Estimates

- Image loading: Instant
- Preview updates: < 1 second
- SVG generation: 2-5 seconds
- STL generation: 5-15 seconds

## Best Practices

### Photography
- Use even, diffuse lighting
- Avoid shadows and glare
- Keep camera parallel to template
- Use highest resolution possible
- Contrasting background helps

### Processing
- Start with default settings
- Make small adjustments
- Check all layer previews
- Verify dimensions before export

### Output
- Test SVG in viewer before printing
- Validate STL in slicer software
- Keep original photos for reference

## Example Values for Sample Images

**Rings2308.jpg:**
- Dimensions: ~240mm × 120mm
- Background: Yellow
- Text: Black
- Contrast: 120
- Threshold: 130

**Settings2323Measure.jpg:**
- Dimensions: 240mm × 120mm (marked in image)
- Background: Yellow
- Text: Black
- Contrast: 110
- Threshold: 125

**HexTeardrop2314Measure.jpg:**
- Dimensions: 272mm × 140mm (marked in image)
- Background: Yellow
- Text: Black
- Contrast: 115
- Threshold: 120

## Getting Help

1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation issues
2. Read [README.md](README.md) for feature overview
3. See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for technical details

## Tips for Best Results

🎯 **Dimensional Accuracy**
- Measure physical template carefully
- Use calipers if available
- Enter exact measurements in mm

🎨 **Image Quality**
- Higher resolution = better results
- 300 DPI or higher recommended
- Avoid compression artifacts

⚙️ **Processing**
- Process in good lighting
- Adjust one slider at a time
- Review all layer tabs
- Save settings that work well

🖨️ **3D Printing**
- Check STL in slicer first
- Verify dimensions in slicer
- Use 0.2mm layer height
- PLA or PETG recommended

---

**Need more help?** See the full documentation files!
