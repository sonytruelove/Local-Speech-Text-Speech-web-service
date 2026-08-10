import io
import wave

import pytest

from app.tts import SynthesisProducedNoAudioError, synthesize_wav_bytes


class _FakeVoice:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def synthesize_wav(self, text: str, wav_file: wave.Wave_write) -> None:
        self.calls.append(text)
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x01" * 50)


class _SilentVoice:
    """Как настоящий Piper на непроизносимом тексте: ни одного чанка, поэтому
    wav_file.setnchannels(...) никогда не вызывается."""

    def synthesize_wav(self, text: str, wav_file: wave.Wave_write) -> None:
        pass


def test_synthesize_wav_bytes_passes_text_through_to_voice():
    voice = _FakeVoice()
    synthesize_wav_bytes(voice, "тестовая фраза")
    assert voice.calls == ["тестовая фраза"]


def test_synthesize_wav_bytes_returns_parseable_wav_with_voice_params():
    voice = _FakeVoice()
    result = synthesize_wav_bytes(voice, "текст")

    assert result[:4] == b"RIFF"
    with wave.open(io.BytesIO(result)) as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == 50


def test_synthesize_wav_bytes_raises_clear_error_when_backend_writes_no_audio():
    voice = _SilentVoice()

    with pytest.raises(SynthesisProducedNoAudioError, match="непроизносимый текст"):
        synthesize_wav_bytes(voice, "непроизносимый текст")
