def test_synthesize_returns_wav_audio_for_given_text(client, fake_synthesizer):
    response = client.post("/api/synthesize", json={"text": "привет"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content
    assert fake_synthesizer.calls == ["привет"]


def test_synthesize_rejects_empty_text_with_400(client, fake_synthesizer):
    response = client.post("/api/synthesize", json={"text": ""})

    assert response.status_code == 400
    assert fake_synthesizer.calls == []


def test_synthesize_rejects_whitespace_only_text_with_400(client, fake_synthesizer):
    response = client.post("/api/synthesize", json={"text": "   "})

    assert response.status_code == 400
    assert fake_synthesizer.calls == []


def test_synthesize_strips_surrounding_whitespace_before_calling_backend(client, fake_synthesizer):
    client.post("/api/synthesize", json={"text": "  привет  "})
    assert fake_synthesizer.calls == ["привет"]


def test_synthesize_missing_text_field_returns_422(client, fake_synthesizer):
    response = client.post("/api/synthesize", json={})

    assert response.status_code == 422
    assert fake_synthesizer.calls == []


def test_synthesize_returns_422_when_backend_produces_no_audio(client, fake_synthesizer):
    """Не всякий непустой (после strip) текст даёт бэкенду хоть одну фонему —
    см. app.tts.SynthesisProducedNoAudioError. Должен быть понятный 422, а не
    необработанное исключение (500 с чужим сообщением в логах)."""

    def raise_no_audio(text: str) -> bytes:
        from app.tts import SynthesisProducedNoAudioError

        raise SynthesisProducedNoAudioError(f"TTS-бэкенд не сгенерировал аудио: text={text!r}")

    fake_synthesizer.synthesize = raise_no_audio

    response = client.post("/api/synthesize", json={"text": "🙂🙂🙂"})

    assert response.status_code == 422
