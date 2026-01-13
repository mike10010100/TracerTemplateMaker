# TracerTemplateMaker

## Project Overview

**TracerTemplateMaker** is a Python desktop application (PyQt6) that converts photographs of physical tracing templates into precise digital formats. It automates the creation of:
*   **SVG Vector Files:** For laser cutting, vinyl cutting, or digital editing.
*   **STL 3D Models:** For 3D printing (supports dual-color printing with raised text).

The core value proposition is **dimensional accuracy**, allowing makers to digitize vintage or physical templates while maintaining exact measurements.

### Key Technologies
*   **Language:** Python 3.8+
*   **GUI:** PyQt6
*   **Image Processing:** OpenCV, Pillow, scikit-image
*   **Vector/3D Generation:** svgwrite, trimesh, numpy-stl, shapely
*   **Visualization:** Matplotlib
*   **Packaging:** setuptools, pyproject.toml

## Architecture

The project follows a modular architecture:

*   **`main.py`**: The application entry point and main window controller. It handles UI setup, event handling, and threading for long-running tasks.
*   **`modules/`**: Contains core logic separated by concern.
    *   **`image_processor.py`**: Handles image loading, preprocessing (contrast/brightness), edge detection (Canny), and color-based layer separation.
    *   **`svg_generator.py`**: Converts processed contours into SVG paths, managing layers (Profile vs. Text) and scaling.
    *   **`stl_generator.py`**: Extrudes 2D masks into 3D meshes, handling thickness, raised text, and watertight mesh generation.
    *   **`ui_components.py`**: Custom Reusable PyQt6 widgets (e.g., Zoomable/Pannable Image Views, Control Panels, NoWheelSlider).
    *   **`config.py`**: Manages default settings and persistent user configuration.
    *   **`app_state.py`**: Encapsulates the application's runtime state to decouple logic from the UI.
    *   **`logger.py`**: Provides structured logging to console and file.

## Setup & Development

### Prerequisites
*   Python 3.8+
*   Virtual Environment (recommended)

### Installation
1.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate   # Windows
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    # OR
    pip install .
    ```

### Running the Application
*   **Standard:** `python main.py`
*   **Linux/macOS Script:** `./run.sh`
*   **Windows Script:** `run.bat`

### Testing
*   **Installation Verification:** `python test_installation.py`
*   **Specific Tests:**
    *   `python test_stl_edge_cases.py` (Tests STL generation robustness)
    *   `python test_stl_watertight.py` (Verifies mesh integrity)

## Development Conventions

*   **Modularity:** Logic should remain separated in `modules/`. UI code stays in `ui_components.py` or `main.py`.
*   **Type Hints:** Use Python type hints for function parameters and return values.
*   **Documentation:** Functions should have docstrings explaining their purpose.
*   **Dimensionality:** All geometric operations must account for the pixel-to-millimeter scale factor to ensure accuracy.
*   **Error Handling:** Use try-except blocks, especially in file I/O and mesh generation, to prevent GUI crashes.
*   **Logging:** Use the `logger` module instead of `print()` for all status and error reporting.
*   **Concurrency:** Heavy operations (image processing, STL generation) MUST run in background threads (`ProcessingThread`) to avoid freezing the UI.
