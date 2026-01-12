# TracerTemplateMaker - Complete Setup Guide

This guide will walk you through setting up and running TracerTemplateMaker on your system, even if you're new to Python.

## Table of Contents
1. [Installing Python](#installing-python)
2. [Setting Up the Project](#setting-up-the-project)
3. [Installing Dependencies](#installing-dependencies)
4. [Running the Application](#running-the-application)
5. [Troubleshooting](#troubleshooting)

## Installing Python

### Windows

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **IMPORTANT**: Check the box "Add Python to PATH" during installation
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   ```

### macOS

1. Install Homebrew (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Python:
   ```bash
   brew install python
   ```

3. Verify installation:
   ```bash
   python3 --version
   ```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

## Setting Up the Project

### 1. Navigate to Project Directory

Open Terminal (macOS/Linux) or Command Prompt (Windows) and navigate to the project:

```bash
cd /path/to/TracerTemplateMaker
```

### 2. Create Virtual Environment

This keeps the project dependencies isolated from your system Python.

**Windows:**
```cmd
python -m venv venv
```

**macOS/Linux:**
```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```cmd
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` appear at the start of your command prompt.

## Installing Dependencies

With the virtual environment activated, first upgrade pip, then install all required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- OpenCV for image processing
- PyQt6 for the GUI
- svgwrite for SVG generation
- numpy-stl and trimesh for 3D modeling
- scikit-image for advanced image processing
- And other supporting libraries

**Note**: Installation may take 5-10 minutes depending on your internet connection.

### Verifying Installation

After installation, you can verify everything is working:

```bash
python test_installation.py
```

You should see "SUCCESS: All tests passed!" if everything is installed correctly.

### Platform-Specific Notes

**macOS**: If you encounter issues with OpenCV, you may need to install system dependencies:
```bash
brew install opencv
```

**Linux**: You may need additional system packages:
```bash
sudo apt install python3-opencv python3-pyqt6
```

## Running the Application

Once everything is installed, run the application:

```bash
python main.py
```

The TracerTemplateMaker window should open.

## Using the Application

### Step-by-Step Workflow

1. **Load an Image**
   - Click "Open Image (JPG/SVG)"
   - Select one of the example images from the `Examples` folder
   - The image appears in the "Original" tab

2. **Set Physical Dimensions**
   - Enter the actual width and height of your template in millimeters
   - This is CRITICAL for dimensional accuracy
   - For example images with "Measure" in the name, you can see the dimensions in the photo

3. **Adjust Image Processing**
   - Use the sliders to adjust:
     - **Contrast**: Make edges more distinct
     - **Brightness**: Lighten or darken the image
     - **Sharpness**: Enhance edge definition
     - **Blur**: Reduce noise (helpful for grainy photos)
     - **Threshold**: Set the cutoff for edge detection
   - Preview updates in real-time in the "Processed" tab

4. **Select Colors**
   - Click the background color button and select the template's background color (usually yellow)
   - Click the text color button and select the text/line color (usually black)
   - This helps separate the layers correctly

5. **Process Image**
   - Click "Process Image"
   - The app separates the image into two layers:
     - Profile Layer: Outer edge and cutout holes
     - Text Layer: Text and guide lines
   - Review both layers in their respective tabs

6. **Generate SVG**
   - Click "Generate SVG"
   - Choose where to save the file
   - The SVG will have two layers for editing/cutting

7. **Generate STL (Optional)**
   - Click "Generate STL"
   - Set the base thickness (typically 1-3mm for templates)
   - Optionally enable "raised text layer" for dual-color printing
   - Click "Generate and Save STL"
   - Choose where to save the file

## Troubleshooting

### Issue: "python command not found"

**Solution**:
- Windows: Make sure Python was installed with "Add to PATH" checked
- macOS/Linux: Use `python3` instead of `python`

### Issue: "No module named 'cv2'" or similar

**Solution**:
- Make sure your virtual environment is activated (you should see `(venv)`)
- Run `pip install -r requirements.txt` again

### Issue: Application won't start

**Solution**:
1. Check that all dependencies installed correctly:
   ```bash
   pip list
   ```
2. Look for any error messages when running `python main.py`
3. Try reinstalling PyQt6:
   ```bash
   pip uninstall PyQt6
   pip install PyQt6
   ```

### Issue: Edges not detected accurately

**Solution**:
- Increase contrast and threshold
- Try adding slight blur to reduce noise
- Ensure good lighting in original photo
- Use the color picker to select exact background color

### Issue: Text layer is empty

**Solution**:
- Use the color picker to select the exact text color from the image
- Adjust threshold value
- Check that text color is different enough from background

### Issue: SVG dimensions are incorrect

**Solution**:
- Double-check the dimensions you entered match the physical template
- Verify the units (should be millimeters)
- Check that your image isn't cropped

### Issue: STL file is corrupted or won't open

**Solution**:
- Make sure the profile layer has closed contours (no gaps)
- Try processing with different threshold settings
- Use online STL repair tools like Microsoft 3D Builder or Netfabb

## Advanced Tips

### Getting Better Results

1. **Image Quality**: Use the highest resolution photos possible (300 DPI or higher)
2. **Lighting**: Photograph templates with even, diffused lighting
3. **Background**: Place template on a contrasting background for easier edge detection
4. **Multiple Attempts**: Don't be afraid to adjust sliders and reprocess several times

### File Organization

Create folders for organization:
```
TracerTemplateMaker/
├── input_images/     # Original photos
├── output_svg/       # Generated SVG files
└── output_stl/       # Generated STL files
```

### Batch Processing

For processing multiple templates, you can modify the code to accept command-line arguments or create a simple batch script.

## Getting Help

If you encounter issues not covered here:

1. Check that you're using Python 3.8 or higher: `python --version`
2. Verify all dependencies are installed: `pip list`
3. Look for error messages in the terminal/console
4. Try with one of the provided example images first

## Deactivating Virtual Environment

When you're done using the application:

```bash
deactivate
```

## Updating the Application

If new features are added:

```bash
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Update dependencies
pip install -r requirements.txt --upgrade
```

---

**Enjoy creating your tracing templates!** 🎨
