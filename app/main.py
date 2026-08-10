"""FastAPI-приложение: тонкие обработчики поверх STT/TTS через DI.

Реальные модели (FasterWhisperRecognizer/PiperSynthesizer) сюда не
импортируются напрямую и не создаются на старте приложения — это делает
entrypoint (см. __main__.py), присваивая их в app.state. Так тесты могут
подставить fake-реализации в app.state, ни разу не коснувшись сети/тяжёлых
моделей.
"""

from __future__ import annotations

import asyncio
import io

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.audio_io import EmptyAudioError, temp_audio_file
from app.config import STATIC_DIR
from app.stt import SpeechRecognizer
from app.tts import SpeechSynthesizer, SynthesisProducedNoAudioError

app = FastAPI(title="Voice Echo: faster-whisper -> Piper")
app.state.recognizer = None
app.state.synthesizer = None
app.state.inference_lock = asyncio.Lock()


def get_recognizer(request: Request) -> SpeechRecognizer:
    recognizer = request.app.state.recognizer
    if recognizer is None:
        raise HTTPException(503, "Распознаватель речи не инициализирован")
    return recognizer


def get_synthesizer(request: Request) -> SpeechSynthesizer:
    synthesizer = request.app.state.synthesizer
    if synthesizer is None:
        raise HTTPException(503, "Синтезатор речи не инициализирован")
    return synthesizer


def get_inference_lock(request: Request) -> asyncio.Lock:
    return request.app.state.inference_lock


class TranscriptionResponse(BaseModel):
    text: str
    language: str


@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    file: UploadFile = File(...),
    recognizer: SpeechRecognizer = Depends(get_recognizer),
    lock: asyncio.Lock = Depends(get_inference_lock),
) -> TranscriptionResponse:
    audio_bytes = await file.read()
    try:
        with temp_audio_file(audio_bytes) as path:
            async with lock:
                result = await asyncio.to_thread(recognizer.transcribe, path)
    except EmptyAudioError as exc:
        raise HTTPException(400, str(exc)) from exc
    return TranscriptionResponse(text=result.text, language=result.language)


class SynthesizeRequest(BaseModel):
    text: str


@app.post("/api/synthesize")
async def synthesize(
    req: SynthesizeRequest,
    synthesizer: SpeechSynthesizer = Depends(get_synthesizer),
    lock: asyncio.Lock = Depends(get_inference_lock),
) -> StreamingResponse:
    text = req.text.strip()
    if not text:
        raise HTTPException(400, f"Пустой текст для озвучки: text={req.text!r}")

    try:
        async with lock:
            wav_bytes = await asyncio.to_thread(synthesizer.synthesize, text)
    except SynthesisProducedNoAudioError as exc:
        raise HTTPException(422, str(exc)) from exc
    return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav")


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
