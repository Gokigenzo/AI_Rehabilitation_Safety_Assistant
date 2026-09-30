# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification for AI REHABILITATION & SAFETY ASSISTANT.
Compiles a standalone, highly-optimized Windows application bundle with all
OpenCV DNN models, PyTorch ExpressionNet weights, MediaPipe Pose & FaceMesh pipelines,
and PyQt5 UI resources included.
"""

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
PROJECT_ROOT = Path(os.path.abspath(SPECPATH))

# Collect MediaPipe data files (binary graphs, tflite models)
mediapipe_datas = collect_data_files('mediapipe')

# Project assets and models to bundle
datas = [
    # Static model binaries
    (str(PROJECT_ROOT / 'modules' / 'face' / 'models'), os.path.join('modules', 'face', 'models')),
    (str(PROJECT_ROOT / 'modules' / 'emotion' / 'models'), os.path.join('modules', 'emotion', 'models')),
    # Baseline shared structures
    (str(PROJECT_ROOT / 'shared' / 'data'), os.path.join('shared', 'data')),
]
datas.extend(mediapipe_datas)

# Comprehensive hidden imports for dynamic C-extensions
hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'cv2',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'torch',
    'torch.nn',
    'torch.nn.functional',
    'mediapipe',
    'mediapipe.python',
    'mediapipe.python.solutions',
    'mediapipe.python.solutions.pose',
    'mediapipe.python.solutions.face_mesh',
    'mediapipe.python.solutions.drawing_utils',
    'google.protobuf',
    'google.protobuf.symbol_database',
    'numpy',
    'dotenv',
    'smtplib',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.base',
    # Project internal packages
    'adapters',
    'adapters.face_adapter',
    'adapters.emotion_adapter',
    'adapters.rehabilitation_adapter',
    'adapters.fall_adapter',
    'core',
    'core.camera_manager',
    'core.drawing_utils',
    'services',
    'services.user_service',
    'services.email_service',
    'services.fall_monitor',
    'services.state_service',
    'modules',
    'modules.fall.fall_detector',
    'modules.rehabilitation.rehab_engine',
    'app',
    'app.dashboard',
    'app.router',
    'app.state',
    'app.registration_dialog',
    'app.patient_management_dialog',
]
hiddenimports.extend(collect_submodules('mediapipe'))

a = Analysis(
    ['main.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython', 'notebook', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI_Rehab_Safety_Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed GUI application without black console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI_Rehab_Safety_Assistant',
)
