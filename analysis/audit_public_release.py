#!/usr/bin/env python3
"""Fail if files unsafe for the public release enter the repository."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DISALLOWED_SUFFIXES = {
    ".mp4", ".mov", ".mkv", ".avi", ".wav", ".m4a", ".mp3", ".vtt", ".srt"
}
DISALLOWED_PATH_TERMS = {
    "transcript", "diarization", "face_track", "batch_outputs", "private", "raw"
}
SECRET_PATTERNS = {
    "OpenAI/OpenRouter-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[A-Za-z0-9_-]{30,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
}
SOURCE_VIDEO_ID = re.compile(r"\bS[1-4]-[12]\s+[AB][1-8]\b")


def main() -> None:
    problems = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT)
        lower = str(rel).lower()
        if path.suffix.lower() in DISALLOWED_SUFFIXES:
            problems.append(f"disallowed media/subtitle file: {rel}")
        if any(term in lower for term in DISALLOWED_PATH_TERMS):
            problems.append(f"disallowed confidential path term: {rel}")
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            problems.append(f"unexpected non-text file: {rel}")
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{label} found in {rel}")
        if rel.parts and rel.parts[0] == "data" and SOURCE_VIDEO_ID.search(text):
            problems.append(f"source video identifier found in public data: {rel}")
    if problems:
        raise SystemExit("Public-release audit failed:\n- " + "\n- ".join(problems))
    print("Public-release audit passed: no media, transcripts, source video IDs, or detected secrets.")


if __name__ == "__main__":
    main()
