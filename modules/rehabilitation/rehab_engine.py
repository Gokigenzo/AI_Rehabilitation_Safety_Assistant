"""
Core Rehabilitation AI Engine for AI Rehabilitation Assistant.
Implements MediaPipe Pose landmark extraction, biomechanical angle calculations,
Finite State Machines (FSM) for repetition counting, form penalty scoring,
real-time HUD telemetry overlay rendering, and periodic TTS voice alerts.

Prioritized Exercises:
1. Arm Raise (Nâng tay qua đầu / Vươn vai)
2. Sit-to-Stand (Đứng lên ngồi xuống / Co duỗi chân)
3. Marching (Đi bộ tại chỗ / Nâng cao đùi)
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np

try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False

logger = logging.getLogger("RehabEngine")


def calculate_angle(a: Any, b: Any, c: Any) -> float:
    """
    Calculate planar angle at vertex b formed by points a, b, c in degrees.
    Points can be MediaPipe landmarks or objects with .x, .y attributes.
    """
    ax, ay = (a.x, a.y) if hasattr(a, "x") else (a[0], a[1])
    bx, by = (b.x, b.y) if hasattr(b, "x") else (b[0], b[1])
    cx, cy = (c.x, c.y) if hasattr(c, "x") else (c[0], c[1])

    radians = math.atan2(cy - by, cx - bx) - math.atan2(ay - by, ax - bx)
    angle = math.degrees(abs(radians))
    if angle > 180.0:
        angle = 360.0 - angle
    return float(angle)


@dataclass
class ExerciseMetrics:
    exercise_id: str
    exercise_name: str
    target_reps: int
    repetitions: int
    correct_reps: int
    incorrect_reps: int
    stage: str
    score: float
    feedback: str
    fps: float


class BaseExerciseTracker:
    """Base class for exercise movement state machines."""

    def __init__(self, target_reps: int = 10) -> None:
        self.target_reps = target_reps
        self.reps = 0
        self.correct_reps = 0
        self.incorrect_reps = 0
        self.stage = "idle"
        self.feedback = "Chuẩn bị vào tư thế"
        self.form_scores: List[float] = []
        self.rep_penalties = 0.0
        self.rep_issues: List[str] = []

    def process(self, lm: Any, w: int, h: int) -> Tuple[str, str, float]:
        raise NotImplementedError


class ArmRaiseTracker(BaseExerciseTracker):
    """
    Arm Raise (Vươn vai / Nâng tay qua đầu) FSM Tracker.
    Stages: down -> raising -> hold_peak -> lowering -> down
    Form Checks:
      - Elevation angle: shoulder angle >= 142 deg at peak
      - Elbow straightness: elbow angle >= 130 deg
      - Bilateral symmetry: left vs right shoulder angle diff <= 25 deg
      - Peak hold duration: >= 0.4 seconds
    """

    def __init__(self, target_reps: int = 10) -> None:
        super().__init__(target_reps=target_reps)
        self.exercise_name = "Nâng tay qua đầu (Arm Raise)"
        self.stage = "down"
        self._hold_start = 0.0

    def process(self, lm: Any, w: int, h: int) -> Tuple[str, str, float]:
        # Indices: Left shoulder=11, Right shoulder=12, Left elbow=13, Right elbow=14,
        # Left wrist=15, Right wrist=16, Left hip=23, Right hip=24
        try:
            ls, rs = lm[11], lm[12]
            le, re = lm[13], lm[14]
            lw, rw = lm[15], lm[16]
            lh, rh = lm[23], lm[24]
        except Exception:
            return self.stage, "Không thấy đầy đủ khớp tay", 100.0

        left_sh_ang = calculate_angle(lh, ls, lw)
        right_sh_ang = calculate_angle(rh, rs, rw)
        left_el_ang = calculate_angle(ls, le, lw)
        right_el_ang = calculate_angle(rs, re, rw)

        sh_ang = (left_sh_ang + right_sh_ang) / 2.0
        symmetry_diff = abs(left_sh_ang - right_sh_ang)
        now = time.time()

        if self.stage == "down":
            if sh_ang > 60:
                self.stage = "raising"
                self.rep_penalties = 0.0
                self.rep_issues = []
                self.feedback = "Đang nâng tay lên..."

        elif self.stage == "raising":
            if left_el_ang < 130 or right_el_ang < 130:
                self.rep_penalties += 5.0
                if "Duỗi thẳng khuỷu tay" not in self.rep_issues:
                    self.rep_issues.append("Duỗi thẳng khuỷu tay")
                self.feedback = "Hãy duỗi thẳng khuỷu tay hơn"

            if symmetry_diff > 25:
                self.rep_penalties += 5.0
                if "Nâng đều 2 tay" not in self.rep_issues:
                    self.rep_issues.append("Nâng đều 2 tay")

            if sh_ang >= 142:
                self.stage = "hold_peak"
                self._hold_start = now
                self.feedback = "Giữ nguyên 1 nhịp trên cao..."

        elif self.stage == "hold_peak":
            hold_time = now - self._hold_start
            if sh_ang < 130:
                if hold_time < 0.35:
                    self.rep_penalties += 10.0
                    self.rep_issues.append("Chưa giữ đủ nhịp")
                self.stage = "lowering"
                self.feedback = "Hạ tay xuống chậm rãi..."
            elif hold_time >= 0.5:
                self.feedback = "Rất tốt! Hạ tay xuống đều"

        elif self.stage == "lowering":
            if sh_ang <= 50:
                self.stage = "down"
                self.reps += 1
                rep_score = max(50.0, 100.0 - self.rep_penalties)
                self.form_scores.append(rep_score)

                if self.rep_penalties < 15.0:
                    self.correct_reps += 1
                    self.feedback = f"Đúng tư thế! (Lần {self.reps})"
                else:
                    self.incorrect_reps += 1
                    issue_msg = ", ".join(self.rep_issues[:1]) or "Biên độ chưa chuẩn"
                    self.feedback = f"Lần {self.reps}: {issue_msg}"

        avg_score = float(np.mean(self.form_scores)) if self.form_scores else 100.0
        return self.stage, self.feedback, round(avg_score, 1)


class SitToStandTracker(BaseExerciseTracker):
    """
    Sit-to-Stand (Co duỗi chân / Đứng lên ngồi xuống) FSM Tracker.
    Stages: sitting -> ascending -> standing -> descending -> sitting
    Form Checks:
      - Knee extension: knee angle >= 162 deg at standing
      - Torso posture: torso angle >= 35 deg to prevent excessive forward lean
    """

    def __init__(self, target_reps: int = 10) -> None:
        super().__init__(target_reps=target_reps)
        self.exercise_name = "Đứng lên ngồi xuống (Sit-to-Stand)"
        self.stage = "sitting"

    def process(self, lm: Any, w: int, h: int) -> Tuple[str, str, float]:
        try:
            lh, rh = lm[23], lm[24]
            lk, rk = lm[25], lm[26]
            la, ra = lm[27], lm[28]
            ls, rs = lm[11], lm[12]
        except Exception:
            return self.stage, "Không thấy đầy đủ phần chân", 100.0

        left_knee = calculate_angle(lh, lk, la)
        right_knee = calculate_angle(rh, rk, ra)
        knee_angle = (left_knee + right_knee) / 2.0

        sh_mid = ((ls.x + rs.x) / 2.0, (ls.y + rs.y) / 2.0)
        hip_mid = ((lh.x + rh.x) / 2.0, (lh.y + rh.y) / 2.0)
        torso_angle = math.degrees(math.atan2(abs(sh_mid[0] - hip_mid[0]), max(1e-4, abs(hip_mid[1] - sh_mid[1]))))

        if self.stage == "sitting":
            if knee_angle > 115:
                self.stage = "ascending"
                self.rep_penalties = 0.0
                self.rep_issues = []
                self.feedback = "Đang đứng lên, giữ thẳng lưng..."

        elif self.stage == "ascending":
            if torso_angle > 45:
                self.rep_penalties += 5.0
                if "Lưng gập quá sâu" not in self.rep_issues:
                    self.rep_issues.append("Lưng gập quá sâu")
                self.feedback = "Giữ thẳng lưng hơn khi đứng dậy"

            if knee_angle >= 162:
                self.stage = "standing"
                self.feedback = "Tốt! Đứng thẳng hoàn toàn"

        elif self.stage == "standing":
            if knee_angle < 145:
                self.stage = "descending"
                self.feedback = "Hạ người ngồi xuống chậm rãi..."

        elif self.stage == "descending":
            if knee_angle <= 105:
                self.stage = "sitting"
                self.reps += 1
                rep_score = max(50.0, 100.0 - self.rep_penalties)
                self.form_scores.append(rep_score)

                if self.rep_penalties < 15.0:
                    self.correct_reps += 1
                    self.feedback = f"Đúng tư thế! (Lần {self.reps})"
                else:
                    self.incorrect_reps += 1
                    issue_msg = ", ".join(self.rep_issues[:1]) or "Cần đứng thẳng hơn"
                    if not self.rep_issues:
                        self.rep_issues.append("Đứng chưa thẳng")
                    self.feedback = f"Lần {self.reps}: {issue_msg}"

        avg_score = float(np.mean(self.form_scores)) if self.form_scores else 100.0
        return self.stage, self.feedback, round(avg_score, 1)


class MarchingTracker(BaseExerciseTracker):
    """
    Marching (Đi bộ tại chỗ / Nâng cao đùi) FSM Tracker.
    Stages: stance -> left_up / right_up -> stance
    Form Checks:
      - Elevation height: knee raised higher than hip threshold (diff < 0.18)
      - Alternating leg execution
    """

    def __init__(self, target_reps: int = 15) -> None:
        super().__init__(target_reps=target_reps)
        self.exercise_name = "Nâng cao đùi tại chỗ (Marching)"
        self.stage = "stance"
        self._last_foot = ""

    def process(self, lm: Any, w: int, h: int) -> Tuple[str, str, float]:
        try:
            lh, rh = lm[23], lm[24]
            lk, rk = lm[25], lm[26]
        except Exception:
            return self.stage, "Vui lòng lùi lại để thấy chân", 100.0

        hip_y = (lh.y + rh.y) / 2.0
        diff_y = rk.y - lk.y  # Positive if left knee is higher (lower y)

        if self.stage == "stance":
            if diff_y > 0.065 and self._last_foot != "left":
                self.stage = "left_up"
                self._last_foot = "left"
                self.reps += 1
                if lk.y < hip_y + 0.18:
                    self.correct_reps += 1
                    self.form_scores.append(100.0)
                    self.feedback = f"Đùi trái nâng tốt! (Bước {self.reps})"
                else:
                    self.incorrect_reps += 1
                    self.form_scores.append(80.0)
                    self.feedback = "Nâng đùi trái cao hơn một chút"
                    self.rep_issues.append("Nâng đầu gối cao hơn")

            elif diff_y < -0.065 and self._last_foot != "right":
                self.stage = "right_up"
                self._last_foot = "right"
                self.reps += 1
                if rk.y < hip_y + 0.18:
                    self.correct_reps += 1
                    self.form_scores.append(100.0)
                    self.feedback = f"Đùi phải nâng tốt! (Bước {self.reps})"
                else:
                    self.incorrect_reps += 1
                    self.form_scores.append(80.0)
                    self.feedback = "Nâng đùi phải cao hơn một chút"
                    self.rep_issues.append("Nâng đầu gối cao hơn")

        elif self.stage in ("left_up", "right_up"):
            if abs(diff_y) < 0.035:
                self.stage = "stance"

        avg_score = float(np.mean(self.form_scores)) if self.form_scores else 100.0
        return self.stage, self.feedback, round(avg_score, 1)


class RehabilitationEngine:
    """
    Main Rehabilitation Vision Engine.
    Executes MediaPipe Pose, routes to the active exercise tracker,
    renders HUD overlay, and computes live performance scores.
    """

    TRACKERS = {
        "sit_to_stand": SitToStandTracker,
        "arm_raise": ArmRaiseTracker,
        "marching": MarchingTracker,
    }

    def __init__(self, voice_feedback_fn: Optional[Callable[[str], None]] = None) -> None:
        self.voice_feedback_fn = voice_feedback_fn
        self._pose = None
        self._active_exercise_id = "arm_raise"
        self._tracker: BaseExerciseTracker = ArmRaiseTracker()
        self._last_spoken_rep = 0
        self._last_form_alert_time = time.time()
        self._last_process_time = time.time()
        self._fps = 30.0
        self._init_pose()

    def _init_pose(self) -> None:
        if MP_AVAILABLE:
            try:
                mp_pose = mp.solutions.pose
                self._pose = mp_pose.Pose(
                    model_complexity=0,
                    min_detection_confidence=0.55,
                    min_tracking_confidence=0.55,
                )
                logger.info("Initialized MediaPipe Pose in RehabilitationEngine.")
            except Exception as e:
                logger.warning("Failed to initialize MediaPipe Pose: %s", e)

    def select_exercise(self, exercise_id: str) -> None:
        """Switch active exercise and instantiate its state machine tracker."""
        if exercise_id in self.TRACKERS:
            self._active_exercise_id = exercise_id
            self._tracker = self.TRACKERS[exercise_id]()
            self._last_spoken_rep = 0
            self._last_form_alert_time = time.time()
            logger.info("RehabilitationEngine selected exercise: %s", exercise_id)

    def _get_rep_voice_prompt(self, reps: int, target: int, score: float) -> str:
        """Generate clear, polite, and encouraging Vietnamese repetition cues."""
        rep_cues = {
            1: "Một. Rất tốt ạ.",
            2: "Hai. Đúng tư thế rồi bác.",
            3: "Ba.",
            4: "Bốn. Động tác rất đều.",
            5: "Năm. Bác đã hoàn thành một nửa rồi nhé.",
            6: "Sáu.",
            7: "Bảy. Rất nhịp nhàng.",
            8: "Tám. Cố lên bác nhé.",
            9: "Chín. Một lần nữa thôi ạ.",
            10: "Mười. Chúc mừng bác đã hoàn thành bài tập xuất sắc!",
        }
        if reps in rep_cues:
            return rep_cues[reps]
        elif reps == target:
            return f"Lần thứ {reps}. Chúc mừng bác đã hoàn thành mục tiêu bài tập!"
        else:
            return f"Lần {reps}."

    def _get_form_correction_prompt(self, issue: str) -> Optional[str]:
        """Generate gentle, courteous Vietnamese form correction cues for older adults."""
        corrections = {
            "Duỗi thẳng khuỷu tay": "Bác chú ý duỗi thẳng khuỷu tay hơn nhé.",
            "Nâng đều 2 tay": "Bác hãy nâng đều hai tay qua vai nhé.",
            "Chưa giữ đủ nhịp": "Bác giữ tay trên cao một nhịp rồi hãy hạ xuống nhé.",
            "Lưng gập quá sâu": "Bác chú ý giữ thẳng lưng khi đứng lên nhé.",
            "Đứng chưa thẳng": "Bác hãy đứng thẳng người lên hoàn toàn nhé.",
            "Nâng đầu gối cao hơn": "Bác hãy nâng đầu gối cao hơn một chút nhé.",
        }
        return corrections.get(issue)

    def get_metrics(self) -> Dict[str, Any]:
        """Return snapshot of current exercise progress."""
        avg_score = float(np.mean(self._tracker.form_scores)) if self._tracker.form_scores else 100.0
        return {
            "exercise_id": self._active_exercise_id,
            "exercise_name": getattr(self._tracker, "exercise_name", self._active_exercise_id),
            "target_reps": self._tracker.target_reps,
            "repetitions": self._tracker.reps,
            "correct_reps": self._tracker.correct_reps,
            "incorrect_reps": self._tracker.incorrect_reps,
            "stage": self._tracker.stage,
            "score": round(avg_score, 1),
            "feedback": self._tracker.feedback,
            "fps": round(self._fps, 1),
        }

    def reset_session(self) -> None:
        """Reset counters for current exercise."""
        self.select_exercise(self._active_exercise_id)

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Process frame with Pose, evaluate exercise state machine, and render HUD.
        """
        t0 = time.time()
        dt = max(1e-4, t0 - self._last_process_time)
        self._fps = 0.9 * self._fps + 0.1 * (1.0 / dt)
        self._last_process_time = t0

        h, w = frame.shape[:2]
        annotated = frame.copy()

        stage = self._tracker.stage
        feedback = self._tracker.feedback
        score = float(np.mean(self._tracker.form_scores)) if self._tracker.form_scores else 100.0

        if self._pose is not None:
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self._pose.process(rgb)

                if results.pose_landmarks:
                    mp_drawing = mp.solutions.drawing_utils
                    mp_pose = mp.solutions.pose
                    mp_drawing.draw_landmarks(
                        annotated,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 220, 255), thickness=2, circle_radius=3),
                        mp_drawing.DrawingSpec(color=(220, 50, 120), thickness=2, circle_radius=2),
                    )

                    lm = results.pose_landmarks.landmark
                    stage, feedback, score = self._tracker.process(lm, w, h)
                else:
                    feedback = "Vui lòng đứng lùi lại để thấy toàn thân"
            except Exception as e:
                logger.debug("Pose estimation error: %s", e)

        # Intelligent Event-Driven Vietnamese Rehabilitation Voice Coach
        now = time.time()
        current_reps = self._tracker.reps

        if self.voice_feedback_fn:
            # Event 1: Completed a repetition -> speak clear, encouraging count in Vietnamese
            if current_reps > self._last_spoken_rep:
                self._last_spoken_rep = current_reps
                self._last_form_alert_time = now # prevent form alert collision
                rep_cue = self._get_rep_voice_prompt(current_reps, self._tracker.target_reps, score)
                self.voice_feedback_fn(rep_cue)

            # Event 2: Form correction during movement -> spoken gently with >= 7.0s cooldown
            elif (now - self._last_form_alert_time >= 7.0) and self._tracker.rep_issues:
                if self._tracker.stage not in ("down", "sitting", "stance", "idle", "ready"):
                    latest_issue = self._tracker.rep_issues[-1]
                    coach_prompt = self._get_form_correction_prompt(latest_issue)
                    if coach_prompt:
                        self.voice_feedback_fn(coach_prompt)
                        self._last_form_alert_time = now

        # Render HUD Overlay
        annotated = self._render_hud(annotated, stage, feedback, score)

        metrics = self.get_metrics()
        return annotated, metrics

    def _render_hud(self, frame: np.ndarray, stage: str, feedback: str, score: float) -> np.ndarray:
        """Render high-contrast biometric exercise HUD with crisp Vietnamese TrueType text."""
        from core.drawing_utils import draw_vietnamese_text

        h, w = frame.shape[:2]

        # Top banner overlay
        cv2.rectangle(frame, (12, 12), (390, 118), (15, 23, 42), -1)
        cv2.rectangle(frame, (12, 12), (390, 118), (59, 130, 246), 2)

        ex_name = getattr(self._tracker, "exercise_name", self._active_exercise_id)
        reps_str = f"Lần tập: {self._tracker.reps} / {self._tracker.target_reps}"
        score_str = f"Form: {score:.1f}%"

        # Friendly Vietnamese translation for movement stage
        stage_map = {
            "down": "Chuẩn bị (Down)",
            "raising": "Đang nâng tay (Raising)",
            "hold_peak": "Giữ đỉnh động tác (Peak)",
            "lowering": "Hạ tay xuống (Lowering)",
            "sitting": "Chuẩn bị ngồi (Sitting)",
            "standing_up": "Đang đứng lên (Standing)",
            "standing": "Đứng thẳng người (Upright)",
            "sitting_down": "Đang ngồi xuống (Sitting)",
            "stepping_left": "Nhấc chân trái (Left)",
            "stepping_right": "Nhấc chân phải (Right)",
            "ready": "Sẵn sàng (Ready)",
        }
        stage_vn = stage_map.get(stage.lower(), stage.upper())
        stage_str = f"Giai đoạn: {stage_vn}"

        # Render top card text
        draw_vietnamese_text(frame, ex_name, (22, 18), font_size=18, color=(255, 255, 255), stroke_color=(0, 0, 0), stroke_width=2)
        draw_vietnamese_text(frame, reps_str, (22, 48), font_size=17, color=(248, 189, 56), stroke_color=(0, 0, 0), stroke_width=2)
        draw_vietnamese_text(frame, score_str, (230, 48), font_size=17, color=(74, 222, 128), stroke_color=(0, 0, 0), stroke_width=2)
        draw_vietnamese_text(frame, stage_str, (22, 78), font_size=15, color=(203, 213, 225), stroke_color=(0, 0, 0), stroke_width=2)

        # Bottom Live Feedback Bar
        bar_y1 = h - 55
        cv2.rectangle(frame, (12, bar_y1), (w - 12, h - 12), (15, 23, 42), -1)
        cv2.rectangle(frame, (12, bar_y1), (w - 12, h - 12), (16, 185, 129), 2)

        icon_text = "HUẤN LUYỆN VIÊN:"
        draw_vietnamese_text(frame, icon_text, (24, h - 45), font_size=16, color=(251, 191, 36), stroke_color=(0, 0, 0), stroke_width=2)
        draw_vietnamese_text(frame, feedback, (200, h - 45), font_size=16, color=(255, 255, 255), stroke_color=(0, 0, 0), stroke_width=2)

        return frame

