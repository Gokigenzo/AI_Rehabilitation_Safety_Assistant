"""
Router and Action Dispatcher for AI Rehabilitation & Safety Assistant.
Connects UI actions, Vision Adapters (Face, Emotion, Rehabilitation, Fall), and State.
Voice is completely removed from runtime.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from PyQt5.QtWidgets import QMessageBox

from adapters import (
    EmotionAdapter,
    FaceAdapter,
    FallAdapter,
    RehabilitationAdapter,
)
from services.state_service import StateService

if TYPE_CHECKING:
    from app.dashboard import DashboardWindow

logger = logging.getLogger("RehabRouter")


class DashboardRouter:
    """Dispatches actions between UI, Vision Adapters, Fall Monitor, and State."""

    def __init__(self, window: Optional[Any] = None) -> None:
        self.window = window

        # State service
        self.state_service = StateService()

        # Core Vision Adapters
        self.face_adapter = FaceAdapter()
        self.emotion_adapter = EmotionAdapter(smoothing_window=8)
        self.rehab_adapter = RehabilitationAdapter()
        self.fall_adapter = FallAdapter()

    def update_recognized_user(self, user_id: str, user_name: Optional[str] = None) -> None:
        """Propagate recognized user identity to FallMonitor."""
        self.fall_adapter.set_current_user(user_id, user_name)

    def start_exercise(self, exercise_id: str) -> None:
        """Switch camera mode to rehabilitation and begin tracking."""
        self.rehab_adapter.start_exercise(exercise_id)
        if self.window and hasattr(self.window, "camera_manager"):
            self.window.camera_manager.set_mode("rehabilitation")
        metrics = self.rehab_adapter.get_result()
        ex_name = metrics.get("exercise_name", "bài tập")

        if self.window and hasattr(self.window, "show_status_message"):
            self.window.show_status_message(f"Bắt đầu bài tập: {ex_name}")
        if self.window and hasattr(self.window, "update_dashboard_ui"):
            self.window.update_dashboard_ui()

    def stop_exercise(self) -> Dict[str, Any]:
        """Stop exercise and return to monitoring mode."""
        metrics = self.rehab_adapter.stop_exercise()
        if self.window and hasattr(self.window, "camera_manager"):
            self.window.camera_manager.set_mode("monitor")

        if self.window and hasattr(self.window, "show_status_message"):
            self.window.show_status_message(f"Đã dừng bài tập. Điểm số: {metrics.get('score')}%")
        if self.window and hasattr(self.window, "update_dashboard_ui"):
            self.window.update_dashboard_ui()
        return metrics

    def show_exercise_result_modal(self) -> None:
        """Display comprehensive session evaluation modal."""
        # Resolve patient name from window property or face adapter
        user_name = "Bác"
        if self.window and hasattr(self.window, "current_patient_name") and self.window.current_patient_name:
            user_name = self.window.current_patient_name
        else:
            profile = self.face_adapter.get_patient_profile()
            if profile and profile.get("name"):
                user_name = profile["name"]

        metrics = self.rehab_adapter.get_result()
        score = metrics.get("score", 100.0)
        reps = metrics.get("repetitions", 0)
        target = metrics.get("target_reps", 10)
        correct = metrics.get("correct_reps", 0)
        incorrect = metrics.get("incorrect_reps", 0)
        ex_name = metrics.get("exercise_name", "Phục hồi chức năng")

        rating = "Xuất sắc! Động tác rất chuẩn xác." if score >= 90 else (
            "Khá tốt! Cần chú ý giữ thẳng lưng và biên độ tay." if score >= 75 else
            "Cần cố gắng hơn ở các lần tập tiếp theo."
        )

        msg = QMessageBox(self.window)
        msg.setWindowTitle("Kết Quả Đánh Giá Phục Hồi Chức Năng")
        msg.setText(f"""
            <div style='color: #FFFFFF; font-size: 14px; line-height: 1.6; padding: 4px;'>
                <h3 style='color: #00E5FA; margin-top: 0;'>BÁO CÁO PHIÊN TẬP PHỤC HỒI CHỨC NĂNG</h3>
                • <b>Người tập:</b> {user_name}<br>
                • <b>Bài tập:</b> <span style='color: #00E5FA;'>{ex_name}</span><br>
                • <b>Tổng số lần hoàn thành:</b> <b>{reps} / {target} lần</b><br>
                • <b>Động tác chuẩn:</b> <span style='color: #10B981;'>{correct}</span>  |  <b>Chưa chuẩn:</b> <span style='color: #EF4444;'>{incorrect}</span><br>
                • <b>Điểm kỹ thuật động tác (Score):</b> <span style='font-size: 18px; font-weight: bold; color: {'#10B981' if score >= 80 else '#F59E0B'};'>{score}%</span><br>
                • <b>Nhận xét chuyên môn:</b> {rating}
            </div>
        """)
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet("""
            QMessageBox { background-color: #1A1D24; border: 1px solid #2D3342; border-radius: 8px; }
            QLabel { color: #FFFFFF !important; background-color: transparent; }
            QPushButton { background-color: #00C4D6; color: #000000 !important; font-weight: bold; border-radius: 6px; padding: 8px 24px; min-width: 90px; }
            QPushButton:hover { background-color: #00E5FA; }
        """)
        msg.exec_()
