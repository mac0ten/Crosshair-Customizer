import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def check_directory_structure():
    """Check if all required directories exist"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)  # Make sure we're in the project root
    
    required_dirs = ['templates', 'static', 'src']
    optional_dirs = ['profiles', 'user_uploads', 'presets']
    
    # Check required directories
    missing_required = []
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_required.append(dir_name)
    
    if missing_required:
        print("ERROR: Required directories are missing:")
        for dir_name in missing_required:
            print(f"  - {dir_name}")
        return False
    
    # Check for optional directories and create if missing
    for dir_name in optional_dirs:
        if not os.path.exists(dir_name):
            print(f"Creating missing directory: {dir_name}")
            os.makedirs(dir_name, exist_ok=True)
    
    # Make sure src/main.py exists
    main_py = os.path.join('src', 'main.py')
    if not os.path.exists(main_py):
        print(f"ERROR: {main_py} not found!")
        return False
    
    print("Directory structure is valid.")
    return True

def clean_build_folders():
    """Remove old build and dist folders"""
    folders_to_clean = ['build', 'dist']
    
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"Removing {folder} directory...")
            try:
                shutil.rmtree(folder)
                print(f"{folder} directory removed successfully")
            except Exception as e:
                print(f"Warning: Could not remove {folder} directory: {e}")
                print("You may need to close any applications using these files.")
                return False
    
    return True

def build_executable():
    """Build the executable using PyInstaller"""
    print("\n=== Building executable with PyInstaller ===\n")
    
    # Get base directory
    base_dir = os.getcwd()
    main_file = os.path.join(base_dir, 'src', 'main.py')
    
    # Create the PyInstaller command with explicit paths
    cmd = [
        'pyinstaller',
        '--name=CrosshairTool',
        '--icon=static/crosshair_icon.ico',
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--add-data=profiles;profiles',
        '--add-data=user_uploads;user_uploads',
        '--add-data=presets;presets',
        '--noconfirm',
        '--clean',
        '--onedir',
        '--console',  # For debugging
        main_file
    ]
    
    # Run the command
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        print("Output:")
        print(process.stdout)
        
        # Check for errors
        if process.returncode != 0:
            print("\nErrors:")
            print(process.stderr)
            print(f"\nCommand failed with code {process.returncode}")
            return False
        
        print("Executable built successfully!")
        return True
    except Exception as e:
        print(f"Error building executable: {e}")
        return False

def main():
    print("=== CrosshairTool Build Script ===")
    
    # Check and setup directory structure
    if not check_directory_structure():
        print("Failed directory structure check. Aborting build.")
        return False
    
    # Clean old builds
    if not clean_build_folders():
        print("Failed to clean build folders. Aborting build.")
        return False
    
    # Build executable
    if not build_executable():
        print("Failed to build executable.")
        return False
    
    # Success
    print("\n=== Build completed successfully! ===")
    
    # Print output locations
    exe_path = os.path.abspath(os.path.join('dist', 'CrosshairTool', 'CrosshairTool.exe'))
    if os.path.exists(exe_path):
        print(f"\nExecutable can be found at:\n{exe_path}")
    else:
        print("\nWarning: Executable not found at expected location.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 