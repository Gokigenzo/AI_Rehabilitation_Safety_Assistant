"""
Adapters package for AI Rehabilitation & Safety Assistant.
Provides thin, robust wrappers for the 4 core subsystems:
1. face_adapter (Personalization & Identity)
2. emotion_adapter (Contextual psychological state)
3. rehabilitation_adapter (Exercise kinematics & scoring)
4. fall_adapter (Real-time posture kinematics & safety monitoring)
"""

from .face_adapter import FaceAdapter
from .emotion_adapter import EmotionAdapter
from .rehabilitation_adapter import RehabilitationAdapter
from .fall_adapter import FallAdapter

__all__ = [
    "FaceAdapter",
    "EmotionAdapter",
    "RehabilitationAdapter",
    "FallAdapter",
]
