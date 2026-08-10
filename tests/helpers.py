"""Небольшие фабрики валидных WAV-байтов для тестов (не настоящие модели)."""

from __future__ import annotations

import io
import wave


def make_wav_bytes(duration_ms: int = 200, sample_rate: int = 16000) -> bytes:
    n_frames = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * n_frames)
    return buf.getvalue()
