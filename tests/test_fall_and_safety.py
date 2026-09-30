"""
Unit Tests for Fall Detection, Temporal Verification FSM, User/Caregiver Service, and Email Alerts.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

# Ensure headless execution
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

from modules.fall.fall_detector import FallDetector, PostureMetrics
from services.fall_monitor import FallEvent, FallMonitor
from services.user_service import UserService
from services.email_service import EmailService
from adapters.fall_adapter import FallAdapter


class MockLandmark:
    def __init__(self, x: float, y: float, z: float = 0.0, visibility: float = 0.95):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility

    def HasField(self, field_name: str) -> bool:
        return hasattr(self, field_name)


def build_mock_pose_landmarks(posture_type: str = "standing") -> Any:
    """Build mock 33 landmarks for various human postures."""
    lms = [MockLandmark(0.5, 0.5) for _ in range(33)]

    if posture_type == "standing":
        # Upright: Shoulders high (y=0.25), Hips middle (y=0.55), Feet low (y=0.90)
        lms[11] = MockLandmark(0.45, 0.25)  # Left shoulder
        lms[12] = MockLandmark(0.55, 0.25)  # Right shoulder
        lms[23] = MockLandmark(0.46, 0.55)  # Left hip
        lms[24] = MockLandmark(0.54, 0.55)  # Right hip
        lms[25] = MockLandmark(0.46, 0.75)  # Left knee
        lms[26] = MockLandmark(0.54, 0.75)  # Right knee
        lms[27] = MockLandmark(0.46, 0.92)  # Left ankle
        lms[28] = MockLandmark(0.54, 0.92)  # Right ankle
    elif posture_type == "sitting":
        # Sitting: Shoulders high (y=0.35), Hips (y=0.65), Knees bent horizontally (y=0.68)
        lms[11] = MockLandmark(0.42, 0.35)
        lms[12] = MockLandmark(0.58, 0.35)
        lms[23] = MockLandmark(0.43, 0.65)
        lms[24] = MockLandmark(0.57, 0.65)
        lms[25] = MockLandmark(0.45, 0.70)
        lms[26] = MockLandmark(0.55, 0.70)
        lms[27] = MockLandmark(0.45, 0.88)
        lms[28] = MockLandmark(0.55, 0.88)
    elif posture_type == "bending":
        # Bending forward: Torso angled (shoulder x shifted), but hips stay high (y=0.55)
        lms[11] = MockLandmark(0.25, 0.50)  # Shoulder forward
        lms[12] = MockLandmark(0.35, 0.50)
        lms[23] = MockLandmark(0.55, 0.55)  # Hip high
        lms[24] = MockLandmark(0.65, 0.55)
        lms[25] = MockLandmark(0.56, 0.75)
        lms[26] = MockLandmark(0.64, 0.75)
        lms[27] = MockLandmark(0.56, 0.92)
        lms[28] = MockLandmark(0.64, 0.92)
    elif posture_type == "fallen":
        # Fallen flat on floor: Shoulders and hips near bottom (y >= 0.75), horizontal width > height
        lms[11] = MockLandmark(0.20, 0.82)
        lms[12] = MockLandmark(0.20, 0.86)
        lms[23] = MockLandmark(0.60, 0.82)
        lms[24] = MockLandmark(0.60, 0.86)
        lms[25] = MockLandmark(0.75, 0.84)
        lms[26] = MockLandmark(0.75, 0.88)
        lms[27] = MockLandmark(0.90, 0.84)
        lms[28] = MockLandmark(0.90, 0.88)

    mock_res = MagicMock()
    mock_res.pose_landmarks.landmark = lms
    return mock_res


class TestFallDetector(unittest.TestCase):
    """Test AI Pose Kinematics Fall Detector."""

    def setUp(self):
        self.detector = FallDetector()

    def test_standing_pose_kinematics(self):
        with patch.object(self.detector.pose, "process", return_value=build_mock_pose_landmarks("standing")):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            metrics = self.detector.analyze_frame(frame)
            self.assertEqual(metrics.posture, "STANDING")
            self.assertFalse(metrics.is_fall_suspect)
            self.assertLess(metrics.fall_confidence, 0.35)
            self.assertLess(metrics.aspect_ratio, 0.90)

    def test_sitting_pose_kinematics(self):
        with patch.object(self.detector.pose, "process", return_value=build_mock_pose_landmarks("sitting")):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            metrics = self.detector.analyze_frame(frame)
            self.assertEqual(metrics.posture, "SITTING")
            self.assertFalse(metrics.is_fall_suspect)
            self.assertLess(metrics.fall_confidence, 0.45)

    def test_bending_pose_not_false_fall(self):
        with patch.object(self.detector.pose, "process", return_value=build_mock_pose_landmarks("bending")):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            metrics = self.detector.analyze_frame(frame)
            self.assertEqual(metrics.posture, "BENDING")
            self.assertFalse(metrics.is_fall_suspect)

    def test_fallen_pose_detected(self):
        with patch.object(self.detector.pose, "process", return_value=build_mock_pose_landmarks("fallen")):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            metrics = self.detector.analyze_frame(frame)
            self.assertEqual(metrics.posture, "LYING")
            self.assertTrue(metrics.is_fall_suspect)
            self.assertGreaterEqual(metrics.fall_confidence, 0.70)
            self.assertGreaterEqual(metrics.aspect_ratio, 1.20)


class TestFallMonitorFSM(unittest.TestCase):
    """Test Temporal Verification FSM states and transitions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.user_service = UserService(data_dir=Path(self.temp_dir) / "users")
        self.user_service.save_user_profile(
            user_id="user_test",
            name="Nguyễn Văn A",
            caregiver_name="Nguyễn Văn B",
            caregiver_email="caregiver.test@gmail.com",
        )
        self.email_service = EmailService(enabled=False)

        self.monitor = FallMonitor(
            confirm_seconds=1.0,  # Fast 1.0s for testing
            cooldown_seconds=2.0,
            confidence_threshold=0.70,
            user_service=self.user_service,
            email_service=self.email_service,
        )
        self.monitor.events_dir = Path(self.temp_dir) / "fall_events"
        self.monitor.events_dir.mkdir(parents=True, exist_ok=True)
        self.monitor.set_current_user("user_test", "Nguyễn Văn A")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_normal_to_suspected_to_confirming_to_fall_confirmed(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # 1. Normal state
        with patch.object(self.monitor.detector.pose, "process", return_value=build_mock_pose_landmarks("standing")):
            _, status = self.monitor.process_frame(frame)
            self.assertEqual(status["fall_state"], FallMonitor.STATE_NORMAL)

        # 2. Enters SUSPECTED on fall detection
        with patch.object(self.monitor.detector.pose, "process", return_value=build_mock_pose_landmarks("fallen")):
            _, status = self.monitor.process_frame(frame)
            self.assertEqual(status["fall_state"], FallMonitor.STATE_SUSPECTED)

            # 3. Persistent for 0.5s -> enters CONFIRMING
            time.sleep(0.55)
            _, status = self.monitor.process_frame(frame)
            self.assertEqual(status["fall_state"], FallMonitor.STATE_CONFIRMING)

            # 4. Remains down for confirm_seconds (1.0s) -> FALL_CONFIRMED!
            time.sleep(1.05)
            _, status = self.monitor.process_frame(frame)
            self.assertEqual(status["fall_state"], FallMonitor.STATE_FALL_CONFIRMED)
            self.assertIsNotNone(self.monitor.last_event)
            self.assertEqual(self.monitor.last_event.user_id, "user_test")
            self.assertEqual(self.monitor.last_event.caregiver_email, "caregiver.test@gmail.com")

            # 5. Subsequent frame enters COOLDOWN
            _, status = self.monitor.process_frame(frame)
            self.assertEqual(status["fall_state"], FallMonitor.STATE_COOLDOWN)

            # Verify event evidence on disk
            event_folders = list(self.monitor.events_dir.glob("fall_*"))
            self.assertGreaterEqual(len(event_folders), 1)
            ev_folder = event_folders[0]
            self.assertTrue((ev_folder / "snapshot.jpg").exists())
            self.assertTrue((ev_folder / "event.json").exists())

    def test_user_recovery_cancels_suspected_state(self):
        """Verify false-alert filtering when user recovers upright."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Triggers SUSPECTED
        with patch.object(self.monitor.detector.pose, "process", return_value=build_mock_pose_landmarks("fallen")):
            _, status = self.monitor.process_frame(frame)
            self.assertEqual(status["fall_state"], FallMonitor.STATE_SUSPECTED)

        # User stands back up immediately (e.g., picking up an object) -> returns to NORMAL
        with patch.object(self.monitor.detector.pose, "process", return_value=build_mock_pose_landmarks("standing")):
            _, status = self.monitor.process_frame(frame)
            self.assertEqual(status["fall_state"], FallMonitor.STATE_NORMAL)
            self.assertIsNone(self.monitor.last_event)


class TestUserService(unittest.TestCase):
    """Test User & Caregiver registration and email validation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.service = UserService(data_dir=Path(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_email_validation(self):
        self.assertTrue(UserService.validate_email("caregiver@gmail.com"))
        self.assertTrue(UserService.validate_email("dr.nguyen_van.a@hospital.org.vn"))
        self.assertFalse(UserService.validate_email("invalid-email"))
        self.assertFalse(UserService.validate_email("caregiver@"))
        self.assertFalse(UserService.validate_email(""))

    def test_save_and_retrieve_user_profile(self):
        self.service.save_user_profile(
            user_id="user_123",
            name="Cụ Nguyễn Thị Mai",
            age=80,
            gender="Nữ",
            notes="Tiền sử huyết áp cao",
            caregiver_name="Nguyễn Văn Cường",
            caregiver_relationship="Con trai",
            caregiver_email="cuong.nguyen@gmail.com",
        )

        profile = self.service.get_user_profile("user_123")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["name"], "Cụ Nguyễn Thị Mai")
        self.assertEqual(profile["caregiver"]["email"], "cuong.nguyen@gmail.com")

        resolved_email = self.service.get_caregiver_email("user_123")
        self.assertEqual(resolved_email, "cuong.nguyen@gmail.com")

    def test_invalid_email_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.service.save_user_profile(
                user_id="user_err",
                name="Lỗi Email",
                caregiver_email="not-an-email",
            )


class TestEmailService(unittest.TestCase):
    """Test Email Service non-crashing behavior and mock delivery."""

    def test_disabled_email_returns_false_safely(self):
        service = EmailService(enabled=False)
        result = service.send_fall_alert(
            recipient_email="caregiver@gmail.com",
            user_name="Bác Nam",
            timestamp="14:00",
        )
        self.assertFalse(result)

    def test_invalid_email_returns_false_safely(self):
        service = EmailService(enabled=True)
        result = service.send_fall_alert(
            recipient_email="bad_email_format",
            user_name="Bác Nam",
            timestamp="14:00",
        )
        self.assertFalse(result)

    @patch("smtplib.SMTP")
    def test_smtp_send_success_mock(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        service = EmailService(
            enabled=True,
            username="system@gmail.com",
            password="app-password-secret",
        )
        success = service.send_fall_alert(
            recipient_email="caregiver@gmail.com",
            user_name="Bác Nam",
            timestamp="14:00 30/09/2026",
            confidence=0.92,
        )
        self.assertTrue(success)
        mock_server.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
