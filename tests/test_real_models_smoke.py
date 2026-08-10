"""Ручная сквозная проверка с настоящими моделями (не fake).

Пропускается по умолчанию (см. pyproject.toml: addopts = -m "not real_models") —
faster-whisper и Silero качают модели при первом запуске (сеть), Piper
дополнительно требует download_models.ps1. Запуск вручную: pytest -m real_models
"""

from __future__ import annotations

import pytest

from app.config import (
    PIPER_MODEL_PATH,
    SILERO_LANGUAGE,
    SILERO_MODEL_ID,
    SILERO_SAMPLE_RATE,
    SILERO_SPEAKER,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_MODEL_SIZE,
)


@pytest.mark.real_models
def test_real_piper_synthesizer_produces_playable_wav():
    from app.tts import PiperSynthesizer

    if not PIPER_MODEL_PATH.exists():
        pytest.skip("Piper-модель не скачана — запустите download_models.ps1")

    synthesizer = PiperSynthesizer(str(PIPER_MODEL_PATH))
    wav_bytes = synthesizer.synthesize("Проверка синтеза речи")

    assert wav_bytes[:4] == b"RIFF"
    assert len(wav_bytes) > 1000


@pytest.mark.real_models
def test_real_silero_synthesizer_produces_playable_wav():
    from app.tts import SileroSynthesizer

    synthesizer = SileroSynthesizer(
        language=SILERO_LANGUAGE,
        model_id=SILERO_MODEL_ID,
        speaker=SILERO_SPEAKER,
        sample_rate=SILERO_SAMPLE_RATE,
    )
    wav_bytes = synthesizer.synthesize("Проверка синтеза речи через Silero")

    assert wav_bytes[:4] == b"RIFF"
    assert len(wav_bytes) > 1000


@pytest.mark.real_models
def test_real_whisper_recognizer_transcribes_silero_generated_wav(tmp_path):
    from app.stt import FasterWhisperRecognizer
    from app.tts import SileroSynthesizer

    synthesizer = SileroSynthesizer(
        language=SILERO_LANGUAGE,
        model_id=SILERO_MODEL_ID,
        speaker=SILERO_SPEAKER,
        sample_rate=SILERO_SAMPLE_RATE,
    )
    wav_bytes = synthesizer.synthesize("Проверка распознавания речи")
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(wav_bytes)

    recognizer = FasterWhisperRecognizer(
        model_size=WHISPER_MODEL_SIZE,
        compute_type=WHISPER_COMPUTE_TYPE,
        device=WHISPER_DEVICE,
    )
    result = recognizer.transcribe(str(wav_path))

    assert isinstance(result.text, str)
    assert len(result.text) > 0
