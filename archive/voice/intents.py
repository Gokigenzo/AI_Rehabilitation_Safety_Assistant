"""
Intent Classification Module for AI Rehabilitation Assistant Voice Subsystem.
Focuses on a small, reliable, and deterministic set of rehabilitation commands.
"""

from __future__ import annotations

import re
from typing import Dict, List

# Reliable Rehabilitation Commands
REHAB_INTENTS: Dict[str, List[str]] = {
    "START_ARM_RAISE": [
        "bắt đầu bài tập nâng tay",
        "tập nâng tay",
        "bài tập nâng tay",
        "nâng tay qua đầu",
        "vươn vai",
        "nâng tay",
        "start arm raise",
        "arm raise",
    ],
    "START_SIT_TO_STAND": [
        "bắt đầu bài tập đứng lên ngồi xuống",
        "đứng lên ngồi xuống",
        "bài tập đứng lên ngồi xuống",
        "tập đứng lên ngồi xuống",
        "tập đứng ngồi",
        "đứng ngồi",
        "co duỗi chân",
        "tập chân",
        "start sit to stand",
        "sit to stand",
    ],
    "START_MARCHING": [
        "bắt đầu bài tập đi bộ",
        "bài tập đi bộ tại chỗ",
        "bài tập đi bộ",
        "đi bộ tại chỗ",
        "nâng cao đùi",
        "tập đi bộ",
        "start marching",
        "marching",
    ],
    "STOP_REHAB": [
        "dừng bài tập",
        "dừng tập",
        "kết thúc bài tập",
        "kết thúc tập",
        "dừng lại",
        "nghỉ tập",
        "thôi tập",
        "stop exercise",
        "stop rehab",
        "stop",
    ],
    "SHOW_RESULT": [
        "kết quả của tôi",
        "xem kết quả",
        "kết quả tập luyện",
        "điểm của tôi",
        "xem điểm",
        "báo cáo",
        "my result",
        "show result",
        "results",
    ],
    "GREETING": [
        "xin chào",
        "chào trợ lý",
        "chào bác sĩ",
        "hello",
        "hi assistant",
    ],
    "HELP": [
        "hướng dẫn",
        "trợ giúp",
        "giúp đỡ",
        "tôi phải làm gì",
        "help",
    ],
}


def normalize_text(text: str) -> str:
    """Normalize text for reliable matching."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u00C0-\u1EF9]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_intent(transcript: str) -> str:
    """
    Deterministic rule-based intent classifier.
    Returns: 'START_ARM_RAISE', 'START_SIT_TO_STAND', 'START_MARCHING',
             'STOP_REHAB', 'SHOW_RESULT', 'GREETING', 'HELP', or 'UNKNOWN'
    """
    norm = normalize_text(transcript)
    if not norm:
        return "UNKNOWN"

    # 1. Exact match check
    for intent, phrases in REHAB_INTENTS.items():
        for phrase in phrases:
            if norm == normalize_text(phrase):
                return intent

    # 2. Substring match check
    for intent, phrases in REHAB_INTENTS.items():
        for phrase in phrases:
            clean_phrase = normalize_text(phrase)
            if clean_phrase in norm:
                return intent

    # 3. Keyword heuristic check
    if "nâng tay" in norm or "vươn vai" in norm:
        return "START_ARM_RAISE"
    if "đứng lên" in norm or "ngồi xuống" in norm:
        return "START_SIT_TO_STAND"
    if "đi bộ" in norm or "nâng cao đùi" in norm:
        return "START_MARCHING"
    if "dừng" in norm or "kết thúc" in norm:
        return "STOP_REHAB"
    if "kết quả" in norm or "điểm" in norm:
        return "SHOW_RESULT"

    return "UNKNOWN"
