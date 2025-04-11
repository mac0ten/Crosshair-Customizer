import sys
import webbrowser
import socket
import ipaddress
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QGroupBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor, QPalette

class CustomGroupBox(QGroupBox):
    """Custom QGroupBox with better title styling"""
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setObjectName("customGroupBox")
        self.title = title

class ControlPanelWindow(QWidget):
    """A modern window to show status and basic controls with styling that matches the web UI."""
    def __init__(self, local_url, network_url=None, overlay_widget=None):
        super().__init__()
        self.local_url = local_url
        self.network_url = self.validate_network_url(network_url)
        self.overlay_widget = overlay_widget # Keep a reference to the overlay
        self.settings = QSettings("CrosshairTool", "ControlPanel")
        self.is_dark_mode = self.settings.value("darkMode", "false") == "true"
        
        # Set up the UI
        self.init_ui()
        
        # Apply theme based on saved setting or default to system
        self.apply_theme(self.is_dark_mode)
        
    def validate_network_url(self, url):
        """Validate that the network URL contains a legitimate local network IP address, not a VPN IP."""
        if not url:
            return None
            
        # Extract IP address from the URL
        try:
            # Assumes URL format like http://192.168.1.100:5000
            parts = url.split('://')
            if len(parts) < 2:
                return None
                
            host_part = parts[1].split(':')[0]
            
            # Check if this is a valid IP address
            try:
                ip = ipaddress.ip_address(host_part)
                
                # Filter out VPN and non-local network IPs
                # Check if it's a private address (local network)
                if ip.is_private:
                    # Additional check for common VPN subnets
                    vpn_prefixes = [
                        '10.0.0.', '10.8.0.', '10.9.0.',  # Common OpenVPN
                        '172.16.', '172.17.',             # Docker and some VPNs
                        '192.168.122.'                     # Some virtual interfaces
                    ]
                    
                    is_vpn = False
                    for prefix in vpn_prefixes:
                        if str(ip).startswith(prefix):
                            is_vpn = True
                            break
                    
                    if not is_vpn:
                        # If it passes our checks, it's probably a valid local network IP
                        return url
                
                # If we're here, it's likely a public IP or VPN IP we want to exclude
                print(f"Network URL contains potential VPN or non-local IP: {host_part}")
                return None
                
            except ValueError:
                # Not a valid IP address
                return None
                
        except Exception as e:
            print(f"Error validating network URL: {e}")
            return None
            
        return url
        
    def init_ui(self):
        self.setWindowTitle("Crosshair Control Panel")
        self.setMinimumWidth(480)
        self.setMinimumHeight(600)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create header
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # App title
        title = QLabel("Crosshair Customizer")
        title.setObjectName("appTitle")
        header_layout.addWidget(title)
        
        # Theme toggle
        self.theme_toggle_btn = QPushButton("Dark Mode")
        self.theme_toggle_btn.setObjectName("themeToggleBtn")
        self.theme_toggle_btn.setCheckable(True)
        self.theme_toggle_btn.setChecked(self.is_dark_mode)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_toggle_btn)
        
        main_layout.addWidget(header)
        
        # Instructions section
        instruction_section = QLabel("Getting Started")
        instruction_section.setObjectName("sectionTitle")
        main_layout.addWidget(instruction_section)
        
        instruction_box = QFrame()
        instruction_box.setObjectName("instructionBox")
        instruction_layout = QVBoxLayout(instruction_box)
        instruction_layout.setContentsMargins(10, 10, 10, 10)
        instruction_layout.setSpacing(8)
        
        # Scrollable instruction area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setObjectName("instructionScroll")
        
        instruction_content = QWidget()
        instruction_content.setObjectName("instructionContent")
        instruction_content_layout = QVBoxLayout(instruction_content)
        instruction_content_layout.setContentsMargins(0, 0, 0, 0)
        instruction_content_layout.setSpacing(2)
        
        instructions = [
            "<b>1.</b> Use the buttons below to show/hide the crosshair or open the web interface",
            "<b>2.</b> In the web interface, customize your crosshair's appearance",
            "<b>3.</b> Your changes apply in real-time to the crosshair overlay",
            "<b>4.</b> Create and save profiles for different games or preferences",
            "<b>5.</b> The app will continue running in the system tray when you close this window"
        ]
        
        for i, instruction in enumerate(instructions):
            instruction_frame = QFrame()
            instruction_frame.setObjectName(f"instruction{i+1}")
            instruction_layout_frame = QVBoxLayout(instruction_frame)
            instruction_layout_frame.setContentsMargins(10, 10, 10, 10)
            
            instruction_label = QLabel(instruction)
            instruction_label.setWordWrap(True)
            instruction_label.setObjectName("instructionText")
            instruction_layout_frame.addWidget(instruction_label)
            
            instruction_content_layout.addWidget(instruction_frame)
            
            # Add some spacing between instruction items
            if i < len(instructions) - 1:
                instruction_content_layout.addSpacing(5)
        
        scroll_area.setWidget(instruction_content)
        instruction_layout.addWidget(scroll_area)
        main_layout.addWidget(instruction_box)
        
        # Position Adjustment Instructions Section
        position_section = QLabel("Adjust Crosshair Position")
        position_section.setObjectName("sectionTitle")
        main_layout.addWidget(position_section)
        
        position_box = QFrame()
        position_box.setObjectName("positionBox")
        position_layout = QVBoxLayout(position_box)
        position_layout.setContentsMargins(10, 10, 10, 10)
        position_layout.setSpacing(5)
        
        position_instruction = QLabel(
            "You can move the crosshair overlay in two ways:\n"
            "? <b>Click and drag</b> the crosshair overlay window itself.\n"
            "? Use <b>Ctrl + Alt + Arrow Keys</b> to nudge the position by 1 pixel.\n\n"
            "The position is saved automatically."
        )
        position_instruction.setWordWrap(True)
        position_instruction.setObjectName("positionInstructionText")
        position_instruction.setTextFormat(Qt.TextFormat.RichText)
        position_layout.addWidget(position_instruction)
        main_layout.addWidget(position_box)
        
        # Access URLs section
        url_section = QLabel("Access Web Interface")
        url_section.setObjectName("sectionTitle")
        main_layout.addWidget(url_section)
        
        url_box = QFrame()
        url_box.setObjectName("urlBox")
        url_layout = QVBoxLayout(url_box)
        url_layout.setContentsMargins(10, 10, 10, 10)
        url_layout.setSpacing(8)
        
        # Local URL Label
        local_frame = QFrame()
        local_frame.setObjectName("localUrlFrame")
        local_frame_layout = QVBoxLayout(local_frame)
        local_frame_layout.setContentsMargins(10, 10, 10, 5)
        
        local_label = QLabel("Local Access:")
        local_label.setObjectName("urlLabel")
        local_frame_layout.addWidget(local_label)
        
        local_url_label = QLabel(f"<a href=\"{self.local_url}\">{self.local_url}</a>")
        local_url_label.setObjectName("urlValue")
        local_url_label.setTextFormat(Qt.TextFormat.RichText)
        local_url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        local_url_label.setOpenExternalLinks(True)
        local_frame_layout.addWidget(local_url_label)
        
        url_layout.addWidget(local_frame)
        
        # Network URL Label (if found)
        if self.network_url:
            network_frame = QFrame()
            network_frame.setObjectName("networkUrlFrame")
            network_frame_layout = QVBoxLayout(network_frame)
            network_frame_layout.setContentsMargins(10, 5, 10, 10)
            
            network_label = QLabel("Network Access (other devices on same WiFi):")
            network_label.setObjectName("urlLabel")
            network_frame_layout.addWidget(network_label)
            
            network_url_label = QLabel(f"<a href=\"{self.network_url}\">{self.network_url}</a>")
            network_url_label.setObjectName("urlValue")
            network_url_label.setTextFormat(Qt.TextFormat.RichText)
            network_url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            network_url_label.setOpenExternalLinks(True)
            network_frame_layout.addWidget(network_url_label)
            
            url_layout.addWidget(network_frame)
        else:
            network_frame = QFrame()
            network_frame.setObjectName("networkUrlFrame")
            network_frame_layout = QVBoxLayout(network_frame)
            network_frame_layout.setContentsMargins(10, 5, 10, 10)
            
            network_label = QLabel("Network Access:")
            network_label.setObjectName("urlLabel")
            network_frame_layout.addWidget(network_label)
            
            network_status = QLabel("(Could not determine IP)")
            network_status.setObjectName("urlValueDisabled")
            network_frame_layout.addWidget(network_status)
            
            url_layout.addWidget(network_frame)
        
        main_layout.addWidget(url_box)
        
        # Control buttons section
        controls_section = QLabel("Controls")
        controls_section.setObjectName("sectionTitle")
        main_layout.addWidget(controls_section)
        
        button_box = QFrame()
        button_box.setObjectName("controlBox")
        button_layout = QHBoxLayout(button_box)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(10)
        
        # Create buttons with modern styling
        self.open_button = QPushButton("Open Web Interface")
        self.open_button.setObjectName("primaryButton")
        self.open_button.clicked.connect(self.open_local_web_ui_browser)
        self.open_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.open_button.setMinimumHeight(40)
        
        self.toggle_overlay_button = QPushButton("Hide Crosshair")
        self.toggle_overlay_button.setObjectName("secondaryButton")
        if self.overlay_widget:
            self.toggle_overlay_button.clicked.connect(self.toggle_overlay_visibility)
            self.update_toggle_button_text()
        else:
            self.toggle_overlay_button.setDisabled(True)
        self.toggle_overlay_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toggle_overlay_button.setMinimumHeight(40)
        
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.toggle_overlay_button)
        
        main_layout.addWidget(button_box)
        
        # Add a note about the system tray
        tray_note = QLabel("Note: This app will continue running in your system tray when closed.")
        tray_note.setObjectName("trayNote")
        tray_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(tray_note)
        
        self.setLayout(main_layout)
        
    def toggle_theme(self, checked):
        self.is_dark_mode = checked
        self.apply_theme(checked)
        self.settings.setValue("darkMode", "true" if checked else "false")
        
    def apply_theme(self, is_dark):
        if is_dark:
            # Dark theme colors
            bg_color = "#121212"
            card_bg = "#1e1e1e"
            content_bg = "#252525"
            text_color = "#e9ecef"
            primary_color = "#6D6FFF"
            secondary_color = "#5658DF"
            border_color = "#2d2d2d"
            muted_color = "#a5a5a5"
            link_color = "#6D9EFF"
            toggle_text = "Light Mode"
        else:
            # Light theme colors
            bg_color = "#f8f9fa"
            card_bg = "#ffffff"
            content_bg = "#f3f4f6"
            text_color = "#212529"
            primary_color = "#5D5FEF"
            secondary_color = "#4648c9"
            border_color = "#dee2e6"
            muted_color = "#6c757d"
            link_color = "#0d6efd"
            toggle_text = "Dark Mode"
        
        # Update the toggle button text
        self.theme_toggle_btn.setText(toggle_text)
        
        # Apply theme to the window
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 13px;
            }}
            
            #header {{
                background-color: {primary_color};
                border-radius: 8px;
            }}
            
            #appTitle {{
                color: white;
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
            }}
            
            #themeToggleBtn {{
                background-color: {'#2d2d2d' if is_dark else 'rgba(255, 255, 255, 0.2)'};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: 500;
            }}
            
            #themeToggleBtn:hover {{
                background-color: {'#3d3d3d' if is_dark else 'rgba(255, 255, 255, 0.3)'};
            }}
            
            #sectionTitle {{
                color: {primary_color};
                font-size: 16px;
                font-weight: bold;
                padding: 0 15px;
                text-shadow: 0px 1px 2px {'rgba(0,0,0,0.3)' if is_dark else 'rgba(0,0,0,0.1)'};
                border-radius: 4px;
                display: inline-block;
            }}
            
            #instructionBox, #urlBox, #controlBox {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 8px;
                margin-top: 5px;
            }}
            
            #instruction1, #instruction2, #instruction3, #instruction4, #instruction5 {{
                background-color: {content_bg};
                border-radius: 6px;
            }}
            
            #instructionText {{
                background-color: transparent;
            }}
            
            #localUrlFrame, #networkUrlFrame {{
                background-color: {content_bg};
                border-radius: 6px;
            }}
            
            #urlLabel {{
                color: {text_color};
                font-weight: 500;
                background-color: transparent;
            }}
            
            #urlValue {{
                color: {link_color};
                background-color: transparent;
            }}
            
            #urlValueDisabled {{
                color: {muted_color};
                background-color: transparent;
                font-style: italic;
            }}
            
            a {{
                color: {link_color};
                text-decoration: none;
            }}
            
            a:hover {{
                text-decoration: underline;
            }}
            
            #primaryButton {{
                background-color: {primary_color};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            
            #primaryButton:hover {{
                background-color: {secondary_color};
            }}
            
            #secondaryButton {{
                background-color: {"#2d2d2d" if is_dark else "#e9ecef"};
                color: {text_color};
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            
            #secondaryButton:hover {{
                background-color: {"#3d3d3d" if is_dark else "#dee2e6"};
            }}
            
            #trayNote {{
                color: {muted_color};
                font-style: italic;
                font-size: 12px;
                background-color: transparent;
                margin-top: 10px;
            }}
            
            QScrollArea, QScrollArea > QWidget > QWidget {{
                background-color: transparent;
                border: none;
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: {"#2d2d2d" if is_dark else "#f8f9fa"};
                width: 8px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {"#4d4d4d" if is_dark else "#ced4da"};
                min-height: 20px;
                border-radius: 4px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            #positionBox {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 8px;
                margin-top: 5px;
            }}
            
            #positionInstructionText {{
                background-color: transparent;
                color: {text_color};
            }}
        """)
        
    def open_local_web_ui_browser(self):
        webbrowser.open(self.local_url)

    def toggle_overlay_visibility(self):
        if self.overlay_widget:
            if self.overlay_widget.isVisible():
                self.overlay_widget.hide()
            else:
                self.overlay_widget.show()
            self.update_toggle_button_text()

    def update_toggle_button_text(self):
        if self.overlay_widget and self.overlay_widget.isVisible():
            self.toggle_overlay_button.setText("Hide Crosshair")
        else:
             self.toggle_overlay_button.setText("Show Crosshair")

    def closeEvent(self, event):
        """Override close event to just hide the window instead of closing."""
        event.ignore() # Don't accept the close event
        self.hide()    # Hide the window
        print("Control Panel hidden. Can be reopened from tray menu.")

# Example Usage (for testing this window directly)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Dummy overlay for testing toggle
    class DummyOverlay(QWidget):
         def __init__(self):
              super().__init__()
              self.label = QLabel("Dummy Overlay", self)
              self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
              self.layout = QVBoxLayout(self)
              self.layout.addWidget(self.label)
              self.setStyleSheet("background-color: rgba(255, 0, 0, 100);")
              self.setWindowTitle("Dummy Overlay")
              
    dummy = DummyOverlay()
    dummy.show()
              
    panel = ControlPanelWindow(
        local_url="http://127.0.0.1:5000", 
        network_url="http://192.168.1.100:5000", # Example network URL
        overlay_widget=dummy
    )
    panel.show()
    sys.exit(app.exec()) 