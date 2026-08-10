"""Статическая проверка Stage 3a #2 (XSS): распознанный текст — это чужой,
не доверенный ввод (речь пользователя), поэтому он обязан попадать в DOM
только через textContent, никогда через innerHTML.

Это не полноценный live-рендер в браузере (в проекте нет JS-тест-раннера/
Playwright) — намеренное ограничение объёма, см. отчёт Stage 5. Проверка
статическая: ищет в исходнике сам небезопасный паттерн присвоения.
"""

from pathlib import Path

APP_JS = Path(__file__).resolve().parent.parent / "static" / "app.js"


def test_transcript_rendered_via_textcontent_not_innerhtml():
    source = APP_JS.read_text(encoding="utf-8")

    assert "transcriptEl.textContent" in source
    assert ".innerHTML" not in source
    assert "insertAdjacentHTML" not in source
    assert "document.write" not in source
