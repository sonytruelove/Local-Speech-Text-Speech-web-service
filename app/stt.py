"""Распознавание речи: интерфейс + реализация на faster-whisper."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str


class SpeechSegment(Protocol):
    text: str


class SpeechRecognizer(Protocol):
    def transcribe(self, audio_path: str) -> Transcription: ...


def join_segments(segments: Iterable[SpeechSegment]) -> str:
    """Склеивает сегменты faster-whisper в одну строку без крайних пробелов."""
    return "".join(segment.text for segment in segments).strip()


class FasterWhisperRecognizer:
    """SpeechRecognizer поверх faster_whisper.WhisperModel (CPU, int8)."""

    def __init__(self, model_size: str, compute_type: str, device: str) -> None:
        from faster_whisper import WhisperModel

        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> Transcription:
        segments, info = self._model.transcribe(audio_path, vad_filter=True)
        return Transcription(text=join_segments(segments), language=info.language)
