"""
Standalone Voice Subsystem CLI Runner for AI Rehabilitation Assistant.
Processes spoken or textual commands using deterministic rehabilitation intent matching.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from adapters.voice_adapter import VoiceAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Voice Command Runner")
    parser.add_argument(
        "--command",
        type=str,
        default="Bắt đầu bài tập nâng tay",
        help="Voice command phrase",
    )
    args = parser.parse_args()

    adapter = VoiceAdapter(enable_tts=False)
    res = adapter.process_command(args.command)
    print(f"Command : {args.command}")
    print(f"Intent  : {res['intent']}")
    print(f"Response: {res['response']}")


if __name__ == "__main__":
    main()
