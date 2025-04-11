# LocalCrosshairCustomizer (Revised)

## Overview

A desktop Python application that displays a customizable crosshair overlay while hosting a local web server. The application allows detailed crosshair customization, including parametric designs, static images, and animated GIFs. A web interface (accessible from any device on the same network) enables real-time configuration and profile management.

---

## Technology Stack

### Backend / Core Application
- **Python** for the application logic.
- **GUI Framework:**
  - **PyQt6/PySide6**: Recommended over Tkinter for superior graphical handling, particularly for animated GIFs using QMovie and for custom drawing with QPainter.

### Web Server
- **Web Framework:**
  - **Flask** (or **FastAPI** as an alternative)
- **Communication:**
  - HTTP requests (GET, POST) and JSON data exchange.

### Image Handling
- **Pillow (PIL fork):**
  - For processing uploaded images, validating format, dimensions, and transparency. Can also assist with frame extraction if needed.

### Frontend
- **Standard HTML, CSS, JavaScript:**
  - For building the dynamic web interface and managing complex UI interactions.

### Data Storage
- **Profile Storage:**
  - Primarily using JSON files (stored in a designated profiles directory).
  - Alternative consideration: SQLite for more robust profile management if complexity increases.

---

## Detailed Functionality

### 1. Python Application Core
- **Initialization:**
  - Set up the PyQt/PySide application and create an overlay window.
    - Requirements: Transparent, borderless, always-on-top, centered on screen.
  - Initialize default crosshair parameters covering parametric, static image, and animated GIF settings.
  - Create directories:
    - `./profiles/` for storing profile JSON files.
    - `./user_uploads/` for storing uploaded image/GIF files.

- **State Management:**
  - Use a central dictionary or class instance to manage the current crosshair configuration.
  - Ensure thread-safe access between Flask and PyQt modules (e.g., via Qt's signals/slots or threading locks).

### 2. Crosshair Rendering Module (PyQt/PySide)
- **Input:** Receives complete crosshair settings including type and all parameters.
- **Rendering Approaches:**
  - **Parametric Crosshair:**
    - Use QPainter (in the widget's paintEvent) for drawing:
      - Center dot, inner/outer lines, outlines.
      - Custom parameters: thickness, gap, length, T-shape option, colors, and opacity.
  - **Static Image Crosshair:**
    - Load and display images using QPixmap/QImage via QPainter.
  - **Animated GIF Crosshair:**
    - Use QMovie for loading and playing GIF files.
    - Manage start/stop operations and transparency.
- **Key Method:**
  - `update_crosshair(settings)`:
    - Accepts the new configuration, loads necessary resources, and triggers a widget repaint.

### 3. Web Server Module (Using Flask)
- **Defined Routes and Their Functions:**
  - **/** (GET):
    - Serves the main HTML page.
  - **/static/<path:path>:**
    - Serves static files such as CSS and JS.
  - **/user_uploads/<path:path>:**
    - Serves the uploaded images/GIFs for previews or display.
  - **/get_settings** (GET):
    - Returns the current crosshair settings as JSON.
  - **/update_settings** (POST):
    - Receives and validates full settings (JSON), updates the shared state, and calls `update_crosshair`.
  - **/upload_image** (POST):
    - Handles image/GIF uploads:
      - Accepts file types: `.png, .jpg, .jpeg, .bmp, .gif`
      - Validates file integrity with Pillow.
      - Saves file to `./user_uploads/` using a sanitized filename.
      - Updates the state for image type accordingly and returns the path/status.
  - **/save_profile** (POST):
    - Receives current settings and a profile name.
    - Saves the settings as `profiles/<name>.json`.
  - **/load_profile** (POST):
    - Receives a profile name.
    - Reads the corresponding JSON file, validates, updates the crosshair, and returns the loaded settings.
  - **/list_profiles** (GET):
    - Scans the profiles directory and returns available profile names (from `.json` files).
  - **/delete_profile** (POST):
    - Receives a profile name and deletes the corresponding JSON file.

### 4. Web Interface (HTML/CSS/JS)
- **HTML Structure:**
  - **Crosshair Type Selector:**
    - Options: "Parametric", "Static Image", "Animated GIF".
  - **Parametric Controls Section:**
    - Controls: Checkboxes, sliders, number inputs, color pickers, opacity controls, T-shape toggle.
    - Shown only when "Parametric" is selected.
  - **Image Upload Section:**
    - File input (accepts specific image and GIF formats).
    - Area to preview the uploaded image and display the filename.
  - **Profile Management Section:**
    - Input field for profile names with "Save" button.
    - Dropdown/list of existing profiles.
    - "Load" and "Delete" buttons.
  - **General Controls:**
    - "Apply Changes" (if not using real-time updates) and "Reset to Default" controls.

- **JavaScript Logic:**
  - **Dynamic UI Controls:**
    - Functions to show/hide sections based on the selected crosshair type.
  - **State Synchronization:**
    - On load, retrieve current settings (`/get_settings`) and profile list (`/list_profiles`).
    - Update controls to reflect current configurations.
  - **Event Handling:**
    - On control change:
      - Gather all settings, package into a JSON object, and send a POST request to `/update_settings`.
    - **Image Upload:**
      - Monitor file input changes, send the file to `/upload_image`, and update the UI upon success.
  - **Profile Management Functions:**
    - **Save:**
      - Send current settings with a profile name to `/save_profile` and update the profile list.
    - **Load:**
      - Request settings from `/load_profile` for a selected profile and update the UI.
    - **Delete:**
      - Send a request to `/delete_profile` to remove the selected profile and update the list.

---

## Communication Flow Example (Adjusting Inner Line Gap)

1. **User Action:**
   - A user on a mobile device adjusts the "Inner Line Gap" slider while "Parametric" is selected.
2. **JavaScript Event:**
   - The event listener gathers all current control values into a JSON object.
   - A POST request is sent to `/update_settings` with the new settings.
3. **Flask Server Processing:**
   - The server updates the shared state and calls `update_crosshair(new_state)`.
4. **PyQt Rendering:**
   - The overlay widget's paintEvent is triggered.
   - The crosshair is redrawn with the updated gap.
5. **Visual Feedback:**
   - Changes appear on the desktop display almost instantaneously.
6. **Response:**
   - The web interface receives confirmation and maintains state synchronization.

---

## Key Implementation Considerations

- **Threading / Concurrency:**
  - Run the Flask server in a separate thread to allow simultaneous handling of GUI events.
  - Ensure communication between Flask and PyQt is thread-safe (using signals/slots or thread-safe queues).

- **Parametric Drawing:**
  - Use QPainter for geometric calculations to draw lines, circles, and other shapes based on the configuration.

- **Animated GIF Handling:**
  - Implement QMovie to play GIFs, ensuring transparency and smooth looping.
  - Manage playback control based on user settings.

- **File Handling:**
  - Use robust file path management for both image uploads and profile storage.
  - Validate and sanitize all input filenames to prevent security issues.

- **User Experience:**
  - Provide real-time updates on the overlay as settings change.
  - Make the web interface intuitive with clear visual feedback and responsive elements. 