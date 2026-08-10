"""Stage 3a п.4 в этом сервисе не про 'следующий номер' (стейта с гонкой нет),
а про сам объект модели: ctranslate2/onnxruntime не документируют потокобезопасность
при параллельных вызовах из нескольких потоков одновременно. app.state.inference_lock
в app/main.py защищает от параллельного входа в model.transcribe/model.synthesize —
этот тест это доказывает, а не молчаливо предполагает.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@dataclass
class SlowFakeSynthesizer:
    """Фиксирует, пересекались ли вызовы synthesize() во времени."""

    busy: bool = False
    overlap_detected: bool = False
    call_count: int = 0
    calls: list[str] = field(default_factory=list)

    def synthesize(self, text: str) -> bytes:
        if self.busy:
            self.overlap_detected = True
        self.busy = True
        time.sleep(0.03)
        self.call_count += 1
        self.calls.append(text)
        self.busy = False
        return b"RIFF----WAVEfmt fake"


@pytest.mark.asyncio
async def test_concurrent_synthesize_requests_never_overlap_in_backend():
    synth = SlowFakeSynthesizer()
    app.state.synthesizer = synth
    app.state.recognizer = None

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            responses = await asyncio.gather(
                *[ac.post("/api/synthesize", json={"text": f"фраза {i}"}) for i in range(8)]
            )
    finally:
        app.state.synthesizer = None

    assert [r.status_code for r in responses] == [200] * 8
    assert synth.call_count == 8
    assert not synth.overlap_detected
