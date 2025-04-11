# Crosshair Tool

![App Screenshot](placeholder.png) <!-- Optional: Add a screenshot -->

A highly customizable crosshair overlay for Windows, macOS, and Linux, controlled via a local web interface.

## Features

*   **Always-on-Top Overlay:** Displays a configurable crosshair over any application or game.
*   **Multiple Crosshair Types:**
    *   **Parametric:** Design your own crosshair with adjustable lines (inner/outer), center dot, gap, thickness, length, color, opacity, outlines, and T-shape option.
    *   **Static Image:** Use your own PNG, JPG, BMP images as crosshairs.
    *   **Animated GIF:** Use animated GIFs for dynamic crosshairs.
*   **Web-Based Control Panel:** Access a sleek web UI from any device on your local network to configure the crosshair in real-time.
*   **Profile Management:** Save and load different crosshair configurations as profiles.
*   **Image/GIF Uploads:** Easily upload your custom image/GIF files through the web UI.
*   **Position Adjustment:**
    *   Click and drag the overlay to position it anywhere on the screen.
    *   Nudge the overlay pixel-by-pixel using `Ctrl + Alt + Arrow Keys`.
    *   Position is automatically saved and restored on restart.
*   **Light/Dark Mode:** Both the control panel and web UI support theme switching.
*   **System Tray Integration:** Runs minimized in the system tray with quick access to controls (Show/Hide Overlay, Open Web UI, Exit).

## Technology Stack

*   **Core Application:** Python
*   **GUI & Overlay:** PySide6 (Qt for Python)
*   **Web Server:** Flask
*   **Web Interface:** HTML, CSS, JavaScript
*   **Image Handling:** Pillow
*   **Configuration Storage:** JSON files

## Architecture

The application consists of two main parts:

1.  **Desktop Application (PySide6):** Manages the overlay window, renders the crosshair using QPainter/QMovie, and handles system tray integration.
2.  **Web Server (Flask):** Runs in a background thread, serves the web UI, provides API endpoints for getting/setting crosshair configurations, managing profiles, and handling file uploads.

These two parts communicate internally to provide real-time updates.

## Installation & Running

**Prerequisites:**

*   Python 3.x
*   pip (Python package installer)

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/CrosshairTool.git # Replace with your repo URL
    cd CrosshairTool
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    python src/main.py
    ```

*(Optional: For running the pre-built executable, download it from the Releases page and run it directly.)*

## Usage

1.  **Start the application:** Run `python src/main.py` or launch the executable.
2.  **System Tray:** The application icon will appear in your system tray.
    *   **Right-click** the icon for options: Show Control Panel, Toggle Crosshair, Open Web Interface, Copy Network URL, Exit.
    *   **Double-click** the icon to open the Control Panel.
3.  **Control Panel (Desktop App):** Provides basic instructions, access URLs, and buttons to toggle the overlay or open the web UI.
4.  **Web Interface (Configuration):**
    *   Open using the tray menu or the Control Panel button.
    *   Access locally via `http://127.0.0.1:5000`.
    *   Access from other devices on the same network using the IP address shown in the Control Panel or tray menu (e.g., `http://192.168.1.21:5000`). You might need to allow the application through your firewall.
    *   Use the web UI to select the crosshair type (Parametric, Static, Animated), adjust parameters, upload images/GIFs, and manage profiles.
5.  **Adjusting Overlay Position:**
    *   **Drag:** Click and drag the overlay window directly.
    *   **Nudge:** Use `Ctrl + Alt + Arrow Keys` for fine adjustments.
    *   The position is saved automatically.

## Building from Source (Optional)

If you want to build the executable yourself:

1.  Ensure you have the development dependencies installed (including `pyinstaller`).
    ```bash
    pip install -r requirements.txt
    pip install pyinstaller
    ```
2.  Run the build script:
    ```bash
    python build_installer.py
    ```
3.  The executable will be located in the `dist` folder.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

[Specify your chosen license here, e.g., MIT License] 