"""Безопасная работа с временными аудио-файлами загрузок."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class EmptyAudioError(ValueError):
    """Загруженный файл записи пуст (0 байт)."""


@contextmanager
def temp_audio_file(data: bytes, suffix: str = ".webm") -> Iterator[str]:
    """Пишет data во временный файл с фиксированным суффиксом и удаляет его при выходе.

    Суффикс всегда фиксирован (не берётся из имени файла клиента), чтобы имя
    загрузки не влияло на путь на диске.
    """
    if not data:
        raise EmptyAudioError(f"Загруженный файл записи пуст (0 байт), suffix={suffix!r}")

    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        yield path
    finally:
        Path(path).unlink(missing_ok=True)
