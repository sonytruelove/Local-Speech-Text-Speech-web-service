"""Пути и константы конфигурации сервиса."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
PIPER_MODEL_PATH = BASE_DIR / "models" / "piper" / "ru_RU-dmitri-medium.onnx"

WHISPER_MODEL_SIZE = "small"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_DEVICE = "cpu"

# Только loopback: сервис рассчитан на одного локального пользователя.
HOST = "127.0.0.1"
PORT = 8000
