"""
UI Components Module for TracerTemplateMaker

This module contains reusable UI components:
- Image preview widgets with pan/zoom
- 3D model preview widgets
- Control panels with sliders
- File dialogs
"""

from PyQt6.QtWidgets import (QWidget, QLabel, QSlider, QPushButton, QVBoxLayout,
                             QHBoxLayout, QFileDialog, QGroupBox, QSpinBox,
                             QDoubleSpinBox, QColorDialog, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QWheelEvent, QMouseEvent, QCursor
import numpy as np
import cv2


class NoWheelSlider(QSlider):
    """QSlider that ignores mouse wheel events to prevent accidental adjustments during scrolling."""
    def wheelEvent(self, event):
        event.ignore()


class NoWheelSpinBox(QSpinBox):
    """QSpinBox that ignores mouse wheel events."""
    def wheelEvent(self, event):
        event.ignore()


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox that ignores mouse wheel events."""
    def wheelEvent(self, event):
        event.ignore()


class ImagePreviewWidget(QWidget):
    """
    Widget for displaying images with pan and zoom capabilities.
    """
    
    # Signal emitted when view changes (zoom, h_scroll, v_scroll)
    view_changed = pyqtSignal(float, int, int)

    def __init__(self, parent=None):
        """Initialize the image preview widget."""
        super().__init__(parent)

        self.image = None
        self.zoom_level = 1.0
        self.last_mouse_pos = None
        self.is_panning = False

        # Create scroll area for panning
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setMinimumSize(500, 500)  # Set minimum size on scroll area
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("border: 1px solid #ccc;")

        # Create label for image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        # Don't set minimum size - let it resize based on pixmap

        # Add label to scroll area
        self.scroll_area.setWidget(self.image_label)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        # Enable mouse tracking for panning
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mouse_press_event
        self.image_label.mouseMoveEvent = self.mouse_move_event
        self.image_label.mouseReleaseEvent = self.mouse_release_event
        self.scroll_area.wheelEvent = self.wheel_event

    def set_view(self, zoom: float, h_scroll: int, v_scroll: int):
        """
        Set view state programmatically.
        Does not emit view_changed to prevent loops.
        """
        update_needed = False
        if abs(self.zoom_level - zoom) > 0.001:
            self.zoom_level = zoom
            update_needed = True
        
        if update_needed:
            self.update_display()
            
        self.scroll_area.horizontalScrollBar().setValue(h_scroll)
        self.scroll_area.verticalScrollBar().setValue(v_scroll)

    def set_image(self, image: np.ndarray):
        """
        Set the image to display.

        Args:
            image: Image as numpy array (BGR format)
        """
        self.image = image.copy()
        self.update_display()

    def update_display(self):
        """Update the displayed image with current zoom and pan."""
        if self.image is None:
            return

        # Convert numpy array to QImage
        if len(self.image.shape) == 3:
            height, width, channel = self.image.shape
            bytes_per_line = 3 * width
            q_image = QImage(self.image.data, width, height, bytes_per_line,
                           QImage.Format.Format_RGB888).rgbSwapped()
        else:
            height, width = self.image.shape
            bytes_per_line = width
            q_image = QImage(self.image.data, width, height, bytes_per_line,
                           QImage.Format.Format_Grayscale8)

        # Apply zoom
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            int(pixmap.width() * self.zoom_level),
            int(pixmap.height() * self.zoom_level),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Set the pixmap and resize label to match
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())

    def mouse_press_event(self, event: QMouseEvent):
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = True
            self.last_mouse_pos = event.globalPosition().toPoint()
            # Change cursor to closed hand while dragging
            self.image_label.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouse_move_event(self, event: QMouseEvent):
        """Handle mouse move for panning."""
        if self.is_panning and self.last_mouse_pos:
            # Calculate how far the mouse has moved
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.last_mouse_pos

            # Move the scroll bars by the delta amount
            h_bar = self.scroll_area.horizontalScrollBar()
            v_bar = self.scroll_area.verticalScrollBar()

            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())

            self.last_mouse_pos = current_pos
            
            # Emit signal
            self.view_changed.emit(self.zoom_level, h_bar.value(), v_bar.value())
        else:
            # Show open hand cursor when hovering (ready to pan)
            if self.zoom_level > 1.0:
                self.image_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.image_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mouse_release_event(self, event: QMouseEvent):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False
            self.last_mouse_pos = None
            # Restore cursor
            if self.zoom_level > 1.0:
                self.image_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.image_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def wheel_event(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        # Get scroll delta
        delta = event.angleDelta().y()

        # Update zoom level
        zoom_factor = 1.1 if delta > 0 else 0.9
        self.zoom_level *= zoom_factor

        # Limit zoom range
        self.zoom_level = max(0.1, min(10.0, self.zoom_level))

        self.update_display()

        # Update cursor based on zoom level
        if self.zoom_level > 1.0:
            self.image_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        else:
            self.image_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            
        # Emit signal
        h_bar = self.scroll_area.horizontalScrollBar()
        v_bar = self.scroll_area.verticalScrollBar()
        self.view_changed.emit(self.zoom_level, h_bar.value(), v_bar.value())

    def reset_view(self):
        """Reset zoom and pan to default."""
        self.zoom_level = 1.0
        self.update_display()
        # Reset scroll bars to center
        h_bar = self.scroll_area.horizontalScrollBar()
        v_bar = self.scroll_area.verticalScrollBar()
        h_bar.setValue(0)
        v_bar.setValue(0)
        # Reset cursor
        self.image_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))


class ControlPanel(QWidget):
    """
    Control panel with sliders for image adjustment.
    """

    # Signals emitted when values change
    contrast_changed = pyqtSignal(float)
    brightness_changed = pyqtSignal(float)
    sharpness_changed = pyqtSignal(float)
    blur_changed = pyqtSignal(int)

    # Profile layer controls
    profile_threshold_changed = pyqtSignal(int)
    profile_tolerance_changed = pyqtSignal(int)
    profile_smoothing_changed = pyqtSignal(int)

    # Text layer controls
    text_threshold_changed = pyqtSignal(int)
    text_tolerance_changed = pyqtSignal(int)
    text_detail_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        """Initialize the control panel."""
        super().__init__(parent)

        # Initialize sliders dictionary BEFORE creating slider groups
        self.sliders = {}

        layout = QVBoxLayout()

        # Contrast control
        contrast_group = self.create_slider_group(
            "Contrast",
            0, 300, 100,
            self.on_contrast_changed
        )
        layout.addWidget(contrast_group)

        # Brightness control
        brightness_group = self.create_slider_group(
            "Brightness",
            0, 300, 100,
            self.on_brightness_changed
        )
        layout.addWidget(brightness_group)

        # Sharpness control
        sharpness_group = self.create_slider_group(
            "Sharpness",
            0, 300, 100,
            self.on_sharpness_changed
        )
        layout.addWidget(sharpness_group)

        # Blur control
        blur_group = self.create_slider_group(
            "Blur (Noise Reduction)",
            0, 15, 0,
            self.on_blur_changed
        )
        layout.addWidget(blur_group)

        # Separator
        layout.addWidget(QLabel("<b>--- Profile Layer (Holes) ---</b>"))

        # Profile Threshold control
        profile_threshold_group = self.create_slider_group(
            "Profile Threshold",
            0, 255, 200,  # Higher default for better hole detection
            self.on_profile_threshold_changed
        )
        layout.addWidget(profile_threshold_group)

        # Profile Color Tolerance
        profile_tolerance_group = self.create_slider_group(
            "Profile Color Tolerance",
            0, 100, 30,
            self.on_profile_tolerance_changed
        )
        layout.addWidget(profile_tolerance_group)

        # Profile Smoothing
        profile_smoothing_group = self.create_slider_group(
            "Profile Smoothing",
            0, 10, 5,
            self.on_profile_smoothing_changed
        )
        layout.addWidget(profile_smoothing_group)

        # Separator
        layout.addWidget(QLabel("<b>--- Text Layer (Markings) ---</b>"))

        # Text Threshold control
        text_threshold_group = self.create_slider_group(
            "Text Threshold",
            0, 255, 127,  # Standard middle value
            self.on_text_threshold_changed
        )
        layout.addWidget(text_threshold_group)

        # Text Color Tolerance
        text_tolerance_group = self.create_slider_group(
            "Text Color Tolerance",
            0, 100, 30,
            self.on_text_tolerance_changed
        )
        layout.addWidget(text_tolerance_group)

        # Text Detail Preservation
        text_detail_group = self.create_slider_group(
            "Text Detail Level",
            0, 10, 2,
            self.on_text_detail_changed
        )
        layout.addWidget(text_detail_group)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_values)
        layout.addWidget(reset_btn)

        layout.addStretch()
        self.setLayout(layout)

    def create_slider_group(self, label: str, min_val: int, max_val: int,
                           default: int, callback) -> QGroupBox:
        """
        Create a labeled slider group.

        Args:
            label: Label text
            min_val: Minimum value
            max_val: Maximum value
            default: Default value
            callback: Function to call when value changes

        Returns:
            QGroupBox: Group box containing slider
        """
        group = QGroupBox(label)
        layout = QHBoxLayout()

        # Create slider
        slider = NoWheelSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval((max_val - min_val) // 10)
        slider.setMinimumWidth(150)

        # Create value label
        value_label = QLabel(str(default))
        value_label.setMinimumWidth(50)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Connect slider to callback and label update
        def on_change(value):
            value_label.setText(str(value))
            callback(value)

        slider.valueChanged.connect(on_change)

        layout.addWidget(slider)
        layout.addWidget(value_label)
        group.setLayout(layout)
        group.setMinimumHeight(60)

        # Store slider
        self.sliders[label] = (slider, default)

        return group

    def on_contrast_changed(self, value: int):
        """Emit contrast changed signal."""
        self.contrast_changed.emit(value / 100.0)

    def on_brightness_changed(self, value: int):
        """Emit brightness changed signal."""
        self.brightness_changed.emit(value / 100.0)

    def on_sharpness_changed(self, value: int):
        """Emit sharpness changed signal."""
        self.sharpness_changed.emit(value / 100.0)

    def on_blur_changed(self, value: int):
        """Emit blur changed signal."""
        # Ensure odd number for kernel size
        kernel = value * 2 + 1 if value > 0 else 0
        self.blur_changed.emit(kernel)

    def on_profile_threshold_changed(self, value: int):
        """Emit profile threshold changed signal."""
        self.profile_threshold_changed.emit(value)

    def on_profile_tolerance_changed(self, value: int):
        """Emit profile color tolerance changed signal."""
        self.profile_tolerance_changed.emit(value)

    def on_profile_smoothing_changed(self, value: int):
        """Emit profile smoothing changed signal."""
        self.profile_smoothing_changed.emit(value)

    def on_text_threshold_changed(self, value: int):
        """Emit text threshold changed signal."""
        self.text_threshold_changed.emit(value)

    def on_text_tolerance_changed(self, value: int):
        """Emit text color tolerance changed signal."""
        self.text_tolerance_changed.emit(value)

    def on_text_detail_changed(self, value: int):
        """Emit text detail level changed signal."""
        self.text_detail_changed.emit(value)

    def set_values(self, values: dict):
        """
        Update all sliders with provided values.
        
        Args:
            values: Dictionary of {label: value}
        """
        for label, value in values.items():
            if label in self.sliders:
                slider, _ = self.sliders[label]
                slider.setValue(value)

    def reset_values(self):
        """Reset all sliders to default values."""
        for slider, default in self.sliders.values():
            slider.setValue(default)


class DimensionInputPanel(QWidget):
    """
    Panel for inputting physical dimensions.
    """

    dimensions_changed = pyqtSignal(float, float)

    def __init__(self, parent=None):
        """Initialize dimension input panel."""
        super().__init__(parent)

        layout = QVBoxLayout()

        # Title
        title = QLabel("Physical Dimensions")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Width input
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width (mm):"))
        self.width_input = NoWheelDoubleSpinBox()
        self.width_input.setRange(1.0, 1000.0)
        self.width_input.setValue(100.0)
        self.width_input.setDecimals(2)
        self.width_input.valueChanged.connect(self.emit_dimensions)
        width_layout.addWidget(self.width_input)
        layout.addLayout(width_layout)

        # Height input
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height (mm):"))
        self.height_input = NoWheelDoubleSpinBox()
        self.height_input.setRange(1.0, 1000.0)
        self.height_input.setValue(50.0)
        self.height_input.setDecimals(2)
        self.height_input.valueChanged.connect(self.emit_dimensions)
        height_layout.addWidget(self.height_input)
        layout.addLayout(height_layout)

        layout.addStretch()
        self.setLayout(layout)

    def emit_dimensions(self):
        """Emit dimension changed signal."""
        self.dimensions_changed.emit(
            self.width_input.value(),
            self.height_input.value()
        )

    def get_dimensions(self) -> tuple:
        """Get current dimensions."""
        return self.width_input.value(), self.height_input.value()


class ColorPickerPanel(QWidget):
    """
    Panel for selecting three colors: background/void, tracer card, and text/lines.
    """

    background_color_changed = pyqtSignal(tuple)  # Void/hole color
    tracer_color_changed = pyqtSignal(tuple)      # Card color
    text_color_changed = pyqtSignal(tuple)        # Text/line color
    eyedropper_requested = pyqtSignal(str)        # Request eyedropper for specific color

    def __init__(self, parent=None):
        """Initialize color picker panel."""
        super().__init__(parent)

        layout = QVBoxLayout()

        # Background/Void color (what shows through holes)
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background/Void:"))
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(50, 30)
        self.bg_color = (255, 255, 255)  # Default white (background) BGR
        self.update_button_color(self.bg_color_btn, self.bg_color)
        self.bg_color_btn.clicked.connect(self.pick_background_color)
        bg_layout.addWidget(self.bg_color_btn)
        # Add eyedropper button
        bg_eyedropper = QPushButton("👁")
        bg_eyedropper.setFixedSize(30, 30)
        bg_eyedropper.setToolTip("Pick color from image")
        bg_eyedropper.clicked.connect(lambda: self.eyedropper_requested.emit("background"))
        bg_layout.addWidget(bg_eyedropper)
        bg_layout.addStretch()
        layout.addLayout(bg_layout)

        # Tracer/Card color
        tracer_layout = QHBoxLayout()
        tracer_layout.addWidget(QLabel("Tracer Card:"))
        self.tracer_color_btn = QPushButton()
        self.tracer_color_btn.setFixedSize(50, 30)
        self.tracer_color = (0, 255, 255)  # Default yellow (BGR format)
        self.update_button_color(self.tracer_color_btn, (255, 255, 0))  # RGB for display
        self.tracer_color_btn.clicked.connect(self.pick_tracer_color)
        tracer_layout.addWidget(self.tracer_color_btn)
        # Add eyedropper button
        tracer_eyedropper = QPushButton("👁")
        tracer_eyedropper.setFixedSize(30, 30)
        tracer_eyedropper.setToolTip("Pick color from image")
        tracer_eyedropper.clicked.connect(lambda: self.eyedropper_requested.emit("tracer"))
        tracer_layout.addWidget(tracer_eyedropper)
        tracer_layout.addStretch()
        layout.addLayout(tracer_layout)

        # Text color
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text/Line:"))
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(50, 30)
        self.text_color = (0, 0, 0)  # Default black
        self.update_button_color(self.text_color_btn, self.text_color)
        self.text_color_btn.clicked.connect(self.pick_text_color)
        text_layout.addWidget(self.text_color_btn)
        # Add eyedropper button
        text_eyedropper = QPushButton("👁")
        text_eyedropper.setFixedSize(30, 30)
        text_eyedropper.setToolTip("Pick color from image")
        text_eyedropper.clicked.connect(lambda: self.eyedropper_requested.emit("text"))
        text_layout.addWidget(text_eyedropper)
        text_layout.addStretch()
        layout.addLayout(text_layout)

        layout.addStretch()
        self.setLayout(layout)

    def update_button_color(self, button: QPushButton, color: tuple):
        """Update button background color."""
        button.setStyleSheet(f"background-color: rgb{color};")

    def pick_background_color(self):
        """Open color picker for background/void."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color = (color.blue(), color.green(), color.red())  # BGR
            self.update_button_color(self.bg_color_btn,
                                    (color.red(), color.green(), color.blue()))
            self.background_color_changed.emit(self.bg_color)

    def pick_tracer_color(self):
        """Open color picker for tracer card."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.tracer_color = (color.blue(), color.green(), color.red())  # BGR
            self.update_button_color(self.tracer_color_btn,
                                    (color.red(), color.green(), color.blue()))
            self.tracer_color_changed.emit(self.tracer_color)

    def pick_text_color(self):
        """Open color picker for text."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color = (color.blue(), color.green(), color.red())  # BGR
            self.update_button_color(self.text_color_btn,
                                    (color.red(), color.green(), color.blue()))
            self.text_color_changed.emit(self.text_color)

    def get_colors(self) -> tuple:
        """Get current colors (background, tracer, text)."""
        return self.bg_color, self.tracer_color, self.text_color

    def set_color_from_pick(self, color_type: str, bgr_color: tuple):
        """
        Set color from eyedropper pick.

        Args:
            color_type: One of 'background', 'tracer', or 'text'
            bgr_color: Color in BGR format (B, G, R)
        """
        rgb_color = (bgr_color[2], bgr_color[1], bgr_color[0])  # Convert BGR to RGB for display

        if color_type == "background":
            self.bg_color = bgr_color
            self.update_button_color(self.bg_color_btn, rgb_color)
            self.background_color_changed.emit(bgr_color)
        elif color_type == "tracer":
            self.tracer_color = bgr_color
            self.update_button_color(self.tracer_color_btn, rgb_color)
            self.tracer_color_changed.emit(bgr_color)
        elif color_type == "text":
            self.text_color = bgr_color
            self.update_button_color(self.text_color_btn, rgb_color)
            self.text_color_changed.emit(bgr_color)
