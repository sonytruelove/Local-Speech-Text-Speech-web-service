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
    SILERO_LANGUAGE,
    SILERO_MODEL_ID,
    SILERO_SAMPLE_RATE,
    SILERO_SPEAKER,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_MODEL_SIZE,
)
from app.main import app
from app.stt import FasterWhisperRecognizer
from app.tts import SileroSynthesizer

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
    )

    log.info("Загружаю Silero TTS (%s, speaker=%s)...", SILERO_MODEL_ID, SILERO_SPEAKER)
    app.state.synthesizer = SileroSynthesizer(
        language=SILERO_LANGUAGE,
        model_id=SILERO_MODEL_ID,
        speaker=SILERO_SPEAKER,
        sample_rate=SILERO_SAMPLE_RATE,
    )

    log.info("Модели загружены, сервис готов.")
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(build_app(), host=HOST, port=PORT)
