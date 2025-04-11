import sys
import threading
import json
import webbrowser
import socket
import os
import subprocess
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtCore import QTimer, QSize

# Import necessary components (adjust paths/imports as needed)
from overlay import OverlayWidget
from server import start_server 
from state import StateManager 
from control_panel import ControlPanelWindow 

# --- Configuration ---
# Size of the overlay window (can be adjusted)
OVERLAY_WIDTH = 200
OVERLAY_HEIGHT = 200

# Flask server configuration (adjust as needed)
FLASK_HOST = '0.0.0.0' # Listen on all network interfaces
FLASK_PORT = 5000
LOCAL_WEB_UI_URL = f"http://127.0.0.1:{FLASK_PORT}" 
# --------------------

# --- Global Variables ---
# Keep references to prevent premature garbage collection
_tray_icon = None 
_tray_menu = None
_control_panel = None 
_app = None
_overlay_widget = None
# ----------------------

def get_local_ip():
    """Attempts to determine the host's primary local IP address."""
    s = None
    try:
        # Connect to an external host (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0) # Non-blocking
        # Use an address unlikely to be filtered/blocked locally
        s.connect(('10.255.255.255', 1)) 
        IP = s.getsockname()[0]
    except Exception as e:
        print(f"Warning: Could not determine local network IP: {e}")
        IP = None
    finally:
        if s: s.close()
    return IP

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_user_data_dir():
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

def create_tray_icon(app, network_url=None):
    """Creates and configures the system tray icon with proper styling."""
    global _tray_icon, _tray_menu
    
    # Look for custom icon in resources folder or use system icon as fallback
    icon_path = get_resource_path(os.path.join('resources', 'crosshair_icon.png'))
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
    else:
        # Fallback to system icon
        style = app.style()
        icon = QIcon(style.standardIcon(style.StandardPixmap.SP_ComputerIcon))
    
    _tray_icon = QSystemTrayIcon(icon, parent=app)
    _tray_icon.setToolTip("Crosshair Customizer")
    
    # Create Menu with modern styling
    _tray_menu = QMenu()
    _tray_menu.setStyleSheet("""
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 5px;
            padding: 5px;
        }
        QMenu::item {
            padding: 8px 25px 8px 10px;
            border-radius: 3px;
        }
        QMenu::item:selected {
            background-color: #5D5FEF;
            color: white;
        }
        QMenu::separator {
            height: 1px;
            background-color: #E0E0E0;
            margin: 5px 10px;
        }
    """)
    
    # Action: Show Control Panel
    show_panel_action = QAction("Show Control Panel", parent=app)
    show_panel_action.triggered.connect(show_control_panel)
    _tray_menu.addAction(show_panel_action)
    
    # Action: Toggle Crosshair Visibility
    toggle_crosshair_action = QAction("Toggle Crosshair", parent=app) 
    toggle_crosshair_action.triggered.connect(toggle_crosshair_visibility)
    _tray_menu.addAction(toggle_crosshair_action)
    
    # Action: Open Web UI
    open_action = QAction("Open Web Interface", parent=app)
    open_action.triggered.connect(open_web_ui)
    _tray_menu.addAction(open_action)
    
    # If network URL is available, add option to copy it
    if network_url:
        network_action = QAction(f"Network URL: {network_url}", parent=app)
        network_action.triggered.connect(lambda: copy_to_clipboard(network_url))
        _tray_menu.addAction(network_action)
    
    _tray_menu.addSeparator()
    
    # Action: Exit
    exit_action = QAction("Exit Application", parent=app)
    exit_action.triggered.connect(app.quit)
    _tray_menu.addAction(exit_action)
    
    # Set Menu and Show Icon
    _tray_icon.setContextMenu(_tray_menu)
    
    # Add double-click action to open control panel
    _tray_icon.activated.connect(handle_tray_activation)
    
    return _tray_icon

def handle_tray_activation(reason):
    """Handle tray icon activation (click, double-click)"""
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        show_control_panel()

def open_web_ui():
    """Opens the local web configuration interface in the default browser."""
    print(f"Opening web UI: {LOCAL_WEB_UI_URL}")
    webbrowser.open(LOCAL_WEB_UI_URL)

def toggle_crosshair_visibility():
    """Toggles the visibility of the crosshair overlay."""
    global _overlay_widget
    if _overlay_widget:
        if _overlay_widget.isVisible():
            _overlay_widget.hide()
        else:
            _overlay_widget.show()
        
        # Also update control panel button text if panel exists
        if _control_panel:
            _control_panel.update_toggle_button_text()

def show_control_panel():
    """Shows the control panel or brings it to the front if already visible."""
    if _control_panel:
        _control_panel.show()
        _control_panel.activateWindow() 
        _control_panel.raise_()

def check_firewall_status(port):
    """Check if Windows Firewall might be blocking the application and display guidance."""
    if sys.platform != 'win32':
        return # Only relevant for Windows
    
    try:
        # Try to check firewall status using netsh
        result = subprocess.run(
            ['netsh', 'advfirewall', 'show', 'currentprofile'], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            output = result.stdout
            if "State                                 ON" in output:
                print("Windows Firewall is enabled. May need to add an exception.")
                return True
        
        # Firewall is either off or we couldn't determine the status
        return False
    except Exception as e:
        print(f"Error checking firewall status: {e}")
        return False

def copy_to_clipboard(text):
    """Copy text to clipboard and show notification."""
    clipboard = QApplication.clipboard()
    clipboard.setText(text)
    
    if _tray_icon:
        _tray_icon.showMessage(
            "Copied to Clipboard",
            f"Network URL copied: {text}",
            QSystemTrayIcon.MessageIcon.Information,
            2000  # Show for 2 seconds
        )

def main():
    global _tray_icon, _tray_menu, _control_panel, _overlay_widget, _app
    _app = QApplication(sys.argv)
    _app.setQuitOnLastWindowClosed(False)  # Prevent app from exiting when windows are closed
    
    # Create user data directory
    user_data_dir = get_user_data_dir()
    os.makedirs(user_data_dir, exist_ok=True)
    
    # Create subdirectories for different types of data
    resources_dir = os.path.join(user_data_dir, 'resources')
    profiles_dir = os.path.join(user_data_dir, 'profiles')
    uploads_dir = os.path.join(user_data_dir, 'uploads')
    
    # Create all required directories
    for directory in [resources_dir, profiles_dir, uploads_dir]:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Determine Network IP for remote access
    network_ip = get_local_ip()
    network_web_ui_url = f"http://{network_ip}:{FLASK_PORT}" if network_ip else None

    # Initialize shared state
    state_manager = StateManager(user_data_dir)
    initial_settings = state_manager.get_settings()

    # Create the overlay widget
    _overlay_widget = OverlayWidget(state_manager)
    _overlay_widget.resize(OVERLAY_WIDTH, OVERLAY_HEIGHT)
    _overlay_widget.center_on_screen()
    
    # Convert initial settings to JSON string before passing
    initial_settings_json = json.dumps(initial_settings)
    _overlay_widget.update_crosshair(initial_settings_json) # Set initial state via JSON
    
    _overlay_widget.show()

    # Create and Show Control Panel
    _control_panel = ControlPanelWindow(
        local_url=LOCAL_WEB_UI_URL, 
        network_url=network_web_ui_url,
        overlay_widget=_overlay_widget
    )
    _control_panel.show()

    # Set up system tray if available
    if QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray available, creating icon...")
        _tray_icon = create_tray_icon(_app, network_web_ui_url)
        _tray_icon.show()
        
        # Show a notification when app starts
        _tray_icon.showMessage(
            "Crosshair Customizer",
            "Application is running. Click the tray icon to access controls.",
            QSystemTrayIcon.MessageIcon.Information,
            3000  # Show for 3 seconds
        )
        
        print("Tray icon created and shown.")
    else:
        print("Warning: System tray not available on this system.")

    # Start Flask Server in a Background Thread
    server_thread = threading.Thread(
        target=start_server, 
        args=(_control_panel, state_manager, _overlay_widget.update_crosshair, FLASK_PORT, user_data_dir, FLASK_HOST),
        daemon=True
    )
    server_thread.start()
    print(f"Flask server started in background thread on {FLASK_HOST}:{FLASK_PORT}")
    print(f"Web UI available at: {LOCAL_WEB_UI_URL}")
    
    # Check if network access is available
    if network_web_ui_url:
        print(f"Network access: {network_web_ui_url}")
        
        # Check for Windows Firewall
        if check_firewall_status(FLASK_PORT):
            firewall_message = (
                f"The application is listening for network connections on {network_web_ui_url}\n\n"
                f"However, Windows Firewall might be blocking incoming connections. If other devices "
                f"cannot connect, you may need to:\n\n"
                f"1. Allow this application through Windows Firewall\n"
                f"2. Make sure your device is on the same network\n"
                f"3. Check that no other security software is blocking port {FLASK_PORT}"
            )
            
            # Show firewall warning in a non-blocking way after a short delay
            QTimer.singleShot(5000, lambda: QMessageBox.information(
                _control_panel, 
                "Network Access Information", 
                firewall_message
            ))
    else:
        print("Network access: Not available (couldn't determine local IP)")

    # Start the Qt application event loop
    print("Starting Qt event loop...")
    sys.exit(_app.exec())

if __name__ == "__main__":
    main() 