"""
Emotion Module Adapter for AI Rehabilitation Assistant.
Focuses strictly on 3 core emotional states:
1. Bình thường (Neutral / Relaxed resting state)
2. Vui vẻ (Happy / Smile - AU12 Zygomaticus Major)
3. Buồn bã (Sad / Frown - AU15 Depressor Anguli Oris & AU1/4)

Integrates MediaPipe FaceMesh biometric FACS kinematics, PyTorch ExpressionNet,
temporal smoothing across a sliding window, and crisp Vietnamese HUD rendering.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# Set writable matplotlib config dir
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

from config import (
    MODULES_DIR,
    SHARED_RESULTS_DIR,
    SHARED_DIR,
)
from core.drawing_utils import draw_pill_badge

# Ensure modules/emotion is on sys.path for internal 'src' imports
EMOTION_ROOT = str(MODULES_DIR / "emotion")
if EMOTION_ROOT not in sys.path:
    sys.path.insert(0, EMOTION_ROOT)

logger = logging.getLogger("EmotionAdapter")

# 3 Focused Emotion States
EMOTION_CLASSES = ["Neutral", "Happy", "Sad"]

EMOTION_VI_MAP = {
    "Neutral": "Bình thường",
    "neutral": "Bình thường",
    "Happy": "Vui vẻ",
    "happy": "Vui vẻ",
    "Sad": "Buồn bã",
    "sad": "Buồn bã",
}


class EmotionAdapter:
    """Stable In-Memory 3-State Emotion Classifier with Biomechanical FACS & Smoothing."""

    def __init__(self, smoothing_window: int = 10) -> None:
        self.emotion_dir: Path = MODULES_DIR / "emotion"
        self.result_file: Path = SHARED_RESULTS_DIR / "emotion.json"
        self.state_file: Path = SHARED_DIR / "state.json"
        self.smoothing_window = smoothing_window
        self.classes = EMOTION_CLASSES

        # Temporal smoothing circular buffer for probabilities [Neutral, Happy, Sad]
        self._prob_history: deque[np.ndarray] = deque(maxlen=smoothing_window)
        self._last_emotion = "Bình thường"
        self._last_confidence = 0.92
        self._model = None
        self._face_mesh = None

        self._init_model()

    def _init_model(self) -> None:
        """Load ExpressionNet PyTorch model and MediaPipe FaceMesh."""
        try:
            import mediapipe as mp
            import torch
            from modules.emotion.main import load_model
            from modules.emotion.src.config import PATHS

            if PATHS.model_path.exists():
                self._model = load_model(PATHS.model_path)
                if self._model is not None:
                    self._model.eval()
                    logger.info("Loaded ExpressionNet PyTorch model successfully.")

            mp_face_mesh = mp.solutions.face_mesh
            self._face_mesh = mp_face_mesh.FaceMesh(
                refine_landmarks=True,
                max_num_faces=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("Initialized MediaPipe FaceMesh for emotion recognition.")
        except Exception as e:
            logger.warning("Could not initialize full Emotion Neural Net: %s", e)

    def _compute_facs_probabilities(self, landmarks: Any) -> np.ndarray:
        """
        Extract Facial Action Coding System (FACS) action units from MediaPipe FaceMesh:
        - AU12: Zygomaticus Major (Lip corner puller -> Happy/Smile)
        - AU15: Depressor Anguli Oris (Lip corner depressor -> Sad/Frown)
        - AU1 + AU4: Corrugator & Frontalis (Inner eyebrow contraction -> Sad)
        - Resting Equilibrium -> Neutral
        """
        # Landmark indices:
        # 33: Left outer eye, 263: Right outer eye
        # 61: Left mouth corner, 291: Right mouth corner
        # 13, 14: Upper & lower inner lip center (stomion)
        # 107: Left inner brow, 336: Right inner brow

        coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark], dtype=np.float32)

        # Scale-invariant normalization factor (distance between outer eye corners)
        p33 = coords[33, :2]
        p263 = coords[263, :2]
        eye_dist = float(np.linalg.norm(p263 - p33))
        if eye_dist < 1e-4:
            return np.array([0.90, 0.05, 0.05], dtype=np.float32)

        # Mouth geometry
        p61 = coords[61, :2]
        p291 = coords[291, :2]
        p13 = coords[13, :2]
        p14 = coords[14, :2]

        mouth_w = float(np.linalg.norm(p291 - p61)) / eye_dist
        lip_center_y = (p13[1] + p14[1]) / 2.0
        corners_y = (p61[1] + p291[1]) / 2.0

        # In image coordinates, y points DOWNWARDS.
        # When smiling, corners move UPWARDS -> corners_y decreases -> (lip_center_y - corners_y) > 0
        corner_elevation = (lip_center_y - corners_y) / eye_dist

        # Eyebrows geometry
        p107 = coords[107, :2]
        p336 = coords[336, :2]
        brow_inner_dist = float(np.linalg.norm(p336 - p107)) / eye_dist

        # 1. Happy score (AU12: Lip Corner Elevation + Mouth Width expansion)
        s_happy = 0.0
        if corner_elevation > 0.012:
            s_happy += (corner_elevation - 0.012) * 40.0
        if mouth_w > 0.49:
            s_happy += (mouth_w - 0.49) * 12.0

        # 2. Sad score (AU15: Lip Corner Depressor + Medial Brow Contraction)
        s_sad = 0.0
        if corner_elevation < -0.010:
            s_sad += (-0.010 - corner_elevation) * 45.0
        if brow_inner_dist < 0.27:
            s_sad += (0.27 - brow_inner_dist) * 10.0

        # Logit computation with strong baseline prior for resting Neutral state
        l_happy = s_happy * 3.6 - 1.2
        l_sad = s_sad * 3.6 - 1.2
        l_neutral = 2.0 - 1.6 * (s_happy + s_sad)

        logits = np.array([l_neutral, l_happy, l_sad], dtype=np.float32)
        exp_l = np.exp(logits - np.max(logits))
        facs_probs = exp_l / np.sum(exp_l)
        return facs_probs

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Extract face landmarks, evaluate 3-state emotion probabilities, apply temporal
        smoothing, and return the filtered dominant emotion.
        """
        import torch
        from modules.emotion.utils.preprocess import normalize_face_landmarks

        dominant_en = "Neutral"
        dominant_vi = "Bình thường"
        confidence = 0.92
        probs_dict = {"Neutral": 0.92, "Happy": 0.04, "Sad": 0.04}

        if self._face_mesh is not None:
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self._face_mesh.process(rgb)
                face_landmarks = results.multi_face_landmarks[0] if results.multi_face_landmarks else None

                if face_landmarks is not None:
                    # 1. Compute Biomechanical FACS probabilities [Neutral, Happy, Sad]
                    facs_probs = self._compute_facs_probabilities(face_landmarks)

                    # 2. Blend with Neural Network logits if available
                    if self._model is not None:
                        try:
                            features = normalize_face_landmarks(face_landmarks)
                            if features is not None:
                                input_tensor = torch.tensor([features], dtype=torch.float32)
                                with torch.no_grad():
                                    raw_logits = self._model(input_tensor).numpy()[0]
                                # Map 5-class model [Neutral(0), Happy(1), Sad(2), Angry(3), Surprised(4)] to 3 classes
                                subset_logits = raw_logits[:3]
                                exp_sub = np.exp(subset_logits - np.max(subset_logits))
                                nn_probs = exp_sub / np.sum(exp_sub)

                                # Weighted ensemble: 75% Biomechanical FACS + 25% Neural Net
                                combined_probs = 0.75 * facs_probs + 0.25 * nn_probs
                            else:
                                combined_probs = facs_probs
                        except Exception:
                            combined_probs = facs_probs
                    else:
                        combined_probs = facs_probs

                    # 3. Sliding window temporal smoothing
                    self._prob_history.append(combined_probs)
                    smoothed_probs = np.mean(np.stack(self._prob_history), axis=0)

                    pred_idx = int(np.argmax(smoothed_probs))
                    dominant_en = self.classes[pred_idx]
                    dominant_vi = EMOTION_VI_MAP.get(dominant_en, "Bình thường")
                    confidence = float(smoothed_probs[pred_idx])

                    probs_dict = {
                        cls_name: round(float(p), 3)
                        for cls_name, p in zip(self.classes, smoothed_probs)
                    }

                    self._last_emotion = dominant_vi
                    self._last_confidence = confidence
                else:
                    # Retain last stable emotion when face is momentarily obscured
                    dominant_vi = self._last_emotion
                    confidence = self._last_confidence
            except Exception as e:
                logger.debug("Emotion evaluation error: %s", e)
                dominant_vi = self._last_emotion
                confidence = self._last_confidence

        result = {
            "dominant_emotion": dominant_en,
            "emotion_vi": dominant_vi,
            "confidence": round(confidence, 3),
            "probabilities": probs_dict,
            "timestamp": datetime.now().isoformat(),
        }

        # Update local results and shared state
        self._persist_result(result)
        return result

    def draw_emotion_badge(self, frame: np.ndarray, emotion_vi: str, confidence: float) -> np.ndarray:
        """Render a clean high-contrast Vietnamese emotion pill badge at top right of video frame."""
        h, w = frame.shape[:2]
        badge_text = f"Tâm trạng: {emotion_vi} ({confidence * 100:.1f}%)"
        
        # Color accent based on emotion state
        if emotion_vi == "Vui vẻ":
            border_color = (0, 220, 100) # Green accent
            text_color = (100, 255, 150)
        elif emotion_vi == "Buồn bã":
            border_color = (180, 100, 255) # Purple/Pink accent
            text_color = (220, 160, 255)
        else: # Bình thường
            border_color = (0, 196, 214) # Cyan accent
            text_color = (0, 229, 250)

        draw_pill_badge(
            frame,
            badge_text,
            top_right=(w - 20, 18),
            bg_color=(18, 24, 36),
            border_color=border_color,
            text_color=text_color,
            font_size=16,
            padding_x=14,
            padding_y=7,
        )
        return frame

    def _persist_result(self, result: Dict[str, Any]) -> None:
        """Write emotion result to local JSON."""
        try:
            with open(self.result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            if self.state_file.exists():
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                state["current_emotion"] = result["emotion_vi"]
                state["emotion_confidence"] = result["confidence"]
                state["last_update"] = datetime.now().isoformat()
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug("Failed writing emotion result: %s", e)

    def record_emotion(self, emotion: str, confidence: float = 0.95) -> Dict[str, Any]:
        """Manually record or override emotion state."""
        dominant_en = emotion.capitalize()
        if dominant_en not in self.classes:
            dominant_en = "Neutral"
        dominant_vi = EMOTION_VI_MAP.get(dominant_en, emotion)
        result = {
            "dominant_emotion": dominant_en,
            "emotion_vi": dominant_vi,
            "confidence": round(float(confidence), 3),
            "probabilities": {c: (0.90 if c == dominant_en else 0.05) for c in self.classes},
            "timestamp": datetime.now().isoformat(),
        }
        self._last_emotion = dominant_vi
        self._last_confidence = confidence
        self._persist_result(result)
        return result

    def get_result(self) -> Dict[str, Any]:
        """Read latest emotion result from local JSON."""
        if self.result_file.exists():
            try:
                with open(self.result_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "dominant_emotion": "Neutral",
            "emotion_vi": "Bình thường",
            "confidence": 0.92,
            "probabilities": {"Neutral": 0.92, "Happy": 0.04, "Sad": 0.04},
            "timestamp": datetime.now().isoformat(),
        }

    # Backward compatibility stubs
    def start(self, use_yolo11: bool = False) -> bool:
        return True

    def stop(self) -> None:
        pass

    def is_running(self) -> bool:
        return True
