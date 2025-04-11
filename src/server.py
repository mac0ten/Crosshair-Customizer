from flask import Flask, jsonify, render_template, request, send_from_directory
import threading
import os
import json
import re
from werkzeug.utils import secure_filename
from PIL import Image
from PySide6.QtCore import QMetaObject, Qt, Q_ARG
import copy
import shutil
import sys

# --- Constants --- 
PROFILES_FOLDER = 'profiles'
UPLOAD_FOLDER = 'uploads'
PRESETS_FOLDER = 'presets'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}

# --- Resource Path Handling ---
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print(f"[DEBUG] Using PyInstaller _MEIPASS path: {base_path}")
    except Exception:
        # If not running as bundled executable, use the script's directory
        base_path = os.path.abspath(os.path.dirname(__file__))
        if os.path.basename(base_path) == 'src':
            # If we're in src folder and trying to access resources in parent dir
            base_path = os.path.abspath(os.path.join(base_path, '..'))
        print(f"[DEBUG] Using development path: {base_path}")
    
    full_path = os.path.join(base_path, relative_path)
    print(f"[DEBUG] Resolved path: {full_path} (exists: {os.path.exists(full_path)})")
    return full_path

# --- Global Variables --- 
state_manager_ref = None
update_callback_ref = None
_main_window_ref = None
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) 
_upload_folder_path = None
_profiles_folder_path = None
_presets_folder_path = None
_template_folder_path = get_resource_path('templates')
_static_folder_path = get_resource_path('static')
app = Flask(__name__, 
           template_folder=_template_folder_path, 
           static_folder=_static_folder_path)

# --- Helper Functions --- 
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Basic profile name validation/sanitization
def sanitize_profile_name(name):
    # Remove potentially harmful characters, keep alphanumeric, spaces, hyphens, underscores
    name = re.sub(r'[^a-zA-Z0-9 _-]', '', name).strip()
    # Replace spaces with underscores (optional, can make filenames simpler)
    # name = name.replace(' ', '_') 
    # Limit length
    return name[:50] # Limit to 50 chars

def validate_settings(data):
    """Validates the structure and basic types of the settings dictionary.
    Raises ValueError on failure.
    """
    if not isinstance(data, dict):
        raise ValueError("Settings must be a dictionary.")

    # Validate top-level type
    valid_types = {'parametric', 'static', 'animated'}
    if 'type' not in data or data['type'] not in valid_types:
        raise ValueError(f"Invalid or missing 'type'. Must be one of {valid_types}.")

    # Validate sub-dictionaries exist
    for key in valid_types:
        if key not in data or not isinstance(data[key], dict):
            raise ValueError(f"Missing or invalid '{key}' settings dictionary.")

    # --- Detailed Parametric Validation --- 
    p = data['parametric']
    bool_keys_p = ['center_dot_enabled', 'inner_lines_enabled', 'outer_lines_enabled', 'outline_enabled', 't_shape']
    num_keys_p = ['center_dot_size', 'center_dot_opacity', 'inner_lines_thickness', 
                    'inner_lines_length', 'inner_lines_gap', 'inner_lines_opacity',
                    'outer_lines_thickness', 'outer_lines_length', 'outer_lines_gap', 
                    'outer_lines_opacity', 'outline_thickness', 'outline_opacity']
    color_keys_p = ['center_dot_color', 'inner_lines_color', 'outer_lines_color', 'outline_color']

    for key in bool_keys_p: 
        if key not in p or not isinstance(p[key], bool): raise ValueError(f"Parametric setting '{key}' must be a boolean.")
    for key in num_keys_p:
        if key not in p or not isinstance(p[key], (int, float)): raise ValueError(f"Parametric setting '{key}' must be a number.")
        if 'opacity' in key and not (0 <= p[key] <= 255): raise ValueError(f"Parametric opacity '{key}' must be between 0 and 255.")
        # Add more range checks if needed (e.g., size/thickness >= 0)
        if ('size' in key or 'thickness' in key or 'length' in key or 'gap' in key) and p[key] < 0: 
             raise ValueError(f"Parametric dimension '{key}' cannot be negative.")
    for key in color_keys_p:
         if key not in p or not isinstance(p[key], str) or not re.match(r'^#[0-9A-Fa-f]{6}$', p[key]): 
              raise ValueError(f"Parametric color '{key}' must be a valid hex string (e.g., #RRGGBB).")

    # --- Detailed Static Validation --- 
    s = data['static']
    if 'image_path' not in s or not (isinstance(s['image_path'], str) or s['image_path'] is None):
        raise ValueError("Static setting 'image_path' must be a string or null.")
    if 'opacity' not in s or not isinstance(s['opacity'], (int, float)) or not (0 <= s['opacity'] <= 255):
        raise ValueError("Static setting 'opacity' must be a number between 0 and 255.")
    if 'scale' not in s or not isinstance(s['scale'], (int, float)) or s['scale'] <= 0:
         raise ValueError("Static setting 'scale' must be a positive number.")

    # --- Detailed Animated Validation --- 
    a = data['animated']
    if 'gif_path' not in a or not (isinstance(a['gif_path'], str) or a['gif_path'] is None):
        raise ValueError("Animated setting 'gif_path' must be a string or null.")
    if 'opacity' not in a or not isinstance(a['opacity'], (int, float)) or not (0 <= a['opacity'] <= 255):
        raise ValueError("Animated setting 'opacity' must be a number between 0 and 255.")
    if 'scale' not in a or not isinstance(a['scale'], (int, float)) or a['scale'] <= 0:
         raise ValueError("Animated setting 'scale' must be a positive number.")
    if 'speed' not in a or not isinstance(a['speed'], (int, float)) or a['speed'] <= 0:
         raise ValueError("Animated setting 'speed' must be a positive number.")

    # Add more checks as needed...
    return True # Validation passed

# --- Routes --- 

@app.route('/')
def index():
    """Serves the main HTML configuration page."""
    try:
        # Debug info about template location
        print(f"[DEBUG] Looking for template in: {app.template_folder}")
        template_path = os.path.join(app.template_folder, 'index.html')
        print(f"[DEBUG] Full template path: {template_path}")
        print(f"[DEBUG] Template exists: {os.path.exists(template_path)}")
        
        # List all templates for debugging
        print(f"[DEBUG] Templates directory contents:")
        try:
            if os.path.exists(app.template_folder):
                for item in os.listdir(app.template_folder):
                    print(f"  - {item}")
            else:
                print(f"  Templates directory not found")
        except Exception as e:
            print(f"  Error listing templates: {e}")
        
        return render_template('index.html')
    except Exception as e:
        print(f"Error rendering template: {e}")
        error_html = f"""
        <h1>Crosshair Configurator</h1>
        <p>Error loading Web UI. Template not found or invalid.</p>
        <p><strong>Debug info:</strong></p>
        <ul>
            <li>Template folder: {app.template_folder}</li>
            <li>Static folder: {app.static_folder}</li>
            <li>Current working directory: {os.getcwd()}</li>
            <li>Error: {str(e)}</li>
        </ul>
        """
        return error_html, 500

@app.route('/user_uploads/<path:filename>')
def serve_upload(filename):
    """Serves uploaded files for preview."""
    try:
        # Debug the request
        print(f"[DEBUG] Serving uploaded file: {filename}")
        print(f"[DEBUG] Looking in uploads folder: {_upload_folder_path}")
        
        # Check if the file exists in the uploads folder
        file_path = os.path.join(_upload_folder_path, filename)
        if os.path.exists(file_path):
            print(f"[DEBUG] Found file at: {file_path}")
            return send_from_directory(_upload_folder_path, filename)
        
        # If not found, try looking in presets folder too
        print(f"[DEBUG] File not found in uploads, checking presets...")
        preset_file_path = os.path.join(_presets_folder_path, filename)
        if os.path.exists(preset_file_path):
            print(f"[DEBUG] Found file in presets: {preset_file_path}")
            # Copy the file to uploads folder for future use
            try:
                os.makedirs(_upload_folder_path, exist_ok=True)
                shutil.copy2(preset_file_path, file_path)
                print(f"[DEBUG] Copied from presets to uploads: {file_path}")
            except Exception as e:
                print(f"[WARNING] Could not copy preset to uploads: {e}")
            
            # Serve from presets folder
            return send_from_directory(os.path.dirname(preset_file_path), os.path.basename(preset_file_path))
        
        # Check in _internal directory if it exists
        internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
        if os.path.exists(internal_dir):
            internal_presets = os.path.join(internal_dir, PRESETS_FOLDER, filename)
            if os.path.exists(internal_presets):
                print(f"[DEBUG] Found file in internal presets: {internal_presets}")
                # Copy to uploads folder for future use
                try:
                    os.makedirs(_upload_folder_path, exist_ok=True)
                    shutil.copy2(internal_presets, file_path)
                    print(f"[DEBUG] Copied from internal presets to uploads: {file_path}")
                except Exception as e:
                    print(f"[WARNING] Could not copy internal preset to uploads: {e}")
                
                # Serve from internal presets
                return send_from_directory(os.path.dirname(internal_presets), os.path.basename(internal_presets))
        
        # If still not found, check in PyInstaller locations if applicable
        if hasattr(sys, '_MEIPASS'):
            meipass_locations = [
                os.path.join(sys._MEIPASS, PRESETS_FOLDER, filename),
                os.path.join(sys._MEIPASS, 'static', 'presets', filename),
                os.path.join(sys._MEIPASS, 'static', 'presets', 'animated', filename)
            ]
            
            for location in meipass_locations:
                if os.path.exists(location):
                    print(f"[DEBUG] Found file in PyInstaller bundle: {location}")
                    # Copy to uploads folder for future use
                    try:
                        os.makedirs(_upload_folder_path, exist_ok=True)
                        shutil.copy2(location, file_path)
                        print(f"[DEBUG] Copied from bundle to uploads: {file_path}")
                    except Exception as e:
                        print(f"[WARNING] Could not copy bundled file to uploads: {e}")
                    
                    # Serve from bundle
                    return send_from_directory(os.path.dirname(location), os.path.basename(location))
        
        # If we get here, file was not found anywhere
        print(f"[ERROR] File not found in any location: {filename}")
        return f"File not found: {filename}", 404
        
    except Exception as e:
        print(f"[ERROR] Error serving uploaded file: {e}")
        return str(e), 500

@app.route('/get_settings')
def get_settings():
    """Returns the current crosshair settings."""
    if state_manager_ref:
        settings = state_manager_ref.get_settings()
        return jsonify(settings)
    else:
        return jsonify({"error": "State manager not initialized"}), 500

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Receives new settings, validates, updates state, and notifies GUI thread."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    new_settings = request.get_json()

    if state_manager_ref and update_callback_ref:
        try:
            validate_settings(new_settings)
            settings_copy = copy.deepcopy(new_settings)
            
            # --- Update State --- 
            state_manager_ref.update_settings(settings_copy)
            
            # --- Schedule GUI Update (passing JSON string) --- 
            settings_json = json.dumps(settings_copy)
            QMetaObject.invokeMethod(
                update_callback_ref.__self__,
                "update_crosshair",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, settings_json) # Pass as string
            )
            # ------------------------------------------------ 
            
            return jsonify({"success": True, "message": "Settings update queued"})
        
        except ValueError as ve:
             print(f"Settings validation failed: {ve}")
             return jsonify({"error": "Invalid settings received", "details": str(ve)}), 400
        except Exception as e:
            print(f"Error processing settings update: {e}")
            return jsonify({"error": "Failed to process settings update", "details": "An internal server error occurred."}), 500
    else:
        return jsonify({"error": "Server components not initialized"}), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """Handles image/GIF uploads, validation, saving, and state update (via GUI thread)."""
    if not state_manager_ref or not update_callback_ref:
         return jsonify({"error": "Server components not initialized"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(_upload_folder_path, exist_ok=True)
        save_path = os.path.join(_upload_folder_path, filename)
        temp_save_path = save_path + ".tmp"
        
        try:
            # Ensure no old temp file exists (shouldn't happen often, but good practice)
            if os.path.exists(temp_save_path):
                try: os.remove(temp_save_path)
                except OSError as e:
                    print(f"Warning: Could not remove old temp file {temp_save_path}: {e}")
            
            # Save to temporary path first
            file.save(temp_save_path)

            # Validate using Pillow
            with Image.open(temp_save_path) as img:
                img.verify() # Check integrity. Raises exception on error.
            
            # --- Overwrite Handling --- 
            # Validation passed. If the final destination file exists, remove it first.
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                    print(f"Removed existing file: {save_path}")
                except OSError as e:
                    # If we can't remove the old file, we can't proceed with rename
                    raise OSError(f"Failed to remove existing file {save_path}: {e}") from e
            # ------------------------

            # Rename temporary file to final name
            os.rename(temp_save_path, save_path)
            print(f"File validated and saved to: {save_path}")

            # --- Prepare settings and Update State --- 
            current_settings = state_manager_ref.get_settings()
            file_ext = filename.rsplit('.', 1)[1].lower()
            if file_ext == 'gif':
                current_settings['type'] = 'animated'
                current_settings['animated']['gif_path'] = filename
                current_settings['static']['image_path'] = None
            else:
                current_settings['type'] = 'static'
                current_settings['static']['image_path'] = filename
                current_settings['animated']['gif_path'] = None
            
            settings_to_update = copy.deepcopy(current_settings)
            state_manager_ref.update_settings(settings_to_update)

            # --- Schedule GUI Update (passing JSON string) --- 
            settings_json = json.dumps(settings_to_update)
            QMetaObject.invokeMethod(
                update_callback_ref.__self__, 
                "update_crosshair",          
                Qt.ConnectionType.QueuedConnection, 
                Q_ARG(str, settings_json) # Pass as string
            )
            # ---------------------------------------------
            
            return jsonify({"success": True, "message": "File uploaded, update queued", "filename": filename, "new_settings": settings_to_update})

        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(temp_save_path):
                try: os.remove(temp_save_path)
                except OSError: pass
            print(f"Error during file upload/validation/save: {e}") # Modified print
            # Distinguish between validation/save errors and file removal errors
            error_msg = "File validation or save failed" 
            if isinstance(e, OSError) and "Failed to remove existing file" in str(e):
                 error_msg = "Failed to overwrite existing file"
            return jsonify({"error": error_msg, "details": str(e)}), 500

    else:
        return jsonify({"error": "File type not allowed"}), 400

# --- Profile Management Routes --- 

@app.route('/list_profiles')
def list_profiles():
    """Lists all available profiles."""
    try:
        if not os.path.exists(_profiles_folder_path):
            os.makedirs(_profiles_folder_path, exist_ok=True)
            
        profiles = []
        for filename in os.listdir(_profiles_folder_path):
            if filename.endswith('.json'):
                profile_name = os.path.splitext(filename)[0]
                profiles.append(profile_name)
        
        # Return with success flag and profiles array
        return jsonify({"success": True, "profiles": profiles})
    except Exception as e:
        print(f"[ERROR] Exception in list_profiles: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/save_profile', methods=['POST'])
def save_profile():
    """Saves the current settings as a named profile."""
    try:
        # Debug the incoming request
        print(f"[DEBUG] Save profile request received")
        print(f"[DEBUG] Request content type: {request.content_type}")
        print(f"[DEBUG] Request has JSON: {request.is_json}")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
            print(f"[DEBUG] Request JSON data: {data}")
        else:
            # Try to parse the data from form or raw body
            try:
                data = request.form.to_dict()
                print(f"[DEBUG] Request form data: {data}")
            except Exception:
                try:
                    # Try to parse raw body as JSON
                    data = json.loads(request.data.decode('utf-8'))
                    print(f"[DEBUG] Request raw body parsed: {data}")
                except Exception as e:
                    print(f"[DEBUG] Failed to parse request data: {e}")
                    data = {}
        
        # Check for required fields
        missing_fields = []
        if not data:
            missing_fields.append("request data")
        elif 'profile_name' not in data:
            missing_fields.append("profile_name")
        elif 'settings' not in data:
            missing_fields.append("settings")
            
        if missing_fields:
            error_message = f"Missing {', '.join(missing_fields)}"
            print(f"[DEBUG] Error: {error_message}")
            return jsonify({"error": error_message}), 400
            
        # Validate and sanitize profile name
        profile_name = sanitize_profile_name(data['profile_name'])
        if not profile_name:
            print(f"[DEBUG] Invalid profile name: {data['profile_name']}")
            return jsonify({"error": "Invalid profile name"}), 400
            
        # Validate settings
        try:
            settings = data['settings']
            # If settings is a string, try to parse it as JSON
            if isinstance(settings, str):
                try:
                    settings = json.loads(settings)
                    print(f"[DEBUG] Parsed settings from string")
                except Exception as e:
                    print(f"[DEBUG] Failed to parse settings string: {e}")
                    return jsonify({"error": f"Invalid settings format: {str(e)}"}), 400
                    
            validate_settings(settings)
        except ValueError as e:
            print(f"[DEBUG] Settings validation failed: {e}")
            return jsonify({"error": f"Invalid settings: {str(e)}"}), 400
            
        # Ensure profiles directory exists
        os.makedirs(_profiles_folder_path, exist_ok=True)
        print(f"[DEBUG] Saving profile to: {_profiles_folder_path}")
        
        # Save the profile
        profile_path = os.path.join(_profiles_folder_path, f"{profile_name}.json")
        with open(profile_path, 'w') as f:
            json.dump(settings, f)
            
        print(f"[DEBUG] Profile saved successfully: {profile_name}")
        return jsonify({"message": f"Profile {profile_name} saved successfully"})
    except Exception as e:
        print(f"[ERROR] Exception in save_profile: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/load_profile/<profile_name>')
def load_profile(profile_name):
    """Loads a named profile."""
    try:
        # Sanitize profile name
        profile_name = sanitize_profile_name(profile_name)
        if not profile_name:
            return jsonify({"error": "Invalid profile name"}), 400
            
        # Check if profile exists
        profile_path = os.path.join(_profiles_folder_path, f"{profile_name}.json")
        if not os.path.exists(profile_path):
            return jsonify({"error": f"Profile {profile_name} not found"}), 404
            
        # Load the profile
        with open(profile_path, 'r') as f:
            settings = json.load(f)
            
        # Update the crosshair settings in the application state
        if state_manager_ref:
            # Use copy to avoid modifying the settings by reference
            settings_to_update = copy.deepcopy(settings)
            state_manager_ref.update_settings(settings_to_update)
            
            # Use JSON string for Qt method invocation, like in other functions
            if update_callback_ref:
                settings_json = json.dumps(settings_to_update)
                QMetaObject.invokeMethod(
                    update_callback_ref.__self__, 
                    "update_crosshair",          
                    Qt.ConnectionType.QueuedConnection, 
                    Q_ARG(str, settings_json)
                )
                
        return jsonify({"success": True, "settings": settings})
    except Exception as e:
        print(f"[ERROR] Error loading profile: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/delete_profile/<profile_name>', methods=['DELETE'])
def delete_profile(profile_name):
    """Deletes a named profile."""
    try:
        # Sanitize profile name
        profile_name = sanitize_profile_name(profile_name)
        if not profile_name:
            return jsonify({"error": "Invalid profile name"}), 400
            
        # Check if profile exists
        profile_path = os.path.join(_profiles_folder_path, f"{profile_name}.json")
        if not os.path.exists(profile_path):
            return jsonify({"error": f"Profile {profile_name} not found"}), 404
            
        # Delete the profile
        os.remove(profile_path)
        return jsonify({"message": f"Profile {profile_name} deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list_gif_presets', methods=['GET'])
def list_gif_presets():
    """Lists available crosshair preset files (GIF/PNG) with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 24, type=int) # Default to 24 presets per page
        if page < 1: page = 1
        if per_page < 1: per_page = 1
        if per_page > 100: per_page = 100 # Add a max limit per page
        
        presets_list = []
        presets_path = _presets_folder_path
        print(f"[DEBUG] Looking for presets in primary path: {presets_path}")
        
        # Consolidate all potential preset locations
        preset_locations_to_scan = set()
        if os.path.exists(presets_path) and os.path.isdir(presets_path):
            preset_locations_to_scan.add(presets_path)
        
        # Check alternative paths if in PyInstaller bundle or primary path is empty/missing
        if hasattr(sys, '_MEIPASS'):
            print(f"[DEBUG] Checking PyInstaller paths...")
            alternative_paths = [
                os.path.join(sys._MEIPASS, 'presets'),
                os.path.join(sys._MEIPASS, 'static', 'presets'),
                os.path.join(os.path.dirname(sys.executable), 'presets') # Also check folder next to exe
            ]
            for alt_path in alternative_paths:
                if os.path.exists(alt_path) and os.path.isdir(alt_path):
                    print(f"[DEBUG] Found presets at alternative path: {alt_path}")
                    preset_locations_to_scan.add(alt_path)
        
        # Check internal directory path if it exists (often used in builds)
        internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
        if os.path.exists(internal_dir) and os.path.isdir(internal_dir):
             internal_presets_path = os.path.join(internal_dir, PRESETS_FOLDER)
             if os.path.exists(internal_presets_path) and os.path.isdir(internal_presets_path):
                 print(f"[DEBUG] Found presets at internal path: {internal_presets_path}")
                 preset_locations_to_scan.add(internal_presets_path)
        
        # If no locations found, return empty
        if not preset_locations_to_scan:
            print("[DEBUG] No presets directory found after trying alternatives")
            return jsonify({"success": False, "presets": [], "error": "No presets found", "total_presets": 0, "page": page, "per_page": per_page})
            
        # Scan all found locations for preset files
        found_presets_map = {}  # Use dict to avoid duplicates based on filename
        print(f"[DEBUG] Scanning locations: {list(preset_locations_to_scan)}") # Log actual list
        total_files_scanned = 0
        total_presets_found_before_dedup = 0
        
        for search_path in preset_locations_to_scan:
            print(f"[DEBUG] --- Scanning Path: {search_path} ---")
            try:
                items_in_dir = os.listdir(search_path)
                print(f"[DEBUG] Found {len(items_in_dir)} items in {search_path}")
                total_files_scanned += len(items_in_dir)
                
                for filename in items_in_dir:
                    if filename.lower().endswith(('.gif', '.png')):
                        total_presets_found_before_dedup += 1
                        # Use filename as key to handle potential duplicates across scanned folders
                        if filename not in found_presets_map:
                            try:
                                file_path = os.path.join(search_path, filename)
                                if os.path.isfile(file_path): # Ensure it's a file
                                    file_size = os.path.getsize(file_path) / 1024  # Convert to KB
                                    preset_name = os.path.splitext(filename)[0]
                                    preset_data = {
                                        'name': preset_name,
                                        'filename': filename,
                                        'size_kb': round(file_size, 1),
                                        'extension': os.path.splitext(filename)[1][1:].upper(),
                                    }
                                    found_presets_map[filename] = preset_data
                            except Exception as e:
                                print(f"[WARN] Error processing file {filename} in {search_path}: {e}")
                        # else: print(f"[DEBUG] Duplicate preset skipped: {filename}") # Optional: log duplicates
                    # else: print(f"[DEBUG] Non-preset file skipped: {filename}") # Optional: log skips
            except Exception as e:
                print(f"[WARN] Error listing directory {search_path}: {e}")
        
        print(f"[DEBUG] Total items seen across all directories: {total_files_scanned}")
        print(f"[DEBUG] Total .gif/.png files found (before deduplication): {total_presets_found_before_dedup}")
        print(f"[DEBUG] Total unique presets added to map: {len(found_presets_map)}")

        # Convert to list and sort
        all_presets = sorted(list(found_presets_map.values()), key=lambda x: x['name'])
        total_presets = len(all_presets)
        print(f"[DEBUG] Final total unique presets after sorting: {total_presets}.")
        
        # Calculate pagination slice
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_presets = all_presets[start_index:end_index]
        
        print(f"[DEBUG] Returning page {page} ({len(paginated_presets)} presets)")
        return jsonify({
            "success": True, 
            "presets": paginated_presets, 
            "total_presets": total_presets,
            "page": page,
            "per_page": per_page
        })
    except Exception as e:
        print(f"[ERROR] Error listing preset animations: {e}")
        return jsonify({"success": False, "presets": [], "error": str(e), "total_presets": 0, "page": 1, "per_page": per_page}), 500

@app.route('/get_preset/<filename>')
def get_preset(filename):
    """Serves a preset animation file."""
    if not filename or '..' in filename:  # Simple path traversal protection
        return "Invalid filename", 400
        
    # Sanitize filename
    filename = os.path.basename(filename)
    
    try:
        # Debug info
        print(f"[DEBUG] Requested preset: {filename}")
        print(f"[DEBUG] Looking in presets folder: {_presets_folder_path}")
        
        # Possible locations to check (same as in list_gif_presets)
        possible_locations = [
            os.path.join(_presets_folder_path, filename),
            os.path.join(_presets_folder_path, 'animated', filename)
        ]
        
        # If in PyInstaller bundle, add more possible locations
        if hasattr(sys, '_MEIPASS'):
            possible_locations.extend([
                os.path.join(sys._MEIPASS, 'presets', filename),
                os.path.join(sys._MEIPASS, 'presets', 'animated', filename),
                os.path.join(sys._MEIPASS, 'static', 'presets', filename),
                os.path.join(sys._MEIPASS, 'static', 'presets', 'animated', filename),
                os.path.join(os.path.dirname(sys.executable), 'presets', filename),
                os.path.join(os.path.dirname(sys.executable), 'presets', 'animated', filename)
            ])
        
        # Check all possible locations
        for location in possible_locations:
            print(f"[DEBUG] Checking location: {location}")
            if os.path.exists(location):
                preset_path = location
                print(f"[DEBUG] Found preset at: {preset_path}")
                # Use send_from_directory with the directory and filename
                return send_from_directory(
                    os.path.dirname(preset_path),
                    os.path.basename(preset_path),
                    as_attachment=False,
                    mimetype='image/gif' if filename.endswith('.gif') else 'image/png'
                )
        
        print(f"[DEBUG] Preset not found in any location: {filename}")
        return f"Preset file not found: {filename}", 404
        
    except Exception as e:
        print(f"[ERROR] Error serving preset: {e}")
        return str(e), 404

@app.route('/apply_gif_preset', methods=['POST'])
def apply_gif_preset():
    """Applies a selected GIF preset."""
    if not state_manager_ref or not update_callback_ref:
        return jsonify({"error": "Server components not initialized"}), 500
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    preset_filename = data.get('preset_filename')
    
    if not preset_filename:
        return jsonify({"error": "No preset filename provided"}), 400
    
    try:
        # Debug info
        print(f"[DEBUG] Applying preset: {preset_filename}")
        print(f"[DEBUG] Looking in presets folder: {_presets_folder_path}")
        
        # Possible locations to check - same as in get_preset
        possible_locations = [
            os.path.join(_presets_folder_path, preset_filename),
            os.path.join(_presets_folder_path, 'animated', preset_filename)
        ]
        
        # If in PyInstaller bundle, add more possible locations
        if hasattr(sys, '_MEIPASS'):
            possible_locations.extend([
                os.path.join(sys._MEIPASS, 'presets', preset_filename),
                os.path.join(sys._MEIPASS, 'presets', 'animated', preset_filename),
                os.path.join(sys._MEIPASS, 'static', 'presets', preset_filename),
                os.path.join(sys._MEIPASS, 'static', 'presets', 'animated', preset_filename),
                os.path.join(os.path.dirname(sys.executable), 'presets', preset_filename),
                os.path.join(os.path.dirname(sys.executable), 'presets', 'animated', preset_filename)
            ])
        
        # Check all possible locations
        preset_path = None
        for location in possible_locations:
            print(f"[DEBUG] Checking location: {location}")
            if os.path.exists(location):
                preset_path = location
                print(f"[DEBUG] Found preset at: {preset_path}")
                break
        
        if not preset_path:
            return jsonify({"success": False, "error": "Preset file not found"}), 404
        
        # Ensure upload folder exists
        os.makedirs(_upload_folder_path, exist_ok=True)
        
        # Copy the preset to the uploads folder
        destination_path = os.path.join(_upload_folder_path, preset_filename)
        print(f"[DEBUG] Copying preset to: {destination_path}")
        shutil.copy2(preset_path, destination_path)
        
        # Update settings
        current_settings = state_manager_ref.get_settings()
        
        # Determine if it's a GIF or static image based on extension
        if preset_filename.lower().endswith('.gif'):
            current_settings['type'] = 'animated'
            current_settings['animated']['gif_path'] = preset_filename
            # Make sure static is not used
            current_settings['static']['image_path'] = None
        else:
            current_settings['type'] = 'static'
            current_settings['static']['image_path'] = preset_filename
            # Make sure animated is not used
            current_settings['animated']['gif_path'] = None
        
        # Update state
        settings_to_update = copy.deepcopy(current_settings)
        state_manager_ref.update_settings(settings_to_update)
        
        # Schedule GUI update
        settings_json = json.dumps(settings_to_update)
        QMetaObject.invokeMethod(
            update_callback_ref.__self__, 
            "update_crosshair",          
            Qt.ConnectionType.QueuedConnection, 
            Q_ARG(str, settings_json)
        )
        
        return jsonify({
            "success": True, 
            "message": "Preset applied successfully", 
            "settings": settings_to_update
        })
        
    except Exception as e:
        print(f"[ERROR] Error applying preset: {e}")
        return jsonify({"success": False, "error": "Failed to apply preset", "details": str(e)}), 500

# --- Server Start Function --- 

def start_server(main_window=None, state_manager=None, update_callback=None, port=5000, user_data_dir=None, host='0.0.0.0'):
    """
    Starts the Flask server with optional integration to GUI components.
    
    Args:
        main_window: QMainWindow reference for closing app with API if needed
        state_manager: Reference to the settings/state manager object
        update_callback: Function to call to update UI after settings change
        port: Port number to use (default: 5000)
        user_data_dir: User data directory for uploads, profiles, etc. (default: None)
        host: Host to bind to (default: '0.0.0.0' to listen on all interfaces)
    """
    global _main_window_ref, state_manager_ref, update_callback_ref, _upload_folder_path, _profiles_folder_path, _presets_folder_path, _template_folder_path, _static_folder_path
    
    print("[DEBUG] Server starting...")
    print(f"[DEBUG] Current directory: {os.getcwd()}")
    print(f"[DEBUG] Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    # Store references to GUI components if provided
    _main_window_ref = main_window
    state_manager_ref = state_manager
    update_callback_ref = update_callback
    
    # Detect if we're running in a PyInstaller bundle
    in_pyinstaller = hasattr(sys, '_MEIPASS')
    print(f"[DEBUG] Running in PyInstaller bundle: {in_pyinstaller}")
    
    # Set up app folders
    if user_data_dir:
        # Use the provided user data directory
        base_dir = user_data_dir
        _upload_folder_path = os.path.join(base_dir, UPLOAD_FOLDER)
        _profiles_folder_path = os.path.join(base_dir, PROFILES_FOLDER)
        
        # For presets, first try in user data dir, then fallback to bundled resources
        _presets_folder_path = os.path.join(base_dir, PRESETS_FOLDER)
        
        # Copy bundled presets to user presets directory if it doesn't exist or is empty
        if in_pyinstaller and (not os.path.exists(_presets_folder_path) or not os.listdir(_presets_folder_path)):
            os.makedirs(_presets_folder_path, exist_ok=True)
            
            # Try to copy presets from bundled resources
            source_presets = [
                os.path.join(sys._MEIPASS, PRESETS_FOLDER),
                os.path.join(sys._MEIPASS, 'static', 'presets'),
                os.path.join(sys._MEIPASS, 'static', 'presets', 'animated')
            ]
            
            for source_path in source_presets:
                if os.path.exists(source_path):
                    print(f"[DEBUG] Found bundled presets in: {source_path}")
                    # Copy presets to user directory
                    for item in os.listdir(source_path):
                        if item.lower().endswith(('.gif', '.png')) and os.path.isfile(os.path.join(source_path, item)):
                            source_file = os.path.join(source_path, item)
                            dest_file = os.path.join(_presets_folder_path, item)
                            print(f"[DEBUG] Copying preset: {item} to user directory")
                            shutil.copy2(source_file, dest_file)
            
            # If still empty, use bundled presets
            if not os.listdir(_presets_folder_path):
                bundled_presets = os.path.join(sys._MEIPASS, PRESETS_FOLDER)
                if os.path.exists(bundled_presets):
                    _presets_folder_path = bundled_presets
                    print(f"[DEBUG] Using bundled presets: {_presets_folder_path}")
    else:
        # Default to folders in the application directory
        if in_pyinstaller:
            # If running from PyInstaller bundle, use executable directory for user data
            exe_dir = os.path.dirname(sys.executable)
            
            # Check for _internal folder structure (common in production installations)
            internal_dir = os.path.join(exe_dir, "_internal")
            if os.path.exists(internal_dir) and os.path.isdir(internal_dir):
                print(f"[DEBUG] Found _internal folder structure: {internal_dir}")
                
                # Use the internal folder for presets
                _presets_folder_path = os.path.join(internal_dir, PRESETS_FOLDER)
                
                # But keep user-specific data in the main app directory
                _upload_folder_path = os.path.join(exe_dir, UPLOAD_FOLDER)
                _profiles_folder_path = os.path.join(exe_dir, PROFILES_FOLDER)
            else:
                # Standard structure without _internal folder
                _upload_folder_path = os.path.join(exe_dir, UPLOAD_FOLDER)
                _profiles_folder_path = os.path.join(exe_dir, PROFILES_FOLDER)
                _presets_folder_path = os.path.join(exe_dir, PRESETS_FOLDER)
            
            # Initialize presets if they don't exist
            if not os.path.exists(_presets_folder_path) or not os.listdir(_presets_folder_path):
                os.makedirs(_presets_folder_path, exist_ok=True)
                
                # Try to copy presets from bundled resources
                source_presets = [
                    os.path.join(sys._MEIPASS, PRESETS_FOLDER),
                    os.path.join(sys._MEIPASS, 'static', 'presets'),
                    os.path.join(sys._MEIPASS, 'static', 'presets', 'animated'),
                    os.path.join(internal_dir, PRESETS_FOLDER) if os.path.exists(internal_dir) else None
                ]
                
                for source_path in source_presets:
                    if source_path and os.path.exists(source_path):
                        print(f"[DEBUG] Found bundled presets in: {source_path}")
                        # Copy presets to user directory
                        for item in os.listdir(source_path):
                            if item.lower().endswith(('.gif', '.png')) and os.path.isfile(os.path.join(source_path, item)):
                                source_file = os.path.join(source_path, item)
                                dest_file = os.path.join(_presets_folder_path, item)
                                print(f"[DEBUG] Copying preset: {item} to executable directory")
                                shutil.copy2(source_file, dest_file)
                
                # If still empty, use bundled presets
                if not os.listdir(_presets_folder_path):
                    # Check in _internal first
                    if os.path.exists(internal_dir):
                        internal_presets = os.path.join(internal_dir, PRESETS_FOLDER)
                        if os.path.exists(internal_presets):
                            _presets_folder_path = internal_presets
                            print(f"[DEBUG] Using internal presets: {_presets_folder_path}")
                    
                    # If still not found, try in MEIPASS
                    if not os.path.exists(_presets_folder_path) or not os.listdir(_presets_folder_path):
                        bundled_presets = os.path.join(sys._MEIPASS, PRESETS_FOLDER)
                        if os.path.exists(bundled_presets):
                            _presets_folder_path = bundled_presets
                            print(f"[DEBUG] Using bundled presets: {_presets_folder_path}")
        else:
            # Development environment
            base_dir = os.path.dirname(os.path.abspath(__file__))
            _upload_folder_path = os.path.join(base_dir, UPLOAD_FOLDER)
            _profiles_folder_path = os.path.join(base_dir, PROFILES_FOLDER)
            _presets_folder_path = get_resource_path(PRESETS_FOLDER)
    
    # Adjust template and static folders for PyInstaller bundled app
    try:
        if in_pyinstaller:
            # If we're in a PyInstaller bundle, use _MEIPASS for template and static paths
            _template_folder_path = os.path.join(sys._MEIPASS, 'templates')
            _static_folder_path = os.path.join(sys._MEIPASS, 'static')
        else:
            # In development, use the usual paths
            _template_folder_path = get_resource_path('templates')
            _static_folder_path = get_resource_path('static')
            
        # Debug info
        print(f"[DEBUG] Template folder path: {_template_folder_path}")
        print(f"[DEBUG] Static folder path: {_static_folder_path}")
        print(f"[DEBUG] Template folder exists: {os.path.exists(_template_folder_path)}")
        print(f"[DEBUG] Static folder exists: {os.path.exists(_static_folder_path)}")
    except Exception as e:
        print(f"[ERROR] Exception while setting template paths: {e}")
        # Fallback to safe defaults
        _template_folder_path = get_resource_path('templates')
        _static_folder_path = get_resource_path('static')
    
    # Update Flask config if needed 
    app.template_folder = _template_folder_path
    app.static_folder = _static_folder_path
    
    # Ensure directories exist
    os.makedirs(_upload_folder_path, exist_ok=True)
    os.makedirs(_profiles_folder_path, exist_ok=True)
    
    # Don't try to create the presets directory if it's inside the bundle
    if not (_presets_folder_path.startswith(sys._MEIPASS) if in_pyinstaller else False):
        os.makedirs(_presets_folder_path, exist_ok=True)
    
    # Configure app
    app.config['UPLOAD_FOLDER'] = _upload_folder_path
    app.config['PROFILES_FOLDER'] = _profiles_folder_path 
    app.config['PRESETS_FOLDER'] = _presets_folder_path
    
    # Create default profile files if the profiles directory is empty
    if os.path.exists(_profiles_folder_path) and not os.listdir(_profiles_folder_path):
        print("[DEBUG] Creating default profile files...")
        
        # Copy selected presets to uploads folder for use in default profiles
        default_presets = [
            {"filename": "crosshair1.gif", "profile_name": "Default_Animated_1"},
            {"filename": "crosshair10.gif", "profile_name": "Default_Animated_2"},
            {"filename": "crosshair16.gif", "profile_name": "Default_Animated_3"}
        ]
        
        # Ensure uploads directory exists
        os.makedirs(_upload_folder_path, exist_ok=True)
        print(f"[DEBUG] Ensuring upload folder exists at: {_upload_folder_path}")
        
        # Create each default profile
        for preset in default_presets:
            preset_filename = preset["filename"]
            profile_name = preset["profile_name"]
            
            # Find the preset file - try multiple locations
            preset_path = None
            possible_preset_locations = [
                os.path.join(_presets_folder_path, preset_filename)
            ]
            
            # Add internal dir location if it exists
            internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
            if os.path.exists(internal_dir):
                possible_preset_locations.append(os.path.join(internal_dir, PRESETS_FOLDER, preset_filename))
            
            # Add PyInstaller locations if applicable
            if in_pyinstaller:
                possible_preset_locations.extend([
                    os.path.join(sys._MEIPASS, PRESETS_FOLDER, preset_filename),
                    os.path.join(sys._MEIPASS, 'static', 'presets', preset_filename)
                ])
            
            # Find the first valid preset path
            for path in possible_preset_locations:
                if os.path.exists(path):
                    preset_path = path
                    print(f"[DEBUG] Found preset at: {preset_path}")
                    break
            
            if preset_path:
                # Copy the preset to uploads folder
                dest_file = os.path.join(_upload_folder_path, preset_filename)
                try:
                    shutil.copy2(preset_path, dest_file)
                    print(f"[DEBUG] Copied {preset_filename} to uploads folder: {dest_file}")
                    
                    # Create default profile using this preset
                    profile_data = {
                        "type": "animated",
                        "parametric": {
                            "center_dot_enabled": True,
                            "center_dot_color": "#ff0000",
                            "center_dot_size": 3,
                            "center_dot_opacity": 255,
                            "inner_lines_enabled": True,
                            "inner_lines_color": "#ffffff",
                            "inner_lines_thickness": 1,
                            "inner_lines_length": 5,
                            "inner_lines_gap": 3,
                            "inner_lines_opacity": 255,
                            "outer_lines_enabled": False,
                            "outer_lines_color": "#00FF00",
                            "outer_lines_thickness": 1,
                            "outer_lines_length": 2,
                            "outer_lines_gap": 8,
                            "outer_lines_opacity": 180,
                            "outline_enabled": True,
                            "outline_color": "#000000",
                            "outline_thickness": 1,
                            "outline_opacity": 150,
                            "t_shape": False
                        },
                        "static": {
                            "image_path": None,
                            "opacity": 255,
                            "scale": 1
                        },
                        "animated": {
                            "gif_path": preset_filename,
                            "opacity": 255,
                            "scale": 1,
                            "speed": 100
                        }
                    }
                    
                    # Save profile file
                    profile_path = os.path.join(_profiles_folder_path, f"{profile_name}.json")
                    with open(profile_path, 'w') as f:
                        json.dump(profile_data, f, indent=4)
                    print(f"[DEBUG] Created default profile: {profile_name} at {profile_path}")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to create default profile {profile_name}: {e}")
            else:
                print(f"[WARNING] Could not find preset file: {preset_filename} in any location")
        
        # Also create a default parametric profile
        default_parametric = {
            "type": "parametric",
            "parametric": {
                "center_dot_enabled": True,
                "center_dot_color": "#00ff00",  # Green dot
                "center_dot_size": 4,
                "center_dot_opacity": 200,
                "inner_lines_enabled": True,
                "inner_lines_color": "#ffffff",  # White lines
                "inner_lines_thickness": 2,
                "inner_lines_length": 8,
                "inner_lines_gap": 4,
                "inner_lines_opacity": 225,
                "outer_lines_enabled": True,
                "outer_lines_color": "#ffffff",  # White outer lines
                "outer_lines_thickness": 1,
                "outer_lines_length": 3,
                "outer_lines_gap": 10,
                "outer_lines_opacity": 180,
                "outline_enabled": True,
                "outline_color": "#000000",  # Black outline
                "outline_thickness": 1,
                "outline_opacity": 150,
                "t_shape": False
            },
            "static": {
                "image_path": None,
                "opacity": 255,
                "scale": 1
            },
            "animated": {
                "gif_path": None,
                "opacity": 255,
                "scale": 1,
                "speed": 100
            }
        }
        
        # Save default parametric profile
        profile_path = os.path.join(_profiles_folder_path, "Default_Parametric.json")
        with open(profile_path, 'w') as f:
            json.dump(default_parametric, f, indent=4)
        print(f"[DEBUG] Created default parametric profile at {profile_path}")
    
    print(f"Server starting on port {port}")
    print(f"Upload folder: {_upload_folder_path}")
    print(f"Profiles folder: {_profiles_folder_path}")
    print(f"Presets folder: {_presets_folder_path} (exists: {os.path.exists(_presets_folder_path)})")
    print(f"Templates folder: {_template_folder_path} (exists: {os.path.exists(_template_folder_path)})")
    print(f"Static folder: {_static_folder_path} (exists: {os.path.exists(_static_folder_path)})")
    
    # Start the server in a separate thread
    threading.Thread(target=lambda: app.run(
        host=host, 
        port=port, 
        debug=False, 
        use_reloader=False
    )).start()
    
    return app

# Example for testing server independently (optional)
if __name__ == '__main__':
    print("Starting Flask server directly for testing...")
    start_server(port=5001) 