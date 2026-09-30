"""
Main Dashboard for AI Rehabilitation Assistant using PyQt5.
Implements the 7-step Core Flow:
Face Recognition (Personalization)
  → Emotion Recognition (Contextual state)
  → Voice Interaction (Natural interaction)
  → Rehabilitation (Core movement analysis)
  → Exercise Evaluation (Form checks & angle limits)
  → Score (Objective performance metrics)
  → Voice Feedback (Real-time coaching & summary)

Uses CameraManager as the single shared camera capture engine.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.registration_dialog import PatientManagementDialog, RegistrationDialog
from app.router import DashboardRouter
from app.state import AppState
from config import (
    CAMERA_INDEX,
    DEFAULT_PATIENT_ID,
    DEFAULT_PATIENT_NAME,
    EXERCISES,
    MODULES_DIR,
)
from core.camera_manager import CameraManager

logger = logging.getLogger("Dashboard")

# ==================== MODERN DARK STYLESHEET ====================
STYLESHEET = """
QMainWindow {
    background-color: #0E1015;
}
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 15px;
    color: #F1F5F9;
}

/* Header Bar */
#HeaderBar {
    background-color: #12151C;
    border-bottom: 1.5px solid #1E232E;
    padding: 10px 20px;
}
#BrandTitle {
    font-size: 22px;
    font-weight: 800;
    color: #00E5FA;
    letter-spacing: 0.5px;
}
#Subtitle {
    font-size: 14px;
    font-weight: 500;
    color: #94A3B8;
}

/* Standard Cards */
QFrame.ui-card {
    background-color: #161920;
    border: 1.5px solid #252A36;
    border-radius: 10px;
    padding: 12px 16px;
}
QFrame.ui-card-highlight {
    background-color: #161920;
    border: 2px solid #00C4D6;
    border-radius: 10px;
    padding: 12px 16px;
}

/* Card Titles and Text */
QLabel.card-title {
    font-size: 16px;
    font-weight: 700;
    color: #F8FAFC;
}
QLabel.card-value {
    font-size: 17px;
    font-weight: bold;
    color: #00E5FA;
}
QLabel.card-subtext {
    font-size: 14px;
    color: #94A3B8;
    line-height: 1.4;
}

/* Action Buttons */
QPushButton.btn-cyan {
    background-color: #00C4D6;
    color: #000000;
    font-size: 15px;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 40px;
}
QPushButton.btn-cyan:hover {
    background-color: #00E5FA;
}
QPushButton.btn-green {
    background-color: #10B981;
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 42px;
}
QPushButton.btn-green:hover {
    background-color: #059669;
}
QPushButton.btn-red {
    background-color: #EF4444;
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 42px;
}
QPushButton.btn-red:hover {
    background-color: #DC2626;
}
QPushButton.btn-exercise {
    background-color: #1A1D26;
    color: #E2E8F0;
    border: 1.5px solid #2E3545;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 15px;
    font-weight: 600;
    text-align: left;
    min-height: 46px;
}
QPushButton.btn-exercise:hover {
    background-color: #242938;
    color: #FFFFFF;
    border-color: #00C4D6;
}
QPushButton.btn-exercise-active {
    background-color: #0E2A38;
    color: #00E5FA;
    border: 2px solid #00E5FA;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 15px;
    font-weight: 700;
    text-align: left;
    min-height: 46px;
}

/* Quick command pills */
QPushButton.btn-pill {
    background-color: #181C26;
    color: #94A3B8;
    border: 1px solid #282E3E;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    min-height: 36px;
}
QPushButton.btn-pill:hover {
    background-color: #252D3D;
    color: #00E5FA;
    border-color: #00E5FA;
}

/* Inputs */
QLineEdit {
    background-color: #0F1217;
    border: 1.5px solid #2D3342;
    border-radius: 8px;
    color: #FFFFFF;
    padding: 8px 14px;
    font-size: 15px;
    min-height: 36px;
}
QLineEdit:focus {
    border: 1.5px solid #00C4D6;
}

/* Progress Bar */
QProgressBar {
    background-color: #141720;
    border: 1px solid #272D3B;
    border-radius: 6px;
    text-align: center;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 14px;
    min-height: 24px;
    height: 24px;
}
QProgressBar::chunk {
    background-color: #00C4D6;
    border-radius: 5px;
}

/* Video viewport */
#VideoContainer {
    background-color: #000000;
    border: 1.5px solid #252A36;
    border-radius: 10px;
}

/* Bottom Status Bar */
#BottomStatusBar {
    background-color: #0A0C10;
    border-top: 1.5px solid #1E232E;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 500;
    color: #94A3B8;
}
"""


class DashboardWindow(QMainWindow):
    """
    Main Application Window for AI Rehabilitation Assistant.
    Unified single-screen interface supporting:
      1. Personalization (Face Recognition)
      2. Emotion Context
      3. Rehabilitation Exercise Engine (Sit-to-stand, Arm raise, Marching)
      4. Voice Command & Feedback
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI REHABILITATION & SAFETY ASSISTANT — Hệ Thống Trợ Lý Phục Hồi & An Toàn")
        self.setMinimumSize(1150, 720)
        self.setStyleSheet(STYLESHEET)

        self.state = AppState()
        self.app_state = self.state
        self.router = DashboardRouter(self)
        self.active_exercise_id = "arm_raise"
        self.current_patient_id = "1"
        self.current_patient_name = "Trần Văn Nam"

        # Initialize CameraManager Singleton
        self.camera_manager = CameraManager.get_instance(camera_index=CAMERA_INDEX)
        self.camera_manager.register_processor(self._process_video_frame)
        self.camera_manager.frame_ready.connect(self._on_frame_ready)

        # Initialize UI Components
        self._init_ui()

        # Start Camera capture engine
        self.camera_manager.start_camera()

        # Setup 1-second periodic timer for UI sync
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.start(1000)

        # Start maximized for full visual experience
        self.showMaximized()

    def _init_ui(self) -> None:
        """Construct the unified single-window user interface."""
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. TOP HEADER BAR
        header = QFrame()
        header.setObjectName("HeaderBar")
        lay_header = QHBoxLayout(header)
        lay_header.setContentsMargins(20, 10, 20, 10)

        # Logo / Title
        v_title = QVBoxLayout()
        lbl_brand = QLabel("AI REHABILITATION & SAFETY ASSISTANT")
        lbl_brand.setObjectName("BrandTitle")
        lbl_sub = QLabel("Hệ Thống Trợ Lý Phục Hồi Chức Năng & Giám Sát An Toàn Thông Minh")
        lbl_sub.setObjectName("Subtitle")
        v_title.addWidget(lbl_brand)
        v_title.addWidget(lbl_sub)
        lay_header.addLayout(v_title)

        lay_header.addStretch()

        # Telemetry / Clock
        self.lbl_clock = QLabel(datetime.now().strftime("%H:%M:%S | %d/%m/%Y"))
        self.lbl_clock.setStyleSheet("font-size: 15px; font-weight: bold; color: #CBD5E1;")

        self.lbl_cam_badge = QLabel("● Camera: Hoạt động (30 FPS)")
        self.lbl_cam_badge.setStyleSheet(
            "font-size: 14px; color: #10B981; font-weight: 600; "
            "background-color: #121E24; border: 1.5px solid #10B981; "
            "border-radius: 8px; padding: 6px 14px;"
        )

        lay_header.addWidget(self.lbl_clock)
        lay_header.addWidget(self.lbl_cam_badge)
        root_layout.addWidget(header)

        # 2. MAIN SPLITTER BODY
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # ==================== LEFT COLUMN: TELEMETRY & VIEWPORT (62%) ====================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(16, 12, 10, 12)
        left_layout.setSpacing(12)

        # Top Context Cards: [Cá nhân hóa] & [Trạng thái cảm xúc]
        top_cards = QHBoxLayout()
        top_cards.setSpacing(12)

        # Card: Nhận diện khuôn mặt & Danh tính (Decoupled Face Recognition)
        card_user = QFrame()
        card_user.setProperty("class", "ui-card")
        lay_card_user = QVBoxLayout(card_user)
        lay_card_user.setContentsMargins(14, 10, 14, 10)
        lay_card_user.setSpacing(6)

        top_u_row = QHBoxLayout()
        lbl_u_title = QLabel("👤 NHẬN DIỆN KHUÔN MẶT & DANH TÍNH")
        lbl_u_title.setProperty("class", "card-title")
        top_u_row.addWidget(lbl_u_title)
        top_u_row.addStretch()

        btn_register = QPushButton("➕ Đăng Ký Người Mới")
        btn_register.setProperty("class", "btn-cyan")
        btn_register.setToolTip("Điền thông tin cá nhân và chụp ảnh mẫu khuôn mặt")
        btn_register.clicked.connect(self._on_open_registration)

        btn_manage = QPushButton("👥 Danh Sách Hồ Sơ")
        btn_manage.setProperty("class", "btn-pill")
        btn_manage.setToolTip("Xem danh sách thông tin người bệnh đã đăng ký")
        btn_manage.clicked.connect(self._on_open_patients_manager)

        top_u_row.addWidget(btn_register)
        top_u_row.addWidget(btn_manage)
        lay_card_user.addLayout(top_u_row)

        self.lbl_face_status = QLabel("🟢 Đang quét nhận diện khuôn mặt...")
        self.lbl_face_status.setStyleSheet("font-size: 17px; font-weight: bold; color: #10B981;")

        self.lbl_face_sub = QLabel("Tự động nhận diện người dùng đã đăng ký trong cơ sở dữ liệu.")
        self.lbl_face_sub.setStyleSheet("font-size: 14px; color: #94A3B8;")

        lay_card_user.addWidget(self.lbl_face_status)
        lay_card_user.addWidget(self.lbl_face_sub)
        top_cards.addWidget(card_user, 1)

        # Card: Cảm xúc (Emotion State)
        card_emo = QFrame()
        card_emo.setProperty("class", "ui-card")
        lay_card_emo = QVBoxLayout(card_emo)
        lay_card_emo.setContentsMargins(14, 10, 14, 10)
        lay_card_emo.setSpacing(6)

        lbl_e_title = QLabel("😊 Ngữ Cảnh Tâm Lý (Emotion Recognition)")
        lbl_e_title.setProperty("class", "card-title")

        self.lbl_current_emotion = QLabel("Trạng thái: Vui vẻ (92.4%)")
        self.lbl_current_emotion.setStyleSheet("font-size: 17px; font-weight: bold; color: #00E5FA;")

        self.lbl_emotion_note = QLabel("Tâm lý tích cực, sẵn sàng cho phiên tập phục hồi.")
        self.lbl_emotion_note.setStyleSheet("font-size: 14px; color: #94A3B8;")

        lay_card_emo.addWidget(lbl_e_title)
        lay_card_emo.addWidget(self.lbl_current_emotion)
        lay_card_emo.addWidget(self.lbl_emotion_note)
        top_cards.addWidget(card_emo, 1)

        left_layout.addLayout(top_cards)

        # Video Viewport
        self.video_container = QFrame()
        self.video_container.setObjectName("VideoContainer")
        lay_vid = QVBoxLayout(self.video_container)
        lay_vid.setContentsMargins(4, 4, 4, 4)

        self.video_display = QLabel()
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setMinimumSize(640, 420)
        self.video_display.setSizePolicy(self.video_display.sizePolicy().Expanding, self.video_display.sizePolicy().Expanding)
        self.video_display.setScaledContents(True)
        lay_vid.addWidget(self.video_display)

        left_layout.addWidget(self.video_container, 1)

        # Live Form Guidance Banner
        self.banner_guidance = QLabel("💡 Hướng dẫn: Đứng trước camera, thẳng người và giữ khoảng cách 1.5m - 2.5m.")
        self.banner_guidance.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #F59E0B; "
            "background-color: #1C1917; border: 1.5px solid #78350F; "
            "border-radius: 8px; padding: 12px 18px;"
        )
        left_layout.addWidget(self.banner_guidance)

        splitter.addWidget(left_widget)

        # ==================== RIGHT COLUMN: REHABILITATION & SAFETY (38%) ====================
        right_widget = QWidget()
        right_widget.setMinimumWidth(440)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 12, 16, 12)
        right_layout.setSpacing(14)

        # 1. Exercise Selection Card
        card_ex = QFrame()
        card_ex.setProperty("class", "ui-card-highlight")
        lay_card_ex = QVBoxLayout(card_ex)
        lay_card_ex.setSpacing(10)

        lbl_ex_title = QLabel("🏋️ CHỌN BÀI TẬP PHỤC HỒI CHỨC NĂNG")
        lbl_ex_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00E5FA;")
        lay_card_ex.addWidget(lbl_ex_title)

        # Exercise Options
        self.btn_ex_arm = QPushButton("🏋️  1. Vươn vai (Nâng tay qua đầu) — Mục tiêu: 12 lần")
        self.btn_ex_arm.setProperty("class", "btn-exercise-active")
        self.btn_ex_arm.clicked.connect(lambda: self._select_exercise("arm_raise"))

        self.btn_ex_sit = QPushButton("🦵  2. Đứng lên ngồi xuống (Sit-to-Stand) — Mục tiêu: 10 lần")
        self.btn_ex_sit.setProperty("class", "btn-exercise")
        self.btn_ex_sit.clicked.connect(lambda: self._select_exercise("sit_to_stand"))

        self.btn_ex_march = QPushButton("🚶  3. Đi bộ tại chỗ (Nâng cao đùi) — Mục tiêu: 20 bước")
        self.btn_ex_march.setProperty("class", "btn-exercise")
        self.btn_ex_march.clicked.connect(lambda: self._select_exercise("marching"))

        lay_card_ex.addWidget(self.btn_ex_arm)
        lay_card_ex.addWidget(self.btn_ex_sit)
        lay_card_ex.addWidget(self.btn_ex_march)

        # Controls row
        ctrl_row = QHBoxLayout()
        self.btn_start = QPushButton("▶️ Bắt đầu tập")
        self.btn_start.setProperty("class", "btn-green")
        self.btn_start.clicked.connect(self._on_start_exercise)

        self.btn_stop = QPushButton("⏹️ Dừng bài tập")
        self.btn_stop.setProperty("class", "btn-red")
        self.btn_stop.clicked.connect(self._on_stop_exercise)

        self.btn_reset = QPushButton("🔄 Đặt lại")
        self.btn_reset.setProperty("class", "btn-cyan")
        self.btn_reset.clicked.connect(self._on_reset_exercise)

        ctrl_row.addWidget(self.btn_start)
        ctrl_row.addWidget(self.btn_stop)
        ctrl_row.addWidget(self.btn_reset)
        lay_card_ex.addLayout(ctrl_row)

        right_layout.addWidget(card_ex)

        # 2. Live Evaluation & Scoring Card
        card_eval = QFrame()
        card_eval.setProperty("class", "ui-card")
        lay_eval = QVBoxLayout(card_eval)
        lay_eval.setSpacing(10)

        lbl_eval_title = QLabel("📊 ĐÁNH GIÁ CHUYÊN MÔN & ĐIỂM SỐ")
        lbl_eval_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F8FAFC;")
        lay_eval.addWidget(lbl_eval_title)

        # Progress bar
        self.lbl_progress = QLabel("Tiến độ: 0 / 12 lần hoàn thành (0%)")
        self.lbl_progress.setStyleSheet("font-size: 15px; color: #CBD5E1; font-weight: 600;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        lay_eval.addWidget(self.lbl_progress)
        lay_eval.addWidget(self.progress_bar)

        # Metrics row
        metrics_row = QHBoxLayout()
        self.lbl_correct_cnt = QLabel("Đúng: 0")
        self.lbl_correct_cnt.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")

        self.lbl_incorrect_cnt = QLabel("Chưa chuẩn: 0")
        self.lbl_incorrect_cnt.setStyleSheet("font-size: 16px; font-weight: bold; color: #EF4444;")

        self.lbl_score_val = QLabel("Điểm: 100.0%")
        self.lbl_score_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #00E5FA;")

        metrics_row.addWidget(self.lbl_correct_cnt)
        metrics_row.addWidget(self.lbl_incorrect_cnt)
        metrics_row.addStretch()
        metrics_row.addWidget(self.lbl_score_val)
        lay_eval.addLayout(metrics_row)

        # Show result report button
        btn_modal_report = QPushButton("📋 Xem Báo Cáo Kết Quả Chi Tiết")
        btn_modal_report.setProperty("class", "btn-cyan")
        btn_modal_report.clicked.connect(self.router.show_exercise_result_modal)
        lay_eval.addWidget(btn_modal_report)

        right_layout.addWidget(card_eval)

        # 3. SAFETY MONITORING & FALL DETECTION CARD
        card_safety = QFrame()
        card_safety.setProperty("class", "ui-card")
        lay_safety = QVBoxLayout(card_safety)
        lay_safety.setSpacing(10)

        lbl_s_title = QLabel("🛡️ GIÁM SÁT AN TOÀN & TÉ NGÃ")
        lbl_s_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F8FAFC;")
        lay_safety.addWidget(lbl_s_title)

        self.lbl_safety_monitor_badge = QLabel("● ĐANG GIÁM SÁT LIÊN TỤC")
        self.lbl_safety_monitor_badge.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #10B981; "
            "background-color: #0E241B; border: 1.5px solid #059669; "
            "border-radius: 8px; padding: 6px 14px;"
        )
        lay_safety.addWidget(self.lbl_safety_monitor_badge)

        self.lbl_fall_status = QLabel("Trạng thái:\n✓ Bình thường")
        self.lbl_fall_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        lay_safety.addWidget(self.lbl_fall_status)

        self.lbl_caregiver_email = QLabel("Người nhận:\nChưa cấu hình Gmail")
        self.lbl_caregiver_email.setStyleSheet("font-size: 14px; color: #94A3B8;")
        self.lbl_caregiver_email.setWordWrap(True)
        lay_safety.addWidget(self.lbl_caregiver_email)

        self.lbl_last_fall_event = QLabel("Sự kiện gần nhất: Không có")
        self.lbl_last_fall_event.setStyleSheet("font-size: 14px; color: #CBD5E1;")
        self.lbl_last_fall_event.setWordWrap(True)
        lay_safety.addWidget(self.lbl_last_fall_event)

        self.lbl_email_status = QLabel("Gmail: ✓ Ready")
        self.lbl_email_status.setStyleSheet("font-size: 15px; color: #38BDF8; font-weight: 600;")
        lay_safety.addWidget(self.lbl_email_status)

        right_layout.addWidget(card_safety)
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([680, 460])
        root_layout.addWidget(splitter, 1)

        # 3. BOTTOM STATUS BAR
        self.status_bar_lbl = QLabel(f"Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')} | Trạng thái: Sẵn sàng | Giám sát an toàn: Sẵn sàng")
        self.status_bar_lbl.setObjectName("BottomStatusBar")
        root_layout.addWidget(self.status_bar_lbl)

    # ==================== VIDEO FRAME PROCESSOR ====================
    def _process_video_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Master Video Processing Callback attached to CameraManager.
        Directly executes Face Recognition, Emotion, or Rehabilitation pipelines
        without any camera conflicts.
        """
        mode = self.camera_manager.get_mode()

        if mode == "rehabilitation":
            # 1. Full Body Pose, Exercise State Machine, Form HUD
            annotated_frame, metrics = self.router.rehab_adapter.process_frame(frame)

            # 2. Overlay live emotion badge at top right
            emo_res = self.router.emotion_adapter.get_result()
            annotated_frame = self.router.emotion_adapter.draw_emotion_badge(
                annotated_frame, emo_res["emotion_vi"], emo_res["confidence"]
            )
            return annotated_frame
        else:
            # 1. Autonomous Face Recognition BBox & Tracking
            annotated_frame = self.router.face_adapter.draw_tracking_overlay(frame)

            # 2. Emotion Recognition with Temporal Smoothing
            emo_res = self.router.emotion_adapter.process_frame(annotated_frame)

            # 3. Fall Detection & Safety Monitoring (Pose Kinematics & Temporal FSM)
            annotated_frame, fall_res = self.router.fall_adapter.process_frame(annotated_frame)

            # 4. Render Emotion Badge
            annotated_frame = self.router.emotion_adapter.draw_emotion_badge(
                annotated_frame, emo_res["emotion_vi"], emo_res["confidence"]
            )
            return annotated_frame

    def _on_frame_ready(self, q_img: QImage) -> None:
        """Render processed frame received from CameraManager onto video display."""
        if not q_img.isNull():
            pix = QPixmap.fromImage(q_img)
            self.video_display.setPixmap(pix)

    # ==================== UI ACTIONS & LOGIC ====================
    def _select_exercise(self, exercise_id: str) -> None:
        """Highlight selected exercise button."""
        self.active_exercise_id = exercise_id
        buttons = {
            "arm_raise": self.btn_ex_arm,
            "sit_to_stand": self.btn_ex_sit,
            "marching": self.btn_ex_march,
        }
        for ex_id, btn in buttons.items():
            if ex_id == exercise_id:
                btn.setProperty("class", "btn-exercise-active")
            else:
                btn.setProperty("class", "btn-exercise")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.router.rehab_adapter.select_exercise(exercise_id)
        metrics = self.router.rehab_adapter.get_result()
        self.banner_guidance.setText(f"💡 Hướng dẫn: {EXERCISES.get(exercise_id, {}).get('instructions', '')}")
        self.update_dashboard_ui()

    def _on_start_exercise(self) -> None:
        """Start rehabilitation exercise."""
        self.router.start_exercise(self.active_exercise_id)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def _on_stop_exercise(self) -> None:
        """Stop exercise and return to monitoring."""
        self.router.stop_exercise()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.router.show_exercise_result_modal()

    def _on_reset_exercise(self) -> None:
        """Reset exercise metrics."""
        self.router.rehab_adapter.start_exercise(self.active_exercise_id)
        self.update_dashboard_ui()

    def _on_open_registration(self) -> None:
        """Open dedicated User Registration modal."""
        dlg = RegistrationDialog(self.router.face_adapter, self)
        dlg.patient_registered.connect(self._on_patient_registered)
        dlg.exec_()

    def _on_open_patients_manager(self) -> None:
        """Open Patient List & Management modal."""
        dlg = PatientManagementDialog(self.router.face_adapter, self)
        dlg.exec_()
        self.update_dashboard_ui()

    def _on_patient_registered(self, profile: dict) -> None:
        """Callback triggered when a new user is enrolled and model retrained."""
        pid = profile.get("patient_id") or profile.get("user_id", "")
        name = profile.get("name", "")
        self.current_patient_id = pid
        self.current_patient_name = name
        self.show_status_message(f"Đã đăng ký và huấn luyện nhận diện người dùng: {name} (Mã: {pid})")
        self.update_dashboard_ui()

    def update_dashboard_ui(self) -> None:
        """Synchronize telemetry metrics into UI components."""
        # 1. Face Recognition Telemetry
        face_info = self.router.face_adapter.get_latest_recognition()
        f_status = face_info.get("status", "no_face")
        profile = {}
        if f_status == "recognized":
            r_name = face_info.get("name", "Người dùng")
            r_id = face_info.get("patient_id", "1")
            r_conf = face_info.get("confidence", 0.95)
            profile = face_info.get("profile") or {}
            age = profile.get("age", 70)
            gender = profile.get("gender", "Nam")
            self.lbl_face_status.setText(f"🟢 Đã nhận diện: {r_name} (Mã: {r_id}, {age} tuổi - {gender})")
            self.lbl_face_status.setStyleSheet("font-size: 17px; font-weight: bold; color: #10B981;")
            self.lbl_face_sub.setText(f"Độ tin cậy: {r_conf * 100:.1f}% | Hồ sơ: Đã xác thực")
            self.current_patient_id = r_id
            self.current_patient_name = r_name
            self.router.update_recognized_user(r_id, r_name)
        elif f_status == "unknown":
            self.lbl_face_status.setText("🟠 Phát hiện người lạ (Chưa đăng ký)")
            self.lbl_face_status.setStyleSheet("font-size: 17px; font-weight: bold; color: #F59E0B;")
            self.lbl_face_sub.setText("Chưa có hồ sơ trong CSDL. Bấm [➕ Đăng Ký Người Mới] để điền thông tin và chụp ảnh.")
        else:
            self.lbl_face_status.setText("⚪ Chưa phát hiện khuôn mặt")
            self.lbl_face_status.setStyleSheet("font-size: 17px; font-weight: bold; color: #94A3B8;")
            self.lbl_face_sub.setText("Vui lòng nhìn thẳng vào camera, hoặc bấm [➕ Đăng Ký Người Mới] để thêm hồ sơ.")

        # 2. Rehabilitation Metrics
        metrics = self.router.rehab_adapter.get_result()
        reps = metrics.get("repetitions", 0)
        target = metrics.get("target_reps", 10)
        correct = metrics.get("correct_reps", 0)
        incorrect = metrics.get("incorrect_reps", 0)
        score = metrics.get("score", 100.0)
        feedback = metrics.get("feedback", "Chuẩn bị")

        pct = min(100, int((reps / max(1, target)) * 100))
        self.progress_bar.setValue(pct)
        self.lbl_progress.setText(f"Tiến độ: {reps} / {target} lần hoàn thành ({pct}%)")

        self.lbl_correct_cnt.setText(f"Đúng: {correct}")
        self.lbl_incorrect_cnt.setText(f"Chưa chuẩn: {incorrect}")
        self.lbl_score_val.setText(f"Điểm: {score}%")
        self.banner_guidance.setText(f"💡 Hướng dẫn & Đánh giá: {feedback}")

        # 3. Emotion Metrics
        emo = self.router.emotion_adapter.get_result()
        self.lbl_current_emotion.setText(f"Trạng thái: {emo['emotion_vi']} ({emo['confidence'] * 100:.1f}%)")

        # 4. Safety & Fall Monitoring Telemetry
        app_state = self.state.get_realtime_metrics()
        fall_st = app_state.get("fall_state", "NORMAL")
        fall_conf = app_state.get("fall_confidence", 0.0)

        if fall_st == "NORMAL":
            self.lbl_fall_status.setText("Trạng thái:\n✓ Bình thường")
            self.lbl_fall_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        elif fall_st in ("SUSPECTED", "CONFIRMING"):
            self.lbl_fall_status.setText(f"Trạng thái:\n🟠 Nghi ngờ ngã — đang xác nhận ({fall_conf*100:.0f}%)")
            self.lbl_fall_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #F59E0B;")
        elif fall_st == "FALL_CONFIRMED":
            self.lbl_fall_status.setText("Trạng thái:\n🔴 Phát hiện dấu hiệu ngã!")
            self.lbl_fall_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #EF4444;")
        elif fall_st == "COOLDOWN":
            self.lbl_fall_status.setText("Trạng thái:\n⏱️ Đang phục hồi sau sự kiện (Cooldown)")
            self.lbl_fall_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8;")

        caregiver_em = app_state.get("caregiver_email") or profile.get("caregiver", {}).get("email", "")
        if caregiver_em:
            self.lbl_caregiver_email.setText(f"Người nhận:\n{caregiver_em}")
        else:
            self.lbl_caregiver_email.setText("Người nhận:\nChưa cấu hình Gmail")

        last_ev = app_state.get("last_fall_event", "Không có")
        self.lbl_last_fall_event.setText(f"Sự kiện gần nhất: {last_ev}")

        email_st = app_state.get("email_status", "Ready")
        self.lbl_email_status.setText(f"Gmail: {email_st}")

    def _on_timer_tick(self) -> None:
        """Periodic real-time UI refresh every 1 second."""
        now_dt = datetime.now()
        self.lbl_clock.setText(now_dt.strftime("%H:%M:%S | %d/%m/%Y"))
        self.update_dashboard_ui()

    def show_status_message(self, message: str) -> None:
        """Display status notification in bottom bar."""
        now_dt = datetime.now()
        self.status_bar_lbl.setText(
            f"Thời gian: {now_dt.strftime('%H:%M:%S %d/%m/%Y')} | {message} | Giám sát: An toàn ✓"
        )

    def closeEvent(self, event) -> None:
        """Clean shutdown of camera engine."""
        self.camera_manager.stop_camera()
        event.accept()
