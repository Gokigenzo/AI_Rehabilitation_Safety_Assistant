"""
Central Camera Manager for AI Rehabilitation Assistant.
Provides a unified, thread-safe camera capture engine to prevent multiple
modules from independently opening or contesting the hardware camera device.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import cv2
import numpy as np

# Qt imports for seamless GUI integration
try:
    from PyQt5.QtCore import QObject, QThread, pyqtSignal
    from PyQt5.QtGui import QImage
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    QThread = object
    pyqtSignal = lambda *args: None

from config import CAMERA_INDEX, FRAME_HEIGHT, FRAME_WIDTH

logger = logging.getLogger("CameraManager")


class CameraManager(QThread if QT_AVAILABLE else object):
    """
    Singleton Camera Capture and Distribution Engine.
    Guarantees that only ONE VideoCapture object exists across the entire system.
    """
    if QT_AVAILABLE:
        frame_ready = pyqtSignal(object)  # Emits QImage or np.ndarray
        raw_frame_ready = pyqtSignal(np.ndarray)

    _instance: Optional[CameraManager] = None
    _lock = threading.Lock()

    MODE_MONITOR = "monitor"
    MODE_REHABILITATION = "rehabilitation"

    def __init__(self, camera_index: int = CAMERA_INDEX) -> None:
        if QT_AVAILABLE:
            super().__init__()
        self.camera_index = camera_index
        self._running = False
        self._paused = False
        self._cap: Optional[cv2.VideoCapture] = None
        self._latest_raw_frame: Optional[np.ndarray] = None
        self._latest_annotated_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._fps: float = 30.0
        self._sim_tick: int = 0
        self._is_hardware_available = False
        self._mode = self.MODE_MONITOR
        self._frame_processors: List[Callable[[np.ndarray], np.ndarray]] = []

    @classmethod
    def get_instance(cls, camera_index: int = CAMERA_INDEX) -> CameraManager:
        """Thread-safe Singleton accessor."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = CameraManager(camera_index=camera_index)
            return cls._instance

    def set_mode(self, mode: str) -> None:
        """Switch active operational mode ('monitor' or 'rehabilitation')."""
        self._mode = mode
        logger.info("CameraManager switched mode to: %s", mode)

    def get_mode(self) -> str:
        return self._mode

    def is_hardware_camera(self) -> bool:
        """Returns True if a real physical camera is open."""
        return self._is_hardware_available

    def register_processor(self, processor_fn: Callable[[np.ndarray], np.ndarray]) -> None:
        """Register an active frame processing filter/annotator."""
        if processor_fn not in self._frame_processors:
            self._frame_processors.append(processor_fn)

    def unregister_processor(self, processor_fn: Callable[[np.ndarray], np.ndarray]) -> None:
        """Remove a previously registered frame processor."""
        if processor_fn in self._frame_processors:
            self._frame_processors.remove(processor_fn)

    def start_camera(self) -> bool:
        """Initialize camera capture and begin background thread."""
        if self._running:
            return True

        self._running = True
        if QT_AVAILABLE and isinstance(self, QThread):
            self.start()
        else:
            self._worker_thread = threading.Thread(target=self.run, daemon=True)
            self._worker_thread.start()
        return True

    def stop_camera(self) -> None:
        """Safely release camera hardware and terminate capture thread."""
        self._running = False
        if self._cap is not None:
            try:
                self._cap.release()
                logger.info("Released camera capture hardware.")
            except Exception as e:
                logger.error("Error releasing camera: %s", e)
            self._cap = None
        self._is_hardware_available = False

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Thread-safe getter for latest raw video frame."""
        with self._frame_lock:
            if self._latest_raw_frame is not None:
                return self._latest_raw_frame.copy()
            return None

    def _generate_simulated_frame(self) -> np.ndarray:
        """Generate high-contrast simulated test frame with dynamic animations."""
        self._sim_tick += 1
        frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)

        # Subtle dark gradient background
        for y in range(FRAME_HEIGHT):
            shade = int(18 + 15 * (y / FRAME_HEIGHT))
            frame[y, :] = (shade + 5, shade, shade - 5)

        # Simulated dynamic pulse avatar
        cx = int(FRAME_WIDTH / 2 + 60 * np.sin(self._sim_tick * 0.05))
        cy = int(FRAME_HEIGHT / 2 + 30 * np.cos(self._sim_tick * 0.05))
        radius = int(70 + 8 * np.sin(self._sim_tick * 0.1))

        # Face avatar circle
        cv2.circle(frame, (cx, cy), radius, (60, 75, 95), -1)
        cv2.circle(frame, (cx, cy), radius, (0, 215, 255), 2)
        # Eyes
        cv2.circle(frame, (cx - 24, cy - 15), 8, (220, 220, 220), -1)
        cv2.circle(frame, (cx + 24, cy - 15), 8, (220, 220, 220), -1)
        # Smile curve
        cv2.ellipse(frame, (cx, cy + 18), (28, 16), 0, 0, 180, (0, 215, 255), 2)

        # Simulated badge
        cv2.putText(
            frame,
            f"SIMULATED FEED [{self._mode.upper()}] - {datetime.now().strftime('%H:%M:%S')}",
            (16, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (0, 229, 250),
            1,
            cv2.LINE_AA,
        )
        return frame

    def run(self) -> None:
        """Main camera acquisition loop running in dedicated thread."""
        try:
            self._cap = cv2.VideoCapture(self.camera_index)
            if self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                self._is_hardware_available = True
                logger.info("Successfully opened physical camera at index %s", self.camera_index)
            else:
                self._is_hardware_available = False
                logger.warning("Hardware camera not found at index %s. Running in Simulation Mode.", self.camera_index)
        except Exception as e:
            self._is_hardware_available = False
            logger.warning("Camera open error: %s. Using simulated feed.", e)

        while self._running:
            if self._paused:
                time.sleep(0.05)
                continue

            raw_frame: Optional[np.ndarray] = None
            if self._is_hardware_available and self._cap is not None:
                ret, frame = self._cap.read()
                if ret and frame is not None and frame.size > 0:
                    raw_frame = frame
                else:
                    raw_frame = self._generate_simulated_frame()
            else:
                raw_frame = self._generate_simulated_frame()

            with self._frame_lock:
                self._latest_raw_frame = raw_frame.copy()

            # Execute active frame processors
            annotated = raw_frame.copy()
            for proc in self._frame_processors:
                try:
                    annotated = proc(annotated)
                except Exception as e:
                    logger.debug("Processor error: %s", e)

            with self._frame_lock:
                self._latest_annotated_frame = annotated

            # Emit Qt signals if available
            if QT_AVAILABLE:
                try:
                    if hasattr(self, "raw_frame_ready"):
                        self.raw_frame_ready.emit(raw_frame)
                    if hasattr(self, "frame_ready"):
                        # Convert to QImage for immediate UI rendering
                        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb.shape
                        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                        self.frame_ready.emit(q_img)
                except Exception as e:
                    logger.debug("Qt signal emission error: %s", e)

            time.sleep(1.0 / self._fps)

        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Released camera capture hardware.")
