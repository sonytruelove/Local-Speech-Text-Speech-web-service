"""Пути и константы конфигурации сервиса."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
PIPER_MODEL_PATH = BASE_DIR / "models" / "piper" / "ru_RU-dmitri-medium.onnx"

WHISPER_MODEL_SIZE = "small"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_DEVICE = "cpu"
# None = автоопределение (нужны и RU, и EN). Само по себе больше не может
# уронить синтез: TTS выбирает голос по письменности РАСПОЗНАННОГО текста
# (app.tts.detect_script_language), не по этому полю, а synthesize() поверх
# любого бэкенда Silero теперь ловит его собственные исключения (см. app/tts.py).
WHISPER_LANGUAGE = None

# TTS: Silero — активный бэкенд по умолчанию (естественнее Piper, ценой
# torch как зависимости). PiperSynthesizer в app/tts.py остаётся рабочим и
# протестированным — переключить обратно можно в server.py. Две языковые
# модели (ru/en): MultiLingualSynthesizer выбирает между ними по тексту.
SILERO_SAMPLE_RATE = 48000
SILERO_RU_MODEL_ID = "v4_ru"
SILERO_RU_SPEAKER = "xenia"
SILERO_EN_MODEL_ID = "v3_en"
SILERO_EN_SPEAKER = "en_0"
SILERO_DEFAULT_LANGUAGE = "ru"

# Только loopback: сервис рассчитан на одного локального пользователя.
HOST = "127.0.0.1"
PORT = 8000
