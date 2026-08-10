"""Пути и константы конфигурации сервиса."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
PIPER_MODEL_PATH = BASE_DIR / "models" / "piper" / "ru_RU-dmitri-medium.onnx"

WHISPER_MODEL_SIZE = "small"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_DEVICE = "cpu"

# TTS: Silero — активный бэкенд по умолчанию (естественнее Piper, ценой
# torch как зависимости). PiperSynthesizer в app/tts.py остаётся рабочим и
# протестированным — переключить обратно можно в server.py.
SILERO_LANGUAGE = "ru"
SILERO_MODEL_ID = "v4_ru"
SILERO_SPEAKER = "xenia"
SILERO_SAMPLE_RATE = 48000

# Только loopback: сервис рассчитан на одного локального пользователя.
HOST = "127.0.0.1"
PORT = 8000
