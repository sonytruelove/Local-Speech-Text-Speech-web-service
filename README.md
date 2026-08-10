# Voice Echo — локальный STT → TTS сервис

Веб-сервис "голосовое эхо": говорите в микрофон (кнопки «Старт» / «Стоп» в
браузере), сервис распознаёт речь и озвучивает тот же текст обратно. Всё
считается локально, на CPU, без внешних API и без отправки аудио куда-либо —
рассчитано на слабое железо (0.5 ГБ VRAM / 8 ГБ RAM, GPU не используется).

## Используемые модели

| Задача | Модель | Движок | Заметки |
|---|---|---|---|
| Speech-to-Text | `faster-whisper` (`small`, int8, CPU) | CTranslate2 | Скачивается автоматически из Hugging Face (`Systran/faster-whisper-small`) при первом запуске |
| Text-to-Speech | Piper, голос `ru_RU-dmitri-medium` | ONNX Runtime | Скачивается через `download_models.ps1` из `rhasspy/piper-voices` |

**Известное ограничение:** качество текущей связки STT/TTS требует доработки —
будет пересмотрено в одной из следующих итераций (замена модели/голоса на
более точный или более естественный вариант).

## Быстрый старт (Windows)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\download_models.ps1
python server.py
```

Открыть `http://127.0.0.1:8000`, разрешить доступ к микрофону.

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
  `SpeechSynthesizer` + реальные реализации на faster-whisper/Piper.
- `app/main.py` — FastAPI-приложение, зависимости внедряются через
  `app.state` (DI), поэтому тесты подставляют fake-бэкенды.
- `server.py` — точка входа: собирает реальные модели и поднимает `uvicorn`.
- `static/` — фронтенд (MediaRecorder API, без фреймворков).
