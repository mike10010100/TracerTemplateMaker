# TracerTemplateMaker

> Convert physical tracing templates into digital SVG and 3D-printable STL files with dimensional accuracy

![Finished STL Example](TracerTemplate%20FinishedSTL.png)
*3D-printable STL model generated from a photograph of a physical template*

---

## Overview

**TracerTemplateMaker** is a Python desktop application that transforms photographs of physical tracing templates into precise digital formats:

- **📐 SVG Vector Files** - Perfect for laser cutting, vinyl cutting, or digital editing
- **🖨️ STL 3D Models** - Ready for 3D printing with optional raised text for dual-color printing
- **✨ Dimensional Accuracy** - Maintains exact measurements from your original template

Whether you need to digitize vintage templates, create duplicates, or modify existing designs, TracerTemplateMaker handles the conversion process automatically while preserving the exact dimensions.

### Key Features

- ✅ **Automated Layer Separation** - Automatically extracts profile outlines and text/markings into separate layers
- ✅ **Independent Layer Controls** - Fine-tune profile and text layers separately with dedicated controls
- ✅ **3D STL Preview** - See your 3D model before exporting
- ✅ **Real-time Processing** - Adjust parameters and see results instantly
- ✅ **Eyedropper Tool** - Pick colors directly from your image for perfect layer separation
- ✅ **Smart Edge Detection** - Advanced algorithms for clean, accurate outlines
- ✅ **Multi-format Export** - SVG for laser cutting, STL for 3D printing

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- 5-10 minutes for setup

### Installation

1. **Clone or download this repository**

2. **Navigate to the project directory**
   ```bash
   cd TracerTemplateMaker
   ```

3. **Create and activate a virtual environment**

   **macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **Windows:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

---

## How to Use

### 1. Load Your Template Image

Click **"Open Image (JPG/SVG)"** and select a photograph of your tracing template.

![Before Processing](TracerTemplate%20Before.png)
*Original photograph of a physical tracing template*

**Tips for best results:**
- Use good, even lighting
- Photograph straight-on (minimize perspective distortion)
- Use a contrasting background
- Higher resolution is better (300 DPI+)

### 2. Set Physical Dimensions

Enter the **actual width and height** of your template in millimeters. This is critical for dimensional accuracy.

### 3. Configure Layer Controls

TracerTemplateMaker separates your template into two layers:

#### **Profile Layer (Holes/Cutouts)**

![Profile Layer](TracerTemplate%20Profile.png)
*Automatically extracted profile with holes*

Use these controls to perfect the profile layer:
- **Profile Threshold (0-255)** - Brightness level for detecting holes (higher = more selective)
- **Profile Color Tolerance (0-100)** - How fuzzy the background color matching is
- **Profile Smoothing (0-10)** - Edge smoothness (higher = smoother edges)

**Eyedropper:** Click the eyedropper button next to "Background/Void" and click on a white/void area in your image.

#### **Text Layer (Markings)**

![Text Layer](TracerTemplate%20Text.png)
*Automatically extracted text and markings*

Use these controls to perfect the text layer:
- **Text Threshold (0-255)** - Darkness level for detecting text
- **Text Color Tolerance (0-100)** - How fuzzy the text color matching is
- **Text Detail Level (0-10)** - Lower values preserve more fine detail

**Eyedropper:** Click the eyedropper button next to "Text/Line" and click on a text area in your image.

### 4. Adjust Image Processing

Fine-tune the image with these controls:
- **Contrast** - Make edges more distinct
- **Brightness** - Lighten or darken the image
- **Sharpness** - Enhance edge definition
- **Blur** - Reduce noise from grainy photos
- **Color Tolerance** - Control how precisely colors are matched

All adjustments update in real-time in the preview tabs.

### 5. Export Your Files

#### **Generate SVG**
Click **"Generate SVG"** for laser cutting or digital editing.

**SVG Output Includes:**
- **Layer 1 (Black):** Profile outlines and holes - no fill, just outlines
- **Layer 2 (Red):** Text and markings - no fill, just outlines
- Both layers perfectly aligned and dimensionally accurate

#### **Generate STL**
Click **"Generate STL"** for 3D printing.

**STL Options:**
- **Base Thickness:** Set the thickness of your template (typically 1-3mm)
- **Raised Text Layer:** Enable for dual-color 3D printing (text always 0.2mm high)
- **3D Preview:** Click "Generate Preview" to see your model before exporting

**STL Features:**
- Text appears on TOP surface (correct orientation for printing)
- Watertight meshes ready for slicing
- Holes properly rendered as voids
- Smart optimization prevents hangs on complex geometry

---

## Advanced Features

### Independent Layer Controls

Version 1.6.0 introduces **completely independent controls** for profile and text layers:

- Adjust profile smoothness without affecting text sharpness
- Preserve fine text detail while smoothing profile edges
- Each layer has its own threshold, tolerance, and detail/smoothing controls

### 3D STL Preview

Before exporting, preview your 3D model:
- Interactive 3D visualization using matplotlib
- Verify text is on the correct side
- Check dimensions and appearance
- Optimized rendering for complex models

### Edge Case Handling

The application automatically handles:
- Noisy images with thousands of tiny contours (filtered automatically)
- Complex shapes with many vertices (simplified intelligently)
- Large numbers of holes (limited to top 100 by area)
- Very complex meshes (skips expensive operations when needed)

---

## Technical Details

### Architecture

```
TracerTemplateMaker/
├── main.py                      # Main application & UI
├── modules/
│   ├── image_processor.py       # Image processing & layer separation
│   ├── svg_generator.py         # SVG export with layers
│   ├── stl_generator.py         # 3D mesh & STL export
│   └── ui_components.py         # Reusable UI widgets
├── Examples/                    # Sample templates
├── requirements.txt             # Python dependencies
└── CHANGELOG.md                 # Version history
```

### Dependencies

- **OpenCV** - Image processing and edge detection
- **PyQt6** - Modern GUI framework
- **svgwrite** - SVG file generation
- **trimesh** - 3D mesh operations
- **numpy-stl** - STL file export
- **shapely** - Geometric operations
- **matplotlib** - 3D visualization

### Dimensional Accuracy

The application maintains pixel-to-millimeter scaling throughout the entire pipeline:

1. User enters physical dimensions in millimeters
2. Scale factor calculated: `scale = width_mm / pixel_width`
3. All contour coordinates multiplied by scale factor
4. SVG and STL outputs use actual millimeter measurements

**Result:** Print or cut output matches original template dimensions exactly.

---

## Troubleshooting

### Common Issues

**Issue: Edges not detected accurately**
- Increase contrast and threshold
- Use eyedropper to pick exact background color
- Try adding slight blur to reduce noise

**Issue: Text layer is empty**
- Use eyedropper to select exact text color
- Adjust text threshold value
- Increase text color tolerance

**Issue: STL preview broken**
- Make sure matplotlib is installed: `pip install matplotlib>=3.7.0`
- Check console for error messages
- Verify masks have content (not empty)

**Issue: SVG has black filled shapes instead of outlines**
- This has been fixed in v1.6.0
- SVG now exports with `fill='none'` for laser cutting
- Profile layer = black strokes, Text layer = red strokes

**Issue: Application won't start**
- Ensure virtual environment is activated: `(venv)` appears in terminal
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.8+)

### Getting Better Results

1. **Image Quality**: Use highest resolution possible (300 DPI or higher)
2. **Lighting**: Even, diffused lighting - no harsh shadows
3. **Background**: Contrasting color makes edge detection easier
4. **Multiple Attempts**: Adjust sliders and reprocess until perfect

---

## Version History

### Current Version: 1.6.1 (2026-01-12)

**Major Features:**
- ⚡ **Asynchronous UI**: Processing and 3D previews now run in the background.
- ⏱️ **Debounced Inputs**: Smoother experience when adjusting sliders.
- 🖱️ **Scroll Protection**: Prevented mouse wheel from accidentally changing slider values.
- 🎯 Independent Profile and Text layer controls
- 🎨 Eyedropper tool for accurate color selection
- 🖼️ 3D STL preview feature
- ⚡ Fixed STL generation hangs with edge case handling
- 🔧 Fixed SVG black fill issues (now outline-only)
- 🔄 Fixed STL text orientation (now on top surface)

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

## System Requirements

- **OS:** Windows 10+, macOS 10.14+, or Linux
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum (8GB recommended for large images)
- **Disk:** 500MB for application and dependencies

---

## Contributing

Contributions are welcome! This project is designed for:
- Jewelry makers and craftspeople
- Laser cutting enthusiasts
- 3D printing hobbyists
- Anyone digitizing physical templates

---

## License

This project is provided as-is for educational and personal use.

---

## Acknowledgments

Built with:
- Python & PyQt6 for the GUI
- OpenCV for image processing
- trimesh & numpy-stl for 3D modeling
- svgwrite for vector graphics
- matplotlib for 3D visualization

Designed for makers, artists, and jewelry designers who need precision template conversion. 🎨

---

**Questions or Issues?** Check the [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed installation help or the [CHANGELOG.md](CHANGELOG.md) for version-specific information.
