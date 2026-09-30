"""
Central Configuration for AI_for_older MVP Integration.
Provides directory paths, runtime settings, thresholds, and logging configuration.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base paths & PyInstaller frozen bundle detection
if getattr(sys, "frozen", False):
    # Running inside compiled PyInstaller binary (.exe)
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BUNDLE_DIR = Path(__file__).resolve().parent
    BASE_DIR = BUNDLE_DIR

load_dotenv(BASE_DIR / ".env")

# Bundled static AI models and assets (read-only)
MODULES_DIR = BUNDLE_DIR / "modules"

# Persistent user data directories (written locally next to .exe)
DATA_DIR = BASE_DIR / "data"
USERS_DIR = DATA_DIR / "users"
SESSIONS_DIR = DATA_DIR / "sessions"
FALL_EVENTS_DIR = DATA_DIR / "fall_events"

SHARED_DIR = BASE_DIR / "shared"
SHARED_DATA_DIR = SHARED_DIR / "data"
SHARED_RESULTS_DIR = SHARED_DIR / "results"
SHARED_ALERTS_DIR = SHARED_DIR / "alerts"
SHARED_RECORDINGS_DIR = SHARED_DIR / "recordings"
SHARED_REPORTS_DIR = SHARED_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Ensure all vital directories exist
for directory in (
    SHARED_DIR,
    SHARED_DATA_DIR,
    SHARED_RESULTS_DIR,
    LOGS_DIR,
    DATA_DIR,
    USERS_DIR,
    SESSIONS_DIR,
    FALL_EVENTS_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)

# Fall Detection & Temporal Verification Parameters (Configurable)
FALL_CONFIRM_SECONDS = float(os.getenv("FALL_CONFIRM_SECONDS", "3.0"))
FALL_CONFIDENCE_THRESHOLD = float(os.getenv("FALL_CONFIDENCE_THRESHOLD", "0.75"))
FALL_COOLDOWN_SECONDS = float(os.getenv("FALL_COOLDOWN_SECONDS", "30.0"))

# Email Alert Configuration (Caregiver notifications)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() in ("true", "1", "yes")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Python runtime executable: prefer project venv
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"
if VENV_PYTHON.exists():
    PYTHON_EXE = str(VENV_PYTHON)
else:
    PYTHON_EXE = sys.executable

# Camera settings
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
FRAME_WIDTH = int(os.getenv("FRAME_WIDTH", "640"))
FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", "480"))
FPS_TARGET = int(os.getenv("FPS_TARGET", "30"))

# Default User / Patient configuration
DEFAULT_PATIENT_ID = "patient_001"
DEFAULT_PATIENT_NAME = "tonghoanganh"

# Rehabilitation Exercise Configurations
EXERCISES = {
    "sit_to_stand": {
        "id": "sit_to_stand",
        "name": "Co duỗi chân (Đứng lên ngồi xuống)",
        "name_short": "Đứng lên ngồi xuống",
        "target_reps": 10,
        "instructions": "Ngồi gập gối vuông góc, sau đó đứng thẳng hoàn toàn rồi ngồi xuống chậm rãi.",
    },
    "arm_raise": {
        "id": "arm_raise",
        "name": "Vươn vai (Nâng tay qua đầu)",
        "name_short": "Nâng tay qua đầu",
        "target_reps": 12,
        "instructions": "Nâng hai tay thẳng lên qua vai, giữ 1 nhịp trên cao rồi hạ đều xuống.",
    },
    "marching": {
        "id": "marching",
        "name": "Đi bộ tại chỗ (Nâng cao đùi)",
        "name_short": "Nâng cao đùi tại chỗ",
        "target_reps": 20,
        "instructions": "Nâng luân phiên đùi trái và đùi phải lên ngang hông, giữ thẳng người.",
    },
}

# Setup standard logging
LOG_FILE = LOGS_DIR / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("AI_Rehab_Assistant")
