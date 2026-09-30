"""
Voice Assistant Module Adapter for AI Rehabilitation Assistant.
Provides deterministic speech command processing, intent mapping for rehabilitation,
and natural voice audio feedback.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from config import (
    MODULES_DIR,
    SHARED_RESULTS_DIR,
    SHARED_DIR,
)
from modules.voice.intents import classify_intent

logger = logging.getLogger("VoiceAdapter")

VOICE_RESPONSES = {
    "START_ARM_RAISE": "Dạ, bắt đầu bài tập nâng tay qua đầu. Bác hãy thả lỏng và nâng hai tay từ từ lên nhé.",
    "START_SIT_TO_STAND": "Dạ, bắt đầu bài tập đứng lên ngồi xuống. Bác hãy giữ thẳng lưng và đứng dậy chậm rãi nhé.",
    "START_MARCHING": "Dạ, bắt đầu bài tập đi bộ tại chỗ. Bác hãy nâng cao đùi nhịp nhàng từng chân nhé.",
    "STOP_REHAB": "Dạ, em đã dừng bài tập rồi. Bác hãy ngồi nghỉ ngơi một chút và xem kết quả tập luyện nhé.",
    "SHOW_RESULT": "Hôm nay bác tập luyện rất chăm chỉ và đạt kết quả rất tốt ạ!",
    "GREETING": "Kính chào bác! Em là trợ lý phục hồi chức năng thông minh. Chúc bác có một buổi tập thật nhiều năng lượng!",
    "HELP": "Dạ bác có thể nói: Bắt đầu bài tập nâng tay, hoặc Đứng lên ngồi xuống, hoặc Dừng bài tập nhé.",
    "UNKNOWN": "Dạ em chưa nghe rõ. Bác có thể nói ví dụ: Bắt đầu bài tập nâng tay, hoặc Dừng tập nhé.",
}


class VoiceAdapter:
    """Stable In-Memory Voice Adapter for Rehabilitation Interaction."""

    def __init__(self, enable_tts: bool = True) -> None:
        self.result_file: Path = SHARED_RESULTS_DIR / "voice.json"
        self.state_file: Path = SHARED_DIR / "state.json"
        self.enable_tts = enable_tts and (os.getenv("AI_CARE_DISABLE_TTS", "0") != "1")
        self.command_callback: Optional[Callable[[str, str], None]] = None
        self._tts_lock = threading.Lock()
        self._active_proc: Optional[subprocess.Popen] = None

    def set_command_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback for voice commands (callback(intent, response_text))."""
        self.command_callback = callback

    def process_command(self, transcript: str) -> Dict[str, Any]:
        """
        Classify intent, determine response, trigger callback, and persist result.
        """
        text = transcript.strip()
        intent = classify_intent(text)
        response_text = VOICE_RESPONSES.get(intent, VOICE_RESPONSES["UNKNOWN"])

        payload = {
            "last_command": text,
            "intent": intent,
            "response": response_text,
            "confidence": 0.95 if intent != "UNKNOWN" else 0.50,
            "timestamp": datetime.now().isoformat(),
        }

        # Save result to local JSON
        try:
            with open(self.result_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            if self.state_file.exists():
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                state["last_voice_command"] = f"{text} -> {intent}"
                state["last_update"] = datetime.now().isoformat()
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug("Error writing voice JSON: %s", e)

        # Trigger registered application callback
        if self.command_callback:
            try:
                self.command_callback(intent, response_text)
            except Exception as e:
                logger.error("Error executing voice command callback: %s", e)

        # Speak response aloud in background thread
        if self.enable_tts:
            self.speak(response_text)

        logger.info("Voice command: '%s' -> %s", text, intent)
        return payload

    def speak(self, text: str) -> None:
        """
        Speak response text non-blockingly via an isolated child subprocess.
        Configures authentic Vietnamese voice (aav/vi) at a calm, elderly-friendly pace.
        Prevents espeak C/ctypes weakref memory deallocation and segfaults on Linux.
        """
        if not self.enable_tts or os.getenv("AI_CARE_DISABLE_TTS", "0") == "1":
            return

        clean_text = text.strip()
        if not clean_text:
            return

        def _worker():
            with self._tts_lock:
                if self._active_proc is not None:
                    try:
                        if self._active_proc.poll() is None:
                            self._active_proc.terminate()
                            self._active_proc.wait(timeout=0.2)
                    except Exception:
                        pass
                    self._active_proc = None

                try:
                    cmd = [
                        sys.executable,
                        "-c",
                        "import sys, pyttsx3\n"
                        "try:\n"
                        "    engine = pyttsx3.init()\n"
                        "    for v in engine.getProperty('voices'):\n"
                        "        if 'vi' in getattr(v, 'languages', []) or 'vi' in v.id.lower():\n"
                        "            engine.setProperty('voice', v.id)\n"
                        "            break\n"
                        "    engine.setProperty('rate', 135)\n"
                        "    engine.setProperty('volume', 1.0)\n"
                        "    engine.say(sys.argv[1])\n"
                        "    engine.runAndWait()\n"
                        "except Exception:\n"
                        "    pass\n",
                        clean_text,
                    ]
                    self._active_proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception as e:
                    logger.debug("TTS subprocess spawn error: %s", e)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def get_result(self) -> Dict[str, Any]:
        """Get latest voice interaction result from local JSON."""
        if self.result_file.exists():
            try:
                with open(self.result_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "last_command": "",
            "intent": "idle",
            "response": "",
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
        }

    # Backward compatibility stubs
    def start(self, mode: str = "runner") -> bool:
        return True

    def stop(self) -> None:
        pass

    def is_running(self) -> bool:
        return True
