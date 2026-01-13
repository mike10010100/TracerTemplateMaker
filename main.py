"""
TracerTemplateMaker - Main Application

A comprehensive tool for converting tracing template images to SVG and STL formats.

Author: TracerTemplateMaker
License: Open Source
"""

import os
import sys

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QMouseEvent, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from modules.app_state import AppState
from modules.config import ConfigManager

# Import our modules
from modules.image_processor import ImageProcessor
from modules.logger import setup_logger
from modules.stl_generator import STLGenerator
from modules.svg_generator import SVGGenerator
from modules.ui_components import (
    ColorPickerPanel,
    ControlPanel,
    DimensionInputPanel,
    ImagePreviewWidget,
    NoWheelDoubleSpinBox,
)

logger = setup_logger("Main")


class ProcessingThread(QThread):
    """
    Thread for handling heavy processing tasks without freezing UI.
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """
    Main application window for TracerTemplateMaker.
    """

    def __init__(self):
        super().__init__()

        # Initialize config and state
        self.config_manager = ConfigManager()
        self.state = AppState()
        self.state.load_from_dict(self.config_manager.settings)

        # Initialize processors
        self.image_processor = ImageProcessor()
        self.svg_generator = None
        self.stl_generator = None

        # Current processing state
        self.processed_image = None
        self.profile_mask = None
        self.text_mask = None
        self.svg_path = None
        self.is_processing = False

        # Eyedropper mode
        self.eyedropper_active = False
        self.eyedropper_target = None  # Which color we're picking for

        # Debounce timer for processing
        self.process_timer = QTimer()
        self.process_timer.setSingleShot(True)
        self.process_timer.setInterval(150)  # 150ms delay
        self.process_timer.timeout.connect(self.start_processing_thread)

        self.init_ui()
        self.apply_state_to_ui()

    def closeEvent(self, event):
        """Save settings when the application is closed."""
        self.config_manager.save_settings(self.state.to_dict())
        event.accept()

    def apply_state_to_ui(self):
        """Update the UI widgets with values from the current state."""
        # Update Dimensions
        self.dimension_panel.width_input.setValue(self.state.width_mm)
        self.dimension_panel.height_input.setValue(self.state.height_mm)

        # Update Colors
        self.color_panel.bg_color = self.state.bg_color
        self.color_panel.update_button_color(
            self.color_panel.bg_color_btn,
            (self.state.bg_color[2], self.state.bg_color[1], self.state.bg_color[0]),
        )

        self.color_panel.tracer_color = self.state.tracer_color
        self.color_panel.update_button_color(
            self.color_panel.tracer_color_btn,
            (self.state.tracer_color[2], self.state.tracer_color[1], self.state.tracer_color[0]),
        )

        self.color_panel.text_color = self.state.text_color
        self.color_panel.update_button_color(
            self.color_panel.text_color_btn,
            (self.state.text_color[2], self.state.text_color[1], self.state.text_color[0]),
        )

        # Update Sliders (ControlPanel needs a set_values method, we'll add it)
        self.control_panel.set_values(
            {
                "Contrast": int(self.state.contrast * 100),
                "Brightness": int(self.state.brightness * 100),
                "Sharpness": int(self.state.sharpness * 100),
                "Blur (Noise Reduction)": (self.state.blur_kernel - 1) // 2
                if self.state.blur_kernel > 0
                else 0,
                "Profile Threshold": self.state.profile_threshold,
                "Profile Color Tolerance": self.state.profile_tolerance,
                "Profile Smoothing": self.state.profile_smoothing,
                "Text Threshold": self.state.text_threshold,
                "Text Color Tolerance": self.state.text_tolerance,
                "Text Detail Level": self.state.text_detail,
            }
        )

    def show_status_message(self, message: str):
        """Safely show a message in the status bar."""
        sb = self.statusBar()
        if sb:
            sb.showMessage(message)

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("TracerTemplateMaker - Image to SVG/STL Converter")
        self.setGeometry(100, 100, 1400, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout()

        # Left side: Controls
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, stretch=1)

        # Right side: Preview and tabs
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, stretch=3)

        central_widget.setLayout(main_layout)

        # Status bar
        self.show_status_message("Ready - Load an image to begin")

    def create_left_panel(self) -> QWidget:
        """Create left control panel."""
        # Create a scroll area to hold the controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumWidth(350)

        # Create the content widget that goes inside the scroll area
        panel = QWidget()
        layout = QVBoxLayout()

        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout()

        load_btn = QPushButton("Open Image (JPG/SVG)")
        load_btn.clicked.connect(self.load_image)
        file_layout.addWidget(load_btn)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Dimensions input
        self.dimension_panel = DimensionInputPanel()
        self.dimension_panel.dimensions_changed.connect(self.on_dimensions_changed)
        layout.addWidget(self.dimension_panel)

        # Color picker
        self.color_panel = ColorPickerPanel()
        self.color_panel.background_color_changed.connect(self.on_bg_color_changed)
        self.color_panel.tracer_color_changed.connect(self.on_tracer_color_changed)
        self.color_panel.text_color_changed.connect(self.on_text_color_changed)
        self.color_panel.eyedropper_requested.connect(self.activate_eyedropper)
        layout.addWidget(self.color_panel)

        # Image adjustment controls
        self.control_panel = ControlPanel()
        self.control_panel.contrast_changed.connect(self.on_contrast_changed)
        self.control_panel.brightness_changed.connect(self.on_brightness_changed)
        self.control_panel.sharpness_changed.connect(self.on_sharpness_changed)
        self.control_panel.blur_changed.connect(self.on_blur_changed)
        # Profile layer controls
        self.control_panel.profile_threshold_changed.connect(self.on_profile_threshold_changed)
        self.control_panel.profile_tolerance_changed.connect(self.on_profile_tolerance_changed)
        self.control_panel.profile_smoothing_changed.connect(self.on_profile_smoothing_changed)
        # Text layer controls
        self.control_panel.text_threshold_changed.connect(self.on_text_threshold_changed)
        self.control_panel.text_tolerance_changed.connect(self.on_text_tolerance_changed)
        self.control_panel.text_detail_changed.connect(self.on_text_detail_changed)
        layout.addWidget(self.control_panel)

        # Process buttons
        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout()

        process_btn = QPushButton("Process Image")
        process_btn.clicked.connect(self.trigger_processing)
        process_layout.addWidget(process_btn)

        svg_btn = QPushButton("Generate SVG")
        svg_btn.clicked.connect(self.generate_svg)
        process_layout.addWidget(svg_btn)

        stl_btn = QPushButton("Generate STL")
        stl_btn.clicked.connect(self.open_stl_window)
        process_layout.addWidget(stl_btn)

        process_group.setLayout(process_layout)
        layout.addWidget(process_group)

        layout.addStretch()
        panel.setLayout(layout)

        scroll_area.setWidget(panel)
        return scroll_area

    def create_right_panel(self) -> QWidget:
        """Create right preview panel."""
        panel = QWidget()
        layout = QVBoxLayout()

        # Tab widget for different views
        self.tab_widget = QTabWidget()

        # Original image tab
        self.original_preview = ImagePreviewWidget()
        self.original_preview.view_changed.connect(self.sync_views)
        self.tab_widget.addTab(self.original_preview, "Original")

        # Processed image tab
        self.processed_preview = ImagePreviewWidget()
        self.processed_preview.view_changed.connect(self.sync_views)
        self.tab_widget.addTab(self.processed_preview, "Processed")

        # Profile mask tab
        self.profile_preview = ImagePreviewWidget()
        self.profile_preview.view_changed.connect(self.sync_views)
        self.tab_widget.addTab(self.profile_preview, "Profile Layer")

        # Text mask tab
        self.text_preview = ImagePreviewWidget()
        self.text_preview.view_changed.connect(self.sync_views)
        self.tab_widget.addTab(self.text_preview, "Text Layer")

        layout.addWidget(self.tab_widget)

        panel.setLayout(layout)
        return panel

    def sync_views(self, zoom: float, h_scroll: int, v_scroll: int):
        """Synchronize zoom and pan across all image previews."""
        sender = self.sender()

        previews = [
            self.original_preview,
            self.processed_preview,
            self.profile_preview,
            self.text_preview,
        ]

        for preview in previews:
            if preview != sender:
                preview.set_view(zoom, h_scroll, v_scroll)

    def load_image(self):
        """Load image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.jpg *.jpeg *.png *.bmp *.svg);;All Files (*)"
        )

        if file_path:
            try:
                self.state.current_image_path = file_path
                image = self.image_processor.load_image(file_path)

                # Display original
                self.original_preview.set_image(image)

                # Auto-detect dimensions from filename if present
                self.auto_detect_dimensions(file_path)

                self.show_status_message(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")

    def auto_detect_dimensions(self, file_path: str):
        """
        Auto-detect dimensions from filename if it contains 'Measure'.
        For example: 'Template_10x5cm_Measure.jpg'
        """
        # This is a placeholder - could be enhanced to parse dimensions from filename
        pass

    def trigger_processing(self):
        """Reset the debounce timer to trigger processing."""
        self.process_timer.start()

    def on_dimensions_changed(self, width_mm: float, height_mm: float):
        """Handle dimension change."""
        self.state.width_mm = width_mm
        self.state.height_mm = height_mm
        self.image_processor.set_dimensions(width_mm, height_mm)
        self.show_status_message(f"Dimensions set: {width_mm}mm x {height_mm}mm")

    def on_contrast_changed(self, value: float):
        """Handle contrast change."""
        self.state.contrast = value
        self.trigger_processing()

    def on_brightness_changed(self, value: float):
        """Handle brightness change."""
        self.state.brightness = value
        self.trigger_processing()

    def on_sharpness_changed(self, value: float):
        """Handle sharpness change."""
        self.state.sharpness = value
        self.trigger_processing()

    def on_blur_changed(self, value: int):
        """Handle blur change."""
        self.state.blur_kernel = value
        self.trigger_processing()

    def on_profile_threshold_changed(self, value: int):
        """Handle profile threshold change."""
        self.state.profile_threshold = value
        self.trigger_processing()

    def on_text_threshold_changed(self, value: int):
        """Handle text threshold change."""
        self.state.text_threshold = value
        self.trigger_processing()

    def on_profile_tolerance_changed(self, value: int):
        """Handle profile color tolerance change."""
        self.state.profile_tolerance = value
        self.trigger_processing()

    def on_profile_smoothing_changed(self, value: int):
        """Handle profile smoothing change."""
        self.state.profile_smoothing = value
        self.trigger_processing()

    def on_text_tolerance_changed(self, value: int):
        """Handle text color tolerance change."""
        self.text_tolerance = value  # Wait, I should use self.state.text_tolerance
        self.state.text_tolerance = value
        self.trigger_processing()

    def on_text_detail_changed(self, value: int):
        """Handle text detail level change."""
        self.state.text_detail = value
        self.trigger_processing()

    def on_bg_color_changed(self, color: tuple):
        """Handle background/void color change."""
        self.state.bg_color = color
        self.trigger_processing()

    def on_tracer_color_changed(self, color: tuple):
        """Handle tracer card color change."""
        self.state.tracer_color = color
        self.trigger_processing()

    def on_text_color_changed(self, color: tuple):
        """Handle text/line color change."""
        self.state.text_color = color
        self.trigger_processing()

    def activate_eyedropper(self, target: str):
        """
        Activate eyedropper mode to pick a color from the image.

        Args:
            target: Which color to set ('background', 'tracer', or 'text')
        """
        if self.processed_image is None:
            QMessageBox.warning(self, "Warning", "Please load an image first")
            return

        self.eyedropper_active = True
        self.eyedropper_target = target
        self.original_preview.image_label.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.show_status_message(f"Click on the image to pick {target} color")

        # Temporarily connect click handler
        self.original_preview.image_label.mousePressEvent = self.eyedropper_click

    def eyedropper_click(self, event: QMouseEvent):
        """Handle eyedropper click to pick color from image."""
        if not self.eyedropper_active:
            return

        # Use original image for color picking (more accurate)
        if self.image_processor.original_image is None:
            return

        # Get click position relative to the label
        pos = event.pos()

        # Calculate position in original image coordinates
        zoom = self.original_preview.zoom_level
        img_x = int(pos.x() / zoom)
        img_y = int(pos.y() / zoom)

        # Get the actual image being displayed
        original_img = self.image_processor.original_image

        # Make sure we're within image bounds
        height, width = original_img.shape[:2]
        if 0 <= img_x < width and 0 <= img_y < height:
            # Get color from original image (BGR)
            if len(original_img.shape) == 3:
                bgr_color = tuple(int(x) for x in original_img[img_y, img_x])
            else:
                # Grayscale - convert to BGR
                gray_val = int(original_img[img_y, img_x])
                bgr_color = (gray_val, gray_val, gray_val)

            # Set the color
            self.color_panel.set_color_from_pick(self.eyedropper_target, bgr_color)
            self.show_status_message(f"Picked color: BGR{bgr_color} at ({img_x}, {img_y})")
        else:
            self.show_status_message(f"Click outside image bounds: ({img_x}, {img_y})")

        # Deactivate eyedropper
        self.eyedropper_active = False
        self.eyedropper_target = None
        self.original_preview.image_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        # Restore normal mouse handler
        self.original_preview.image_label.mousePressEvent = self.original_preview.mouse_press_event

    def start_processing_thread(self):
        """Collect parameters and start the background thread."""
        if self.image_processor.original_image is None:
            return

        # If already processing, the timer will just fire again later
        self.is_processing = True
        self.show_status_message("Processing...")

        # Collect all current parameters from self.state
        params = {
            "contrast": self.state.contrast,
            "brightness": self.state.brightness,
            "sharpness": self.state.sharpness,
            "blur_kernel": self.state.blur_kernel,
            "bg_color": self.state.bg_color,
            "tracer_color": self.state.tracer_color,
            "text_color": self.state.text_color,
            "profile_tolerance": self.state.profile_tolerance,
            "profile_threshold": self.state.profile_threshold,
            "profile_smoothing": self.state.profile_smoothing,
            "text_tolerance": self.state.text_tolerance,
            "text_threshold": self.state.text_threshold,
            "text_detail": self.state.text_detail,
        }

        # Create thread
        self.thread = ProcessingThread(self.run_full_pipeline, self.image_processor, **params)
        self.thread.finished.connect(self.on_processing_finished)
        self.thread.error.connect(self.on_processing_error)
        self.thread.start()

    @staticmethod
    def run_full_pipeline(processor, **kwargs):
        """
        Static method to run the full image processing pipeline.
        This runs in a separate thread.
        """
        # 1. Apply image adjustments
        processed = processor.process_image(
            contrast=kwargs["contrast"],
            brightness=kwargs["brightness"],
            sharpness=kwargs["sharpness"],
            blur_kernel=kwargs["blur_kernel"],
        )

        # 2. Separate layers
        profile_mask, text_mask = processor.separate_layers(
            processed,
            kwargs["bg_color"],
            kwargs["tracer_color"],
            kwargs["text_color"],
            profile_tolerance=kwargs["profile_tolerance"],
            profile_threshold=kwargs["profile_threshold"],
            profile_smoothing=kwargs["profile_smoothing"],
            text_tolerance=kwargs["text_tolerance"],
            text_threshold=kwargs["text_threshold"],
            text_detail=kwargs["text_detail"],
        )

        return processed, profile_mask, text_mask

    def on_processing_finished(self, result):
        """Handle successful processing."""
        self.is_processing = False
        processed, profile_mask, text_mask = result

        self.processed_image = processed
        self.profile_mask = profile_mask
        self.text_mask = text_mask

        # Update previews
        try:
            self.processed_preview.set_image(processed)
            self.profile_preview.set_image(cv2.cvtColor(profile_mask, cv2.COLOR_GRAY2BGR))
            self.text_preview.set_image(cv2.cvtColor(text_mask, cv2.COLOR_GRAY2BGR))
            self.show_status_message("Image processed - layers separated")
        except Exception as e:
            self.on_processing_error(str(e))

    def on_processing_error(self, error_msg):
        """Handle processing error."""
        self.is_processing = False
        self.show_status_message(f"Processing error: {error_msg}")
        logger.error(f"Error in processing thread: {error_msg}")

    def generate_svg(self):
        """Generate SVG from processed masks."""
        if self.profile_mask is None:
            QMessageBox.warning(self, "Warning", "Please process the image first")
            return

        # Get dimensions
        width_mm, height_mm = self.dimension_panel.get_dimensions()

        # Ask for save location
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save SVG File", "", "SVG Files (*.svg);;All Files (*)"
        )

        if not save_path:
            return

        try:
            # Create SVG generator
            self.svg_generator = SVGGenerator(width_mm, height_mm)

            # Profile mask has holes as white, card as black
            # SVG generator expects solid as white, holes as black (same as STL)
            # Therefore we need to INVERT the profile mask for SVG generation
            inverted_profile = cv2.bitwise_not(self.profile_mask)

            self.svg_path = self.svg_generator.create_layered_svg(
                inverted_profile,  # Inverted: solid card is white, holes are black
                self.text_mask,
                save_path,
                include_metadata=True,
            )

            QMessageBox.information(self, "Success", f"SVG saved to:\n{save_path}")
            self.show_status_message(f"SVG generated: {os.path.basename(save_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"SVG generation failed: {str(e)}")

    def open_stl_window(self):
        """Open STL generation window."""
        if self.profile_mask is None:
            QMessageBox.warning(self, "Warning", "Please process the image first")
            return

        # Create STL dialog
        dialog = STLGeneratorDialog(
            self, self.profile_mask, self.text_mask, self.dimension_panel.get_dimensions()
        )
        dialog.exec()


class STLGeneratorDialog(QDialog):
    """
    Dialog for STL generation with preview.
    """

    def __init__(self, parent, profile_mask, text_mask, dimensions):
        super().__init__(parent)
        self.profile_mask = profile_mask
        self.text_mask = text_mask
        self.width_mm, self.height_mm = dimensions
        self.is_processing = False

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("STL Generator")
        self.setGeometry(200, 200, 1000, 700)

        # Main layout with splitter for preview
        main_layout = QHBoxLayout()

        # Left side: Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Title
        title = QLabel("3D Model Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(title)

        # Thickness control
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel("Base Thickness (mm):"))
        self.thickness_input = NoWheelDoubleSpinBox()
        self.thickness_input.setRange(0.5, 10.0)
        self.thickness_input.setValue(2.0)
        self.thickness_input.setDecimals(2)
        self.thickness_input.valueChanged.connect(self.update_preview)
        thickness_layout.addWidget(self.thickness_input)
        thickness_layout.addStretch()
        left_layout.addLayout(thickness_layout)

        # Separate text option
        self.separate_text_check = QCheckBox("Create raised text layer (for dual-color printing)")
        self.separate_text_check.setChecked(False)
        self.separate_text_check.stateChanged.connect(self.update_preview)
        left_layout.addWidget(self.separate_text_check)

        # Preview button
        preview_btn = QPushButton("Generate Preview")
        preview_btn.clicked.connect(self.update_preview)
        left_layout.addWidget(preview_btn)

        # Generate button
        generate_btn = QPushButton("Generate and Save STL")
        generate_btn.clicked.connect(self.generate_stl)
        left_layout.addWidget(generate_btn)

        # Info label
        info = QLabel(
            "Note: The STL will maintain dimensional accuracy based on your input dimensions. "
            "Click 'Generate Preview' to see a 3D visualization."
        )
        info.setStyleSheet("color: #666; font-style: italic;")
        info.setWordWrap(True)
        left_layout.addWidget(info)

        left_layout.addStretch()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(400)

        # Right side: Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        preview_title = QLabel("3D Preview")
        preview_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        right_layout.addWidget(preview_title)

        self.preview_label = QLabel("Click 'Generate Preview' to see 3D model")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "border: 2px solid #ccc; background-color: #f5f5f5; min-height: 400px;"
        )
        right_layout.addWidget(self.preview_label)

        right_widget.setLayout(right_layout)

        # Add both sides to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)  # Give preview more space

        self.setLayout(main_layout)

        # Store preview mesh for reuse
        self.preview_mesh = None

    def update_preview(self):
        """Start background thread to generate 3D preview."""
        if self.is_processing:
            return

        self.preview_label.setText("Generating preview...")
        self.is_processing = True

        # Collect params
        params = {
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "profile_mask": self.profile_mask,
            "text_mask": self.text_mask,
            "thickness": self.thickness_input.value(),
            "separate_text": self.separate_text_check.isChecked(),
        }

        self.thread = ProcessingThread(self.generate_preview_data, **params)
        self.thread.finished.connect(self.on_preview_finished)
        self.thread.error.connect(self.on_preview_error)
        self.thread.start()

    @staticmethod
    def generate_preview_data(
        width_mm, height_mm, profile_mask, text_mask, thickness, separate_text
    ):
        """Generate preview image data in background."""
        import matplotlib

        matplotlib.use("Agg")
        from io import BytesIO

        import matplotlib.pyplot as plt
        import trimesh
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        # Create STL generator
        stl_gen = STLGenerator(width_mm, height_mm)

        # Prepare masks
        inverted_profile = cv2.bitwise_not(profile_mask)

        # Generate meshes
        if separate_text and text_mask is not None:
            # Create dual layer
            text_height = 0.2
            base_mesh = stl_gen.extrude_mask_to_mesh(inverted_profile, thickness, 0.0)
            text_mesh = stl_gen.extrude_mask_to_mesh(text_mask, text_height, thickness)

            if len(text_mesh.vertices) > 0:
                combined_mesh = trimesh.util.concatenate([base_mesh, text_mesh])
            else:
                combined_mesh = base_mesh

            # Apply transform
            mirror_matrix = np.array(
                [
                    [1, 0, 0, 0],  # Keep X
                    [0, 1, 0, 0],  # Keep Y
                    [0, 0, -1, 0],  # Flip Z
                    [0, 0, 0, 1],
                ]
            )
            combined_mesh.apply_transform(mirror_matrix)
            min_z = combined_mesh.bounds[0][2]
            if min_z < 0:
                combined_mesh.apply_translation([0, 0, -min_z])

            mesh_to_render = combined_mesh
        else:
            # Simple mesh
            if text_mask is not None:
                combined_mask = cv2.bitwise_or(inverted_profile, text_mask)
            else:
                combined_mask = inverted_profile
            mesh_to_render = stl_gen.extrude_mask_to_mesh(combined_mask, thickness, 0.0)

        # Check if mesh is valid
        if len(mesh_to_render.vertices) == 0 or len(mesh_to_render.faces) == 0:
            return None

        # Render mesh to image
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection="3d")

        # Render surface
        # We render the full mesh using Poly3DCollection which is robust for complex topologies
        # Simplification algorithms often destroy topology of flat, extruded shapes.

        # Use Poly3DCollection to avoid plot_trisurf artifacts ("random triangles")
        # on flat surfaces with holes.
        # Note: trimesh.Trimesh.triangles contains the (n, 3, 3) vertex data
        mesh_poly = Poly3DCollection(
            mesh_to_render.triangles, alpha=0.8, shade=True, facecolors=(0.2, 0.7, 0.8)
        )
        mesh_poly.set_edgecolor("none")
        ax.add_collection3d(mesh_poly)
        title = "STL Preview (Text side on top)"

        # Set labels and view
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_zlabel("Z (mm)")
        ax.set_title(title)

        # Set equal aspect ratio
        bounds_min = mesh_to_render.bounds[0]
        bounds_max = mesh_to_render.bounds[1]

        max_range = (bounds_max - bounds_min).max() / 2.0
        mid = (bounds_max + bounds_min) * 0.5

        ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
        ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
        ax.set_zlim(mid[2] - max_range, mid[2] + max_range)

        ax.view_init(elev=30, azim=45)

        # Save to buffer
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return buf.read()

    def on_preview_finished(self, image_data):
        """Handle preview generation success."""
        self.is_processing = False
        if image_data is None:
            self.preview_label.setText(
                "Preview failed: No geometry generated.\nCheck that your masks have content."
            )
            return

        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self.preview_label.setPixmap(
            pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def on_preview_error(self, error_msg):
        """Handle preview generation error."""
        self.is_processing = False
        self.preview_label.setText(f"Preview generation failed:\n{error_msg}")
        logger.error(f"Preview error: {error_msg}")

    def generate_stl(self):
        """Generate STL file."""
        # Pre-flight check: Warn if too many contours (noise)
        if self.profile_mask is not None:
            contours, _ = cv2.findContours(
                self.profile_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            count = len(contours)
            if count > 1000:
                reply = QMessageBox.question(
                    self,
                    "High Complexity Warning",
                    f"Detected {count} shapes/holes in the profile layer.\n\n"
                    "This usually indicates image noise (tiny specks). "
                    "Generating this model may take a very long time "
                    "and produce an unusable file.\n\n"
                    "Recommended: Cancel and adjust 'Profile Threshold' "
                    "or 'Blur' to reduce noise.\n\n"
                    "Do you want to proceed anyway?",
                )
                if reply == QMessageBox.StandardButton.No:
                    return

        # Ask for save location
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save STL File", "", "STL Files (*.stl);;All Files (*)"
        )

        if not save_path:
            return

        try:
            # Create STL generator
            stl_gen = STLGenerator(self.width_mm, self.height_mm)

            # Profile mask has holes as white, card as black
            # STL generator expects solid as white, holes as black
            # Therefore we need to INVERT the profile mask for STL generation
            inverted_profile = cv2.bitwise_not(self.profile_mask)

            thickness = self.thickness_input.value()
            separate_text = self.separate_text_check.isChecked()

            stl_gen.create_template_stl(
                inverted_profile,  # Inverted: solid card is white, holes are black
                self.text_mask,
                thickness,
                save_path,
                separate_text=separate_text,
            )

            QMessageBox.information(self, "Success", f"STL saved to:\n{save_path}")
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"STL generation failed: {str(e)}")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
