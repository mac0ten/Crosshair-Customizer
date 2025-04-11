# Task Plan

## Phase 1: Core Setup & Basic Overlay

1.  [x] **Project Structure**: Set up directories (`src`, `profiles`, `user_uploads`, `static`, `templates`). - *Done*
2.  [x] **Memory Files**: Initialize `product_requirement_docs.md`, `technical.md`, `architecture.md`, `tasks_plan.md`, `active_context.md`. - *Done*
3.  [x] **Dependencies**: Create `requirements.txt` with initial dependencies (PyQt6/PySide6, Flask, Pillow). - *Done*
4.  [x] **Basic PyQt Window**: Create a basic, transparent, always-on-top, borderless PyQt window (`src/main.py`, `src/overlay.py`). - *Done*
5.  [x] **Basic Flask Server**: Set up a minimal Flask server (`src/server.py`) running in a separate thread. - *Done*
6.  [x] **State Management**: Implement a basic state dictionary/class (`src/state.py`) and integrate. - *Done*
7.  [x] **Inter-thread Communication**: Establish basic communication via callback function (`overlay.update_crosshair`) passed to server thread. - *Done*

## Phase 2: Crosshair Rendering

1.  [x] **Parametric Rendering**: Implement QPainter logic in `overlay.py` to draw crosshairs based on parameters (lines, dot, gap, color, etc.). - *Done*
2.  [x] **Static Image Rendering**: Load and display static images (`.png`, `.jpg`) in the overlay. - *Done*
3.  [x] **Animated GIF Rendering**: Integrate QMovie to display animated GIFs in the overlay. - *Done*
4.  [x] **`update_crosshair` Method**: Refine the method in `overlay.py` to handle switching between rendering types and updating visuals. - *Done (Integrated into previous steps)*

## Phase 3: Web Interface & API Endpoints

1.  [x] **Basic HTML Structure**: Create `templates/index.html` with sections for type selection, parametric controls, image upload, and profile management. - *Done*
2.  [x] **Basic CSS Styling**: Create `static/style.css` for basic layout and usability. - *Done*
3.  [x] **Basic JavaScript Logic**: Create `static/script.js` for dynamic UI (showing/hiding sections). - *Done*
4.  [x] **`/get_settings` Endpoint**: Implement Flask route to return the current state. - *Done (Basic)*
5.  [x] **`/update_settings` Endpoint**: Implement Flask route to receive settings, update state, and trigger PyQt update. - *Done (Basic)*
6.  [x] **JS State Sync**: Implement JS to fetch initial state and update UI controls. - *Done*
7.  [x] **JS Event Handling**: Implement JS to send updates to `/update_settings` on control changes. - *Done*

## Phase 4: File Handling & Profiles

1.  [x] **`/upload_image` Endpoint**: Implement Flask route for file uploads, validation (Pillow), and saving to `user_uploads/`. - *Done*
2.  [x] **JS Image Upload**: Implement JS to handle file selection and POSTing to `/upload_image`. - *Done*
3.  [x] **Profile Endpoints**: Implement Flask routes for `/save_profile`, `/load_profile`, `/list_profiles`, `/delete_profile` (interacting with JSON files in `profiles/`). - *Done*
4.  [x] **JS Profile Management**: Implement JS functions to interact with the profile endpoints and update the UI. - *Done*

## Phase 5: Refinement & Packaging

1.  [~] **Error Handling**: Add robust error handling (Flask validation done, JS feedback blocked). - *Partially Done*
2.  [x] **Thread Safety**: Ensure the Shared State Manager is fully thread-safe. - *Done*
3.  [~] **UI/UX Polish**: Refine the web interface and overlay behavior (JS feedback blocked). - *Partially Blocked*
4.  [-] **Testing**: Add basic unit/integration tests (optional but recommended). - *Skipped by User*
5.  [x] **Packaging**: Create setup instructions or a simple executable. - *README created*

## Phase 6: Desktop UI/UX Enhancements (New)

1.  [x] **System Tray Icon**: Implement `QSystemTrayIcon` to show the app is running. - *Done*
2.  [x] **Tray Menu**: Add a context menu to the tray icon with actions (e.g., "Open Web UI", "Exit"). - *Done*
3.  [x] **Application Lifecycle**: Ensure the app keeps running when the overlay is hidden/closed and exits cleanly via the tray menu. - *Done*
4.  [x] **[Optional] Control Panel GUI**: Create a basic GUI window accessible from the tray for status/controls. - *Done* 