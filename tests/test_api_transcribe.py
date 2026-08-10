def test_transcribe_returns_recognized_text_and_language(client, fake_recognizer):
    fake_recognizer.text = "привет мир"
    fake_recognizer.language = "ru"

    response = client.post(
        "/api/transcribe",
        files={"file": ("speech.webm", b"non-empty-audio-bytes", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "привет мир", "language": "ru"}
    assert len(fake_recognizer.calls) == 1


def test_transcribe_rejects_empty_upload_with_400(client):
    response = client.post(
        "/api/transcribe",
        files={"file": ("speech.webm", b"", "audio/webm")},
    )
    assert response.status_code == 400


def test_transcribe_missing_file_field_returns_422(client):
    response = client.post("/api/transcribe")
    assert response.status_code == 422


def test_transcribe_silence_returns_empty_text_and_never_calls_synthesizer(
    client, fake_recognizer, fake_synthesizer
):
    fake_recognizer.text = ""
    fake_recognizer.language = "ru"

    response = client.post(
        "/api/transcribe",
        files={"file": ("speech.webm", b"silence-bytes", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json()["text"] == ""
    assert fake_synthesizer.calls == []
