"""
Fall Monitoring Service with Temporal Verification FSM & False-Alert Filtering.
States: NORMAL -> SUSPECTED -> CONFIRMING -> FALL_CONFIRMED -> COOLDOWN -> NORMAL.
Saves evidence snapshot to data/fall_events/ and triggers Caregiver Gmail alert.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from config import (
    FALL_COOLDOWN_SECONDS,
    FALL_CONFIDENCE_THRESHOLD,
    FALL_CONFIRM_SECONDS,
    FALL_EVENTS_DIR,
)
from modules.fall.fall_detector import FallDetector, PostureMetrics
from services.email_service import EmailService
from services.user_service import UserService

logger = logging.getLogger("FallMonitor")


@dataclass
class FallEvent:
    event_id: str
    user_id: str
    user_name: str
    timestamp: str
    confidence: float
    snapshot_path: str
    caregiver_email: str
    email_status: str  # "sent", "failed", "disabled", "no_email"
    video_path: Optional[str] = None


class FallMonitor:
    """
    Manages Fall State Machine with Temporal Confirmation and Evidence Recording.
    Guarantees no single-frame false alarms and enforces cooldown period.
    """

    # FSM State Constants
    STATE_NORMAL = "NORMAL"
    STATE_SUSPECTED = "SUSPECTED"
    STATE_CONFIRMING = "CONFIRMING"
    STATE_FALL_CONFIRMED = "FALL_CONFIRMED"
    STATE_COOLDOWN = "COOLDOWN"

    def __init__(
        self,
        confirm_seconds: float = FALL_CONFIRM_SECONDS,
        cooldown_seconds: float = FALL_COOLDOWN_SECONDS,
        confidence_threshold: float = FALL_CONFIDENCE_THRESHOLD,
        user_service: Optional[UserService] = None,
        email_service: Optional[EmailService] = None,
    ) -> None:
        self.confirm_seconds = confirm_seconds
        self.cooldown_seconds = cooldown_seconds
        self.confidence_threshold = confidence_threshold

        self.detector = FallDetector()
        self.user_service = user_service or UserService()
        self.email_service = email_service or EmailService()

        # FSM tracking
        self.current_state: str = self.STATE_NORMAL
        self.suspect_start_time: Optional[float] = None
        self.confirm_start_time: Optional[float] = None
        self.cooldown_start_time: Optional[float] = None

        # Last event record
        self.last_event: Optional[FallEvent] = None
        self.last_metrics: Optional[PostureMetrics] = None
        self.current_user_id: str = "1"
        self.current_user_name: str = "Người dùng"

        # Evidence folder
        self.events_dir: Path = FALL_EVENTS_DIR
        self.events_dir.mkdir(parents=True, exist_ok=True)

    def set_current_user(self, user_id: str, user_name: Optional[str] = None) -> None:
        """Update active recognized identity for alert dispatching."""
        if user_id and str(user_id) != "unknown":
            self.current_user_id = str(user_id)
            if user_name:
                self.current_user_name = user_name
            else:
                profile = self.user_service.get_user_profile(self.current_user_id)
                if profile:
                    self.current_user_name = profile.get("name", self.current_user_name)

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Execute frame analysis, step Temporal FSM, and render safety overlay.
        Returns: (annotated_frame, status_dict)
        """
        now = time.time()
        metrics = self.detector.analyze_frame(frame)
        self.last_metrics = metrics

        # Step FSM based on current state & incoming metrics
        self._update_fsm(metrics, frame, now)

        # Render overlay on frame
        annotated = self.detector.draw_overlay(frame, metrics)

        # Render FSM status badge at top-right
        annotated = self._draw_fsm_badge(annotated)

        return annotated, self.get_status()

    def _update_fsm(self, metrics: PostureMetrics, frame: np.ndarray, now: float) -> None:
        """Evaluate temporal transitions according to Section 10 & 16."""
        is_suspect = metrics.is_fall_suspect and (metrics.fall_confidence >= self.confidence_threshold)

        if self.current_state == self.STATE_NORMAL:
            if is_suspect:
                self.current_state = self.STATE_SUSPECTED
                self.suspect_start_time = now
                logger.info(
                    "Fall state: NORMAL -> SUSPECTED (confidence=%.2f, torso_angle=%.1f°)",
                    metrics.fall_confidence,
                    metrics.torso_angle,
                )

        elif self.current_state == self.STATE_SUSPECTED:
            if not is_suspect:
                # User recovered immediately or movement was brief (e.g., normal bending)
                logger.debug("User recovered from SUSPECTED posture -> NORMAL")
                self.current_state = self.STATE_NORMAL
                self.suspect_start_time = None
            elif self.suspect_start_time and (now - self.suspect_start_time >= 0.5):
                # Persistent abnormal condition for 0.5s -> begin strict confirmation timer
                self.current_state = self.STATE_CONFIRMING
                self.confirm_start_time = now
                logger.info("Fall state: SUSPECTED -> CONFIRMING (awaiting %ss)", self.confirm_seconds)

        elif self.current_state == self.STATE_CONFIRMING:
            if not is_suspect:
                # User stood back up or recovered vertical posture during confirmation window!
                logger.info("User recovered to upright posture during confirmation window. Resetting to NORMAL.")
                self.current_state = self.STATE_NORMAL
                self.confirm_start_time = None
                self.suspect_start_time = None
            elif self.confirm_start_time and (now - self.confirm_start_time >= self.confirm_seconds):
                # Fall confirmed by continuous temporal evidence!
                self.current_state = self.STATE_FALL_CONFIRMED
                logger.warning(
                    "Fall state: CONFIRMING -> FALL_CONFIRMED! (Persistent down for %.1fs, confidence=%.2f)",
                    self.confirm_seconds,
                    metrics.fall_confidence,
                )
                self._handle_fall_confirmed(frame, metrics)

        elif self.current_state == self.STATE_FALL_CONFIRMED:
            # Transition to COOLDOWN to prevent duplicate spamming
            self.current_state = self.STATE_COOLDOWN
            self.cooldown_start_time = now
            logger.info("Fall state: FALL_CONFIRMED -> COOLDOWN (%ss)", self.cooldown_seconds)

        elif self.current_state == self.STATE_COOLDOWN:
            if self.cooldown_start_time and (now - self.cooldown_start_time >= self.cooldown_seconds):
                if not is_suspect:
                    self.current_state = self.STATE_NORMAL
                    self.cooldown_start_time = None
                    logger.info("Cooldown expired and posture safe. Fall state: COOLDOWN -> NORMAL.")

    def _handle_fall_confirmed(self, frame: np.ndarray, metrics: PostureMetrics) -> None:
        """Save evidence snapshot, write event JSON, resolve caregiver, and dispatch Gmail alert."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        iso_timestamp = datetime.now().isoformat()
        event_id = f"fall_{timestamp_str}"

        # 1. Create event folder: data/fall_events/fall_YYYYMMDD_HHMMSS/
        event_dir = self.events_dir / event_id
        event_dir.mkdir(parents=True, exist_ok=True)

        # 2. Save evidence snapshot
        snapshot_file = event_dir / "snapshot.jpg"
        try:
            cv2.imwrite(str(snapshot_file), frame)
            logger.info("Evidence snapshot saved: %s", snapshot_file)
        except Exception as e:
            logger.error("Evidence save failed: %s", e)

        # 3. Resolve caregiver email using UserService
        caregiver_email = self.user_service.get_caregiver_email(self.current_user_id) or ""

        # 4. Dispatch emergency Gmail alert
        email_status = "no_email"
        if caregiver_email:
            sent = self.email_service.send_fall_alert(
                recipient_email=caregiver_email,
                user_name=self.current_user_name,
                timestamp=datetime.now().strftime("%H:%M:%S ngày %d/%m/%Y"),
                confidence=metrics.fall_confidence,
                snapshot_path=str(snapshot_file),
            )
            email_status = "sent" if sent else "failed"
        else:
            logger.warning("No valid caregiver email found for user_id '%s'", self.current_user_id)

        # 5. Persist normalized FallEvent JSON
        event = FallEvent(
            event_id=event_id,
            user_id=self.current_user_id,
            user_name=self.current_user_name,
            timestamp=iso_timestamp,
            confidence=metrics.fall_confidence,
            snapshot_path=str(snapshot_file),
            caregiver_email=caregiver_email,
            email_status=email_status,
        )
        self.last_event = event

        event_json_path = event_dir / "event.json"
        try:
            with open(event_json_path, "w", encoding="utf-8") as f:
                json.dump(asdict(event), f, ensure_ascii=False, indent=2)
            logger.info("Fall event created and saved: %s", event_id)
        except Exception as e:
            logger.error("Failed saving event.json: %s", e)

    def _draw_fsm_badge(self, frame: np.ndarray) -> np.ndarray:
        """Render prominent safety badge at top of video stream."""
        h, w = frame.shape[:2]
        badge_w, badge_h = 240, 42
        bx = w - badge_w - 14
        by = 14

        if self.current_state == self.STATE_NORMAL:
            badge_text = "● AN TOÀN: BÌNH THƯỜNG"
            bg_color = (25, 60, 25)
            border_color = (50, 205, 50)
            text_color = (80, 240, 80)
        elif self.current_state in (self.STATE_SUSPECTED, self.STATE_CONFIRMING):
            badge_text = "⚠️ NGHI NGỜ NGÃ (XÁC NHẬN)"
            bg_color = (15, 60, 100)
            border_color = (0, 165, 255)
            text_color = (50, 200, 255)
        elif self.current_state == self.STATE_FALL_CONFIRMED:
            badge_text = "🚨 CẢNH BÁO: ĐÃ PHÁT HIỆN NGÃ!"
            bg_color = (20, 20, 120)
            border_color = (0, 0, 255)
            text_color = (255, 255, 255)
        else:  # COOLDOWN
            badge_text = "⏱️ ĐANG HỒI PHỤC (COOLDOWN)"
            bg_color = (50, 50, 60)
            border_color = (140, 140, 160)
            text_color = (200, 220, 255)

        overlay = frame.copy()
        cv2.rectangle(overlay, (bx, by), (bx + badge_w, by + badge_h), bg_color, -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(frame, (bx, by), (bx + badge_w, by + badge_h), border_color, 2)

        from core.drawing_utils import draw_vietnamese_text
        draw_vietnamese_text(
            frame,
            badge_text,
            (bx + 10, by + 12),
            font_size=13,
            color=text_color,
            stroke_color=(0, 0, 0),
            stroke_width=2,
        )
        return frame

    def get_status(self) -> Dict[str, Any]:
        """Return snapshot of current fall monitoring telemetry."""
        posture = self.last_metrics.posture if self.last_metrics else "UNKNOWN"
        posture_vi = self.last_metrics.posture_vi if self.last_metrics else "Không rõ"
        confidence = self.last_metrics.fall_confidence if self.last_metrics else 0.0

        caregiver_email = self.user_service.get_caregiver_email(self.current_user_id) or ""

        last_ev_desc = "Không có"
        if self.last_event:
            ev_time = self.last_event.timestamp.split("T")[-1][:8] if "T" in self.last_event.timestamp else ""
            last_ev_desc = f"Ngã lúc {ev_time} ({self.last_event.email_status})"

        email_status = "Ready"
        if self.last_event:
            if self.last_event.email_status == "sent":
                email_status = "Đã gửi Gmail"
            elif self.last_event.email_status == "failed":
                email_status = "Không thể gửi Gmail"
            elif self.last_event.email_status == "no_email":
                email_status = "Chưa có Gmail người thân"

        return {
            "fall_state": self.current_state,
            "posture": posture,
            "posture_vi": posture_vi,
            "confidence": confidence,
            "current_user_id": self.current_user_id,
            "current_user_name": self.current_user_name,
            "caregiver_email": caregiver_email,
            "last_fall_event": last_ev_desc,
            "email_status": email_status,
            "last_event": asdict(self.last_event) if self.last_event else None,
        }
