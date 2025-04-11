import sys
import os # Added os
import json # Added json
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, Signal, QPoint, QRectF, QRect, Slot, QSize, QTimer # Added QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap, QMovie, QCursor, QMouseEvent, QKeyEvent # Added QCursor, QMouseEvent, QKeyEvent

# Amount to move the overlay per key press
NUDGE_AMOUNT = 1

class OverlayWidget(QWidget):
    # Signal to indicate settings have changed and repaint is needed
    settings_updated = Signal()
    position_changed = Signal(int, int) # Signal emitted when position is changed by user

    def __init__(self, state_manager):
        super().__init__()
        self.state_manager = state_manager
        self._mouse_press_pos = None
        self._mouse_move_pos = None
        self._show_bounding_box = False # Renamed flag
        self._nudge_box_timer = QTimer(self) # Timer for nudge feedback
        self._nudge_box_timer.setSingleShot(True)
        self._nudge_box_timer.setInterval(400) # Show box for 400ms after nudge
        self._nudge_box_timer.timeout.connect(self._hide_bounding_box)
        
        # Basic window setup
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) # REMOVE this line
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool # Prevents appearing in taskbar/alt-tab
        )
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor)) # Indicate movability
        
        # Load initial state
        self.settings = {} # Will be loaded via update_crosshair
        self.static_pixmap = None
        self.animated_movie = None
        self._load_initial_position()

    def _load_initial_position(self):
        """Load saved overlay position from state manager or center if none saved."""
        app_config = self.state_manager.get_app_config()
        print(f"Overlay [LoadPos]: Read app_config: {app_config}")
        x = app_config.get('overlay_x')
        y = app_config.get('overlay_y')
        print(f"Overlay [LoadPos]: Got x={x}, y={y}")
        
        if x is not None and y is not None:
            # Schedule the move to happen slightly after initialization
            print(f"Overlay [LoadPos]: Scheduling move to ({x}, {y})")
            QTimer.singleShot(0, lambda: self._apply_initial_position(x, y))
        else:
            print("Overlay [LoadPos]: No saved position found or values are None, centering on screen.")
            self.center_on_screen()

    def _apply_initial_position(self, x, y):
        """Applies the loaded position, called via QTimer."""
        print(f"Overlay [ApplyPos]: Applying position ({x}, {y})")
        self.move(x, y)
        print(f"Overlay [ApplyPos]: Position after scheduled move() call: {self.pos().x()}, {self.pos().y()}")

    def mousePressEvent(self, event: QMouseEvent):
        """Capture initial mouse position for dragging and set dragging flag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_press_pos = event.globalPosition().toPoint()
            self._show_bounding_box = True
            if self._nudge_box_timer.isActive(): # Stop nudge timer if dragging starts
                self._nudge_box_timer.stop()
            self.update() # Trigger repaint to show bounding box
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Move the window based on mouse drag."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._mouse_press_pos:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self._mouse_press_pos
            self.move(self.pos() + delta)
            self._mouse_press_pos = current_pos # Update press position for next move event
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Save the new position when dragging stops and clear dragging flag."""
        if event.button() == Qt.MouseButton.LeftButton and self._mouse_press_pos:
            self._mouse_press_pos = None
            self._show_bounding_box = False
            if self._nudge_box_timer.isActive(): # Ensure nudge timer is stopped
                self._nudge_box_timer.stop()
            self.update() # Trigger repaint to hide bounding box
            new_pos = self.pos()
            print(f"Overlay: Position changed to ({new_pos.x()}, {new_pos.y()}). Saving...")
            self.state_manager.update_app_config('overlay_x', new_pos.x())
            self.state_manager.update_app_config('overlay_y', new_pos.y())
            self.position_changed.emit(new_pos.x(), new_pos.y())
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key presses for nudging the overlay position."""
        modifiers = event.modifiers()
        key = event.key()

        # Check for Ctrl + Alt modifiers
        if modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
            current_pos = self.pos()
            new_x, new_y = current_pos.x(), current_pos.y()
            moved = False

            if key == Qt.Key.Key_Up:
                new_y -= NUDGE_AMOUNT
                moved = True
            elif key == Qt.Key.Key_Down:
                new_y += NUDGE_AMOUNT
                moved = True
            elif key == Qt.Key.Key_Left:
                new_x -= NUDGE_AMOUNT
                moved = True
            elif key == Qt.Key.Key_Right:
                new_x += NUDGE_AMOUNT
                moved = True

            if moved:
                print(f"Overlay: Nudging position to ({new_x}, {new_y})")
                self.move(new_x, new_y)
                # Save the new position immediately
                self.state_manager.update_app_config('overlay_x', new_x)
                self.state_manager.update_app_config('overlay_y', new_y)
                self.position_changed.emit(new_x, new_y) # Emit signal if needed elsewhere
                
                # Show bounding box and start timer
                self._show_bounding_box = True
                self.update()
                self._nudge_box_timer.start() # Start/restart the timer
                
                event.accept()
                return # Event handled

        # If not handled, pass to base class
        super().keyPressEvent(event)

    def _get_color(self, hex_color, opacity):
        """Helper to create QColor from hex string and opacity (0-255)."""
        color = QColor(hex_color)
        color.setAlpha(opacity)
        return color

    @Slot()
    def _on_frame_changed(self):
        """Slot connected to QMovie's frameChanged signal."""
        print(f"_on_frame_changed: Frame {self.animated_movie.currentFrameNumber()}")
        self.update() # Trigger a repaint

    def paintEvent(self, event):
        """Handles drawing the crosshair and the temporary bounding box."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get center point
        center_x = self.width() // 2
        center_y = self.height() // 2
        center = QPoint(center_x, center_y)
        
        # --- Draw Crosshair --- 
        crosshair_type = self.settings.get('type', 'parametric')
        if not self.settings: # Don't draw if settings not loaded
            return

        # --- Parametric Drawing --- 
        if crosshair_type == 'parametric':
            params = self.settings.get('parametric', {})
            if not params: return # Ensure params exist
            # (Parametric drawing code as before...)
            # Outline settings
            outline_enabled = params.get('outline_enabled', False)
            outline_thickness = params.get('outline_thickness', 1)
            outline_color = self._get_color(params.get('outline_color', '#000000'), params.get('outline_opacity', 150))
            # --- Draw Outline ---
            if outline_enabled and outline_thickness > 0:
                outline_pen = QPen(outline_color, outline_thickness * 2 + 1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap)
                painter.setPen(outline_pen)
                self._draw_parametric_lines(painter, center, params, is_outline=True, outline_thickness=outline_thickness)
            # --- Draw Main Crosshair ---
            painter.setPen(Qt.PenStyle.NoPen)
            # Center Dot
            if params.get('center_dot_enabled', False):
                dot_size = params.get('center_dot_size', 3)
                dot_color = self._get_color(params.get('center_dot_color', '#FF0000'), params.get('center_dot_opacity', 200))
                painter.setBrush(dot_color)
                painter.drawEllipse(center, dot_size, dot_size)
            # Inner Lines
            painter.setBrush(Qt.BrushStyle.NoBrush)
            self._draw_parametric_lines(painter, center, params, is_outline=False)
            # Outer Lines (TODO)

        # --- Static Image Drawing --- 
        elif crosshair_type == 'static':
            static_params = self.settings.get('static', {})
            if self.static_pixmap and not self.static_pixmap.isNull():
                scale = static_params.get('scale', 1.0)
                opacity = static_params.get('opacity', 255) / 255.0 # QPainter opacity is 0.0-1.0

                w = int(self.static_pixmap.width() * scale)
                h = int(self.static_pixmap.height() * scale)
                x = center_x - w // 2
                y = center_y - h // 2

                painter.setOpacity(opacity)
                painter.drawPixmap(x, y, w, h, self.static_pixmap)
                painter.setOpacity(1.0) # Reset opacity
            else:
                # Optional: Draw an indicator if image failed to load
                painter.setPen(QPen(QColor("red"), 2))
                painter.drawLine(center_x - 5, center_y - 5, center_x + 5, center_y + 5)
                painter.drawLine(center_x - 5, center_y + 5, center_x + 5, center_y - 5)

        # --- Animated GIF Drawing --- 
        elif crosshair_type == 'animated':
            anim_params = self.settings.get('animated', {})
            if self.animated_movie and self.animated_movie.isValid():
                # Debug: Print frame number being drawn
                # print(f"paintEvent: Drawing frame {self.animated_movie.currentFrameNumber()}") 
                pixmap = self.animated_movie.currentPixmap()
                if not pixmap.isNull():
                    scale = anim_params.get('scale', 1.0)
                    opacity = anim_params.get('opacity', 255) / 255.0
                    w = int(pixmap.width() * scale)
                    h = int(pixmap.height() * scale)
                    x = center_x - w // 2
                    y = center_y - h // 2
                    painter.setOpacity(opacity)
                    painter.drawPixmap(x, y, w, h, pixmap)
                    painter.setOpacity(1.0)
                else: 
                    self._draw_placeholder_error(painter, center)
            else:
                # Draw indicator if movie failed to load or isn't set
                 self._draw_placeholder_error(painter, center, QColor("lime")) # Lime X for unloaded GIF

        # --- Draw Bounding Box if Dragging --- 
        if self._show_bounding_box:
            painter.setPen(QPen(QColor(0, 150, 255, 180), 1, Qt.PenStyle.SolidLine)) # Light blue, semi-transparent
            painter.setBrush(Qt.BrushStyle.NoBrush) # No fill
            # Draw rectangle slightly inset from the edges
            rect = self.rect().adjusted(0, 0, -1, -1) # Adjust for pen width
            painter.drawRect(rect)

    def _draw_placeholder_error(self, painter, center, color=QColor("red")):
        """Draws a colored X."""
        painter.setPen(QPen(color, 2))
        painter.drawLine(center.x() - 5, center.y() - 5, center.x() + 5, center.y() + 5)
        painter.drawLine(center.x() - 5, center.y() + 5, center.x() + 5, center.y() - 5)

    def _draw_parametric_lines(self, painter, center, params, is_outline=False, outline_thickness=0, use_outer=False):
        """Helper function to draw inner or outer lines (and optionally their outlines)."""
        line_prefix = 'outer_' if use_outer else 'inner_'
        enabled = params.get(f'{line_prefix}lines_enabled', False)
        if not enabled and not is_outline: # If drawing main lines and they're disabled, exit
             return
        if is_outline and not params.get('inner_lines_enabled', False) and not params.get('outer_lines_enabled', False):
             return # If drawing outline but no lines are enabled, exit

        # Use inner line settings if drawing outline and outer lines are disabled or not requested
        if is_outline and (not use_outer or not params.get('outer_lines_enabled')): 
            line_prefix = 'inner_'
        # Also check if inner lines are actually enabled when drawing outline
        if is_outline and line_prefix == 'inner_' and not params.get('inner_lines_enabled'):
             return
        # Similarly for outer lines
        if is_outline and line_prefix == 'outer_' and not params.get('outer_lines_enabled'):
             return

        color_hex = params.get(f'{line_prefix}lines_color', '#FFFFFF')
        thickness = params.get(f'{line_prefix}lines_thickness', 1)
        length = params.get(f'{line_prefix}lines_length', 5)
        gap = params.get(f'{line_prefix}lines_gap', 3)
        opacity = params.get(f'{line_prefix}lines_opacity', 255)
        t_shape = params.get('t_shape', False)

        if not is_outline:
            if thickness <= 0 or length <= 0: return # Don't draw invisible/zero-length lines
            color = self._get_color(color_hex, opacity)
            pen = QPen(color, thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap) # FlatCap looks better for adjacent lines
            painter.setPen(pen)
        # else: pen is already set for outline drawing

        # Calculate line coordinates
        gap_offset = gap + (params.get('center_dot_size', 0) if params.get('center_dot_enabled') else 0)
        
        # Adjust gap and length for outline drawing
        if is_outline:
             effective_thickness = thickness + outline_thickness * 2
             gap_offset -= outline_thickness 
             length += outline_thickness # Extend length slightly for outline
             thickness = effective_thickness # Use combined thickness for outline pen already set

        if gap_offset < 0 : gap_offset = 0 # Prevent negative gap

        p1_top = QPoint(center.x(), center.y() - gap_offset)
        p2_top = QPoint(center.x(), center.y() - gap_offset - length)
        p1_bottom = QPoint(center.x(), center.y() + gap_offset)
        p2_bottom = QPoint(center.x(), center.y() + gap_offset + length)
        p1_left = QPoint(center.x() - gap_offset, center.y())
        p2_left = QPoint(center.x() - gap_offset - length, center.y())
        p1_right = QPoint(center.x() + gap_offset, center.y())
        p2_right = QPoint(center.x() + gap_offset + length, center.y())

        # Draw lines
        if not (t_shape and not is_outline): # Don't draw top line in T-Shape mode (unless it's the outline)
             if p1_top.y() > p2_top.y(): # Ensure positive length
                 painter.drawLine(p1_top, p2_top)
        if p1_bottom.y() < p2_bottom.y():
             painter.drawLine(p1_bottom, p2_bottom)
        if p1_left.x() > p2_left.x():
             painter.drawLine(p1_left, p2_left)
        if p1_right.x() < p2_right.x():
             painter.drawLine(p1_right, p2_right)

    @Slot(str)
    def update_crosshair(self, new_settings_json: str):
        """Updates the internal settings (from JSON string), loads resources, and triggers repaint."""
        try:
            # Parse the JSON string back into a dictionary
            new_settings = json.loads(new_settings_json)
            # Basic check if it's a dictionary after parsing
            if not isinstance(new_settings, dict):
                 print("Overlay Error: Received settings are not a valid dictionary after JSON parsing.")
                 return

        except json.JSONDecodeError as e:
            print(f"Overlay Error: Failed to parse settings JSON: {e}")
            return

        print(f"Overlay: Received settings update via JSON: {new_settings}") # Debug
        self.settings = new_settings

        # --- Clear previous resources --- 
        self.static_pixmap = None
        if self.animated_movie:
            self.animated_movie.stop()
            try: 
                self.animated_movie.frameChanged.disconnect(self._on_frame_changed)
            except RuntimeError: pass 
            self.animated_movie = None

        # --- Load new resources based on type --- 
        crosshair_type = self.settings.get('type')

        if crosshair_type == 'static':
            static_params = self.settings.get('static', {})
            image_name = static_params.get('image_path')
            if image_name:
                # Get user data directory
                user_data_dir = self._get_user_data_dir()
                full_path = os.path.join(user_data_dir, 'uploads', image_name)
                print(f"Overlay: Attempting to load static image: {full_path}")
                pixmap = QPixmap(full_path)
                if pixmap.isNull():
                    print(f"Overlay: Error loading static image at {full_path}")
                    self.static_pixmap = None
                else:
                    print(f"Overlay: Static image loaded successfully from {full_path}")
                    self.static_pixmap = pixmap
            else:
                self.static_pixmap = None

        elif crosshair_type == 'animated':
            anim_params = self.settings.get('animated', {})
            gif_name = anim_params.get('gif_path')
            if gif_name:
                # Get user data directory
                user_data_dir = self._get_user_data_dir()
                full_path = os.path.join(user_data_dir, 'uploads', gif_name)
                print(f"Overlay: Attempting to load animated GIF: {full_path}")
                movie = QMovie(full_path)
                if not movie.isValid():
                    print(f"Overlay: Error loading or invalid GIF format at {full_path}")
                    self.animated_movie = None
                else:
                    print(f"Overlay: Animated GIF loaded successfully from {full_path}")
                    self.animated_movie = movie
                    self.animated_movie.setCacheMode(QMovie.CacheMode.CacheAll)
                    speed = anim_params.get('speed', 100)
                    self.animated_movie.setSpeed(speed)
                    self.animated_movie.frameChanged.connect(self._on_frame_changed)
                    self.animated_movie.start()
                    print(f"Overlay: Started GIF animation with speed: {speed}")
            else:
                 self.animated_movie = None

        self.update() # Request repaint

    def _get_user_data_dir(self):
        """Get the platform-specific user data directory."""
        app_name = "CrosshairTool"
        if sys.platform == 'win32':
            # On Windows, use %APPDATA%\CrosshairTool
            return os.path.join(os.environ['APPDATA'], app_name)
        elif sys.platform == 'darwin':
            # On macOS, use ~/Library/Application Support/CrosshairTool
            return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
        else:
            # On Linux, use ~/.local/share/CrosshairTool
            return os.path.join(os.path.expanduser('~'), '.local', 'share', app_name)

    def center_on_screen(self):
        """Centers the widget on the primary screen."""
        if screen_geometry := QApplication.primaryScreen().availableGeometry():
            self.setGeometry(
                screen_geometry.center().x() - self.width() // 2,
                screen_geometry.center().y() - self.height() // 2,
                self.width(),
                self.height()
            )
        else:
            print("Warning: Could not get screen geometry to center window.")

    def _hide_bounding_box(self):
        """Slot connected to _nudge_box_timer timeout."""
        self._show_bounding_box = False
        self.update() # Trigger a repaint

# Example usage (for testing this file directly)
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- Test Settings (Parametric) ---
    # test_settings = {
    #     "type": "parametric",
    #     "parametric": { ... } # (settings from previous version) 
    # }

    # --- Test Settings (Static - uncomment and ensure image exists) ---
    # Ensure you have an image named 'test_crosshair.png' in the 'user_uploads' directory
    # test_settings = {
    #     "type": "static",
    #     "static": {
    #         "image_path": "test_crosshair.png",
    #         "opacity": 200,
    #         "scale": 1.5
    #     }
    # }

    # --- Test Settings (Animated) ---
    # Ensure you have 'test_anim.gif' in 'user_uploads'
    # test_settings = {
    #     "type": "animated",
    #     "parametric": { ... },
    #     "static": { ... },
    #     "animated": { "gif_path": "test_anim.gif", "opacity": 255, "scale": 1.0, "speed": 100 }
    # }

    # --- Default Test (Parametric) --- 
    test_settings = {
        "type": "parametric",
        "parametric": {
            "center_dot_enabled": True,
            "center_dot_color": "#FFFF00", "center_dot_size": 4, "center_dot_opacity": 255,
            "inner_lines_enabled": True,
            "inner_lines_color": "#FFFFFF", "inner_lines_thickness": 2, "inner_lines_length": 8, "inner_lines_gap": 5, "inner_lines_opacity": 255,
            "outer_lines_enabled": False,
            "outline_enabled": True,
            "outline_color": "#000000", "outline_thickness": 1, "outline_opacity": 200,
            "t_shape": False
        },
         "static": { "image_path": None, "opacity": 255, "scale": 1.0 }, # Need default structs
         "animated": { "gif_path": None, "opacity": 255, "scale": 1.0, "speed": 100 }
    }

    overlay = OverlayWidget()
    overlay.resize(200, 200) # Window size - crosshair is drawn relative to center
    overlay.center_on_screen()
    overlay.update_crosshair(json.dumps(test_settings)) # Load test settings
    overlay.show()
    sys.exit(app.exec()) 