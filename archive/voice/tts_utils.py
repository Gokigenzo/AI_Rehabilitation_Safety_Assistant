"""
Text-to-Speech Utility
----------------------
Provides crash-safe speak() function for verbal responses.
Uses isolated subprocess execution to prevent espeak / ctypes Segmentation faults on Linux.
"""

from __future__ import annotations

import os
import subprocess
import sys


def speak(text: str) -> None:
    """
    Speak text aloud safely in an isolated child process.
    Prevents espeak C/ctypes weakref deallocation and core dump.
    """
    if os.getenv("AI_CARE_DISABLE_TTS") == "1" or not text.strip():
        print(f"[Assistant speaking (simulated)]: {text}")
        return

    print(f"[Assistant speaking]: {text}")
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
            text.strip(),
        ]
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[TTS Error]: {e}")
