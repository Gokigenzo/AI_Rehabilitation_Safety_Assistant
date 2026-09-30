"""
User Registration and Patient Management Modals.
Completely decouples patient enrollment from the live monitoring and face recognition view,
providing clear personal information fields and live camera snapshot capture.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from adapters.face_adapter import FaceAdapter
from core.camera_manager import CameraManager

logger = logging.getLogger("RegistrationDialog")

DIALOG_STYLESHEET = """
QDialog {
    background-color: #0F1218;
    color: #F8FAFC;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 15px;
}
QLabel {
    color: #E2E8F0;
    font-size: 14px;
}
QLabel.section-title {
    font-size: 16px;
    font-weight: bold;
    color: #00E5FA;
    margin-bottom: 4px;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #171B24;
    border: 1.5px solid #2D3342;
    border-radius: 8px;
    color: #FFFFFF;
    padding: 8px 14px;
    font-size: 15px;
    min-height: 36px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #00E5FA;
    background-color: #1C222E;
}
QPushButton.btn-primary {
    background-color: #10B981;
    color: #FFFFFF;
    font-size: 15px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px 22px;
    min-height: 42px;
}
QPushButton.btn-primary:hover {
    background-color: #059669;
}
QPushButton.btn-capture {
    background-color: #00C4D6;
    color: #000000;
    font-size: 15px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    min-height: 42px;
}
QPushButton.btn-capture:hover {
    background-color: #00E5FA;
}
QPushButton.btn-secondary {
    background-color: #242938;
    color: #CBD5E1;
    font-size: 15px;
    font-weight: 600;
    border: 1px solid #333C4E;
    border-radius: 8px;
    padding: 10px 20px;
    min-height: 42px;
}
QPushButton.btn-secondary:hover {
    background-color: #2E3547;
    color: #FFFFFF;
}
QPushButton.btn-danger {
    background-color: #EF4444;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 38px;
}
QPushButton.btn-danger:hover {
    background-color: #DC2626;
}
QFrame.card {
    background-color: #141721;
    border: 1.5px solid #232836;
    border-radius: 10px;
    padding: 14px;
}
QTableWidget {
    background-color: #141721;
    border: 1.5px solid #232836;
    border-radius: 10px;
    gridline-color: #252B3B;
    color: #F8FAFC;
    font-size: 14px;
    selection-background-color: #0E2A38;
    selection-color: #00E5FA;
}
QHeaderView::section {
    background-color: #1A1E2B;
    color: #94A3B8;
    font-weight: bold;
    font-size: 14px;
    border: none;
    padding: 10px 8px;
}
"""


class RegistrationDialog(QDialog):
    """
    Dedicated User Registration Modal.
    Provides clear, prominent personal information inputs (Họ tên, ID, Tuổi, Giới tính, Ghi chú)
    and live camera face photo sample capture.
    """

    patient_registered = pyqtSignal(dict)

    def __init__(self, face_adapter: FaceAdapter, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.face_adapter = face_adapter
        self.camera_manager = CameraManager.get_instance()
        self.captured_faces: List[np.ndarray] = []

        self.setWindowTitle("Đăng Ký Hồ Sơ Người Dùng Mới — Thông Tin Cá Nhân & Nhận Diện")
        self.setMinimumSize(980, 640)
        self.setStyleSheet(DIALOG_STYLESHEET)

        self._init_ui()

        # Preview update timer
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self._update_preview)
        self.preview_timer.start(40)  # ~25 FPS

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title
        lbl_head = QLabel("➕ ĐĂNG KÝ HỒ SƠ NGƯỜI DÙNG / BỆNH NHÂN MỚI")
        lbl_head.setStyleSheet("font-size: 20px; font-weight: 800; color: #00E5FA;")
        lbl_desc = QLabel(
            "Vui lòng điền đầy đủ thông tin cá nhân bên dưới và chụp ít nhất 1 ảnh khuôn mặt mẫu. "
            "Dữ liệu sẽ được lưu vào cơ sở dữ liệu và huấn luyện mô hình nhận diện tự động."
        )
        lbl_desc.setStyleSheet("font-size: 14px; color: #94A3B8;")
        main_layout.addWidget(lbl_head)
        main_layout.addWidget(lbl_desc)

        # Body: Left Form (50%) + Right Camera Preview (50%)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)

        # ==================== CỘT 1: ĐIỀN THÔNG TIN CÁ NHÂN ====================
        form_frame = QFrame()
        form_frame.setProperty("class", "card")
        lay_form = QVBoxLayout(form_frame)
        lay_form.setSpacing(10)

        lbl_f_title = QLabel("📋 1. ĐIỀN THÔNG TIN CÁ NHÂN")
        lbl_f_title.setProperty("class", "section-title")
        lay_form.addWidget(lbl_f_title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # 1. Mã ID
        existing_patients = self.face_adapter.get_all_patients()
        next_id = str(len(existing_patients) + 1)
        lbl_id = QLabel("Mã bệnh nhân (ID) (*):")
        lbl_id.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.edit_id = QLineEdit(next_id)
        self.edit_id.setPlaceholderText("VD: 001, 1...")
        self.edit_id.setFixedWidth(140)
        grid.addWidget(lbl_id, 0, 0)
        grid.addWidget(self.edit_id, 0, 1)

        # 2. Họ và tên
        lbl_name = QLabel("Họ và tên (*):")
        lbl_name.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Nhập đầy đủ họ và tên (VD: Trần Văn Nam)...")
        grid.addWidget(lbl_name, 1, 0)
        grid.addWidget(self.edit_name, 1, 1)

        # 3. Tuổi
        lbl_age = QLabel("Tuổi:")
        lbl_age.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.spin_age = QSpinBox()
        self.spin_age.setRange(1, 120)
        self.spin_age.setValue(70)
        self.spin_age.setFixedWidth(140)
        grid.addWidget(lbl_age, 2, 0)
        grid.addWidget(self.spin_age, 2, 1)

        # 4. Giới tính
        lbl_gender = QLabel("Giới tính:")
        lbl_gender.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.combo_gender = QComboBox()
        self.combo_gender.addItems(["Nam", "Nữ", "Khác"])
        self.combo_gender.setFixedWidth(140)
        grid.addWidget(lbl_gender, 3, 0)
        grid.addWidget(self.combo_gender, 3, 1)

        # 5. Ghi chú bệnh lý
        lbl_notes = QLabel("Ghi chú / Tình trạng:")
        lbl_notes.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.edit_notes = QLineEdit()
        self.edit_notes.setPlaceholderText("VD: Phục hồi khớp vai sau tai biến...")
        grid.addWidget(lbl_notes, 4, 0)
        grid.addWidget(self.edit_notes, 4, 1)

        # 6. Thông tin Người Chăm Sóc / Người Thân (Bắt buộc Gmail để nhận cảnh báo ngã)
        lbl_cg_title = QLabel("👨‍👩‍👧 THÔNG TIN NGƯỜI CHĂM SÓC / NGƯỜI THÂN")
        lbl_cg_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38BDF8; margin-top: 8px;")
        grid.addWidget(lbl_cg_title, 5, 0, 1, 2)

        lbl_cg_name = QLabel("Họ tên người thân:")
        lbl_cg_name.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.edit_cg_name = QLineEdit()
        self.edit_cg_name.setPlaceholderText("VD: Nguyễn Văn B")
        grid.addWidget(lbl_cg_name, 6, 0)
        grid.addWidget(self.edit_cg_name, 6, 1)

        lbl_cg_rel = QLabel("Mối quan hệ:")
        lbl_cg_rel.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.combo_cg_rel = QComboBox()
        self.combo_cg_rel.addItems(["Con cái", "Vợ / Chồng", "Cháu", "Người giám hộ", "Điều dưỡng / Bác sĩ", "Khác"])
        grid.addWidget(lbl_cg_rel, 7, 0)
        grid.addWidget(self.combo_cg_rel, 7, 1)

        lbl_cg_email = QLabel("Gmail nhận cảnh báo (*):")
        lbl_cg_email.setStyleSheet("font-weight: 600; color: #EF4444;")
        self.edit_cg_email = QLineEdit()
        self.edit_cg_email.setPlaceholderText("VD: caregiver@gmail.com (Bắt buộc để gửi cảnh báo khi ngã)")
        grid.addWidget(lbl_cg_email, 8, 0)
        grid.addWidget(self.edit_cg_email, 8, 1)

        lay_form.addLayout(grid)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #232836; background-color: #232836; margin: 4px 0;")
        lay_form.addWidget(sep)

        # Photo Capture Summary
        lbl_p_title = QLabel("📸 2. ẢNH MẪU KHUÔN MẶT ĐÃ CHỤP")
        lbl_p_title.setProperty("class", "section-title")
        lay_form.addWidget(lbl_p_title)

        self.lbl_photo_status = QLabel("Chưa có ảnh mẫu nào. (Cần ít nhất 1 ảnh rõ mặt)")
        self.lbl_photo_status.setStyleSheet("font-size: 14px; color: #F59E0B; font-weight: 600;")
        lay_form.addWidget(self.lbl_photo_status)

        # Thumbnails strip
        self.thumb_layout = QHBoxLayout()
        self.thumb_layout.setSpacing(6)
        lay_form.addLayout(self.thumb_layout)

        # Photo Action Buttons
        btn_box_photo = QHBoxLayout()
        btn_box_photo.setSpacing(8)

        self.btn_capture = QPushButton("📸 Chụp Ảnh Ngay")
        self.btn_capture.setProperty("class", "btn-capture")
        self.btn_capture.clicked.connect(self._on_capture_click)

        self.btn_upload = QPushButton("📁 Chọn Ảnh...")
        self.btn_upload.setProperty("class", "btn-secondary")
        self.btn_upload.clicked.connect(self._on_upload_photo)

        self.btn_clear_photos = QPushButton("🗑️ Xóa Lại")
        self.btn_clear_photos.setProperty("class", "btn-secondary")
        self.btn_clear_photos.clicked.connect(self._on_clear_photos)

        btn_box_photo.addWidget(self.btn_capture)
        btn_box_photo.addWidget(self.btn_upload)
        btn_box_photo.addWidget(self.btn_clear_photos)
        lay_form.addLayout(btn_box_photo)

        lay_form.addStretch()
        body_layout.addWidget(form_frame, 50)

        # ==================== CỘT 2: CAMERA TRỰC TIẾP & HƯỚNG DẪN ====================
        cam_frame = QFrame()
        cam_frame.setProperty("class", "card")
        lay_cam = QVBoxLayout(cam_frame)
        lay_cam.setSpacing(8)

        lbl_c_title = QLabel("📷 3. CAMERA TRỰC TIẾP CĂN CHỈNH KHUÔN MẶT")
        lbl_c_title.setProperty("class", "section-title")
        lay_cam.addWidget(lbl_c_title)

        # Preview display
        self.preview_display = QLabel()
        self.preview_display.setMinimumSize(420, 290)
        self.preview_display.setAlignment(Qt.AlignCenter)
        self.preview_display.setStyleSheet("background-color: #000000; border: 1.5px solid #232836; border-radius: 8px;")
        lay_cam.addWidget(self.preview_display, 1)

        # Guiding Status
        self.lbl_guidance = QLabel("⚪ Đang kết nối luồng camera...")
        self.lbl_guidance.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #00E5FA; "
            "background-color: #121E24; padding: 8px 12px; border-radius: 6px;"
        )
        lay_cam.addWidget(self.lbl_guidance)

        # Instructions note
        lbl_note = QLabel("💡 Lưu ý: Ngồi hoặc đứng thẳng cách camera 1.0m - 2.0m, đủ ánh sáng. Có thể chụp 2-3 góc mặt để nhận diện chuẩn nhất.")
        lbl_note.setStyleSheet("font-size: 13px; color: #94A3B8;")
        lbl_note.setWordWrap(True)
        lay_cam.addWidget(lbl_note)

        body_layout.addWidget(cam_frame, 50)
        main_layout.addLayout(body_layout, 1)

        # ==================== HÀNG NÚT DƯỚI CÙNG ====================
        lay_footer = QHBoxLayout()
        lay_footer.addStretch()

        self.btn_cancel = QPushButton("Hủy / Đóng")
        self.btn_cancel.setProperty("class", "btn-secondary")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("💾 Lưu Hồ Sơ & Huấn Luyện Nhận Diện")
        self.btn_save.setProperty("class", "btn-primary")
        self.btn_save.clicked.connect(self._on_save_patient)

        lay_footer.addWidget(self.btn_cancel)
        lay_footer.addWidget(self.btn_save)
        main_layout.addLayout(lay_footer)

    def _update_preview(self) -> None:
        """Render live camera feed with real-time face detection indicator."""
        frame = self.camera_manager.get_latest_frame()
        if frame is None:
            return

        display_frame = frame.copy()
        det = self.face_adapter.detect_face(display_frame)

        if det is not None:
            bx, by, bw, bh, conf = det
            cv2.rectangle(display_frame, (bx, by), (bx + bw, by + bh), (74, 222, 128), 2)
            cv2.putText(
                display_frame,
                f"Face OK ({conf * 100:.0f}%)",
                (bx, max(20, by - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (74, 222, 128),
                2,
            )
            self.lbl_guidance.setText("🟢 Khuôn mặt rõ nét! Bấm 'Chụp Ảnh Ngay' để lấy mẫu.")
            self.lbl_guidance.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #10B981; "
                "background-color: #0E2419; padding: 6px 10px; border-radius: 4px;"
            )
        else:
            self.lbl_guidance.setText("🟠 Chưa thấy khuôn mặt rõ. Vui lòng nhìn thẳng vào camera...")
            self.lbl_guidance.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #F59E0B; "
                "background-color: #241A0E; padding: 6px 10px; border-radius: 4px;"
            )

        # Convert to QPixmap
        h, w, ch = display_frame.shape
        bytes_per_line = ch * w
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self.preview_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview_display.setPixmap(pix)

    def _on_capture_click(self) -> None:
        """Capture face crop from latest frame."""
        frame = self.camera_manager.get_latest_frame()
        if frame is None:
            QMessageBox.warning(self, "Lỗi Camera", "Không nhận được tín hiệu từ camera.")
            return

        det = self.face_adapter.detect_face(frame)
        if det is None:
            QMessageBox.warning(
                self,
                "Không Tìm Thấy Mặt",
                "Chưa phát hiện khuôn mặt rõ nét trong khung hình. Vui lòng nhìn thẳng vào camera và thử lại.",
            )
            return

        face_crop = self.face_adapter.crop_face(frame, box=det)
        self.captured_faces.append(face_crop)
        self._refresh_thumbnails()

    def _on_upload_photo(self) -> None:
        """Allow user to select an existing face photo from disk."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh khuôn mặt mẫu",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp)",
        )
        if not file_path:
            return

        img = cv2.imread(file_path)
        if img is None:
            QMessageBox.warning(self, "Lỗi đọc tệp", "Không thể đọc tệp hình ảnh đã chọn.")
            return

        det = self.face_adapter.detect_face(img)
        face_crop = self.face_adapter.crop_face(img, box=det)
        self.captured_faces.append(face_crop)
        self._refresh_thumbnails()

    def _refresh_thumbnails(self) -> None:
        """Update photo count and thumbnail strip."""
        while self.thumb_layout.count():
            item = self.thumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        count = len(self.captured_faces)
        if count == 0:
            self.lbl_photo_status.setText("Chưa có ảnh mẫu nào. (Cần ít nhất 1 ảnh rõ mặt)")
            self.lbl_photo_status.setStyleSheet("font-size: 12px; color: #F59E0B; font-weight: 600;")
        else:
            self.lbl_photo_status.setText(f"✅ Đã có {count} ảnh mẫu khuôn mặt sẵn sàng.")
            self.lbl_photo_status.setStyleSheet("font-size: 12px; color: #10B981; font-weight: 600;")

            for idx, crop in enumerate(self.captured_faces[-4:]):
                rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                lbl_thumb = QLabel()
                lbl_thumb.setFixedSize(60, 60)
                lbl_thumb.setScaledContents(True)
                lbl_thumb.setPixmap(QPixmap.fromImage(qimg))
                lbl_thumb.setStyleSheet("border: 1.5px solid #00E5FA; border-radius: 4px;")
                self.thumb_layout.addWidget(lbl_thumb)

        self.thumb_layout.addStretch()

    def _on_clear_photos(self) -> None:
        """Clear captured face samples."""
        self.captured_faces.clear()
        self._refresh_thumbnails()

    def _on_save_patient(self) -> None:
        """Validate, register patient, save photos, and trigger model retraining."""
        pid = self.edit_id.text().strip()
        name = self.edit_name.text().strip()
        age = self.spin_age.value()
        gender = self.combo_gender.currentText()
        notes = self.edit_notes.text().strip()

        if not pid:
            QMessageBox.warning(self, "Thiếu Thông Tin", "Vui lòng nhập Mã định danh (ID).")
            self.edit_id.setFocus()
            return

        if not name:
            QMessageBox.warning(self, "Thiếu Thông Tin", "Vui lòng nhập Họ và tên người bệnh.")
            self.edit_name.setFocus()
            return

        cg_name = self.edit_cg_name.text().strip()
        cg_rel = self.combo_cg_rel.currentText()
        cg_email = self.edit_cg_email.text().strip()

        from services.user_service import UserService

        if not cg_email:
            QMessageBox.warning(
                self,
                "Thiếu Gmail Cảnh Báo",
                "Vui lòng nhập Gmail của người thân/người chăm sóc để hệ thống gửi cảnh báo khẩn cấp khi phát hiện ngã.",
            )
            self.edit_cg_email.setFocus()
            return

        if not UserService.validate_email(cg_email):
            QMessageBox.warning(
                self,
                "Gmail Không Hợp Lệ",
                f"Địa chỉ '{cg_email}' không đúng định dạng email tiêu chuẩn.\nVí dụ hợp lệ: nguoi_than@gmail.com",
            )
            self.edit_cg_email.setFocus()
            return

        if not self.captured_faces:
            # Auto-attempt capture from live frame
            frame = self.camera_manager.get_latest_frame()
            if frame is not None:
                det = self.face_adapter.detect_face(frame)
                if det is not None:
                    crop = self.face_adapter.crop_face(frame, box=det)
                    self.captured_faces.append(crop)

        if not self.captured_faces:
            QMessageBox.warning(
                self,
                "Chưa Có Ảnh Nhận Diện",
                "Hệ thống cần ít nhất 1 ảnh khuôn mặt mẫu. Hãy bấm '📸 Chụp Ảnh Ngay' hoặc '📁 Chọn Ảnh...' trước khi lưu.",
            )
            return

        # Register and train
        profile = self.face_adapter.register_patient(
            name=name,
            patient_id=pid,
            age=age,
            gender=gender,
            notes=notes,
            face_images=self.captured_faces,
            caregiver_name=cg_name,
            caregiver_relationship=cg_rel,
            caregiver_email=cg_email,
        )

        QMessageBox.information(
            self,
            "Đăng Ký Thành Công",
            f"Đã lưu thành công hồ sơ người dùng:\n"
            f"• Mã ID: {pid}\n"
            f"• Họ tên: {name} ({age} tuổi - {gender})\n"
            f"• Người thân: {cg_name or 'Người chăm sóc'} ({cg_rel})\n"
            f"• Gmail cảnh báo: {cg_email}\n"
            f"• Số ảnh mẫu: {len(self.captured_faces)}\n\n"
            f"Hệ thống đã tự động huấn luyện nhận diện danh tính {name}.",
        )

        self.preview_timer.stop()
        self.patient_registered.emit(profile)
        self.accept()

    def closeEvent(self, event) -> None:
        self.preview_timer.stop()
        event.accept()


class PatientManagementDialog(QDialog):
    """
    Dialog to inspect and manage all registered patient profiles.
    Allows viewing all personal info, deleting, or registering new patients.
    """

    patient_selected = pyqtSignal(dict)

    def __init__(self, face_adapter: FaceAdapter, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.face_adapter = face_adapter

        self.setWindowTitle("Quản Lý Danh Sách Người Bệnh & Hồ Sơ")
        self.setMinimumSize(980, 560)
        self.setStyleSheet(DIALOG_STYLESHEET)

        self._init_ui()
        self._load_table_data()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 20, 22, 20)
        main_layout.setSpacing(14)

        # Header
        top_row = QHBoxLayout()
        v_title = QVBoxLayout()
        lbl_head = QLabel("👥 DANH SÁCH HỒ SƠ NGƯỜI BỆNH ĐÃ ĐĂNG KÝ")
        lbl_head.setStyleSheet("font-size: 18px; font-weight: 800; color: #00E5FA;")
        lbl_desc = QLabel("Xem danh sách thông tin cá nhân và dữ liệu nhận diện khuôn mặt trong hệ thống.")
        lbl_desc.setStyleSheet("font-size: 14px; color: #94A3B8;")
        v_title.addWidget(lbl_head)
        v_title.addWidget(lbl_desc)
        top_row.addLayout(v_title)

        top_row.addStretch()

        btn_add = QPushButton("➕ Đăng Ký Người Mới")
        btn_add.setProperty("class", "btn-primary")
        btn_add.clicked.connect(self._on_open_register)
        top_row.addWidget(btn_add)

        main_layout.addLayout(top_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Mã ID", "Họ và Tên", "Tuổi", "Giới Tính", "Người Thân", "Gmail Cảnh Báo", "Số Ảnh", "Ghi Chú"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.table, 1)

        # Footer Actions
        lay_footer = QHBoxLayout()
        btn_delete = QPushButton("🗑️ Xóa Hồ Sơ Đang Chọn")
        btn_delete.setProperty("class", "btn-danger")
        btn_delete.clicked.connect(self._on_delete_selected)

        btn_close = QPushButton("Đóng")
        btn_close.setProperty("class", "btn-secondary")
        btn_close.clicked.connect(self.accept)

        lay_footer.addWidget(btn_delete)
        lay_footer.addStretch()
        lay_footer.addWidget(btn_close)
        main_layout.addLayout(lay_footer)

    def _load_table_data(self) -> None:
        """Populate table with registered patients."""
        patients = self.face_adapter.get_all_patients()
        self.table.setRowCount(len(patients))

        for row, p in enumerate(patients):
            cg = p.get("caregiver") or {}
            cg_name = cg.get("name", "—") if isinstance(cg, dict) else "—"
            cg_email = cg.get("email", "—") if isinstance(cg, dict) else "—"

            self.table.setItem(row, 0, QTableWidgetItem(str(p.get("patient_id") or p.get("user_id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(p.get("name", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(p.get("age", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(p.get("gender", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(str(cg_name)))
            self.table.setItem(row, 5, QTableWidgetItem(str(cg_email)))
            self.table.setItem(row, 6, QTableWidgetItem(f"{p.get('image_count', 1)} ảnh"))
            self.table.setItem(row, 7, QTableWidgetItem(str(p.get("notes", ""))))

    def _on_delete_selected(self) -> None:
        """Delete selected patient profile."""
        cur_row = self.table.currentRow()
        if cur_row < 0:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một người dùng trong bảng để xóa.")
            return

        pid_item = self.table.item(cur_row, 0)
        name_item = self.table.item(cur_row, 1)
        if not pid_item or not name_item:
            return

        pid = pid_item.text()
        name = name_item.text()

        confirm = QMessageBox.question(
            self,
            "Xác Nhận Xóa",
            f"Bạn có chắc muốn xóa hồ sơ của:\n• Mã ID: {pid}\n• Họ tên: {name}?\n\n(Dữ liệu khuôn mặt mẫu cũng sẽ bị xóa)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            self.face_adapter.delete_patient(pid)
            self._load_table_data()
            QMessageBox.information(self, "Đã Xóa", f"Đã xóa thành công hồ sơ của {name}.")

    def _on_open_register(self) -> None:
        """Open registration modal from manager."""
        dlg = RegistrationDialog(self.face_adapter, self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_table_data()
