"""Синтез речи: интерфейс + реализация на Piper."""

from __future__ import annotations

import io
import os
import shutil
import wave
from pathlib import Path
from typing import Protocol

# Файл-маркер, который пишем сами после успешного копирования bundled espeak-ng
# data — отличает "это наша полная копия" от произвольной чужой директории с
# тем же именем (см. ascii_safe_espeak_data_dir).
_COPY_MARKER_NAME = ".voice-echo-service-copy-complete"


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str) -> bytes: ...


class WavWriter(Protocol):
    def synthesize_wav(self, text: str, wav_file: wave.Wave_write) -> None: ...


class SynthesisProducedNoAudioError(RuntimeError):
    """TTS-бэкенд не сгенерировал ни одного аудио-сэмпла для переданного текста
    (например, текст состоит только из символов, для которых у бэкенда нет
    фонем — эмодзи, неподдерживаемая письменность, управляющие символы)."""


def synthesize_wav_bytes(voice: WavWriter, text: str) -> bytes:
    """Прогоняет voice.synthesize_wav через in-memory WAV-буфер и возвращает байты.

    Текст приходит от пользователя (внешний вход, см. Stage 3a), а не все
    непустые строки после strip() дают хотя бы одну фонему — Piper/espeak-ng
    в этом случае никогда не вызывает wav_file.setnchannels(...), и close()
    падает с низкоуровневым 'wave.Error: # channels not specified'. Ловим
    это и превращаем в понятную, типизированную ошибку с текстом в контексте
    вместо необработанного 500 с чужим сообщением об ошибке.
    """
    buf = io.BytesIO()
    try:
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
    except wave.Error as exc:
        raise SynthesisProducedNoAudioError(
            f"TTS-бэкенд не сгенерировал аудио: text={text!r}"
        ) from exc
    return buf.getvalue()


def ascii_safe_espeak_data_dir(bundled_dir: Path, cache_root: Path) -> Path:
    """Piper зовёт espeak-ng (скомпилированный C-код) для фонемизации, а тот
    открывает свои файлы данных через узкие (не wide-char) файловые API —
    на Windows это не может открыть путь с не-ASCII символами и тихо падает
    на путь, зашитый при сборке пакета (см. регрессию в тестах: без этой
    функции phonemize() на кириллическом пути молча возвращает 0 фонем вместо
    ошибки). Если путь к бандлу не ASCII, копируем данные один раз в
    cache_root/espeak-ng-data — оттуда espeak-ng их откроет нормально.

    Каталог обязательно свой (не голое "espeak-ng-data" в cache_root): на этой
    же машине уже может стоять другой espeak-ng с директорией такого же имени,
    но с другим (неполным для наших голосов) набором данных — маркер-файл,
    который пишем сами, отличает "это наша полная копия" от чужой находки с
    тем же путём.
    """
    if str(bundled_dir).isascii():
        return bundled_dir

    cache_dir = cache_root / "voice-echo-service" / "espeak-ng-data"
    marker = cache_dir / _COPY_MARKER_NAME
    if not marker.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(bundled_dir, cache_dir, dirs_exist_ok=True)
        marker.touch()
    return cache_dir


class PiperSynthesizer:
    """SpeechSynthesizer поверх piper.PiperVoice."""

    def __init__(self, model_path: str) -> None:
        from piper import PiperVoice
        from piper.phonemize_espeak import ESPEAK_DATA_DIR

        cache_root = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        data_dir = ascii_safe_espeak_data_dir(ESPEAK_DATA_DIR, cache_root)
        self._voice = PiperVoice.load(model_path, espeak_data_dir=str(data_dir))

    def synthesize(self, text: str) -> bytes:
        return synthesize_wav_bytes(self._voice, text)
