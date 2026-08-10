from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.stt import Transcription
from tests.helpers import make_wav_bytes


@dataclass
class FakeRecognizer:
    """Детерминированный SpeechRecognizer: возвращает заданный текст без
    какой-либо реальной обработки audio_path."""

    text: str = "привет мир"
    language: str = "ru"
    calls: list[str] = field(default_factory=list)

    def transcribe(self, audio_path: str) -> Transcription:
        self.calls.append(audio_path)
        return Transcription(text=self.text, language=self.language)


@dataclass
class FakeSynthesizer:
    """Детерминированный SpeechSynthesizer: запоминает переданный текст,
    возвращает валидный (но фиктивный) WAV."""

    calls: list[str] = field(default_factory=list)

    def synthesize(self, text: str) -> bytes:
        self.calls.append(text)
        return make_wav_bytes()


@pytest.fixture
def fake_recognizer() -> FakeRecognizer:
    return FakeRecognizer()


@pytest.fixture
def fake_synthesizer() -> FakeSynthesizer:
    return FakeSynthesizer()


@pytest.fixture
def client(fake_recognizer: FakeRecognizer, fake_synthesizer: FakeSynthesizer):
    """TestClient с fake-бэкендами, подставленными через app.state (тот же DI-путь,
    которым в проде server.py подставляет настоящие модели)."""
    app.state.recognizer = fake_recognizer
    app.state.synthesizer = fake_synthesizer
    with TestClient(app) as test_client:
        yield test_client
    app.state.recognizer = None
    app.state.synthesizer = None
