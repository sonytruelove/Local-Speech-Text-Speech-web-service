"""Точка входа: собирает реальные STT/TTS-бэкенды и поднимает uvicorn.

Тесты используют app.main:app напрямую и никогда не выполняют этот файл —
поэтому конструирование тяжёлых моделей (сеть, CPU-инференс) живёт только
здесь, а не в app.main на уровне импорта.
"""

from __future__ import annotations

import logging

from app.config import (
    HOST,
    PORT,
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
from app.main import app
from app.stt import FasterWhisperRecognizer
from app.tts import MultiLingualSynthesizer, SileroSynthesizer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("voice-echo")


def build_app():
    log.info(
        "Загружаю faster-whisper (%s, %s, %s)...",
        WHISPER_MODEL_SIZE,
        WHISPER_COMPUTE_TYPE,
        WHISPER_DEVICE,
    )
    app.state.recognizer = FasterWhisperRecognizer(
        model_size=WHISPER_MODEL_SIZE,
        compute_type=WHISPER_COMPUTE_TYPE,
        device=WHISPER_DEVICE,
        language=WHISPER_LANGUAGE,
    )

    log.info("Загружаю Silero TTS (ru: %s, en: %s)...", SILERO_RU_MODEL_ID, SILERO_EN_MODEL_ID)
    app.state.synthesizer = MultiLingualSynthesizer(
        backends={
            "ru": SileroSynthesizer(
                language="ru",
                model_id=SILERO_RU_MODEL_ID,
                speaker=SILERO_RU_SPEAKER,
                sample_rate=SILERO_SAMPLE_RATE,
            ),
            "en": SileroSynthesizer(
                language="en",
                model_id=SILERO_EN_MODEL_ID,
                speaker=SILERO_EN_SPEAKER,
                sample_rate=SILERO_SAMPLE_RATE,
            ),
        },
        default_language=SILERO_DEFAULT_LANGUAGE,
    )

    log.info("Модели загружены, сервис готов.")
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(build_app(), host=HOST, port=PORT)
