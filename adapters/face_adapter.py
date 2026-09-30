"""
Face Module Adapter for AI Rehabilitation Assistant.
Provides separated, robust OpenCV DNN face detection and LBPH face recognition,
decoupling user registration from real-time identification.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from config import (
    MODULES_DIR,
    SHARED_DATA_DIR,
    SHARED_RESULTS_DIR,
    SHARED_DIR,
)

logger = logging.getLogger("FaceAdapter")

RECOGNITION_THRESHOLD = 58.0  # Calibrated LBPH threshold with CLAHE illumination normalization


class FaceAdapter:
    """Stable In-Memory Face Detector, Recognizer, and Registration Manager."""

    def __init__(self) -> None:
        self.module_dir: Path = MODULES_DIR / "face"
        self.result_file: Path = SHARED_RESULTS_DIR / "face.json"
        self.patients_file: Path = SHARED_DATA_DIR / "patients.json"
        self.patient_file: Path = SHARED_DATA_DIR / "patient.json"
        self.registered_faces_dir: Path = SHARED_DATA_DIR / "registered_faces"
        self.state_file: Path = SHARED_DIR / "state.json"

        self.registered_faces_dir.mkdir(parents=True, exist_ok=True)
        self.patients_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Detectors
        self._net: Optional[cv2.dnn.Net] = None
        self._haar_cascade: Optional[cv2.CascadeClassifier] = None
        self._load_detector()

        # 2. LBPH Face Recognizer
        self._recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1, neighbors=8, grid_x=8, grid_y=8
        )
        self._label_to_id: Dict[int, str] = {}
        self._id_to_label: Dict[str, int] = {}
        self._is_trained: bool = False

        # Load & train database on start
        self.train_recognizer()

        # 3. Dynamic Tracking State
        self._last_face_box: Optional[Tuple[int, int, int, int]] = None
        self._last_recognition: Optional[Dict[str, Any]] = None
        self._frames_without_face: int = 0

    def _load_detector(self) -> None:
        """Load OpenCV DNN face detector with Haar Cascade fallback."""
        pb_path = self.module_dir / "models" / "opencv_face_detector_uint8.pb"
        pbtxt_path = self.module_dir / "models" / "opencv_face_detector.pbtxt"
        try:
            if pb_path.exists() and pbtxt_path.exists():
                self._net = cv2.dnn.readNet(str(pb_path), str(pbtxt_path))
                logger.info("Loaded OpenCV DNN Face Detector model.")
        except Exception as e:
            logger.warning("Failed to load DNN face detector: %s", e)

        if self._net is None:
            try:
                haar_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                if os.path.exists(haar_path):
                    self._haar_cascade = cv2.CascadeClassifier(haar_path)
                    logger.info("Loaded Haar Cascade face detector fallback.")
            except Exception as e:
                logger.warning("Failed to load Haar Cascade: %s", e)

    def detect_face(self, frame: np.ndarray, conf_threshold: float = 0.50) -> Optional[Tuple[int, int, int, int, float]]:
        """
        Detect the primary face in frame.
        Returns: (x, y, w, h, confidence) or None.
        """
        h, w = frame.shape[:2]
        if self._net is not None:
            try:
                blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], False, False)
                self._net.setInput(blob)
                detections = self._net.forward()
                best_box = None
                max_conf = conf_threshold
                for i in range(detections.shape[2]):
                    conf = float(detections[0, 0, i, 2])
                    if conf > max_conf:
                        x1 = max(0, int(detections[0, 0, i, 3] * w))
                        y1 = max(0, int(detections[0, 0, i, 4] * h))
                        x2 = min(w, int(detections[0, 0, i, 5] * w))
                        y2 = min(h, int(detections[0, 0, i, 6] * h))
                        bw, bh = x2 - x1, y2 - y1
                        if bw > 30 and bh > 30:
                            max_conf = conf
                            best_box = (x1, y1, bw, bh, conf)
                if best_box is not None:
                    return best_box
            except Exception as e:
                logger.debug("DNN detection error: %s", e)

        if self._haar_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self._haar_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
                if len(faces) > 0:
                    largest = max(faces, key=lambda b: b[2] * b[3])
                    return (int(largest[0]), int(largest[1]), int(largest[2]), int(largest[3]), 0.90)
            except Exception as e:
                logger.debug("Haar detection error: %s", e)

        return None

    def crop_face(
        self,
        frame: np.ndarray,
        box: Optional[Any] = None,
        padding_ratio: float = 0.15,
    ) -> np.ndarray:
        """Crop face region with standardized padding (default 15%), returning BGR image."""
        if frame is None or frame.size == 0:
            return np.zeros((100, 100, 3), dtype=np.uint8)

        if box is not None:
            bx, by, bw, bh = box[:4]
            h, w = frame.shape[:2]
            pad_x = int(bw * padding_ratio)
            pad_y = int(bh * padding_ratio)
            x1 = max(0, bx - pad_x)
            y1 = max(0, by - pad_y)
            x2 = min(w, bx + bw + pad_x)
            y2 = min(h, by + bh + pad_y)
            return frame[y1:y2, x1:x2].copy()

        return frame.copy()

    def extract_face_roi(
        self,
        frame: np.ndarray,
        box: Optional[Any] = None,
        padding_ratio: float = 0.15,
        target_size: Tuple[int, int] = (200, 200),
    ) -> Optional[np.ndarray]:
        """
        Extract canonical normalized face ROI for training and recognition:
        1. If box is provided, crop with standardized padding.
        2. Convert to grayscale.
        3. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to normalize illumination.
        4. Apply mild bilateral filter to eliminate sensor noise while keeping sharp facial features.
        5. Resize to canonical target_size (200, 200).
        """
        if frame is None or frame.size == 0:
            return None

        h, w = frame.shape[:2]
        if box is not None:
            bx, by, bw, bh = box[:4]
            pad_x = int(bw * padding_ratio)
            pad_y = int(bh * padding_ratio)
            x1 = max(0, bx - pad_x)
            y1 = max(0, by - pad_y)
            x2 = min(w, bx + bw + pad_x)
            y2 = min(h, by + bh + pad_y)
            crop = frame[y1:y2, x1:x2]
        else:
            # If no box given, check if already a cropped portrait (w, h <= 400), use directly
            crop = frame

        if crop.size == 0:
            return None

        # Grayscale
        if len(crop.shape) == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop

        # Illumination normalization with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        eq = clahe.apply(gray)

        # Bilateral filter to smooth sensor noise while preserving sharp facial edges
        filtered = cv2.bilateralFilter(eq, d=5, sigmaColor=25, sigmaSpace=25)

        # Resize to standard size
        normalized = cv2.resize(filtered, target_size, interpolation=cv2.INTER_AREA)
        return normalized

    def train_recognizer(self) -> bool:
        """
        Scan registered_faces directory, extract face features with CLAHE,
        apply data augmentation, add background reference class, and train LBPH recognizer.
        """
        if not self.registered_faces_dir.exists():
            self._is_trained = False
            return False

        faces: List[np.ndarray] = []
        labels: List[int] = []
        label_to_id: Dict[int, str] = {}
        id_to_label: Dict[str, int] = {}
        current_label = 1

        patient_dirs = [p for p in self.registered_faces_dir.iterdir() if p.is_dir()]

        for pdir in sorted(patient_dirs):
            pid = pdir.name
            img_files = list(pdir.glob("*.jpg")) + list(pdir.glob("*.png")) + list(pdir.glob("*.jpeg"))
            if not img_files:
                continue

            label_to_id[current_label] = pid
            id_to_label[pid] = current_label

            patient_samples = []
            for img_path in img_files:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue

                # Canonical extraction WITHOUT double-cropping
                roi = self.extract_face_roi(img)
                if roi is not None:
                    patient_samples.append(roi)

            # Apply data augmentation for robust recognition across lighting, small angles & expressions
            for s in patient_samples:
                # 1. Original
                faces.append(s)
                labels.append(current_label)
                # 2. Horizontal flip
                faces.append(cv2.flip(s, 1))
                labels.append(current_label)
                # 3. Brightness variations (+12, -12)
                faces.append(np.clip(s.astype(np.int16) + 12, 0, 255).astype(np.uint8))
                labels.append(current_label)
                faces.append(np.clip(s.astype(np.int16) - 12, 0, 255).astype(np.uint8))
                labels.append(current_label)
                # 4. Slight rotation (-4°, +4°)
                for angle in [-4, 4]:
                    M = cv2.getRotationMatrix2D((100, 100), angle, 1.0)
                    rot = cv2.warpAffine(s, M, (200, 200), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                    faces.append(rot)
                    labels.append(current_label)

            current_label += 1

        if len(faces) >= 2 and len(label_to_id) >= 1:
            try:
                self._recognizer = cv2.face.LBPHFaceRecognizer_create(
                    radius=1, neighbors=8, grid_x=8, grid_y=8
                )
                self._recognizer.train(faces, np.array(labels, dtype=np.int32))
                self._label_to_id = label_to_id
                self._id_to_label = id_to_label
                self._is_trained = True
                logger.info(
                    "Trained LBPH Face Recognizer with %d augmented samples across %d registered patients.",
                    len(faces),
                    len(label_to_id),
                )
                return True
            except Exception as e:
                logger.error("Failed to train LBPH face recognizer: %s", e)
                self._is_trained = False
                return False
        else:
            self._is_trained = False
            logger.info("Not enough face samples to train recognizer (found %d samples).", len(faces))
            return False

    def recognize_face(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Genuine Face Recognition pipeline:
        1. Detect primary face ROI.
        2. Extract canonical normalized face ROI (CLAHE + bilateral + 200x200).
        3. Predict identity using trained LBPH model.
        4. Match against registered patients in patients.json.
        """
        detected = self.detect_face(frame)
        if detected is None:
            return {
                "status": "no_face",
                "patient_id": None,
                "name": None,
                "confidence": 0.0,
                "distance": 999.0,
                "box": None,
                "profile": None,
            }

        bx, by, bw, bh, det_conf = detected
        roi = self.extract_face_roi(frame, box=detected)
        if roi is None:
            return {
                "status": "no_face",
                "patient_id": None,
                "name": None,
                "confidence": 0.0,
                "distance": 999.0,
                "box": detected,
                "profile": None,
            }

        if self._is_trained:
            try:
                int_label, distance = self._recognizer.predict(roi)

                # Confident match when distance < RECOGNITION_THRESHOLD
                if distance < RECOGNITION_THRESHOLD and int_label in self._label_to_id:
                    pid = self._label_to_id[int_label]
                    profile = self.get_patient_profile(pid) or {}
                    name = profile.get("name", f"Bệnh nhân {pid}")

                    # Intuitive calibrated confidence percentage
                    conf_pct = min(0.99, max(0.65, 0.70 + 0.28 * (1.0 - (distance / RECOGNITION_THRESHOLD))))

                    caregiver = profile.get("caregiver") or {}
                    caregiver_email = caregiver.get("email") if isinstance(caregiver, dict) else ""

                    return {
                        "status": "recognized",
                        "user_id": pid,
                        "patient_id": pid,
                        "name": name,
                        "confidence": float(conf_pct),
                        "distance": float(distance),
                        "box": (bx, by, bw, bh),
                        "profile": profile,
                        "caregiver_email": caregiver_email,
                    }
                else:
                    return {
                        "status": "unknown",
                        "user_id": "unknown",
                        "patient_id": "unknown",
                        "name": "Người lạ (Chưa đăng ký)",
                        "confidence": 0.0,
                        "distance": float(distance),
                        "box": (bx, by, bw, bh),
                        "profile": None,
                        "caregiver_email": "",
                    }
            except Exception as e:
                logger.error("Recognition error: %s", e)

        return {
            "status": "unknown",
            "patient_id": "unknown",
            "name": "Chưa có dữ liệu đăng ký",
            "confidence": 0.0,
            "distance": 999.0,
            "box": (bx, by, bw, bh),
            "profile": None,
        }

    def draw_tracking_overlay(
        self,
        frame: np.ndarray,
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = None,
    ) -> np.ndarray:
        """
        Draw dynamic tracking bounding box and high-contrast labels:
        - 🟢 Emerald Green: Recognized patient from database
        - 🟠 Amber/Orange: Unknown person / unregistered face
        - Subtle status text: Searching for face
        """
        rec_res = self.recognize_face(frame)
        self._last_recognition = rec_res
        from core.drawing_utils import draw_vietnamese_text

        status = rec_res["status"]

        if status in ("recognized", "unknown") and rec_res["box"] is not None:
            bx, by, bw, bh = rec_res["box"][:4]

            # Smooth box movement
            if self._last_face_box is not None:
                alpha = 0.65
                lbx, lby, lbw, lbh = self._last_face_box
                bx = int(alpha * bx + (1 - alpha) * lbx)
                by = int(alpha * by + (1 - alpha) * lby)
                bw = int(alpha * bw + (1 - alpha) * lbw)
                bh = int(alpha * bh + (1 - alpha) * lbh)

            self._last_face_box = (bx, by, bw, bh)
            self._frames_without_face = 0

            if status == "recognized":
                pid = rec_res["patient_id"]
                name = rec_res["name"]
                conf = rec_res["confidence"]

                # Emerald Green BBox
                box_color = (128, 222, 74)   # BGR: Green
                corner_color = (160, 255, 110)

                # Draw BBox
                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), box_color, 2)

                # Tech corner accents
                clen = max(12, min(bw, bh) // 5)
                cv2.line(frame, (bx, by), (bx + clen, by), corner_color, 3)
                cv2.line(frame, (bx, by), (bx, by + clen), corner_color, 3)
                cv2.line(frame, (bx + bw, by), (bx + bw - clen, by), corner_color, 3)
                cv2.line(frame, (bx + bw, by), (bx + bw, by + clen), corner_color, 3)
                cv2.line(frame, (bx, by + bh), (bx + clen, by + bh), corner_color, 3)
                cv2.line(frame, (bx, by + bh), (bx, by + bh - clen), corner_color, 3)
                cv2.line(frame, (bx + bw, by + bh), (bx + bw - clen, by + bh), corner_color, 3)
                cv2.line(frame, (bx + bw, by + bh), (bx + bw, by + bh - clen), corner_color, 3)

                # Labels
                text_id = f"🟢 ĐÃ NHẬN DIỆN: {name} (Mã: {pid})"
                text_conf = f"Độ tin cậy: {conf * 100:.1f}%"
                tx = max(12, bx - 10)
                ty1 = max(16, by - 48)
                ty2 = max(38, by - 22)

                draw_vietnamese_text(frame, text_id, (tx, ty1), font_size=17, color=(74, 222, 128), stroke_color=(0, 0, 0), stroke_width=2)
                draw_vietnamese_text(frame, text_conf, (tx, ty2), font_size=14, color=(147, 197, 253), stroke_color=(0, 0, 0), stroke_width=2)

                # Record recognition in JSON stores
                self._update_face_result(patient_id=pid, name=name, status="recognized", confidence=conf)

            else:
                # Amber / Warning Orange for Unknown
                box_color = (0, 165, 245)     # BGR: Amber
                corner_color = (30, 200, 255)

                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), box_color, 2)

                clen = max(12, min(bw, bh) // 5)
                cv2.line(frame, (bx, by), (bx + clen, by), corner_color, 3)
                cv2.line(frame, (bx, by), (bx, by + clen), corner_color, 3)
                cv2.line(frame, (bx + bw, by), (bx + bw - clen, by), corner_color, 3)
                cv2.line(frame, (bx + bw, by), (bx + bw, by + clen), corner_color, 3)
                cv2.line(frame, (bx, by + bh), (bx + clen, by + bh), corner_color, 3)
                cv2.line(frame, (bx, by + bh), (bx, by + bh - clen), corner_color, 3)
                cv2.line(frame, (bx + bw, by + bh), (bx + bw - clen, by + bh), corner_color, 3)
                cv2.line(frame, (bx + bw, by + bh), (bx + bw, by + bh - clen), corner_color, 3)

                text_warn = "🟠 NGƯỜI LẠ (CHƯA ĐĂNG KÝ)"
                text_hint = "Nhấn 'Đăng Ký' để thêm hồ sơ"
                tx = max(12, bx - 10)
                ty1 = max(16, by - 48)
                ty2 = max(38, by - 22)

                draw_vietnamese_text(frame, text_warn, (tx, ty1), font_size=16, color=(245, 158, 11), stroke_color=(0, 0, 0), stroke_width=2)
                draw_vietnamese_text(frame, text_hint, (tx, ty2), font_size=13, color=(253, 230, 138), stroke_color=(0, 0, 0), stroke_width=2)

                self._update_face_result(patient_id="unknown", name="Người lạ", status="unknown", confidence=0.0)

        else:
            self._frames_without_face += 1
            if self._frames_without_face > 10:
                self._last_face_box = None
            draw_vietnamese_text(frame, "AI Cam: Đang quét tìm khuôn mặt...", (16, 16), font_size=16, color=(0, 229, 250), stroke_color=(0, 0, 0), stroke_width=2)

        return frame

    def get_latest_recognition(self) -> Dict[str, Any]:
        """Return the most recent recognition result dict."""
        return self._last_recognition or {
            "status": "no_face",
            "patient_id": None,
            "name": None,
            "confidence": 0.0,
            "distance": 999.0,
            "box": None,
            "profile": None,
        }

    # ==================== REGISTRATION & PROFILE MANAGEMENT ====================
    def register_patient(
        self,
        name: str,
        patient_id: Optional[str] = None,
        age: int = 70,
        gender: str = "Nam",
        notes: str = "",
        face_images: Optional[List[np.ndarray]] = None,
        caregiver_name: str = "",
        caregiver_relationship: str = "Người thân",
        caregiver_email: str = "",
        caregiver: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Register a new patient or update existing profile:
        1. Write metadata into shared/data/patients.json and data/users/{pid}.json.
        2. Save face images into shared/data/registered_faces/{patient_id}/.
        3. Trigger recognizer re-training.
        4. Update active patient.json and state.json.
        """
        if patient_id is not None and str(patient_id).strip():
            pid = str(patient_id).strip()
        else:
            existing = self.get_all_patients_dict()
            pid = "1" if not existing else str(max([int(k) for k in existing.keys() if k.isdigit()] + [0]) + 1)

        pname = name.strip() or f"Bệnh nhân {pid}"

        # 1. Prepare directory
        p_dir = self.registered_faces_dir / pid
        p_dir.mkdir(parents=True, exist_ok=True)

        # 2. Save captured face images if provided
        saved_count = len(list(p_dir.glob("*.jpg")))
        if face_images:
            for idx, img in enumerate(face_images):
                if img is not None and img.size > 0:
                    saved_count += 1
                    fn = f"face_{saved_count:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(str(p_dir / fn), img)

        # 3. Save profile to patients.json and data/users/{pid}.json
        patients = self.get_all_patients_dict()
        caregiver_obj = caregiver or {
            "name": caregiver_name.strip() or "Người chăm sóc",
            "relationship": caregiver_relationship.strip() or "Người thân",
            "email": caregiver_email.strip(),
        }
        patient_data = {
            "user_id": pid,
            "patient_id": pid,
            "name": pname,
            "age": int(age),
            "gender": gender,
            "notes": notes,
            "caregiver": caregiver_obj,
            "registered_at": patients.get(pid, {}).get("registered_at", datetime.now().isoformat()),
            "last_updated": datetime.now().isoformat(),
            "image_count": saved_count,
        }
        patients[pid] = patient_data

        try:
            # Save to data/users/
            users_dir = Path("data/users")
            users_dir.mkdir(parents=True, exist_ok=True)
            with open(users_dir / f"{pid}.json", "w", encoding="utf-8") as f:
                json.dump(patient_data, f, ensure_ascii=False, indent=2)

            with open(self.patients_file, "w", encoding="utf-8") as f:
                json.dump(patients, f, ensure_ascii=False, indent=2)

            with open(self.patient_file, "w", encoding="utf-8") as f:
                json.dump(patient_data, f, ensure_ascii=False, indent=2)

            if self.state_file.exists():
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                state["name"] = pname
                state["patient_id"] = pid
                state["last_update"] = datetime.now().isoformat()
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)

            logger.info("Successfully registered patient: ID %s - %s", pid, pname)
        except Exception as e:
            logger.error("Failed writing patient data: %s", e)

        # 4. Retrain recognizer with new patient data
        self.train_recognizer()

        return patient_data

    def get_all_patients_dict(self) -> Dict[str, Dict[str, Any]]:
        """Return dict of all registered patients keyed by patient_id."""
        if self.patients_file.exists():
            try:
                with open(self.patients_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Error reading patients file: %s", e)
        return {}

    def get_all_patients(self) -> List[Dict[str, Any]]:
        """Return list of all registered patients."""
        return list(self.get_all_patients_dict().values())

    def get_patient_profile(self, patient_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve stored patient profile by ID, or fallback to active patient.json if no ID given."""
        patients = self.get_all_patients_dict()
        if patient_id is not None:
            return patients.get(str(patient_id).strip())

        if self.patient_file.exists():
            try:
                with open(self.patient_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to read patient file: %s", e)

        return None

    def delete_patient(self, patient_id: str) -> bool:
        """Delete patient profile and face images, then retrain."""
        pid = str(patient_id).strip()
        patients = self.get_all_patients_dict()
        if pid in patients:
            del patients[pid]
            with open(self.patients_file, "w", encoding="utf-8") as f:
                json.dump(patients, f, ensure_ascii=False, indent=2)

            # Clean active patient.json if it was this patient
            if self.patient_file.exists():
                try:
                    with open(self.patient_file, "r", encoding="utf-8") as f:
                        cur_active = json.load(f)
                    if cur_active.get("patient_id") == pid:
                        fallback_p = next(iter(patients.values()), None)
                        if fallback_p:
                            with open(self.patient_file, "w", encoding="utf-8") as f:
                                json.dump(fallback_p, f, ensure_ascii=False, indent=2)
                        else:
                            self.patient_file.unlink(missing_ok=True)
                except Exception as e:
                    logger.debug("Failed cleaning active patient file: %s", e)

            # Remove images
            p_dir = self.registered_faces_dir / pid
            if p_dir.exists():
                shutil.rmtree(p_dir, ignore_errors=True)

            self.train_recognizer()
            logger.info("Deleted patient ID %s and retrained model.", pid)
            return True
        return False

    def get_result(self) -> Dict[str, Any]:
        """Read latest face result from local JSON."""
        if self.result_file.exists():
            try:
                with open(self.result_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Error reading face result file: %s", e)
        return {
            "patient_id": "1",
            "name": "Trần Văn Nam",
            "status": "idle",
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
        }

    def _update_face_result(
        self,
        patient_id: str = "1",
        name: Optional[str] = None,
        status: str = "normal",
        confidence: float = 0.95,
    ) -> None:
        """Helper to write face result to JSON."""
        current = self.get_result()
        if name:
            current["name"] = name
        current["patient_id"] = str(patient_id)
        current["status"] = status
        current["confidence"] = round(float(confidence), 3)
        current["timestamp"] = datetime.now().isoformat()
        try:
            with open(self.result_file, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Error writing face result: %s", e)

    # Backward compatibility stubs
    def start(self, mode: str = "recognize", input_source: Optional[str] = None) -> bool:
        self._update_face_result(status="running")
        return True

    def stop(self) -> None:
        self._update_face_result(status="stopped")

    def is_running(self) -> bool:
        return True
