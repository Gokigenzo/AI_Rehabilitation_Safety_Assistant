"""
Main Entry Point for AI_for_older MVP System.
Launches the PyQt5 AI Care & Rehabilitation System Dashboard.
"""

from __future__ import annotations

import logging
import os
import sys

# Configure environment for MediaPipe Protobuf & Qt platform plugins
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import PyQt5
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication

pyqt5_plugins = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
pyqt5_platforms = os.path.join(pyqt5_plugins, "platforms")
if os.path.exists(pyqt5_platforms):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = pyqt5_platforms
QCoreApplication.setLibraryPaths([pyqt5_plugins])

from config import LOG_FILE

logger = logging.getLogger("Main")


def main() -> int:
    """Initialize and run PyQt5 application event loop."""
    logger.info("Starting AI CARE & REHABILITATION SYSTEM (PyQt5)...")
    logger.info("Logging to: %s", LOG_FILE)

    app = QApplication(sys.argv)
    app.setApplicationName("AI Care & Rehabilitation System")

    # Import DashboardWindow and STYLESHEET after QApplication is created
    from app.dashboard import DashboardWindow, STYLESHEET
    app.setStyleSheet(STYLESHEET)

    # If --test flag is passed, instantiate window, test UI sync and exit cleanly
    if "--test" in sys.argv:
        window = DashboardWindow()
        window.update_dashboard_ui()
        window._on_timer_tick()
        app.processEvents()
        logger.info("Dashboard initialized and UI updated successfully in test mode. Exiting.")
        window.camera_manager.stop_camera()
        if hasattr(window.camera_manager, "wait"):
            window.camera_manager.wait(1000)
        return 0

    window = DashboardWindow()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
