"""Регрессия из живого прогона: пользователь сказал по-английски, faster-whisper
распознал это как EN, а единственный (русский) голос Silero упал с ValueError
на попытке озвучить английский текст. detect_script_language + MultiLingualSynthesizer
выбирают язык-специфичный бэкенд по самому тексту, не полагаясь на то, что
Whisper-детект языка вообще совпадёт с набором поддерживаемых голосов.
"""

from dataclasses import dataclass, field

import pytest

from app.tts import MultiLingualSynthesizer, detect_script_language


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Привет, как дела?", "ru"),
        ("Hello, how are you?", "en"),
        ("Mix кириллицы and latin", "ru"),  # хотя бы одна кириллическая буква -> ru
        ("", "en"),  # нет кириллицы вообще -> дефолт en
        ("12345 !?.", "en"),
    ],
)
def test_detect_script_language(text: str, expected: str) -> None:
    assert detect_script_language(text) == expected


@dataclass
class _FakeBackend:
    calls: list[str] = field(default_factory=list)

    def synthesize(self, text: str) -> bytes:
        self.calls.append(text)
        return b"RIFF" + text.encode("utf-8")


def test_multilingual_synthesizer_routes_cyrillic_text_to_ru_backend():
    ru, en = _FakeBackend(), _FakeBackend()
    synth = MultiLingualSynthesizer(backends={"ru": ru, "en": en}, default_language="ru")

    synth.synthesize("Привет, мир")

    assert ru.calls == ["Привет, мир"]
    assert en.calls == []


def test_multilingual_synthesizer_routes_latin_text_to_en_backend():
    ru, en = _FakeBackend(), _FakeBackend()
    synth = MultiLingualSynthesizer(backends={"ru": ru, "en": en}, default_language="ru")

    synth.synthesize("Hello, world")

    assert en.calls == ["Hello, world"]
    assert ru.calls == []


def test_multilingual_synthesizer_falls_back_to_default_when_backend_missing():
    ru = _FakeBackend()
    synth = MultiLingualSynthesizer(backends={"ru": ru}, default_language="ru")

    synth.synthesize("Hello, world")  # en-текст, но en-бэкенда нет в словаре

    assert ru.calls == ["Hello, world"]
