import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

def ensure_directories():
    """Ensure necessary directories exist."""
    os.makedirs('dist', exist_ok=True)
    os.makedirs('build', exist_ok=True)
    os.makedirs('profiles', exist_ok=True)
    os.makedirs('user_uploads', exist_ok=True)
    os.makedirs('presets', exist_ok=True)  # Add presets directory
    
    # Verify critical directories exist
    required_dirs = ['templates', 'static', 'src']
    missing = []
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing.append(dir_name)
    
    if missing:
        print("ERROR: Required directories are missing:")
        for dir_name in missing:
            print(f"  - {dir_name}")
        print("These directories are required for the application to function correctly.")
        return False
    
    return True

def run_command(command, description):
    """Run a command and print its output."""
    print(f"\n\n{'=' * 80}\n{description}\n{'=' * 80}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    
    if result.stdout:
        print("\nOutput:")
        print(result.stdout)
    
    if result.stderr:
        print("\nErrors:")
        print(result.stderr)
        
    if result.returncode != 0:
        print(f"\nCommand failed with code {result.returncode}")
        return False
        
    print(f"\nCommand completed successfully!")
    return True

def clean_build():
    """Clean previous build artifacts."""
    # First, try to terminate any running instances of our application
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            if 'CrosshairTool.exe' in proc.info['name']:
                print(f"Terminating running instance with PID {proc.info['pid']}")
                try:
                    proc_obj = psutil.Process(proc.info['pid'])
                    proc_obj.terminate()
                    # Wait for up to 3 seconds for process to terminate
                    proc_obj.wait(timeout=3)
                except Exception as e:
                    print(f"Could not terminate process: {e}")
    except ImportError:
        print("psutil not installed, skipping process termination")
    except Exception as e:
        print(f"Error while checking for running processes: {e}")
    
    # Add a small delay to let processes fully terminate
    time.sleep(1)
    
    # Now try to remove directories
    try:
        if os.path.exists('build'):
            print("Removing build directory...")
            try:
                shutil.rmtree('build')
                print("Build directory removed successfully")
            except Exception as e:
                print(f"Warning: Could not remove build directory: {e}")
        
        if os.path.exists('dist'):
            print("Removing dist directory...")
            try:
                # We'll try to selectively remove files, ignoring locked ones
                for root, dirs, files in os.walk('dist', topdown=False):
                    for name in files:
                        try:
                            os.unlink(os.path.join(root, name))
                        except Exception as e:
                            print(f"Warning: Could not remove {os.path.join(root, name)}: {e}")
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except Exception as e:
                            print(f"Warning: Could not remove directory {os.path.join(root, name)}: {e}")
                
                # Try to remove the main dist directory as well
                try:
                    os.rmdir('dist')
                    print("Dist directory removed successfully")
                except Exception as e:
                    print(f"Warning: Could not remove dist directory: {e}")
            except Exception as e:
                print(f"Warning: Error while cleaning dist directory: {e}")
                
    except Exception as e:
        print(f"Error cleaning build directories: {e}")
        print("You may need to close any applications using these files.")
        
    # Print reminder to the user
    print("\nNOTE: If you're seeing access denied errors, please:")
    print("1. Close any File Explorer windows that might be viewing the dist or build folders")
    print("2. Ensure no CrosshairTool.exe process is running in Task Manager")
    print("3. Try again\n")

def build_executable():
    """Build the executable using PyInstaller."""
    # Clean previous builds
    try:
        clean_build()
    except:
        print("Warning: Could not clean previous builds. Continuing anyway.")
    
    # Ensure required directories exist
    if not ensure_directories():
        print("ERROR: Missing required directories. Cannot continue.")
        return False
    
    # Copy any presets to ensure they're included
    presets_dir = os.path.join(os.getcwd(), 'presets')
    if not os.path.exists(presets_dir) or len(os.listdir(presets_dir)) == 0:
        # Try to copy presets from static/presets if available
        static_presets = os.path.join(os.getcwd(), 'static', 'presets')
        if os.path.exists(static_presets) and os.listdir(static_presets):
            print(f"Copying presets from {static_presets} to {presets_dir}")
            if not os.path.exists(presets_dir):
                os.makedirs(presets_dir)
            for item in os.listdir(static_presets):
                source = os.path.join(static_presets, item)
                if os.path.isfile(source) and (item.endswith('.gif') or item.endswith('.png')):
                    destination = os.path.join(presets_dir, item)
                    shutil.copy2(source, destination)
                    print(f"  - Copied {item}")
    
    # Print debug info about presets
    print("\nPresets directory contents:")
    if os.path.exists(presets_dir):
        presets_files = os.listdir(presets_dir)
        if presets_files:
            for item in presets_files:
                print(f"  - {item}")
        else:
            print("  (empty)")
    else:
        print("  (directory not found)")
    
    # Define explicit data directories to include
    data_includes = [
        f"--add-data=templates{os.pathsep}templates",
        f"--add-data=static{os.pathsep}static",
        f"--add-data=profiles{os.pathsep}profiles",
        f"--add-data=user_uploads{os.pathsep}user_uploads",
        f"--add-data=presets{os.pathsep}presets"
    ]
    
    # Define libraries to exclude - PyQt5 conflicts with PySide6
    exclude_libs = [
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        "--exclude-module=IPython",
        "--exclude-module=matplotlib",
        "--exclude-module=notebook"
    ]
    
    # Build PyInstaller command with explicit data includes
    pyinstaller_cmd = "pyinstaller --clean -y --noconsole "  # Add console flag for debugging
    pyinstaller_cmd += " ".join(data_includes) + " "
    pyinstaller_cmd += " ".join(exclude_libs) + " "
    pyinstaller_cmd += " --name=CrosshairTool --icon=static/crosshair_icon.ico src/main.py"
    
    # Run PyInstaller with explicit options
    success = run_command(
        pyinstaller_cmd,
        "Building executable with PyInstaller"
    )
    
    if not success:
        print("Failed to build executable.")
        return False
    
    # Verify that presets were included in the build
    dist_presets = os.path.join('dist', 'CrosshairTool', 'presets')
    print("\nVerifying presets in build:")
    if os.path.exists(dist_presets):
        dist_presets_files = os.listdir(dist_presets)
        if dist_presets_files:
            print("Presets included in build:")
            for item in dist_presets_files:
                print(f"  - {item}")
        else:
            print("WARNING: Presets directory is empty in the build")
    else:
        print("WARNING: Presets directory not found in the build")
        
    print("\nExecutable built successfully!")
    return True

def find_nsis():
    """Try to find NSIS installation."""
    # Common NSIS installation paths
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]
    
    for path in nsis_paths:
        if os.path.exists(path):
            return path
            
    return None

def create_nsis_script(installer_filename="CrosshairTool-Installer-v1.0.0.exe"):
    """Create an NSIS installation script with the specified output filename."""
    version = "1.0.0"  # You may want to get this from your project
    
    nsis_script = f"""
; CrosshairTool Installer Script
!include "MUI2.nsh"

; Basic definitions
Name "Crosshair Tool"
OutFile "dist\\{installer_filename}"
InstallDir "$PROGRAMFILES64\\CrosshairTool"
InstallDirRegKey HKCU "Software\\CrosshairTool" ""

; Request application privileges
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-install.ico"
!define MUI_UNICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-uninstall.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installation section
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Add files/directories
    File /r "dist\\CrosshairTool\\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\Crosshair Tool"
    CreateShortcut "$SMPROGRAMS\\Crosshair Tool\\Crosshair Tool.lnk" "$INSTDIR\\CrosshairTool.exe"
    CreateShortcut "$SMPROGRAMS\\Crosshair Tool\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    CreateShortcut "$DESKTOP\\Crosshair Tool.lnk" "$INSTDIR\\CrosshairTool.exe"
    
    ; Write registry keys for uninstall
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\CrosshairTool" \\
                     "DisplayName" "Crosshair Tool"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\CrosshairTool" \\
                     "UninstallString" "$\\"$INSTDIR\\uninstall.exe$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\CrosshairTool" \\
                     "DisplayIcon" "$INSTDIR\\CrosshairTool.exe,0"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\CrosshairTool" \\
                     "Publisher" "Your Organization"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\CrosshairTool" \\
                     "DisplayVersion" "{version}"
SectionEnd

; Uninstallation section
Section "Uninstall"
    ; Remove files and uninstaller
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\\Crosshair Tool.lnk"
    RMDir /r "$SMPROGRAMS\\Crosshair Tool"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\CrosshairTool"
SectionEnd
"""

    # Write the NSIS script to a file
    script_path = "installer.nsi"
    with open(script_path, "w") as f:
        f.write(nsis_script)
        
    return script_path

def build_installer():
    """Build an installer using NSIS if available."""
    nsis_path = find_nsis()
    
    if not nsis_path:
        print("\nNSIS not found. Installing NSIS would allow you to create a proper installer.")
        print("Download NSIS from: https://nsis.sourceforge.io/Download")
        return False
    
    # Create a timestamp-based installer filename to avoid conflicts
    version = "1.0.0"
    installer_filename = f"CrosshairTool-Installer-v{version}-{int(time.time())}.exe"
    
    # Create the NSIS script with the new filename
    try:
        script_path = create_nsis_script(installer_filename)
    except Exception as e:
        print(f"Error creating NSIS script: {e}")
        return False
    
    # Run NSIS
    success = run_command(
        f'"{nsis_path}" "{script_path}"',
        "Building installer with NSIS"
    )
    
    if not success:
        print("Failed to build installer.")
        return False
        
    print("\nInstaller built successfully!")
    return True

def create_zip_package():
    """Create a ZIP package of the application as an alternative to an installer."""
    import zipfile
    
    dist_dir = os.path.join(os.getcwd(), 'dist', 'CrosshairTool')
    zip_path = os.path.join(os.getcwd(), 'dist', 'CrosshairTool-Portable.zip')
    
    if not os.path.exists(dist_dir):
        print("Distribution directory not found. Build the executable first.")
        return False
    
    try:
        print(f"\nCreating ZIP package at {zip_path}...")
        # Delete existing zip if it exists
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
                print(f"Removed existing zip file: {zip_path}")
            except Exception as e:
                print(f"Warning: Could not remove existing zip file: {e}")
                # Try an alternative filename
                zip_path = os.path.join(os.getcwd(), 'dist', f'CrosshairTool-Portable-{int(time.time())}.zip')
                print(f"Using alternative filename: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        arcname = os.path.relpath(file_path, dist_dir)
                        zipf.write(file_path, arcname)
                    except Exception as e:
                        print(f"Warning: Could not add {file_path} to zip: {e}")
        
        print("\nZIP package created successfully!")
        return True
    except Exception as e:
        print(f"Error creating ZIP package: {e}")
        return False

def main():
    print("CrosshairTool Build Script")
    print("==========================")
    
    # Build the executable
    exe_success = build_executable()
    if not exe_success:
        sys.exit(1)
    
    # Create a portable ZIP package
    zip_success = create_zip_package()
    
    # Try to build an installer
    installer_built = False
    installer_file = None
    
    try:
        # Try to find the most recent installer file before building
        old_installers = [f for f in os.listdir('dist') if f.startswith('CrosshairTool-Installer') and f.endswith('.exe')]
        old_installers_with_time = [(f, os.path.getmtime(os.path.join('dist', f))) for f in old_installers]
        old_installers_with_time.sort(key=lambda x: x[1])  # Sort by modification time
        
        # Build the installer
        installer_built = build_installer()
        
        # Find the new installer file
        if installer_built:
            new_installers = [f for f in os.listdir('dist') if f.startswith('CrosshairTool-Installer') and f.endswith('.exe')]
            if len(old_installers) < len(new_installers):
                # Find the file that wasn't in the old list
                for f in new_installers:
                    if f not in old_installers:
                        installer_file = f
                        break
            
            # If we couldn't find it that way, take the most recently modified file
            if not installer_file:
                new_installers_with_time = [(f, os.path.getmtime(os.path.join('dist', f))) for f in new_installers]
                new_installers_with_time.sort(key=lambda x: x[1], reverse=True)  # Sort by newest
                if new_installers_with_time:
                    installer_file = new_installers_with_time[0][0]
    except Exception as e:
        print(f"Error while building installer: {e}")
        installer_built = False
    
    # Final messages
    print("\n\nBuild Summary:")
    print("=============")
    print(f"Executable: {'? Success' if exe_success else '? Failed'}")
    print(f"ZIP Package: {'? Success' if zip_success else '? Failed'}")
    print(f"Installer: {'? Success' if installer_built else '? Not created (NSIS not found)'}")
    
    print("\nOutput files:")
    if exe_success:
        print(f"- Executable: {os.path.abspath('dist/CrosshairTool/CrosshairTool.exe')}")
    if zip_success:
        # Find the zip file that was actually created
        zip_files = [f for f in os.listdir('dist') if f.endswith('.zip') and f.startswith('CrosshairTool-Portable')]
        if zip_files:
            # Get the most recent one
            zip_files.sort(key=lambda f: os.path.getmtime(os.path.join('dist', f)), reverse=True)
            print(f"- ZIP Package: {os.path.abspath(os.path.join('dist', zip_files[0]))}")
        else:
            print(f"- ZIP Package: {os.path.abspath('dist/CrosshairTool-Portable.zip')}")
            
    if installer_built and installer_file:
        print(f"- Installer: {os.path.abspath(os.path.join('dist', installer_file))}")
    elif installer_built:
        print(f"- Installer: {os.path.abspath('dist')} (check for CrosshairTool-Installer-* files)")
    
    print("\nNext steps:")
    if not installer_built:
        print("- To create an installer, download and install NSIS from https://nsis.sourceforge.io/Download")
        print("  Then run this script again.")
    
    print("- Test the application by running the executable in the dist folder")
    print("- Distribute the ZIP package or installer to your users")

if __name__ == "__main__":
    main() 