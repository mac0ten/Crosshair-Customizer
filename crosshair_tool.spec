# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None

# Use current working directory instead of SPECPATH
base_dir = os.path.abspath(os.getcwd())
print(f"Base directory: {base_dir}")

# Define source file
main_file = os.path.join(base_dir, 'src', 'main.py')
if not os.path.exists(main_file):
    print(f"ERROR: Source file not found: {main_file}")
    sys.exit(1)

# Collect all required data files
data_files = [
    # Important folders that need to be included
    (os.path.join(base_dir, 'templates'), 'templates'),
    (os.path.join(base_dir, 'static'), 'static'),
    (os.path.join(base_dir, 'profiles'), 'profiles'),
    (os.path.join(base_dir, 'user_uploads'), 'user_uploads'),
    (os.path.join(base_dir, 'presets'), 'presets'),
]

# Filter out non-existent directories
filtered_data_files = []
for src_path, dest_path in data_files:
    if not os.path.exists(src_path):
        print(f"WARNING: Directory {src_path} does not exist!")
    else:
        print(f"Found directory: {src_path}")
        filtered_data_files.append((src_path, dest_path))

# Make sure we have at least templates and static
if not any(dest == 'templates' for _, dest in filtered_data_files):
    print("ERROR: Templates directory not found! Application will not work correctly.")
    sys.exit(1)
if not any(dest == 'static' for _, dest in filtered_data_files):
    print("ERROR: Static directory not found! Application will not work correctly.")
    sys.exit(1)

a = Analysis(
    [main_file],
    pathex=[base_dir],
    binaries=[],
    datas=filtered_data_files,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'flask',
        'PIL',
        'werkzeug.middleware',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'IPython', 'matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Print debug info about what's being collected
for data_item in a.datas:
    if 'template' in data_item[0] or 'static' in data_item[0] or 'preset' in data_item[0]:
        print(f"Including: {data_item}")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CrosshairTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True temporarily for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_dir, 'static', 'crosshair_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CrosshairTool',
) 