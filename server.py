"""Точка входа: собирает реальные STT/TTS-бэкенды и поднимает uvicorn.

Тесты используют app.main:app напрямую и никогда не выполняют этот файл —
поэтому конструирование тяжёлых моделей (сеть, CPU-инференс) живёт только
здесь, а не в app.main на уровне импорта.
"""

from __future__ import annotations

import logging

from app.config import (
    HOST,
    PIPER_MODEL_PATH,
    PORT,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_MODEL_SIZE,
)
from app.main import app
from app.stt import FasterWhisperRecognizer
from app.tts import PiperSynthesizer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("voice-echo")


def build_app():
    if not PIPER_MODEL_PATH.exists():
        raise RuntimeError(
            f"Не найдена модель Piper: {PIPER_MODEL_PATH}. "
            "Запустите download_models.ps1 перед стартом сервера."
        )

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

    log.info("Загружаю голос Piper: %s", PIPER_MODEL_PATH.name)
    app.state.synthesizer = PiperSynthesizer(str(PIPER_MODEL_PATH))

    log.info("Модели загружены, сервис готов.")
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(build_app(), host=HOST, port=PORT)
