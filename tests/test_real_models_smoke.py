"""Ручная сквозная проверка с настоящими моделями (не fake).

Пропускается по умолчанию (см. pyproject.toml: addopts = -m "not real_models") —
faster-whisper и Silero качают модели при первом запуске (сеть), Piper
дополнительно требует download_models.ps1. Запуск вручную: pytest -m real_models
"""

from __future__ import annotations

import pytest

from app.config import (
    PIPER_MODEL_PATH,
    SILERO_DEFAULT_LANGUAGE,
    SILERO_EN_MODEL_ID,
    SILERO_EN_SPEAKER,
    SILERO_RU_MODEL_ID,
    SILERO_RU_SPEAKER,
    SILERO_SAMPLE_RATE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_LANGUAGE,
    WHISPER_MODEL_SIZE,
)


def _build_ru_synthesizer():
    from app.tts import SileroSynthesizer

    return SileroSynthesizer(
        language="ru",
        model_id=SILERO_RU_MODEL_ID,
        speaker=SILERO_RU_SPEAKER,
        sample_rate=SILERO_SAMPLE_RATE,
    )


def _build_en_synthesizer():
    from app.tts import SileroSynthesizer

    return SileroSynthesizer(
        language="en",
        model_id=SILERO_EN_MODEL_ID,
        speaker=SILERO_EN_SPEAKER,
        sample_rate=SILERO_SAMPLE_RATE,
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
def test_real_silero_ru_synthesizer_produces_playable_wav():
    wav_bytes = _build_ru_synthesizer().synthesize("Проверка синтеза речи через Silero")

    assert wav_bytes[:4] == b"RIFF"
    assert len(wav_bytes) > 1000


@pytest.mark.real_models
def test_real_silero_en_synthesizer_produces_playable_wav():
    wav_bytes = _build_en_synthesizer().synthesize("This is a Silero speech synthesis check.")

    assert wav_bytes[:4] == b"RIFF"
    assert len(wav_bytes) > 1000


@pytest.mark.real_models
def test_real_multilingual_synthesizer_picks_backend_by_script():
    from app.tts import MultiLingualSynthesizer

    synthesizer = MultiLingualSynthesizer(
        backends={"ru": _build_ru_synthesizer(), "en": _build_en_synthesizer()},
        default_language=SILERO_DEFAULT_LANGUAGE,
    )

    ru_wav = synthesizer.synthesize("Привет, это проверка на русском.")
    en_wav = synthesizer.synthesize("Hello, this is a check in English.")

    assert ru_wav[:4] == b"RIFF"
    assert en_wav[:4] == b"RIFF"


@pytest.mark.real_models
def test_real_whisper_recognizer_transcribes_silero_generated_wav(tmp_path):
    from app.stt import FasterWhisperRecognizer

    wav_bytes = _build_ru_synthesizer().synthesize("Проверка распознавания речи")
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(wav_bytes)

    recognizer = FasterWhisperRecognizer(
        model_size=WHISPER_MODEL_SIZE,
        compute_type=WHISPER_COMPUTE_TYPE,
        device=WHISPER_DEVICE,
        language=WHISPER_LANGUAGE,
    )
    result = recognizer.transcribe(str(wav_path))

    assert isinstance(result.text, str)
    assert len(result.text) > 0
