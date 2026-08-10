# Voice Echo — локальный STT → TTS сервис

Веб-сервис "голосовое эхо": говорите в микрофон (кнопки «Старт» / «Стоп» в
браузере), сервис распознаёт речь и озвучивает тот же текст обратно. Всё
считается локально, на CPU, без внешних API и без отправки аудио куда-либо —
рассчитано на слабое железо (0.5 ГБ VRAM / 8 ГБ RAM, GPU не используется).

## Используемые модели

| Задача | Модель | Движок | Заметки |
|---|---|---|---|
| Speech-to-Text | `faster-whisper` (`small`, int8, CPU) | CTranslate2 | Скачивается автоматически из Hugging Face (`Systran/faster-whisper-small`) при первом запуске |
| Text-to-Speech | **Silero TTS** (`v4_ru`, голос `xenia`, 48 кГц) — активный бэкенд | torch (CPU) | Скачивается автоматически через `torch.hub` при первом запуске |

**Альтернативный TTS-бэкенд:** Piper (`ru_RU-dmitri-medium`, ONNX Runtime,
легче по ресурсам) — код и тесты остаются в `app/tts.py` (`PiperSynthesizer`),
но по умолчанию не используется: субъективно менее естественный голос.
Переключить обратно — поменять `SileroSynthesizer` на `PiperSynthesizer` в
`server.py`. Голос Piper (если нужен) качается через `download_models.ps1`.

**Известное ограничение:** даже с Silero качество озвучки может требовать
дальнейшей доработки под конкретный вкус — следующий кандидат на замену,
если Silero тоже не устроит, — более крупная/другая модель STT или TTS.

## Быстрый старт (Windows)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python server.py
```

Открыть `http://127.0.0.1:8000`, разрешить доступ к микрофону. Модели (Silero,
faster-whisper) скачаются сами при первом запуске — нужен интернет один раз.

Если хотите попробовать Piper вместо Silero — дополнительно понадобится
`.\download_models.ps1` (качает голос `ru_RU-dmitri-medium`).

## Тесты

```powershell
pip install -r requirements-dev.txt
pytest
```

Быстрый набор (юнит + API + Gherkin-сценарии) работает на fake-моделях, без
сети. Прогон с реальными моделями — `pytest -m real_models` (качает модели,
медленнее). Конвенции и security baseline проекта — см. `CLAUDE.md`.

## Архитектура

- `app/stt.py`, `app/tts.py` — `Protocol`-интерфейсы `SpeechRecognizer` /
  `SpeechSynthesizer` + реальные реализации (faster-whisper; Silero и Piper
  для TTS — оба реализуют один интерфейс, активный выбирается в `server.py`).
- `app/main.py` — FastAPI-приложение, зависимости внедряются через
  `app.state` (DI), поэтому тесты подставляют fake-бэкенды.
- `server.py` — точка входа: собирает реальные модели и поднимает `uvicorn`.
- `static/` — фронтенд (MediaRecorder API, без фреймворков).
