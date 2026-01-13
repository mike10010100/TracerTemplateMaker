# Recommended Improvements

This document outlines recommended improvements for the TracerTemplateMaker project, prioritized by impact on user experience and code maintainability.

## 1. Critical Performance & UX Fixes (High Priority)

**Goal:** Prevent UI freezing during heavy operations.

-   **Background Processing:** The `ProcessingThread` class is defined but currently unused. All image processing, STL generation, and SVG generation currently happen on the main UI thread, causing the application to "hang" during these operations.
    -   **Action:** Move `process_image`, `generate_svg`, and `generate_stl` calls to background threads.
-   **Debouncing:** Slider inputs (contrast, brightness, etc.) trigger immediate reprocessing. Rapid movements cause a backlog of processing requests.
    -   **Action:** Implement a debounce timer (e.g., 100-200ms) for all slider events. Only trigger the processing thread once the user stops moving the slider.
-   **3D Preview Optimization:** The matplotlib generation in the STL dialog is heavy.
    -   **Action:** Run the preview generation in a non-blocking thread and update the UI only when the image is ready.

## 2. Architectural Improvements (Medium Priority)

**Goal:** Improve code maintainability and testability.

-   **Separation of Concerns (MVC/MVVM):** `main.py` currently handles UI layout, event handling, and business logic state.
    -   **Action:** Extract application state (settings, colors, file paths) into a dedicated `AppState` or `Controller` class. `MainWindow` should only handle UI rendering and user inputs.
-   **Configuration Management:**
    -   **Action:** Move hardcoded constants (default colors, thresholds, window size) into a `config.py` file.
    -   **Action:** Allow saving/loading user preferences to a JSON file.

## 3. Image Pipeline Optimization (Medium Priority)

**Goal:** Reduce unnecessary computation.

-   **Pipeline Caching:** The current `process_image` re-runs the entire pipeline (Blur → Contrast → Brightness → Sharpness) even if only the last step changes.
    -   **Action:** Cache intermediate results. For example, if `contrast` changes but `blur` remains the same, start processing from the cached "blurred" image rather than the original.

## 4. Code Quality & Modernization (Low Priority)

**Goal:** adhere to modern Python standards.

-   **Logging:** Replace `print()` statements (especially in `stl_generator.py`) with the `logging` module. This enables file-based logging for easier user debugging.
-   **Packaging:** (Completed) Created `pyproject.toml` to standardize build and dependency management, replacing `requirements.txt`.
-   **Type Hinting:** Ensure all public methods across modules have complete type hints (mypy compliance).

## 5. Robustness (Low Priority)

-   **Pre-flight Checks:**
    -   **Action:** Analyze the image *before* attempting STL generation. Warn the user if the contour count is dangerously high (indicating noise) to prevent long wait times or crashes.
