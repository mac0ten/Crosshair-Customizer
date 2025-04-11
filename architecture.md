# Architecture Overview

## Core Components

1.  **PyQt Application (`main.py`, `overlay.py`):**
    -   Manages the main application lifecycle.
    -   Creates and displays the transparent, always-on-top overlay window (`OverlayWidget`).
    -   Handles rendering of the crosshair based on current settings (parametric, static, animated).
    -   Listens for updates from the Flask server (via signals/slots or queues).

2.  **Flask Web Server (`server.py`):**
    -   Runs in a separate thread.
    -   Exposes API endpoints for:
        -   Serving the web UI (HTML, CSS, JS).
        -   Serving uploaded user images/GIFs.
        -   Getting/updating crosshair settings.
        -   Managing profiles (CRUD operations on JSON files).
        -   Handling file uploads.
    -   Communicates updates to the PyQt application thread.

3.  **Shared State Manager (`state.py` - *proposed*):**
    -   A thread-safe module/class to hold the current crosshair configuration.
    -   Provides methods for safely reading and writing the state from both the PyQt and Flask threads.

4.  **Web Interface (`templates/index.html`, `static/style.css`, `static/script.js`):**
    -   Provides the user interface for configuration.
    -   Communicates with the Flask server via asynchronous JavaScript requests (fetch API).

## Interaction Flow

-   The PyQt app starts, initializes the overlay, and launches the Flask server in a background thread.
-   The user accesses the web interface from a browser.
-   The web interface fetches the current state from the Flask server (`/get_settings`).
-   User changes settings in the web UI.
-   JavaScript sends updated settings to Flask (`/update_settings`).
-   Flask updates the Shared State Manager.
-   Flask notifies the PyQt application thread (e.g., emits a signal).
-   The PyQt `OverlayWidget` receives the notification, reads the new state from the Shared State Manager, and triggers a repaint to render the updated crosshair.
-   Profile and file operations follow similar request/response patterns between the Web Interface and Flask Server, with Flask interacting with the filesystem. 